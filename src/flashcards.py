"""
Flashcards avec algorithme SM-2 (SuperMemo 2)
=============================================
Génère des flashcards depuis les concepts analysés via l'IA,
puis planifie les révisions avec l'algorithme de répétition espacée SM-2.

SM-2 : https://en.wikipedia.org/wiki/SuperMemo#Description_of_SM-2_algorithm
"""

import json
import math
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import google.generativeai as genai
import os


DATA_FILE = Path("data/flashcards.json")


# ── SM-2 Algorithm ──────────────────────────────────────────────────

def sm2(quality: int, repetitions: int, easiness: float, interval: int) -> Tuple[int, float, int]:
    """
    Algorithme SM-2 de répétition espacée.

    Args:
        quality: Note de qualité de la réponse (0-5)
            0 — Réponse complètement oubliée
            1 — Réponse incorrecte, souvenir vague
            2 — Réponse incorrecte, mais se souvient partiellement
            3 — Réponse correcte avec difficulté
            4 — Réponse correcte après hésitation
            5 — Réponse parfaite
        repetitions: Nombre de bonnes réponses consécutives
        easiness: Facteur de facilité (EF >= 1.3)
        interval: Intervalle actuel en jours

    Returns:
        (new_repetitions, new_easiness, new_interval)
    """
    if quality < 0:
        quality = 0
    if quality > 5:
        quality = 5

    # Mise à jour du facteur de facilité
    new_easiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_easiness = max(1.3, new_easiness)

    if quality < 3:
        # Réponse incorrecte — on repart à zéro
        new_repetitions = 0
        new_interval = 1
    else:
        # Réponse correcte
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = int(math.ceil(interval * new_easiness))

    return new_repetitions, new_easiness, new_interval


# ── Flashcard Manager ────────────────────────────────────────────────

class FlashcardManager:
    """Gère la création, le stockage et la révision SM-2 des flashcards."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3-pro-preview"):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = model
        self.data_file = DATA_FILE
        self.model = None

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)

        self.cards = self._load()

    # ── Persistence ──

    def _load(self) -> List[Dict]:
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.cards, f, indent=2, ensure_ascii=False)

    # ── Génération IA ──

    def generate_from_concepts(self, concepts: List[Dict],
                                module: str = None,
                                num_cards: int = 10) -> int:
        """
        Génère des flashcards depuis les concepts via l'IA.
        Évite les doublons (même concept_id).

        Returns:
            Nombre de nouvelles cartes créées.
        """
        existing_ids = {c.get('concept_id') for c in self.cards}

        filtered = concepts
        if module:
            filtered = [c for c in concepts if c.get('module') == module]

        # Ne garder que les concepts sans flashcard existante
        candidates = [c for c in filtered if c.get('id') not in existing_ids]
        if not candidates:
            return 0

        selected = random.sample(candidates, min(num_cards, len(candidates)))

        created = 0
        for concept in selected:
            cards = self._generate_cards_for_concept(concept)
            for card in cards:
                self.cards.append(card)
                created += 1

        self._save()
        return created

    def _generate_cards_for_concept(self, concept: Dict) -> List[Dict]:
        """Génère 2 à 4 flashcards PREMIUM pour un concept donné — orientation Énergie."""
        try:
            module = concept.get('module', 'N/A')
            keywords = concept.get('keywords', [])
            page_ref = concept.get('page_references', '')
            source_doc = concept.get('source_document', '')

            # Contexte module enrichi
            module_context = {
                "AA01": "Conduite d'équipe sur chantier de réseau",
                "AA02": "Formation des apprentis électriciens de réseau",
                "AA03": "Préparation de chantier : plans, matériel, logistique",
                "AA04": "Gestion de mandat : offre, exécution, facturation",
                "AA05": "Sécurité : 5 règles, EPI, SUVA, consignation",
                "AA06": "Contrôle qualité et conformité des travaux",
                "AA07": "Stratégies de maintenance : préventive, corrective, prédictive",
                "AA08": "Maintenance des équipements de réseau MT/BT",
                "AA09": "Électrotechnique : Ohm, Kirchhoff, triphasé, puissances",
                "AA10": "Mécanique : forces, moments, supports de lignes",
                "AA11": "Mathématiques appliquées : trigonométrie, géométrie",
                "AE01": "Étude de projet réseau : dimensionnement, chute de tension",
                "AE02": "Sécurité sur installations électriques sous tension",
                "AE03": "Éclairage public : normes EN 13201, LED, lux",
                "AE04": "Documentation réseaux : SIG/GIS, schémas unifilaires",
                "AE05": "Mise à terre : piquet, résistance de terre, TN/TT/IT",
                "AE06": "Exploitation de réseaux MT/BT : manœuvres, perturbations",
                "AE07": "Technique de mesure : mégohmmètre, boucle de défaut",
                "AE09": "Protection : fusibles, disjoncteurs, sélectivité, Ik",
                "AE10": "Maintenance des réseaux : contrôles périodiques, localisation de défauts",
                "AE11": "Travail de projet : gestion de A à Z, présentation",
                "AE12": "Lignes souterraines : câbles, jonctions, pose en tranchée",
                "AE13": "Lignes aériennes : supports, conducteurs ACSR, portées",
            }.get(module, "Spécialiste de réseau orientation Énergie")

            prompt = f"""Tu es un formateur expert du CIFER pour le Brevet Fédéral Spécialiste de Réseau, orientation ÉNERGIE (Suisse).

Génère des flashcards de HAUTE QUALITÉ pour mémoriser ce concept technique.

**Concept :** {concept.get('name', 'N/A')}
**Description :** {concept.get('description', 'N/A')}
**Module :** {module} — {module_context}
**Mots-clés techniques :** {', '.join(keywords) if keywords else 'N/A'}
**Référence cours :** {page_ref if page_ref else 'N/A'}
**Document source :** {source_doc if source_doc else 'N/A'}

Génère entre 2 et 4 flashcards avec des ANGLES DIFFÉRENTS parmi :
1. **Définition technique précise** — terme métier + définition exacte avec unités/valeurs
2. **Valeur normative à retenir** — norme (NIBT, ESTI, SUVA, EN) + valeur/seuil/limite
3. **Application pratique terrain** — situation concrète de travail sur réseau → action/procédure
4. **Formule ou calcul** — formule avec variables et unités, exemple numérique rapide
5. **Distinction/comparaison** — différence entre deux concepts souvent confondus

EXIGENCES DE QUALITÉ :
- Front : question COURTE mais PRÉCISE (1-2 phrases max) — PAS de "Qu'est-ce que..." trop vague
- Back : réponse COMPLÈTE mais CONCISE (2-5 phrases), avec les VALEURS NUMÉRIQUES et NORMES quand applicable
- Hint : un seul MOT-CLÉ technique ou début de réponse qui aide sans tout révéler
- Utiliser le vocabulaire MÉTIER suisse romand (consignation, DDR, mégohmmètre, manœuvre, etc.)
- Chaque carte doit être AUTONOME (compréhensible sans les autres)

Réponds en JSON strict (liste) :
[
  {{
    "front": "Question technique précise et ciblée",
    "back": "Réponse complète avec valeurs/normes/formules si applicable",
    "hint": "Un mot-clé technique ou indice",
    "card_type": "definition|norme|pratique|formule|comparaison"
  }}
]

IMPORTANT : Tout en français. Niveau professionnel. Pas de carte triviale."""
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()

            raw_cards = json.loads(text)
            if not isinstance(raw_cards, list):
                raw_cards = [raw_cards]

            now = datetime.now().isoformat()
            result = []
            for rc in raw_cards:
                # Validation qualité : rejeter les cartes trop courtes
                front = rc.get('front', '')
                back = rc.get('back', '')
                if len(front) < 15 or len(back) < 20:
                    continue
                
                card = {
                    "id": f"fc_{concept.get('id', 'x')}_{len(self.cards) + len(result)}",
                    "concept_id": concept.get('id'),
                    "concept_name": concept.get('name'),
                    "module": concept.get('module'),
                    "front": front,
                    "back": back,
                    "hint": rc.get('hint', ''),
                    "card_type": rc.get('card_type', 'definition'),
                    "source_ref": f"{source_doc} {page_ref}".strip(),
                    # SM-2 state
                    "repetitions": 0,
                    "easiness": 2.5,
                    "interval": 1,
                    "next_review": now,
                    "last_reviewed": None,
                    "review_count": 0,
                    "created_at": now,
                }
                result.append(card)
            return result

        except Exception as e:
            print(f"Erreur génération flashcard: {e}")
            # Fallback
            now = datetime.now().isoformat()
            return [{
                "id": f"fc_{concept.get('id', 'x')}_{len(self.cards)}",
                "concept_id": concept.get('id'),
                "concept_name": concept.get('name'),
                "module": concept.get('module'),
                "front": f"Qu'est-ce que '{concept.get('name', '?')}' ?",
                "back": concept.get('description', 'Pas de description disponible.'),
                "hint": concept.get('name', '')[:20],
                "repetitions": 0,
                "easiness": 2.5,
                "interval": 1,
                "next_review": now,
                "last_reviewed": None,
                "review_count": 0,
                "created_at": now,
            }]

    # ── Révision SM-2 ──

    def review_card(self, card_id: str, quality: int):
        """
        Enregistre la révision d'une carte avec la note de qualité SM-2.
        Met à jour les paramètres SM-2 et planifie la prochaine révision.
        """
        for card in self.cards:
            if card['id'] == card_id:
                reps, ef, interval = sm2(
                    quality=quality,
                    repetitions=card['repetitions'],
                    easiness=card['easiness'],
                    interval=card['interval']
                )
                card['repetitions'] = reps
                card['easiness'] = round(ef, 2)
                card['interval'] = interval
                card['next_review'] = (datetime.now() + timedelta(days=interval)).isoformat()
                card['last_reviewed'] = datetime.now().isoformat()
                card['review_count'] = card.get('review_count', 0) + 1
                break

        self._save()

    # ── Files de révision ──

    def get_due_cards(self, module: str = None, limit: int = 20) -> List[Dict]:
        """Retourne les cartes dont la révision est due (next_review <= maintenant)."""
        now = datetime.now().isoformat()
        due = [c for c in self.cards if c.get('next_review', '') <= now]

        if module:
            due = [c for c in due if c.get('module') == module]

        # Trier : les moins révisées d'abord, puis par easiness croissant (plus difficiles d'abord)
        due.sort(key=lambda c: (c.get('easiness', 2.5), c.get('review_count', 0)))
        return due[:limit]

    def get_new_cards(self, module: str = None, limit: int = 5) -> List[Dict]:
        """Retourne les cartes jamais révisées."""
        new = [c for c in self.cards if c.get('review_count', 0) == 0]
        if module:
            new = [c for c in new if c.get('module') == module]
        return new[:limit]

    # ── Statistiques ──

    def get_stats(self) -> Dict:
        """Statistiques globales des flashcards."""
        if not self.cards:
            return {
                'total_cards': 0,
                'due_today': 0,
                'new_cards': 0,
                'mastered': 0,
                'learning': 0,
                'average_easiness': 0,
                'modules': {},
                'review_streak': 0,
            }

        now = datetime.now().isoformat()
        due = [c for c in self.cards if c.get('next_review', '') <= now]
        new = [c for c in self.cards if c.get('review_count', 0) == 0]
        mastered = [c for c in self.cards if c.get('interval', 0) >= 21]  # 3+ semaines
        learning = [c for c in self.cards if 0 < c.get('review_count', 0) and c.get('interval', 0) < 21]

        # Stats par module
        modules = defaultdict(lambda: {'total': 0, 'due': 0, 'mastered': 0})
        for c in self.cards:
            mod = c.get('module', 'Inconnu')
            modules[mod]['total'] += 1
            if c.get('next_review', '') <= now:
                modules[mod]['due'] += 1
            if c.get('interval', 0) >= 21:
                modules[mod]['mastered'] += 1

        eases = [c.get('easiness', 2.5) for c in self.cards if c.get('review_count', 0) > 0]

        return {
            'total_cards': len(self.cards),
            'due_today': len(due),
            'new_cards': len(new),
            'mastered': len(mastered),
            'learning': len(learning),
            'average_easiness': round(sum(eases) / len(eases), 2) if eases else 2.5,
            'modules': dict(modules),
            'review_streak': self._calc_streak(),
        }

    def _calc_streak(self) -> int:
        """Calcule le nombre de jours consécutifs de révision."""
        reviewed_dates = set()
        for c in self.cards:
            lr = c.get('last_reviewed')
            if lr:
                reviewed_dates.add(lr[:10])  # YYYY-MM-DD

        if not reviewed_dates:
            return 0

        streak = 0
        day = datetime.now().date()
        while day.isoformat() in reviewed_dates:
            streak += 1
            day -= timedelta(days=1)

        return streak

    def get_module_list(self) -> List[str]:
        """Liste des modules ayant des flashcards."""
        mods = sorted(set(c.get('module', 'Inconnu') for c in self.cards))
        return [m for m in mods if m]

    def delete_card(self, card_id: str):
        """Supprime une flashcard."""
        self.cards = [c for c in self.cards if c.get('id') != card_id]
        self._save()

    def reset_all(self):
        """Réinitialise toutes les flashcards."""
        self.cards = []
        self._save()

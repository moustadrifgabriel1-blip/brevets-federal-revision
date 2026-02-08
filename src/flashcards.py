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
        """Génère 1 à 3 flashcards pour un concept donné."""
        try:
            prompt = f"""Génère des flashcards pour réviser ce concept du Brevet Fédéral Spécialiste de Réseau.

**Concept :** {concept.get('name', 'N/A')}
**Description :** {concept.get('description', 'N/A')}
**Module :** {concept.get('module', 'N/A')}
**Mots-clés :** {', '.join(concept.get('keywords', []))}

Génère entre 1 et 3 flashcards avec des angles différents :
- Définition / terme technique
- Application pratique
- Règle ou norme à retenir

Réponds en JSON strict (liste) :
[
  {{
    "front": "Question ou terme à mémoriser (concis)",
    "back": "Réponse ou définition complète",
    "hint": "Indice optionnel (un mot-clé ou début de réponse)"
  }}
]

IMPORTANT :
- Tout en français
- Front : court (1-2 phrases max)
- Back : réponse complète mais concise (2-4 phrases)
- Hint : un seul mot-clé ou début de phrase
"""
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
                card = {
                    "id": f"fc_{concept.get('id', 'x')}_{len(self.cards) + len(result)}",
                    "concept_id": concept.get('id'),
                    "concept_name": concept.get('name'),
                    "module": concept.get('module'),
                    "front": rc.get('front', ''),
                    "back": rc.get('back', ''),
                    "hint": rc.get('hint', ''),
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

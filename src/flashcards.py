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

# Extraction de texte PDF
try:
    import pdfplumber
except ImportError:
    pdfplumber = None
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


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

    # Dossiers de cours possibles (local + cloud)
    COURS_DIRS = ["cours", "cours_local_backup"]

    # Mapping module code → nom de dossier (gère les variantes d'écriture)
    MODULE_FOLDER_MAP = {
        "AA01": "AA01", "AA02": "AA02", "AA03": "AA03", "AA04": "AA04",
        "AA05": "AA05", "AA06": "AA06", "AA07": "AA07", "AA08": "AA08",
        "AA09": "AA09", "AA10": "AA10", "AA11": "AA11",
        "AE01": "AE01", "AE02": "AE02", "AE03": "AE03", "AE04": "AE04",
        "AE05": "AE05", "AE05_": "AE05_", "AE06": "AE06", "AE07": "AE07",
        "AE09": "AE09", "AE10": "AE10", "AE11": "AE11", "AE12": "AE12",
        "AE13": "AE13",
    }

    def _find_module_folder(self, module: str) -> Optional[Path]:
        """Trouve le dossier de cours pour un module donné."""
        for cours_dir in self.COURS_DIRS:
            base = Path(cours_dir)
            if not base.exists():
                continue
            for child in base.iterdir():
                if child.is_dir() and child.name.upper().startswith(module.upper()):
                    return child
        return None

    def _extract_pdf_text(self, pdf_path: Path, max_chars: int = 15000) -> str:
        """Extrait le texte d'un PDF (avec fallback)."""
        text_parts = []
        try:
            if pdfplumber:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        try:
                            text = page.extract_text()
                            if text:
                                text_parts.append(text)
                        except Exception:
                            continue
            elif PyPDF2:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        try:
                            text = page.extract_text()
                            if text:
                                text_parts.append(text)
                        except Exception:
                            continue
        except Exception:
            return ""
        
        full_text = "\n\n".join(text_parts)
        # Tronquer si trop long (limites API)
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n[... texte tronqué ...]"
        return full_text

    def _get_course_content_for_module(self, module: str) -> str:
        """Scanne et extrait le contenu textuel de TOUS les PDFs d'un module."""
        folder = self._find_module_folder(module)
        if not folder:
            return ""
        
        all_texts = []
        pdf_files = sorted(folder.glob("*.pdf"))
        
        # Budget total de caractères pour le contenu cours
        MAX_TOTAL = 40000
        per_file_limit = MAX_TOTAL // max(1, len(pdf_files))
        
        for pdf_path in pdf_files:
            text = self._extract_pdf_text(pdf_path, max_chars=per_file_limit)
            if text.strip():
                all_texts.append(f"=== {pdf_path.name} ===\n{text}")
        
        return "\n\n".join(all_texts)

    def generate_from_concepts(self, concepts: List[Dict],
                                module: str = None,
                                num_cards: int = 10) -> int:
        """
        Génère des flashcards en scannant les cours du module sélectionné.
        L'IA lit le contenu réel des PDFs pour générer des cartes précises.

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

        # Scanner le contenu du cours pour le module
        target_module = module or (selected[0].get('module') if selected else None)
        course_content = ""
        if target_module:
            course_content = self._get_course_content_for_module(target_module)

        created = 0
        # Générer par batch si on a du contenu de cours
        if course_content and self.model:
            batch_cards = self._generate_batch_from_course(selected, course_content, target_module)
            for card in batch_cards:
                self.cards.append(card)
                created += 1
        else:
            # Fallback : concept par concept
            for concept in selected:
                cards = self._generate_cards_for_concept(concept, course_content)
                for card in cards:
                    self.cards.append(card)
                    created += 1

        self._save()
        return created

    def _generate_batch_from_course(self, concepts: List[Dict], course_content: str,
                                     module: str) -> List[Dict]:
        """Génère toutes les flashcards en un batch avec le contenu réel du cours."""
        if not self.model:
            return []

        module_label = self.MODULE_CONTEXT.get(module, "Spécialiste de réseau orientation Énergie")

        # Construire la liste des concepts à couvrir
        concept_list = "\n".join([
            f"  {i+1}. **{c.get('name', '?')}** (mots-clés: {', '.join(c.get('keywords', []))})"
            for i, c in enumerate(concepts)
        ])

        prompt = f"""Tu es un formateur expert du CIFER pour le Brevet Fédéral Spécialiste de Réseau, orientation ÉNERGIE (Suisse).

### CONTENU DU COURS — Module {module} ({module_label})
Voici le contenu RÉEL extrait des supports de cours. 
Utilise EXCLUSIVEMENT ces informations pour créer des flashcards PRÉCISES et FACTUELLES.

{course_content}

### CONCEPTS À COUVRIR
Génère exactement 3 flashcards par concept (soit {len(concepts) * 3} cartes au total).

{concept_list}

### EXIGENCES DE QUALITÉ ULTRA-PRO

Pour chaque concept, créer 3 cartes avec des NIVEAUX COGNITIFS DIFFÉRENTS (Bloom) :
1. **MÉMORISER** (card_type=definition) — Terme technique + définition exacte avec valeurs numériques/unités/normes tirées du cours
2. **COMPRENDRE/APPLIQUER** (card_type=pratique) — Situation concrète de terrain → action, procédure ou choix correct. Ou formule avec exemple chiffré
3. **ANALYSER** (card_type=analyse) — Comparaison entre concepts proches, diagnostic de situation, ou "pourquoi" technique (cause-effet)

RÈGLES STRICTES :
- **Front** : question DIRECTE et PRÉCISE (1-2 phrases). Exemples :
  ✅ "Quelle est la distance de sécurité pour travaux à prox. d'une ligne 16 kV ?"
  ✅ "Formule de la chute de tension en monophasé ?"
  ✅ "Différence entre régime TN-C et TN-S ?"
  ❌ "Qu'est-ce que..." ou "Définissez..." ou "Parlez de..."
- **Back** : réponse FACTUELLE tirée du cours (3-6 phrases). OBLIGATOIRE : inclure des VALEURS NUMÉRIQUES, NORMES (NIBT, ESTI, SUVA, EN), FORMULES ou PROCÉDURES concrètes
- **Hint** : UN seul mot-clé technique ou début de réponse (max 5 mots)
- **Difficulty** : 1 (facile, rappel pur), 2 (moyen, compréhension), 3 (difficile, analyse/synthèse)
- Vocabulaire MÉTIER suisse romand (consignation, DDR, mégohmmètre, sectionneur de terre, etc.)
- Chaque carte doit être AUTONOME et VÉRIFIABLE dans le cours

FORMATS DE CARTES ATTENDUS :
- **definition** : terme → définition exacte avec valeurs
- **norme** : norme/prescription → seuil/limite/obligation
- **pratique** : situation terrain → procédure/action correcte  
- **formule** : formule → variables, unités, exemple numérique
- **comparaison** : concept A vs B → tableau de différences
- **analyse** : pourquoi/comment → explication cause-effet

Réponds UNIQUEMENT avec un tableau JSON :
[
  {{
    "concept_name": "Nom du concept",
    "front": "Question technique précise et directe",
    "back": "Réponse factuelle du cours avec valeurs/normes/formules",
    "hint": "Mot-clé",
    "card_type": "definition|norme|pratique|formule|comparaison|analyse",
    "difficulty": 1
  }}
]

IMPORTANT : Tout en français. CHAQUE réponse DOIT contenir au moins 1 VALEUR NUMÉRIQUE ou 1 NORME ou 1 FORMULE."""

        try:
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
            
            # Associer les cartes aux concepts
            concept_by_name = {c.get('name', '').lower(): c for c in concepts}
            
            for rc in raw_cards:
                front = rc.get('front', '')
                back = rc.get('back', '')
                # Validation de qualité renforcée
                if len(front) < 20 or len(back) < 30:
                    continue
                # Rejeter les cartes trop vagues (pas de valeur/norme/formule dans la réponse)
                back_lower = back.lower()
                has_substance = any([
                    any(c.isdigit() for c in back),  # Contient un chiffre
                    any(norm in back_lower for norm in ['nibt', 'esti', 'suva', 'oibt', 'olei', 'en ', 'sia ']),
                    any(sym in back for sym in ['=', '×', '÷', '√', 'Ω', 'kV', 'mm²', '°C', '%']),
                    'selon' in back_lower or 'norme' in back_lower or 'article' in back_lower,
                ])
                # Accepter quand même si c'est pratique/analyse et assez long
                if not has_substance and len(back) < 100:
                    continue

                # Trouver le concept correspondant
                rc_concept_name = rc.get('concept_name', '').lower()
                matched_concept = concept_by_name.get(rc_concept_name)
                if not matched_concept:
                    # Fuzzy match
                    for cname, c in concept_by_name.items():
                        if rc_concept_name in cname or cname in rc_concept_name:
                            matched_concept = c
                            break
                if not matched_concept and concepts:
                    matched_concept = concepts[min(len(result) // 3, len(concepts) - 1)]

                # Déterminer la difficulté
                difficulty = rc.get('difficulty', 2)
                try:
                    difficulty = int(difficulty)
                    difficulty = max(1, min(3, difficulty))
                except (ValueError, TypeError):
                    difficulty = 2

                card = {
                    "id": f"fc_{matched_concept.get('id', 'x')}_{len(self.cards) + len(result)}",
                    "concept_id": matched_concept.get('id'),
                    "concept_name": matched_concept.get('name'),
                    "module": matched_concept.get('module'),
                    "front": front,
                    "back": back,
                    "hint": rc.get('hint', ''),
                    "card_type": rc.get('card_type', 'definition'),
                    "difficulty": difficulty,
                    "source_ref": matched_concept.get('source_document', ''),
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
            print(f"Erreur génération batch flashcards: {e}")
            return []

    # Contexte module enrichi
    MODULE_CONTEXT = {
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
    }

    def _generate_cards_for_concept(self, concept: Dict, course_content: str = "") -> List[Dict]:
        """Génère 2 à 4 flashcards PREMIUM pour un concept donné — avec contenu du cours."""
        try:
            module = concept.get('module', 'N/A')
            keywords = concept.get('keywords', [])
            page_ref = concept.get('page_references', '')
            source_doc = concept.get('source_document', '')

            module_context = self.MODULE_CONTEXT.get(module, "Spécialiste de réseau orientation Énergie")

            # Si pas de contenu de cours global, essayer de scanner juste ce module
            content_section = course_content
            if not content_section and module != 'N/A':
                content_section = self._get_course_content_for_module(module)

            # Construire le bloc contenu cours
            course_block = ""
            if content_section:
                # Extraire seulement la partie pertinente (autour des mots-clés)
                relevant = self._extract_relevant_content(content_section, concept.get('name', ''), keywords)
                if relevant:
                    course_block = f"""
### CONTENU DU COURS (extrait pertinent)
{relevant}
"""

            prompt = f"""Tu es un formateur expert du CIFER pour le Brevet Fédéral Spécialiste de Réseau, orientation ÉNERGIE (Suisse).

Génère des flashcards de HAUTE QUALITÉ pour mémoriser ce concept technique.
{course_block}
**Concept :** {concept.get('name', 'N/A')}
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
- Back : réponse COMPLÈTE, FACTUELLE, basée sur le contenu du cours (2-5 phrases), avec VALEURS NUMÉRIQUES et NORMES
- Hint : un seul MOT-CLÉ technique ou début de réponse qui aide sans tout révéler
- Vocabulaire MÉTIER suisse romand (consignation, DDR, mégohmmètre, manœuvre, etc.)
- Chaque carte AUTONOME

Réponds en JSON strict (liste) :
[
  {{
    "front": "Question technique précise et ciblée",
    "back": "Réponse complète basée sur le cours avec valeurs/normes/formules",
    "hint": "Un mot-clé technique ou indice",
    "card_type": "definition|norme|pratique|formule|comparaison"
  }}
]

IMPORTANT : Tout en français. Niveau professionnel. Les réponses DOIVENT contenir des FAITS PRÉCIS."""
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
            # Fallback — carte basique mais correcte
            now = datetime.now().isoformat()
            name = concept.get('name', '?')
            keywords = concept.get('keywords', [])
            kw_text = ', '.join(keywords[:3]) if keywords else 'N/A'
            return [{
                "id": f"fc_{concept.get('id', 'x')}_{len(self.cards)}",
                "concept_id": concept.get('id'),
                "concept_name": name,
                "module": concept.get('module'),
                "front": f"Expliquez le rôle et l'importance de « {name} » dans le contexte des réseaux de distribution électrique.",
                "back": f"« {name} » est un concept clé du module {concept.get('module', '?')}. Mots-clés associés : {kw_text}. Consultez le support de cours pour les détails techniques et les normes applicables.",
                "hint": keywords[0] if keywords else name[:20],
                "card_type": "definition",
                "repetitions": 0,
                "easiness": 2.5,
                "interval": 1,
                "next_review": now,
                "last_reviewed": None,
                "review_count": 0,
                "created_at": now,
            }]

    def _extract_relevant_content(self, full_content: str, concept_name: str, keywords: List[str],
                                   context_chars: int = 3000) -> str:
        """Extrait les passages pertinents du cours autour du concept et de ses mots-clés."""
        if not full_content:
            return ""
        
        search_terms = [concept_name.lower()] + [k.lower() for k in keywords[:5]]
        lines = full_content.split('\n')
        relevant_lines = set()
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for term in search_terms:
                if term in line_lower:
                    # Inclure quelques lignes avant/après pour le contexte
                    start = max(0, i - 3)
                    end = min(len(lines), i + 4)
                    for j in range(start, end):
                        relevant_lines.add(j)
        
        if not relevant_lines:
            # Rien trouvé — renvoyer le début du document
            return full_content[:context_chars]
        
        sorted_lines = sorted(relevant_lines)
        passages = []
        current_passage = []
        prev_idx = -10
        
        for idx in sorted_lines:
            if idx - prev_idx > 5:
                if current_passage:
                    passages.append('\n'.join(current_passage))
                current_passage = []
            current_passage.append(lines[idx])
            prev_idx = idx
        
        if current_passage:
            passages.append('\n'.join(current_passage))
        
        result = '\n\n[...]\n\n'.join(passages)
        if len(result) > context_chars:
            result = result[:context_chars] + "\n[... tronqué ...]"
        return result

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

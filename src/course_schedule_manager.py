"""
Gestionnaire de Planning de Cours
==================================
Parse et gère le planning de formation pour synchroniser avec les révisions
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import re

try:
    import pandas as pd
    from openpyxl import load_workbook
except ImportError:
    print("⚠️ Installez pandas et openpyxl: pip install pandas openpyxl")


@dataclass
class CourseSession:
    """Représente une session de cours"""
    module_code: str  # AA01, AE03, etc.
    module_name: str
    date: datetime
    duration_hours: float
    topics: List[str] = field(default_factory=list)
    status: str = "planned"  # planned, completed, cancelled
    notes: str = ""


class CourseScheduleManager:
    """Gère le planning de formation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.sessions: List[CourseSession] = []
        self.schedule_file = Path("data/course_schedule.json")
    
    def add_session(self, session: CourseSession):
        """Ajoute une session au planning"""
        self.sessions.append(session)
        self._sort_sessions()
    
    def _sort_sessions(self):
        """Trie les sessions par date"""
        self.sessions.sort(key=lambda s: s.date)
    
    def parse_excel_schedule(self, file_path: str) -> List[CourseSession]:
        """
        Parse un fichier Excel de planning
        
        Format attendu:
        | Date | Module | Durée | Thèmes |
        |------|--------|-------|--------|
        """
        sessions = []
        
        try:
            df = pd.read_excel(file_path)
            
            # Détecter les colonnes
            date_col = self._find_column(df, ['date', 'jour', 'day'])
            module_col = self._find_column(df, ['module', 'cours', 'course', 'matière'])
            duration_col = self._find_column(df, ['durée', 'duration', 'heures', 'hours', 'h'])
            topics_col = self._find_column(df, ['thème', 'thèmes', 'topics', 'sujet', 'sujets'])
            
            if not date_col or not module_col:
                raise ValueError("Colonnes 'Date' et 'Module' obligatoires")
            
            for _, row in df.iterrows():
                # Parser la date
                date_val = row[date_col]
                if pd.isna(date_val):
                    continue
                
                if isinstance(date_val, str):
                    date = self._parse_date_string(date_val)
                else:
                    date = pd.to_datetime(date_val)
                
                # Extraire le code et nom du module
                module_text = str(row[module_col])
                module_code, module_name = self._parse_module_name(module_text)
                
                # Durée
                duration = 0
                if duration_col and not pd.isna(row[duration_col]):
                    duration = self._parse_duration(str(row[duration_col]))
                
                # Thèmes
                topics = []
                if topics_col and not pd.isna(row[topics_col]):
                    topics = self._parse_topics(str(row[topics_col]))
                
                session = CourseSession(
                    module_code=module_code,
                    module_name=module_name,
                    date=date,
                    duration_hours=duration,
                    topics=topics
                )
                sessions.append(session)
        
        except Exception as e:
            print(f"Erreur lors du parsing Excel: {e}")
            raise
        
        self.sessions.extend(sessions)
        self._sort_sessions()
        return sessions
    
    def parse_manual_input(self, data: Dict) -> CourseSession:
        """
        Crée une session à partir d'une saisie manuelle
        
        Args:
            data: {
                'module': 'AA01',
                'date': '2026-03-15',
                'duration': 4,
                'topics': ['Loi d\'Ohm', 'Puissance électrique']
            }
        """
        date = datetime.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date']
        
        module_code = data['module']
        module_name = ""
        
        # Chercher le nom du module dans la config
        if 'modules' in self.config and module_code in self.config['modules']:
            module_info = self.config['modules'][module_code]
            if isinstance(module_info, dict):
                module_name = module_info.get('name', '')
        
        session = CourseSession(
            module_code=module_code,
            module_name=module_name,
            date=date,
            duration_hours=data.get('duration', 0),
            topics=data.get('topics', []),
            status=data.get('status', 'planned')
        )
        
        self.add_session(session)
        return session
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Trouve une colonne par noms possibles (insensible à la casse)"""
        df_columns_lower = [col.lower() for col in df.columns]
        for name in possible_names:
            for i, col in enumerate(df_columns_lower):
                if name.lower() in col:
                    return df.columns[i]
        return None
    
    def _parse_date_string(self, date_str: str) -> datetime:
        """Parse une date en format texte"""
        # Essayer différents formats
        formats = [
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d.%m.%y',
            '%d/%m/%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Essayer avec pandas
        try:
            return pd.to_datetime(date_str)
        except:
            raise ValueError(f"Format de date non reconnu: {date_str}")
    
    def _parse_module_name(self, text: str) -> Tuple[str, str]:
        """Extrait le code et le nom du module"""
        # Format: "AA01 - Conduite de collaborateurs" ou "AA01" ou "AA01 Conduite"
        match = re.match(r'([A-Z]{2}\d{2})\s*[-:]?\s*(.*)', text)
        if match:
            code = match.group(1)
            name = match.group(2).strip()
            return code, name
        return text, ""
    
    def _parse_duration(self, duration_str: str) -> float:
        """Parse une durée (4h, 4.5, 4 heures, etc.)"""
        # Enlever les unités
        clean = re.sub(r'[^\d.,]', '', duration_str)
        clean = clean.replace(',', '.')
        try:
            return float(clean)
        except ValueError:
            return 0
    
    def _parse_topics(self, topics_str: str) -> List[str]:
        """Parse une liste de thèmes"""
        # Séparer par virgules, points-virgules, ou retours à la ligne
        topics = re.split(r'[,;\n]', topics_str)
        return [t.strip() for t in topics if t.strip()]
    
    def get_completed_sessions(self, until_date: Optional[datetime] = None) -> List[CourseSession]:
        """Retourne les sessions déjà effectuées"""
        if until_date is None:
            until_date = datetime.now()
        
        return [s for s in self.sessions if s.date <= until_date]
    
    def get_upcoming_sessions(self, from_date: Optional[datetime] = None) -> List[CourseSession]:
        """Retourne les sessions à venir"""
        if from_date is None:
            from_date = datetime.now()
        
        return [s for s in self.sessions if s.date > from_date]
    
    def get_sessions_by_module(self, module_code: str) -> List[CourseSession]:
        """Retourne toutes les sessions d'un module"""
        return [s for s in self.sessions if s.module_code == module_code]
    
    def is_module_started(self, module_code: str, at_date: Optional[datetime] = None) -> bool:
        """Vérifie si un module a déjà commencé"""
        if at_date is None:
            at_date = datetime.now()
        
        sessions = self.get_sessions_by_module(module_code)
        return any(s.date <= at_date for s in sessions)
    
    def is_module_completed(self, module_code: str, at_date: Optional[datetime] = None) -> bool:
        """Vérifie si toutes les sessions d'un module sont passées"""
        if at_date is None:
            at_date = datetime.now()
        
        sessions = self.get_sessions_by_module(module_code)
        if not sessions:
            return False
        
        return all(s.date <= at_date for s in sessions)
    
    def get_module_progress(self, module_code: str) -> Dict:
        """Retourne la progression d'un module"""
        sessions = self.get_sessions_by_module(module_code)
        if not sessions:
            return {
                'total_sessions': 0,
                'completed': 0,
                'upcoming': 0,
                'total_hours': 0,
                'progress_percent': 0
            }
        
        now = datetime.now()
        completed = [s for s in sessions if s.date <= now]
        upcoming = [s for s in sessions if s.date > now]
        
        return {
            'total_sessions': len(sessions),
            'completed': len(completed),
            'upcoming': len(upcoming),
            'total_hours': sum(s.duration_hours for s in sessions),
            'progress_percent': (len(completed) / len(sessions) * 100) if sessions else 0,
            'next_session': min(upcoming, key=lambda s: s.date) if upcoming else None
        }
    
    def get_learned_topics(self, until_date: Optional[datetime] = None) -> Dict[str, List[str]]:
        """Retourne tous les thèmes déjà vus, groupés par module"""
        completed = self.get_completed_sessions(until_date)
        
        topics_by_module = {}
        for session in completed:
            if session.module_code not in topics_by_module:
                topics_by_module[session.module_code] = []
            topics_by_module[session.module_code].extend(session.topics)
        
        return topics_by_module
    
    def save(self):
        """Sauvegarde le planning"""
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'sessions': [
                {
                    'module_code': s.module_code,
                    'module_name': s.module_name,
                    'date': s.date.isoformat(),
                    'duration_hours': s.duration_hours,
                    'topics': s.topics,
                    'status': s.status,
                    'notes': s.notes
                }
                for s in self.sessions
            ]
        }
        
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """Charge le planning sauvegardé et synchronise les statuts"""
        if not self.schedule_file.exists():
            return
        
        with open(self.schedule_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.sessions = [
            CourseSession(
                module_code=s['module_code'],
                module_name=s['module_name'],
                date=datetime.fromisoformat(s['date']),
                duration_hours=s['duration_hours'],
                topics=s['topics'],
                status=s.get('status', 'planned'),
                notes=s.get('notes', '')
            )
            for s in data.get('sessions', [])
        ]
        
        self._sort_sessions()
        
        # Auto-synchroniser les statuts : sessions passées → "completed"
        self._sync_statuses()
    
    def _sync_statuses(self):
        """Met à jour automatiquement le statut des sessions passées"""
        now = datetime.now()
        changed = False
        
        for session in self.sessions:
            if session.date <= now and session.status == "planned":
                session.status = "completed"
                changed = True
            elif session.date > now and session.status == "completed":
                # Correction inverse : si une session future est marquée complétée par erreur
                session.status = "planned"
                changed = True
        
        if changed:
            self.save()
    
    def export_to_markdown(self, output_path: str):
        """Exporte le planning en Markdown"""
        lines = ["# 📅 Planning de Formation\n"]
        
        # Statistiques globales
        total_hours = sum(s.duration_hours for s in self.sessions)
        completed = self.get_completed_sessions()
        upcoming = self.get_upcoming_sessions()
        
        lines.append(f"**Total:** {len(self.sessions)} sessions, {total_hours:.1f}h")
        lines.append(f"**Complété:** {len(completed)} sessions")
        lines.append(f"**À venir:** {len(upcoming)} sessions\n")
        
        # Par module
        modules = {}
        for session in self.sessions:
            if session.module_code not in modules:
                modules[session.module_code] = []
            modules[session.module_code].append(session)
        
        for module_code in sorted(modules.keys()):
            sessions = modules[module_code]
            module_name = sessions[0].module_name if sessions[0].module_name else ""
            
            lines.append(f"\n## {module_code} - {module_name}\n")
            
            for session in sessions:
                status_icon = "✅" if session.date <= datetime.now() else "📅"
                date_str = session.date.strftime("%d.%m.%Y")
                
                lines.append(f"### {status_icon} {date_str} ({session.duration_hours}h)")
                
                if session.topics:
                    lines.append("\n**Thèmes:**")
                    for topic in session.topics:
                        lines.append(f"- {topic}")
                
                lines.append("")
        
        Path(output_path).write_text('\n'.join(lines), encoding='utf-8')


if __name__ == "__main__":
    # Test
    config = {}
    manager = CourseScheduleManager(config)
    
    # Ajouter une session test
    session = manager.parse_manual_input({
        'module': 'AA01',
        'date': '2026-02-15',
        'duration': 4,
        'topics': ['Introduction', 'Bases']
    })
    
    print(f"Session créée: {session.module_code} le {session.date.strftime('%d.%m.%Y')}")

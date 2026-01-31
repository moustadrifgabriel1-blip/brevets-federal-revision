"""
📁 Importateur de Dossiers de Cours
===================================
Importe une structure de dossiers de formation et détecte le contenu
"""

import os
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json
import yaml


@dataclass
class ModuleInfo:
    """Informations sur un module de formation"""
    code: str  # AA01, AE02, etc.
    name: str
    order: int
    has_content: bool
    files: List[str] = field(default_factory=list)
    file_count: int = 0
    total_size_kb: float = 0
    category: str = "base"  # "base" (AA) ou "avance" (AE)
    last_modified: Optional[datetime] = None


class FolderImporter:
    """Importe et analyse une structure de dossiers de formation"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.md', '.pptx', '.ppt', '.xlsx', '.xls'}
    
    def __init__(self, config: dict):
        self.config = config
        self.modules: Dict[str, ModuleInfo] = {}
        self.import_log: List[str] = []
    
    def scan_source_folder(self, source_path: str) -> List[ModuleInfo]:
        """
        Scanne un dossier source pour détecter les modules et leur contenu
        
        Args:
            source_path: Chemin vers le dossier contenant les dossiers AA01, AE02, etc.
            
        Returns:
            Liste des modules détectés avec leurs informations
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Le dossier {source_path} n'existe pas")
        
        modules = []
        order = 0
        
        # Scanner tous les sous-dossiers
        for item in sorted(source.iterdir()):
            if item.is_dir() and self._is_module_folder(item.name):
                order += 1
                module = self._analyze_module_folder(item, order)
                modules.append(module)
                self.modules[module.code] = module
        
        return modules
    
    def _is_module_folder(self, name: str) -> bool:
        """Vérifie si le nom correspond à un dossier de module (AA01, AE02, etc.)"""
        if len(name) < 4:
            return False
        prefix = name[:2].upper()
        return prefix in ['AA', 'AE'] or name.lower().startswith('directive')
    
    def _analyze_module_folder(self, folder_path: Path, order: int) -> ModuleInfo:
        """Analyse un dossier de module et retourne ses informations"""
        name = folder_path.name
        
        # Extraire le code et le nom
        parts = name.split(' ', 1)
        code = parts[0] if parts else name
        module_name = parts[1] if len(parts) > 1 else name
        
        # Déterminer la catégorie
        category = "base" if code.upper().startswith("AA") else "avance"
        if "directive" in name.lower():
            category = "directive"
        
        # Scanner les fichiers
        files = []
        total_size = 0
        last_modified = None
        
        for file_path in folder_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                files.append(str(file_path.relative_to(folder_path)))
                total_size += file_path.stat().st_size
                
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if last_modified is None or file_mtime > last_modified:
                    last_modified = file_mtime
        
        has_content = len(files) > 0
        
        return ModuleInfo(
            code=code,
            name=module_name,
            order=order,
            has_content=has_content,
            files=files,
            file_count=len(files),
            total_size_kb=total_size / 1024,
            category=category,
            last_modified=last_modified
        )
    
    def import_folders(self, source_path: str, destination_path: str, 
                       copy_mode: bool = True) -> Dict[str, any]:
        """
        Importe les dossiers de cours vers la destination
        
        Args:
            source_path: Chemin source des dossiers
            destination_path: Chemin destination (dossier cours/)
            copy_mode: True pour copier, False pour créer des liens symboliques
            
        Returns:
            Rapport d'importation
        """
        source = Path(source_path)
        dest = Path(destination_path)
        dest.mkdir(parents=True, exist_ok=True)
        
        # Scanner d'abord
        modules = self.scan_source_folder(source_path)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'source': source_path,
            'destination': destination_path,
            'modules_imported': [],
            'modules_empty': [],
            'total_files': 0,
            'total_size_kb': 0
        }
        
        for module in modules:
            module_dest = dest / module.code
            module_source = source / f"{module.code} {module.name}" if module.name != module.code else source / module.code
            
            # Chercher le bon dossier source
            for item in source.iterdir():
                if item.name.startswith(module.code):
                    module_source = item
                    break
            
            if module_source.exists():
                if copy_mode:
                    if module_dest.exists():
                        shutil.rmtree(module_dest)
                    shutil.copytree(module_source, module_dest)
                else:
                    if not module_dest.exists():
                        os.symlink(module_source, module_dest)
                
                if module.has_content:
                    report['modules_imported'].append({
                        'code': module.code,
                        'name': module.name,
                        'files': module.file_count,
                        'size_kb': round(module.total_size_kb, 1)
                    })
                    report['total_files'] += module.file_count
                    report['total_size_kb'] += module.total_size_kb
                else:
                    report['modules_empty'].append({
                        'code': module.code,
                        'name': module.name
                    })
                
                self.import_log.append(f"✓ {module.code}: {module.name} ({module.file_count} fichiers)")
        
        report['total_size_kb'] = round(report['total_size_kb'], 1)
        
        # Sauvegarder le rapport
        report_path = dest.parent / 'data' / 'import_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def get_modules_status(self) -> Dict[str, List[ModuleInfo]]:
        """Retourne les modules groupés par statut"""
        return {
            'with_content': [m for m in self.modules.values() if m.has_content],
            'empty': [m for m in self.modules.values() if not m.has_content],
            'base': [m for m in self.modules.values() if m.category == 'base'],
            'advanced': [m for m in self.modules.values() if m.category == 'avance']
        }
    
    def update_config_modules(self, config_path: str):
        """Met à jour la configuration avec les modules détectés"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'modules' not in config:
            config['modules'] = {}
        
        for code, module in self.modules.items():
            config['modules'][code] = {
                'name': module.name,
                'has_content': module.has_content,
                'category': module.category,
                'order': module.order,
                'file_count': module.file_count
            }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    def generate_learning_order(self) -> List[str]:
        """
        Génère un ordre d'apprentissage basé sur:
        1. D'abord les modules de base (AA) avec contenu
        2. Ensuite les modules avancés (AE) avec contenu
        3. Les modules vides sont marqués pour plus tard
        """
        order = []
        
        # Modules de base avec contenu
        base_with_content = sorted(
            [m for m in self.modules.values() if m.category == 'base' and m.has_content],
            key=lambda x: x.order
        )
        order.extend([m.code for m in base_with_content])
        
        # Modules avancés avec contenu
        advanced_with_content = sorted(
            [m for m in self.modules.values() if m.category == 'avance' and m.has_content],
            key=lambda x: x.order
        )
        order.extend([m.code for m in advanced_with_content])
        
        return order
    
    def to_dict(self) -> Dict:
        """Exporte les données des modules en dictionnaire"""
        return {
            code: {
                'code': m.code,
                'name': m.name,
                'order': m.order,
                'has_content': m.has_content,
                'file_count': m.file_count,
                'total_size_kb': round(m.total_size_kb, 1),
                'category': m.category,
                'files': m.files
            }
            for code, m in self.modules.items()
        }


def calculate_study_time(weekday_minutes: int = 30, weekend_hours: int = 8) -> Dict:
    """
    Calcule le temps d'étude disponible par semaine
    
    Args:
        weekday_minutes: Minutes par jour en semaine
        weekend_hours: Heures totales le week-end
        
    Returns:
        Dictionnaire avec les calculs de temps
    """
    weekday_hours = weekday_minutes / 60
    weekly_weekday = weekday_hours * 5  # Lundi à vendredi
    weekly_total = weekly_weekday + weekend_hours
    
    return {
        'weekday_minutes': weekday_minutes,
        'weekday_hours': weekday_hours,
        'weekend_hours': weekend_hours,
        'weekly_weekday_hours': weekly_weekday,
        'weekly_total_hours': weekly_total,
        'monthly_hours': weekly_total * 4.33,
        'schedule': {
            'lundi': f"{weekday_minutes} min",
            'mardi': f"{weekday_minutes} min",
            'mercredi': f"{weekday_minutes} min",
            'jeudi': f"{weekday_minutes} min",
            'vendredi': f"{weekday_minutes} min",
            'samedi': f"{weekend_hours // 2}h",
            'dimanche': f"{weekend_hours - weekend_hours // 2}h"
        }
    }


if __name__ == "__main__":
    # Test
    config = {'paths': {'cours': './cours'}}
    importer = FolderImporter(config)
    
    # Calculer le temps d'étude
    study_time = calculate_study_time(30, 8)
    print(f"Temps hebdomadaire: {study_time['weekly_total_hours']:.1f}h")
    print(f"Temps mensuel: {study_time['monthly_hours']:.1f}h")

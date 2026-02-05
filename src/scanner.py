"""
Scanner de Documents
====================
Scanne et extrait le texte de tous les documents (PDF, Word, etc.)
"""

import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Supprimer les warnings pdfplumber liés aux PDFs corrompus
warnings.filterwarnings('ignore', category=UserWarning, module='pdfminer')
warnings.filterwarnings('ignore', message='.*invalid float value.*')
warnings.filterwarnings('ignore', message='.*Cannot set.*color.*')

# Rediriger stderr temporairement pour supprimer les messages pdfminer
import io
import contextlib

@contextlib.contextmanager
def suppress_pdfminer_warnings():
    """Supprime les messages d'erreur de pdfminer sur stderr"""
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        yield
    finally:
        sys.stderr = old_stderr

# Importations pour le traitement de documents
try:
    import PyPDF2
    import pdfplumber
    from docx import Document as DocxDocument
except ImportError as e:
    print(f"⚠️  Certaines dépendances manquent. Lancez: pip install -r requirements.txt")

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class DocumentInfo:
    """Informations sur un document scanné"""
    path: str
    filename: str
    extension: str
    category: str  # 'cours', 'directive', 'planning'
    module: Optional[str]
    content: str
    word_count: int
    scanned_at: datetime
    

class DocumentScanner:
    """Scanne et extrait le contenu des documents"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.md'}
    
    def __init__(self, config: dict):
        self.config = config
        self.documents: List[DocumentInfo] = []
        
    def scan_directory(self, directory: str, category: str) -> List[DocumentInfo]:
        """Scanne tous les documents d'un répertoire"""
        path = Path(directory)
        documents = []
        
        if not path.exists():
            console.print(f"[yellow]⚠️  Le dossier {directory} n'existe pas. Création...[/yellow]")
            path.mkdir(parents=True, exist_ok=True)
            return documents
        
        # Liste tous les fichiers supportés
        files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            files.extend(path.rglob(f"*{ext}"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"📂 Scan de {directory}...", total=len(files))
            
            for file_path in files:
                try:
                    content = self._extract_content(file_path)
                    module = self._detect_module(file_path)
                    
                    doc = DocumentInfo(
                        path=str(file_path),
                        filename=file_path.name,
                        extension=file_path.suffix.lower(),
                        category=category,
                        module=module,
                        content=content,
                        word_count=len(content.split()),
                        scanned_at=datetime.now()
                    )
                    documents.append(doc)
                    progress.update(task, advance=1)
                    
                except Exception as e:
                    console.print(f"[red]❌ Erreur lors du scan de {file_path.name}: {e}[/red]")
        
        return documents
    
    def _extract_content(self, file_path: Path) -> str:
        """Extrait le contenu textuel d'un fichier"""
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return self._extract_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self._extract_docx(file_path)
        elif ext in ['.txt', '.md']:
            return self._extract_text(file_path)
        else:
            raise ValueError(f"Extension non supportée: {ext}")
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extrait le texte d'un PDF avec gestion d'erreurs robuste"""
        text_parts = []
        
        # Essai avec pdfplumber (meilleure extraction)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    except Exception:
                        # Ignorer silencieusement les pages problématiques
                        continue
        except Exception:
            # Fallback avec PyPDF2
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for i, page in enumerate(reader.pages):
                        try:
                            text = page.extract_text()
                            if text:
                                text_parts.append(text)
                        except Exception:
                            continue
            except Exception as e:
                # Si tout échoue, retourner une chaîne vide
                return ""
        
        return "\n\n".join(text_parts)
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extrait le texte d'un document Word"""
        doc = DocxDocument(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    
    def _extract_text(self, file_path: Path) -> str:
        """Lit un fichier texte"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _detect_module(self, file_path: Path) -> Optional[str]:
        """Détecte le module à partir du chemin du fichier (AA01, AE02, etc.)"""
        parts = file_path.parts
        for part in parts:
            # Détection modules AA01, AE02, etc.
            if len(part) >= 4:
                prefix = part[:2].upper()
                if prefix in ['AA', 'AE']:
                    # Extraire juste le code (AA01, AE03, etc.)
                    code = part.split()[0] if ' ' in part else part[:4]
                    return code
            # Ancien format module/Module
            if part.startswith('module') or part.startswith('Module'):
                return part
            # Pattern M1, M2, etc.
            if len(part) >= 2 and part[0].upper() == 'M' and part[1].isdigit():
                return part
        return None
    
    def scan_all(self) -> Dict[str, List[DocumentInfo]]:
        """Scanne tous les dossiers configurés"""
        results = {}
        
        console.print("\n[bold blue]🔍 Démarrage du scan des documents...[/bold blue]\n")
        
        # Scan des cours
        cours_path = self.config['paths']['cours']
        results['cours'] = self.scan_directory(cours_path, 'cours')
        console.print(f"  ✅ {len(results['cours'])} fichiers de cours trouvés")
        
        # Scan des directives
        directives_path = self.config['paths']['directives']
        results['directives'] = self.scan_directory(directives_path, 'directive')
        console.print(f"  ✅ {len(results['directives'])} directives trouvées")
        
        # Scan du planning
        planning_path = self.config['paths']['planning']
        results['planning'] = self.scan_directory(planning_path, 'planning')
        console.print(f"  ✅ {len(results['planning'])} fichiers de planning trouvés")
        
        # Stocker tous les documents
        self.documents = [doc for docs in results.values() for doc in docs]
        
        # Filtrer selon les modules configurés (uniquement avec contenu)
        if 'modules' in self.config:
            modules_with_content = {
                code: info for code, info in self.config['modules'].items()
                if isinstance(info, dict) and info.get('has_content', False)
            }
            
            # Garder tous les non-cours et filtrer les cours par module
            filtered_docs = []
            skipped = 0
            for doc in self.documents:
                if doc.category != 'cours':
                    filtered_docs.append(doc)
                elif doc.module is None or doc.module in modules_with_content:
                    filtered_docs.append(doc)
                else:
                    skipped += 1
            
            self.documents = filtered_docs
            if skipped > 0:
                console.print(f"  ℹ️  {skipped} fichiers ignorés (modules sans cours configurés)")
        
        # Statistiques globales
        modules_found = set(doc.module for doc in self.documents if doc.module)
        total_words = sum(doc.word_count for doc in self.documents)
        
        console.print(f"\n[bold green]📊 Total: {len(self.documents)} documents, ~{total_words:,} mots[/bold green]")
        if modules_found:
            console.print(f"📚 Modules détectés: {', '.join(sorted(modules_found))}\n")
        
        return results
    
    def get_documents_by_category(self, category: str) -> List[DocumentInfo]:
        """Retourne les documents d'une catégorie"""
        return [doc for doc in self.documents if doc.category == category]
    
    def get_summary(self) -> str:
        """Génère un résumé des documents scannés"""
        summary = []
        summary.append("=" * 50)
        summary.append("RÉSUMÉ DES DOCUMENTS SCANNÉS")
        summary.append("=" * 50)
        
        categories = {}
        for doc in self.documents:
            if doc.category not in categories:
                categories[doc.category] = []
            categories[doc.category].append(doc)
        
        for cat, docs in categories.items():
            summary.append(f"\n📁 {cat.upper()}")
            summary.append("-" * 30)
            for doc in docs:
                module_info = f" [{doc.module}]" if doc.module else ""
                summary.append(f"  • {doc.filename}{module_info} ({doc.word_count} mots)")
        
        return "\n".join(summary)


if __name__ == "__main__":
    # Test du scanner
    import yaml
    
    with open("config/config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    scanner = DocumentScanner(config)
    results = scanner.scan_all()
    print(scanner.get_summary())

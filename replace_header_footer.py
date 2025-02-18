import os
from pathlib import Path
from docx import Document
from docx.shared import Inches
import subprocess
import platform

# Configuration des chemins
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(SCRIPT_DIR, "input_docs")
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "output_docs")
PDF_OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "pdf_output")
LOGO_PATH = os.path.join(SCRIPT_DIR, "logo.png")
FOOTER_PATH = os.path.join(SCRIPT_DIR, "footer.txt")

# Extensions supportées
SUPPORTED_EXTENSIONS = {
    '.docx': 'Document Word',
    '.pptx': 'PowerPoint',
    '.xlsx': 'Excel'
}

def setup_folders():
    """Crée les dossiers nécessaires s'ils n'existent pas"""
    for folder in [INPUT_FOLDER, OUTPUT_FOLDER, PDF_OUTPUT_FOLDER]:
        os.makedirs(folder, exist_ok=True)
        print(f"✓ Dossier créé/vérifié : {folder}")

def get_footer_text():
    """Lit le texte du pied de page depuis le fichier footer.txt"""
    try:
        with open(FOOTER_PATH, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"⚠️  Le fichier footer.txt n'a pas été trouvé à l'emplacement : {FOOTER_PATH}")
        print("➡️  Création du fichier footer.txt avec le texte par défaut")
        default_footer = "© 2024 So'Managements | Mentions légales"
        with open(FOOTER_PATH, 'w', encoding='utf-8') as f:
            f.write(default_footer)
        return default_footer

def process_document(doc_path, output_path, footer_text):
    """Traite un document Word"""
    doc = Document(doc_path)
    
    for section in doc.sections:
        # Modification de l'en-tête
        header = section.header
        for paragraph in header.paragraphs:
            paragraph.clear()
        if not header.paragraphs:
            header.add_paragraph()
        run = header.paragraphs[0].add_run()
        run.add_picture(LOGO_PATH, width=Inches(1.5))
        
        # Modification du pied de page
        footer = section.footer
        for paragraph in footer.paragraphs:
            paragraph.clear()
        if not footer.paragraphs:
            footer.add_paragraph()
        footer.paragraphs[0].text = footer_text
    
    doc.save(output_path)

def process_file(input_path, output_path, file_type, footer_text):
    """Traite un fichier selon son type"""
    try:
        if file_type == '.docx':
            process_document(input_path, output_path, footer_text)
        return True
    except Exception as e:
        print(f"❌ Erreur lors du traitement de {input_path}: {str(e)}")
        return False

# Création des dossiers nécessaires
for folder in [INPUT_FOLDER, OUTPUT_FOLDER, PDF_OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ... reste du code ...
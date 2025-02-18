import os
from pathlib import Path
from docx import Document
from docx.shared import Inches

# Configuration des chemins
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(SCRIPT_DIR, "input_docs")
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "output_docs")
PDF_OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "pdf_output")
LOGO_PATH = os.path.join(SCRIPT_DIR, "logo.png")
FOOTER_PATH = os.path.join(SCRIPT_DIR, "footer.txt")

# Création des dossiers nécessaires
for folder in [INPUT_FOLDER, OUTPUT_FOLDER, PDF_OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ... reste du code ...
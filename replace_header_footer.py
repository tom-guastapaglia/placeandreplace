import os
from pathlib import Path

# Déterminer si nous sommes en production
IS_PRODUCTION = os.environ.get("VERCEL_ENV") == "production"

# Configuration des chemins
if IS_PRODUCTION:
    BASE_DIR = "/tmp"
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration
INPUT_FOLDER = os.path.join(BASE_DIR, "input_docs")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output_docs")
PDF_OUTPUT_FOLDER = os.path.join(BASE_DIR, "pdf_output")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
FOOTER_PATH = os.path.join(BASE_DIR, "footer.txt")

# Création des dossiers nécessaires
for folder in [INPUT_FOLDER, OUTPUT_FOLDER, PDF_OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ... reste du code ... 
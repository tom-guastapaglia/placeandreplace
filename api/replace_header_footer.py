# Modification des chemins pour Vercel
SCRIPT_DIR = "/tmp" if os.environ.get("VERCEL") else os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join("/tmp", "input_docs")
OUTPUT_FOLDER = os.path.join("/tmp", "output_docs")
PDF_OUTPUT_FOLDER = os.path.join("/tmp", "pdf_output")
LOGO_PATH = os.path.join("/tmp", "logo.png") if os.environ.get("VERCEL") else os.path.join(SCRIPT_DIR, "logo.png")
FOOTER_PATH = os.path.join("/tmp", "footer.txt") if os.environ.get("VERCEL") else os.path.join(SCRIPT_DIR, "footer.txt") 
import streamlit as st
import os
from pathlib import Path
import shutil
from replace_header_footer import (
    process_file, 
    get_footer_text, 
    SUPPORTED_EXTENSIONS,
    setup_folders,
    SCRIPT_DIR,
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    PDF_OUTPUT_FOLDER,
    LOGO_PATH
)
import zipfile
from io import BytesIO

st.set_page_config(
    page_title="Management Solution - Gestionnaire de Documents",
    page_icon="📄",
    layout="wide"
)

def init_session_state():
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = []
    if 'footer_text' not in st.session_state:
        st.session_state.footer_text = get_footer_text()
    if 'should_reprocess' not in st.session_state:
        st.session_state.should_reprocess = False

def create_zip_buffer(files_dict):
    """Crée un buffer ZIP contenant tous les fichiers"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, zip_path in files_dict.items():
            if os.path.exists(file_path):
                zip_file.write(file_path, zip_path)
    zip_buffer.seek(0)
    return zip_buffer

def reprocess_all_documents():
    """Retraite tous les documents avec les nouveaux paramètres"""
    if not st.session_state.processed_files:
        return
    
    progress_text = "Mise à jour des documents..."
    progress_bar = st.progress(0)
    
    for index, file in enumerate(st.session_state.processed_files):
        input_path = os.path.join(INPUT_FOLDER, file)
        output_path = os.path.join(OUTPUT_FOLDER, file)
        file_type = Path(file).suffix
        
        if os.path.exists(input_path):
            process_file(input_path, output_path, file_type, st.session_state.footer_text)
        
        progress_bar.progress((index + 1) / len(st.session_state.processed_files))
    
    st.success("✅ Documents mis à jour avec succès!")
    st.session_state.should_reprocess = False

def main():
    init_session_state()
    
    st.title("🏢 Management Solution - Gestionnaire de Documents")
    
    # Création des colonnes pour une meilleure organisation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📁 Téléversement des documents")
        uploaded_files = st.file_uploader(
            "Déposez vos documents ici",
            accept_multiple_files=True,
            type=list(SUPPORTED_EXTENSIONS.keys()),
            help="Formats supportés : " + ", ".join(SUPPORTED_EXTENSIONS.keys())
        )
        
        if uploaded_files:
            setup_folders()  # Assure que les dossiers nécessaires existent
            
            progress_text = "Traitement des documents en cours..."
            progress_bar = st.progress(0)
            
            for index, uploaded_file in enumerate(uploaded_files):
                if uploaded_file.name not in st.session_state.processed_files:
                    # Sauvegarde temporaire du fichier
                    input_path = os.path.join(INPUT_FOLDER, uploaded_file.name)
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Traitement du fichier
                    output_path = os.path.join(OUTPUT_FOLDER, uploaded_file.name)
                    file_type = Path(uploaded_file.name).suffix
                    
                    if process_file(input_path, output_path, file_type, st.session_state.footer_text):
                        st.session_state.processed_files.append(uploaded_file.name)
                
                progress_bar.progress((index + 1) / len(uploaded_files))
            
            st.success(f"✅ {len(uploaded_files)} documents traités avec succès!")

    with col2:
        st.subheader("⚙️ Configuration")
        
        # Upload du logo
        st.write("##### Logo")
        new_logo = st.file_uploader("Changer le logo", type=['png', 'jpg', 'jpeg'])
        if new_logo:
            with open(LOGO_PATH, "wb") as f:
                f.write(new_logo.getbuffer())
            st.success("✅ Logo mis à jour!")
            st.session_state.should_reprocess = True
        
        # Modification du pied de page
        st.write("##### Pied de page")
        new_footer = st.text_area("Modifier le texte du pied de page", st.session_state.footer_text)
        if new_footer != st.session_state.footer_text:
            with open(os.path.join(SCRIPT_DIR, "footer.txt"), "w", encoding='utf-8') as f:
                f.write(new_footer)
            st.session_state.footer_text = new_footer
            st.success("✅ Pied de page mis à jour!")
            st.session_state.should_reprocess = True
    
    # Retraitement des documents si nécessaire
    if st.session_state.should_reprocess:
        reprocess_all_documents()
    
    # Section des fichiers traités
    if st.session_state.processed_files:
        st.subheader("📋 Documents traités")
        
        # Bouton pour tout télécharger
        files_to_zip = {}
        for file in st.session_state.processed_files:
            # Ajout du fichier original
            output_path = os.path.join(OUTPUT_FOLDER, file)
            if os.path.exists(output_path):
                files_to_zip[output_path] = os.path.join("documents", file)
            
            # Ajout de la version PDF
            pdf_path = os.path.join(PDF_OUTPUT_FOLDER, file.rsplit('.', 1)[0] + '.pdf')
            if os.path.exists(pdf_path):
                files_to_zip[pdf_path] = os.path.join("pdf", file.rsplit('.', 1)[0] + '.pdf')
        
        if files_to_zip:
            zip_buffer = create_zip_buffer(files_to_zip)
            col_download_all = st.columns([6, 2])[1]
            with col_download_all:
                st.download_button(
                    label="📦 Tout télécharger",
                    data=zip_buffer,
                    file_name="documents_traites.zip",
                    mime="application/zip",
                    help="Télécharger tous les documents et leurs versions PDF"
                )
        
        # Affichage de la liste des fichiers
        for file in st.session_state.processed_files:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {file}")
            with col2:
                output_path = os.path.join(OUTPUT_FOLDER, file)
                if os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Télécharger",
                            data=f,
                            file_name=file,
                            mime="application/octet-stream"
                        )
            with col3:
                pdf_path = os.path.join(PDF_OUTPUT_FOLDER, file.rsplit('.', 1)[0] + '.pdf')
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="PDF",
                            data=f,
                            file_name=file.rsplit('.', 1)[0] + '.pdf',
                            mime="application/pdf"
                        )

if __name__ == "__main__":
    main() 
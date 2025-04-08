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
    LOGO_PATH,
    process_client_template
)
import zipfile
from io import BytesIO
from datetime import datetime
import sqlite3
import json
import pandas as pd

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
    if 'selected_client_id' not in st.session_state:
        st.session_state.selected_client_id = None
    if 'footer_data' not in st.session_state:
        st.session_state.footer_data = {
            'raison_socialOF': "",
            'StatuOF': "",
            'capitalOF': "",
            'AdresseOF': "",
            'CodepostaleOF': "",
            'VilleOF': "",
            'PaysOF': "France",
            'TéléphoneOF': "",
            'MailOF': "",
            'siretOF': "",
            'RCSOF': "",
            'APEOF': "",
            'TVAOF': "",
            'NDAOF': "",
            'RégiondrieetsOF': "",
            'DatemajdocOF': ""
        }
    
    # Initialiser la base de données
    setup_database()

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

def generate_footer_text(footer_data):
    """Génère le texte du pied de page selon le format demandé"""
    return f"""{footer_data['raison_socialOF']}– {footer_data['StatuOF']} au capital de {footer_data['capitalOF']} EUR
{footer_data['AdresseOF']} {footer_data['CodepostaleOF']} {footer_data['VilleOF']}– {footer_data['PaysOF']}
Téléphone : {footer_data['TéléphoneOF']} - Email : {footer_data['MailOF']}
SIRET : {footer_data['siretOF']}  - RCS : {footer_data['RCSOF']} - APE : {footer_data['APEOF']}  -TVA : {footer_data['TVAOF']}
Enregistrée sous le numéro NDA {footer_data['NDAOF']} auprès du Préfet de la Région de {footer_data['RégiondrieetsOF']} Cet enregistrement ne vaut pas agrément de l'État
V1.0 – {footer_data['DatemajdocOF']}"""

def generate_client_documents(uploaded_templates, uploaded_logo):
    """Génère les documents pour le client"""
    if not uploaded_templates:
        st.error("⚠️ Veuillez d'abord télécharger les templates")
        return
    
    try:
        # Afficher un statut global
        status_container = st.empty()
        status_container.info("🔄 Préparation de la génération des documents...")
        
        # Créer une barre de progression principale
        progress_bar = st.progress(0)
        
        # Créer un conteneur pour les messages d'état détaillés
        details_container = st.empty()
        
        # Calculer le nombre total d'étapes
        total_steps = len(uploaded_templates) + 3  # Templates + préparation + création du ZIP + finalisation
        current_step = 0
        
        # Fonction pour mettre à jour la progression
        def update_progress(step_name, increment=1):
            nonlocal current_step
            current_step += increment
            progress_value = min(current_step / total_steps, 1.0)
            progress_bar.progress(progress_value)
            details_container.info(f"🔄 {step_name} ({int(progress_value * 100)}%)")
        
        # Étape 1: Préparation
        update_progress("Préparation de l'environnement")
        
        # Créer un dossier temporaire pour le client
        client_folder = os.path.join(OUTPUT_FOLDER, "temp_client")
        os.makedirs(client_folder, exist_ok=True)
        
        # Sauvegarder le logo du client s'il est fourni
        client_logo_path = None
        if uploaded_logo:
            client_logo_path = os.path.join(client_folder, "logo.png")
            with open(client_logo_path, "wb") as f:
                f.write(uploaded_logo.getvalue())
        
        # Générer le pied de page personnalisé
        footer_text = generate_footer_text(st.session_state.footer_data)
        
        # Créer un rapport de traitement
        rapport = []
        rapport.append("=== Rapport de traitement des documents ===\n")
        rapport.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        rapport.append(f"Client : {st.session_state.footer_data.get('raison_socialOF', 'Non spécifié')}\n")
        rapport.append("Informations client :")
        for key, value in st.session_state.footer_data.items():
            rapport.append(f"{key} : {value}")
        rapport.append("\nFichiers traités :")
        
        processed_files = []  # Liste pour suivre les fichiers traités avec succès
        processing_errors = []  # Liste pour suivre les erreurs
        
        # Traiter chaque template
        for i, template_file in enumerate(uploaded_templates):
            file_name = template_file.name
            file_type = os.path.splitext(file_name)[1].lower()
            output_path = os.path.join(client_folder, file_name)
            
            # Mettre à jour la progression
            update_progress(f"Traitement de {file_name}")
            
            rapport.append(f"\nTraitement de : {file_name}")
            
            # Sauvegarder le template temporairement
            temp_path = os.path.join(client_folder, f"temp_{file_name}")
            with open(temp_path, "wb") as f:
                f.write(template_file.getvalue())
            
            # Vérifier si le fichier est supporté
            if file_type not in SUPPORTED_EXTENSIONS:
                error_msg = f"❌ Échec : Type de fichier non supporté ({file_type})"
                rapport.append(error_msg)
                processing_errors.append(error_msg)
                details_container.warning(f"⚠️ {file_name} : Type de fichier non supporté")
                continue
            
            # Traiter le template
            try:
                success = process_client_template(
                    temp_path,
                    output_path,
                    file_type,
                    st.session_state.footer_data,
                    footer_text,
                    client_logo_path
                )
                
                # Vérifier si le fichier a été modifié
                if success and os.path.exists(output_path):
                    # Vérifier que le fichier de sortie est différent du fichier d'entrée
                    with open(temp_path, "rb") as f1, open(output_path, "rb") as f2:
                        if f1.read() != f2.read():
                            rapport.append(f"✓ Succès : {file_name}")
                            processed_files.append(file_name)
                            details_container.success(f"✅ {file_name} : Traité avec succès")
                        else:
                            error_msg = f"❌ Échec : Le fichier n'a pas été modifié"
                            rapport.append(error_msg)
                            processing_errors.append(error_msg)
                            details_container.warning(f"⚠️ {file_name} : Non modifié")
                else:
                    error_msg = f"❌ Échec : Erreur lors du traitement"
                    rapport.append(error_msg)
                    processing_errors.append(error_msg)
                    details_container.error(f"❌ {file_name} : Erreur de traitement")
            except Exception as e:
                error_msg = f"❌ Échec : {str(e)}"
                rapport.append(error_msg)
                processing_errors.append(error_msg)
                details_container.error(f"❌ {file_name} : {str(e)}")
            
            # Nettoyer le fichier temporaire
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # Liste pour suivre les erreurs de ZIP
        zip_errors = []
        
        # Mettre à jour la progression - création du ZIP
        update_progress("Création du fichier ZIP")
        
        # Créer le ZIP
        zip_path = os.path.join(client_folder, "documents_client.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Ajouter les documents traités
            for file_name in processed_files:
                file_path = os.path.join(client_folder, file_name)
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.join("documents", file_name))
                    details_container.info(f"📦 {file_name} ajouté au ZIP")
                else:
                    error_msg = f"❌ Erreur : {file_name} n'a pas été trouvé"
                    details_container.error(error_msg)
                    zip_errors.append(error_msg)
            
            # Ajouter toutes les erreurs au rapport
            for error in zip_errors:
                rapport.append(f"\n{error}")
            
            # Sauvegarder le rapport final
            rapport_path = os.path.join(client_folder, "rapport_traitement.txt")
            with open(rapport_path, "w", encoding="utf-8") as f:
                f.write("\n".join(rapport))
            
            # Ajouter le rapport au ZIP (une seule fois)
            zipf.write(rapport_path, "rapport_traitement.txt")
            details_container.info("📄 Rapport ajouté au ZIP")
        
        # Mettre à jour la progression - finalisation
        update_progress("Finalisation")
        
        # Lire le contenu du ZIP
        with open(zip_path, "rb") as f:
            zip_data = f.read()
        
        # Nettoyer les fichiers temporaires
        shutil.rmtree(client_folder)
        
        # Effacer les conteneurs temporaires
        progress_bar.empty()
        details_container.empty()
        
        # Mettre à jour le statut final
        if processed_files:
            status_container.success(f"✅ Traitement terminé : {len(processed_files)} documents générés avec succès")
        else:
            status_container.error("❌ Aucun document n'a pu être généré")
        
        # Créer le bouton de téléchargement
        st.download_button(
            label="📥 Télécharger les documents",
            data=zip_data,
            file_name="documents_client.zip",
            mime="application/zip"
        )
        
        # Afficher les résultats
        if processing_errors or zip_errors:
            st.warning(f"⚠️ {len(processing_errors) + len(zip_errors)} erreurs se sont produites pendant le traitement")
        
    except Exception as e:
        st.error(f"❌ Une erreur est survenue : {str(e)}")
        # Nettoyer en cas d'erreur
        if os.path.exists(client_folder):
            shutil.rmtree(client_folder)

def setup_database():
    """Initialise la base de données SQLite pour stocker les clients"""
    # Créer un dossier pour la base de données
    db_folder = os.path.join(SCRIPT_DIR, "database")
    os.makedirs(db_folder, exist_ok=True)
    
    # Chemin vers le fichier de la base de données
    db_path = os.path.join(db_folder, "clients.db")
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Création de la table clients si elle n'existe pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        data TEXT NOT NULL,
        creation_date TEXT,
        logo_path TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    
    return db_path

def save_client(name, data, logo_file=None):
    """Sauvegarde un client dans la base de données"""
    db_path = os.path.join(SCRIPT_DIR, "database", "clients.db")
    
    # Sauvegarder le logo si fourni
    logo_path = None
    if logo_file:
        logo_folder = os.path.join(SCRIPT_DIR, "database", "logos")
        os.makedirs(logo_folder, exist_ok=True)
        logo_path = os.path.join(logo_folder, f"{name.replace(' ', '_')}_logo.png")
        with open(logo_path, "wb") as f:
            f.write(logo_file.getvalue())
    
    # Convertir les données en JSON
    data_json = json.dumps(data)
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier si le client existe déjà
    cursor.execute("SELECT id FROM clients WHERE name = ?", (name,))
    result = cursor.fetchone()
    
    if result:
        # Mettre à jour le client existant
        cursor.execute(
            "UPDATE clients SET data = ?, logo_path = ? WHERE name = ?",
            (data_json, logo_path, name)
        )
        client_id = result[0]
    else:
        # Créer un nouveau client
        cursor.execute(
            "INSERT INTO clients (name, data, creation_date, logo_path) VALUES (?, ?, ?, ?)",
            (name, data_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), logo_path)
        )
        client_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return client_id

def get_all_clients():
    """Récupère tous les clients de la base de données"""
    db_path = os.path.join(SCRIPT_DIR, "database", "clients.db")
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer tous les clients
    cursor.execute("SELECT id, name, data, creation_date, logo_path FROM clients ORDER BY name")
    clients = cursor.fetchall()
    
    conn.close()
    
    # Convertir en liste de dictionnaires
    clients_list = []
    for client in clients:
        client_dict = {
            "id": client[0],
            "name": client[1],
            "data": json.loads(client[2]),
            "creation_date": client[3],
            "logo_path": client[4]
        }
        clients_list.append(client_dict)
    
    return clients_list

def get_client_by_id(client_id):
    """Récupère un client par son ID"""
    db_path = os.path.join(SCRIPT_DIR, "database", "clients.db")
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer le client
    cursor.execute("SELECT id, name, data, creation_date, logo_path FROM clients WHERE id = ?", (client_id,))
    client = cursor.fetchone()
    
    conn.close()
    
    if client:
        client_dict = {
            "id": client[0],
            "name": client[1],
            "data": json.loads(client[2]),
            "creation_date": client[3],
            "logo_path": client[4]
        }
        return client_dict
    
    return None

def delete_client(client_id):
    """Supprime un client de la base de données"""
    db_path = os.path.join(SCRIPT_DIR, "database", "clients.db")
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer le chemin du logo
    cursor.execute("SELECT logo_path FROM clients WHERE id = ?", (client_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        logo_path = result[0]
        if os.path.exists(logo_path):
            os.remove(logo_path)
    
    # Supprimer le client
    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    
    conn.commit()
    conn.close()

def load_client_data(client_id):
    """Charge les données d'un client dans st.session_state.footer_data"""
    client = get_client_by_id(client_id)
    if client:
        st.session_state.footer_data = client["data"]
        st.session_state.selected_client_id = client_id
        
        # Charger le logo du client si disponible
        if client["logo_path"] and os.path.exists(client["logo_path"]):
            try:
                with open(client["logo_path"], "rb") as f:
                    logo_bytes = f.read()
                    st.session_state.client_logo_bytes = logo_bytes
            except Exception as e:
                print(f"Erreur lors du chargement du logo : {str(e)}")
        
        return client
    return None

def reset_client_data():
    """Réinitialise les données du client"""
    st.session_state.footer_data = {
        'raison_socialOF': "",
        'StatuOF': "",
        'capitalOF': "",
        'AdresseOF': "",
        'CodepostaleOF': "",
        'VilleOF': "",
        'PaysOF': "France",
        'TéléphoneOF': "",
        'MailOF': "",
        'siretOF': "",
        'RCSOF': "",
        'APEOF': "",
        'TVAOF': "",
        'NDAOF': "",
        'RégiondrieetsOF': "",
        'DatemajdocOF': ""
    }
    st.session_state.selected_client_id = None
    if hasattr(st.session_state, 'client_logo_bytes'):
        del st.session_state.client_logo_bytes

def main():
    init_session_state()
    
    st.title("🏢 Management Solution - Gestionnaire de Documents")
    
    # Création d'onglets pour organiser l'interface
    tab1, tab2, tab3 = st.tabs(["📁 Traitement des documents", "👤 Création de client", "📋 Liste des clients"])
    
    with tab1:
        # Contenu existant pour le traitement des documents
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
            
            # Configuration du pied de page
            st.write("##### Pied de page")
            st.write("Remplissez les informations ci-dessous pour générer le pied de page")
            
            # Création de deux colonnes pour le formulaire
            footer_col1, footer_col2 = st.columns(2)
            
            with footer_col1:
                st.session_state.footer_data['raison_socialOF'] = st.text_input("Raison sociale", st.session_state.footer_data['raison_socialOF'], key="config_raison_social")
                st.session_state.footer_data['StatuOF'] = st.text_input("Statut juridique", st.session_state.footer_data['StatuOF'], key="config_statut")
                st.session_state.footer_data['capitalOF'] = st.text_input("Capital (EUR)", st.session_state.footer_data['capitalOF'], key="config_capital")
                st.session_state.footer_data['AdresseOF'] = st.text_input("Adresse", st.session_state.footer_data['AdresseOF'], key="config_adresse")
                st.session_state.footer_data['CodepostaleOF'] = st.text_input("Code postal", st.session_state.footer_data['CodepostaleOF'], key="config_codepostal")
                st.session_state.footer_data['VilleOF'] = st.text_input("Ville", st.session_state.footer_data['VilleOF'], key="config_ville")
                st.session_state.footer_data['PaysOF'] = st.text_input("Pays", st.session_state.footer_data['PaysOF'], key="config_pays")
                st.session_state.footer_data['TéléphoneOF'] = st.text_input("Téléphone", st.session_state.footer_data['TéléphoneOF'], key="config_telephone")
            
            with footer_col2:
                st.session_state.footer_data['MailOF'] = st.text_input("Email", st.session_state.footer_data['MailOF'], key="config_email")
                st.session_state.footer_data['siretOF'] = st.text_input("N° SIRET", st.session_state.footer_data['siretOF'], key="config_siret")
                st.session_state.footer_data['RCSOF'] = st.text_input("RCS", st.session_state.footer_data['RCSOF'], key="config_rcs")
                st.session_state.footer_data['APEOF'] = st.text_input("Code APE", st.session_state.footer_data['APEOF'], key="config_ape")
                st.session_state.footer_data['TVAOF'] = st.text_input("N° TVA", st.session_state.footer_data['TVAOF'], key="config_tva")
                st.session_state.footer_data['NDAOF'] = st.text_input("N° NDA", st.session_state.footer_data['NDAOF'], key="config_nda")
                st.session_state.footer_data['RégiondrieetsOF'] = st.text_input("Région DRIEETS", st.session_state.footer_data['RégiondrieetsOF'], key="config_region")
                st.session_state.footer_data['DatemajdocOF'] = st.text_input("Date maj doc", st.session_state.footer_data['DatemajdocOF'], key="config_date")
            
            # Aperçu du pied de page
            st.write("##### Aperçu du pied de page")
            preview_footer = generate_footer_text(st.session_state.footer_data)
            st.text_area("", preview_footer, height=150, disabled=True)
            
            # Bouton pour mettre à jour le pied de page
            if st.button("Mettre à jour le pied de page"):
                st.session_state.footer_text = preview_footer
                with open(os.path.join(SCRIPT_DIR, "footer.txt"), "w", encoding='utf-8') as f:
                    f.write(preview_footer)
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
                
                # Ajout de la version PDF si c'est un fichier docx
                if file.endswith('.docx'):
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
                    # Affichage du bouton PDF uniquement pour les fichiers docx
                    if file.endswith('.docx'):
                        pdf_path = os.path.join(PDF_OUTPUT_FOLDER, file.rsplit('.', 1)[0] + '.pdf')
                        if os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="PDF",
                                    data=f,
                                    file_name=file.rsplit('.', 1)[0] + '.pdf',
                                    mime="application/pdf"
                                )

    with tab2:
        st.subheader("👤 Création d'un nouveau client")
        
        # Sélection d'un client existant
        clients = get_all_clients()
        client_names = ["Nouveau client"] + [client["name"] for client in clients]
        
        selected_client_name = st.selectbox(
            "Sélectionner un client existant ou créer un nouveau client",
            client_names,
            index=0
        )
        
        # Si un client existant est sélectionné, charger ses données
        if selected_client_name != "Nouveau client":
            selected_client = next((c for c in clients if c["name"] == selected_client_name), None)
            if selected_client:
                load_client_data(selected_client["id"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input("Nom du client", 
                                      st.session_state.footer_data.get('raison_socialOF', ""), 
                                      key="client_name")
            st.session_state.footer_data['raison_socialOF'] = st.text_input("Raison sociale", 
                                                                          st.session_state.footer_data['raison_socialOF'], 
                                                                          key="client_raison_social")
            st.session_state.footer_data['StatuOF'] = st.text_input("Statut juridique", 
                                                                  st.session_state.footer_data['StatuOF'], 
                                                                  key="client_statut")
            st.session_state.footer_data['capitalOF'] = st.text_input("Capital (EUR)", 
                                                                    st.session_state.footer_data['capitalOF'], 
                                                                    key="client_capital")
            st.session_state.footer_data['AdresseOF'] = st.text_input("Adresse", 
                                                                    st.session_state.footer_data['AdresseOF'], 
                                                                    key="client_adresse")
            st.session_state.footer_data['CodepostaleOF'] = st.text_input("Code postal", 
                                                                        st.session_state.footer_data['CodepostaleOF'], 
                                                                        key="client_codepostal")
            st.session_state.footer_data['VilleOF'] = st.text_input("Ville", 
                                                                  st.session_state.footer_data['VilleOF'], 
                                                                  key="client_ville")
            st.session_state.footer_data['PaysOF'] = st.text_input("Pays", 
                                                                 st.session_state.footer_data['PaysOF'], 
                                                                 key="client_pays")
        
        with col2:
            st.session_state.footer_data['TéléphoneOF'] = st.text_input("Téléphone", 
                                                                       st.session_state.footer_data['TéléphoneOF'], 
                                                                       key="client_telephone")
            st.session_state.footer_data['MailOF'] = st.text_input("Email", 
                                                                 st.session_state.footer_data['MailOF'], 
                                                                 key="client_email")
            st.session_state.footer_data['siretOF'] = st.text_input("N° SIRET", 
                                                                  st.session_state.footer_data['siretOF'], 
                                                                  key="client_siret")
            st.session_state.footer_data['RCSOF'] = st.text_input("RCS", 
                                                                st.session_state.footer_data['RCSOF'], 
                                                                key="client_rcs")
            st.session_state.footer_data['APEOF'] = st.text_input("Code APE", 
                                                                st.session_state.footer_data['APEOF'], 
                                                                key="client_ape")
            st.session_state.footer_data['TVAOF'] = st.text_input("N° TVA", 
                                                                st.session_state.footer_data['TVAOF'], 
                                                                key="client_tva")
            st.session_state.footer_data['NDAOF'] = st.text_input("N° NDA", 
                                                                st.session_state.footer_data['NDAOF'], 
                                                                key="client_nda")
            st.session_state.footer_data['RégiondrieetsOF'] = st.text_input("Région DRIEETS", 
                                                                          st.session_state.footer_data['RégiondrieetsOF'], 
                                                                          key="client_region")
            st.session_state.footer_data['DatemajdocOF'] = st.text_input("Date maj doc", 
                                                                       st.session_state.footer_data['DatemajdocOF'], 
                                                                       key="client_date")
        
        # Upload des dossiers/templates
        st.write("##### Dossiers templates")
        uploaded_templates = st.file_uploader(
            "Déposez vos documents templates ici",
            accept_multiple_files=True,
            type=list(SUPPORTED_EXTENSIONS.keys()),
            key="client_templates"
        )
        
        # Upload du logo client
        st.write("##### Logo du client")
        
        # Afficher le logo actuel s'il est disponible
        if hasattr(st.session_state, 'client_logo_bytes') and st.session_state.client_logo_bytes:
            st.image(st.session_state.client_logo_bytes, width=150, caption="Logo actuel")
        
        uploaded_logo = st.file_uploader("Logo du client", type=['png', 'jpg', 'jpeg'], key="client_logo_upload")
        
        # Si le logo est téléversé, le stocker
        if uploaded_logo:
            logo_to_use = uploaded_logo
        # Sinon utiliser le logo existant
        elif hasattr(st.session_state, 'client_logo_bytes') and st.session_state.client_logo_bytes:
            # Créer un fichier temporaire avec le logo existant
            from io import BytesIO
            logo_to_use = BytesIO(st.session_state.client_logo_bytes)
            logo_to_use.name = "logo_existant.png"  # Ajouter un nom pour que streamlit le traite comme un UploadedFile
        else:
            logo_to_use = None
        
        # Bouton pour générer les documents
        if st.button("Générer les documents avec les informations client"):
            if uploaded_templates:
                generate_client_documents(uploaded_templates, logo_to_use)
            else:
                st.warning("Veuillez d'abord téléverser des documents templates.")
        
        # Bouton pour sauvegarder le client
        if st.button("Sauvegarder ce client"):
            if client_name:
                # Utiliser le nom du client si différent de la raison sociale
                name_to_save = client_name or st.session_state.footer_data['raison_socialOF']
                client_id = save_client(name_to_save, st.session_state.footer_data, logo_to_use)
                st.session_state.selected_client_id = client_id
                st.success(f"✅ Client '{name_to_save}' sauvegardé avec succès!")
                
                # Si un logo a été fourni, le stocker en session
                if logo_to_use:
                    logo_to_use.seek(0)
                    st.session_state.client_logo_bytes = logo_to_use.read()
            else:
                st.error("⚠️ Veuillez entrer un nom pour le client")
    
    with tab3:
        st.subheader("📋 Liste des clients")
        
        # Bouton pour créer un nouveau client
        col_create, col_dummy = st.columns([1, 3])
        with col_create:
            if st.button("➕ Créer un nouveau client", type="primary"):
                reset_client_data()
                st.success("✅ Les champs ont été réinitialisés. Allez dans l'onglet 'Création de client' pour continuer.")
                st.balloons()
        
        # Récupérer tous les clients
        clients = get_all_clients()
        
        if not clients:
            st.info("Aucun client n'a été créé pour l'instant.")
        else:
            # Créer un DataFrame pour afficher les clients
            clients_df = []
            for client in clients:
                clients_df.append({
                    "ID": client["id"],
                    "Nom": client["name"],
                    "Raison sociale": client["data"].get("raison_socialOF", ""),
                    "Date de création": client["creation_date"],
                    "Logo": "Oui" if client["logo_path"] else "Non"
                })
            
            df = pd.DataFrame(clients_df)
            st.dataframe(df, use_container_width=True)
            
            # Sélection d'un client pour le modifier ou le supprimer
            col1, col2 = st.columns(2)
            
            with col1:
                client_to_load = st.selectbox(
                    "Sélectionner un client pour le modifier",
                    [client["name"] for client in clients]
                )
                
                if st.button("Charger ce client"):
                    selected_client = next((c for c in clients if c["name"] == client_to_load), None)
                    if selected_client:
                        load_client_data(selected_client["id"])
                        st.success(f"✅ Client '{client_to_load}' chargé avec succès!")
                        st.rerun()
            
            with col2:
                client_to_delete = st.selectbox(
                    "Sélectionner un client pour le supprimer",
                    [client["name"] for client in clients],
                    key="delete_client_selectbox"
                )
                
                # Trouver l'ID du client sélectionné pour la suppression
                selected_client_to_delete = next((c for c in clients if c["name"] == client_to_delete), None)
                
                # Initialiser les variables d'état si elles n'existent pas
                if "delete_confirmation_requested" not in st.session_state:
                    st.session_state.delete_confirmation_requested = False
                if "client_to_delete_id" not in st.session_state:
                    st.session_state.client_to_delete_id = None
                
                # Fonction pour demander confirmation
                def request_delete_confirmation():
                    st.session_state.delete_confirmation_requested = True
                    if selected_client_to_delete:
                        st.session_state.client_to_delete_id = selected_client_to_delete["id"]
                
                # Fonction pour confirmer la suppression
                def confirm_delete():
                    if st.session_state.client_to_delete_id:
                        delete_client(st.session_state.client_to_delete_id)
                        st.session_state.delete_confirmation_requested = False
                        st.session_state.client_to_delete_id = None
                        reset_client_data()
                        st.success(f"✅ Client '{client_to_delete}' supprimé avec succès!")
                        st.rerun()
                
                # Fonction pour annuler la suppression
                def cancel_delete():
                    st.session_state.delete_confirmation_requested = False
                    st.session_state.client_to_delete_id = None
                
                # Afficher le bouton de suppression initial ou la confirmation
                if not st.session_state.delete_confirmation_requested:
                    st.button("Supprimer ce client", on_click=request_delete_confirmation, disabled=not selected_client_to_delete)
                else:
                    st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer définitivement le client '{client_to_delete}'? Cette action est irréversible.")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        st.button("☢️ Oui, supprimer", on_click=confirm_delete, key="confirm_delete_btn")
                    with col_cancel:
                        st.button("❌ Annuler", on_click=cancel_delete, key="cancel_delete_btn")

if __name__ == "__main__":
    main() 
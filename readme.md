# Management Solution - Gestionnaire de Documents 📄

Application web permettant de gérer automatiquement les en-têtes et pieds de page des documents professionnels.

## 🌟 Fonctionnalités

- ✨ Interface web intuitive
- 📝 Traitement automatique des documents Word
- 🖼️ Personnalisation du logo
- ✍️ Personnalisation du pied de page
- 📦 Export en lot au format ZIP
- 📱 Interface responsive

## 🚀 Accès à l'application

L'application est accessible à l'adresse :
[https://placeandreplace.streamlit.app](https://placeandreplace.streamlit.app)

## 👨‍💻 Développement

### Prérequis

- Python 3.11 ou supérieur
- Git

### Installation locale

```bash
# Cloner le dépôt
git clone git@github.com:tom-guastapaglia/placeandreplace.git
cd placeandreplace

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Windows :
venv\Scripts\activate
# Sur macOS/Linux :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

### Structure du projet

```
placeandreplace/
├── app.py                 # Application principale
├── replace_header_footer.py # Logique de traitement des documents
├── requirements.txt       # Dépendances Python
├── footer.txt            # Texte du pied de page
├── logo.png              # Logo par défaut
└── .streamlit/           # Configuration Streamlit
    └── config.toml
```

## 🔄 Déploiement

L'application est hébergée sur Streamlit Cloud. Pour déployer une mise à jour :

1. Pousser les modifications sur la branche main :
```bash
git add .
git commit -m "Description des modifications"
git push origin main
```

2. Le déploiement est automatique ! Streamlit Cloud détecte les changements et met à jour l'application.

## ⚙️ Administration

### Interface d'administration Streamlit Cloud

1. Accéder à [https://share.streamlit.io/](https://share.streamlit.io/)
2. Se connecter avec le compte GitHub associé
3. Sélectionner l'application "placeandreplace"

Dans l'interface d'administration, vous pouvez :
- 📊 Voir les logs de l'application
- 🔄 Redémarrer l'application
- ⚙️ Modifier les paramètres
- 📈 Voir les statistiques d'utilisation

### Modification des paramètres par défaut

#### Logo
- Format : PNG
- Dimensions recommandées : 300x100 pixels
- Emplacement : `logo.png` à la racine du projet

#### Pied de page
- Fichier : `footer.txt`
- Encodage : UTF-8
- Format : Texte simple

## 🔒 Sécurité

- Les documents uploadés sont temporaires et supprimés après traitement
- Les données ne sont pas stockées de manière permanente
- L'application utilise HTTPS pour toutes les communications

## 🤝 Contribution

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
```bash
git checkout -b feature/ma-fonctionnalite
```
3. Commiter vos changements
```bash
git commit -m "Ajout de ma fonctionnalité"
```
4. Pousser sur votre fork
```bash
git push origin feature/ma-fonctionnalite
```
5. Créer une Pull Request

## 📝 Licence

© 2024 Management Solution - Tous droits réservés

## 📞 Support

Pour toute question ou assistance :
- 📧 Email : [contact@somanagements.fr](mailto:contact@somanagements.fr)
- 💬 GitHub Issues : [Créer un ticket](https://github.com/tom-guastapaglia/placeandreplace/issues)

## ⚡ Performance

- Temps de traitement moyen : < 2s par document
- Taille maximale des fichiers : 200 MB
- Formats supportés : .docx, .pptx, .xlsx
```
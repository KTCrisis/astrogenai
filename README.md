## AstroGenAI 🌌
AstroGenAI est une application web complète et modulaire conçue pour la génération de contenu astrologique par intelligence artificielle. Elle combine des modèles de langage locaux (via Ollama), la génération d'images et de vidéos (via ComfyUI), et des calculs astronomiques précis pour créer des horoscopes, des cartes du ciel, et des vidéos prêtes à être publiées sur les réseaux sociaux.


## Fonctionnalités Clés ✨
🔮 Horoscopes par IA : Génération d'horoscopes quotidiens ou individuels basés sur des données astrales réelles et des modèles de langage (Llama, Mistral).

🤖 Chat Astral : Une interface de chat pour converser avec un astrologue IA et poser des questions sur n'importe quel sujet astrologique.

** celestial_map:️ Carte du Ciel** : Génération et affichage de la carte du ciel pour n'importe quelle date, montrant les positions planétaires exactes.

🎬 Génération de Vidéos de Constellations : Création automatique de clips vidéo animés représentant les constellations du zodiaque via ComfyUI.

🎞️ Montage Vidéo Automatisé :

Synthèse vocale (Text-to-Speech) des horoscopes en français.

Transcription et incrustation de sous-titres synchronisés.

Mixage avec une musique de fond.

Assemblage de vidéos complètes prêtes à l'emploi.

🚀 Workflows Complets : Scripts et endpoints API pour orchestrer l'ensemble du processus, de la génération de texte à l'upload final sur YouTube.

📤 Upload sur YouTube : Service intégré pour téléverser les vidéos générées directement sur une chaîne YouTube via l'API.

## Architecture du Projet 🛠️
L'application repose sur une architecture de services modulaire ("MCP" - Master Control Program) où chaque grande fonctionnalité est gérée par un service dédié situé dans le package astro_core. Un serveur web Flask (main.py) sert d'interface et d'orchestrateur, exposant une API REST complète pour communiquer avec les services et le frontend.

main.py: Serveur web Flask, gestion des routes API.

config.py: Configuration centralisée du projet.

astro_core/services/: Contient les modules logiques.

astro_mcp.py: Gère les calculs astraux et la génération de texte.

comfyui_mcp.py: Interface avec le serveur ComfyUI pour la génération vidéo.

video_mcp.py: Gère le montage (transcription, sous-titres, assemblage).

youtube_mcp.py: Gère la communication avec l'API YouTube.

static/ & templates/: Fichiers du frontend web (JS, CSS, HTML).

scripts/: Contient des outils de maintenance (nettoyage, etc.).

## Technologies Utilisées 💻
Backend: Python 3.10+, Flask

IA (Texte): Ollama (avec des modèles comme Llama 3.1, Mistral, etc.)

IA (Vidéo): ComfyUI avec AnimateDiff

IA (Audio): gTTS (Text-to-Speech), openai-whisper (Transcription)

Calculs Astronomiques: skyfield

Montage Vidéo: ffmpeg

Frontend: HTML5, CSS3, JavaScript (vanilla)

Dépendances Python: requests, python-dotenv, mutagen, matplotlib, google-api-python-client, etc. (voir requirements.txt)

## Installation & Configuration ⚙️
Suivez ces étapes pour lancer le projet en local.

### Prérequis
Assurez-vous d'avoir les éléments suivants installés et en cours d'exécution :

Python 3.10 ou supérieur.

Git.

Ollama : ollama.com. Après installation, tirez les modèles nécessaires (ex: ollama pull mistral).

ComfyUI : Suivez les instructions d'installation sur le GitHub de ComfyUI.

FFmpeg : Doit être installé et accessible depuis votre PATH.

### Étapes d'installation
Clonez le dépôt :

Bash

git clone https://github.com/KTCrisis/astrogenai.git
cd astrogenai
Créez un environnement virtuel et activez-le :

Bash

python -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate
Installez les dépendances Python :

Bash

pip install -r requirements.txt
Configurez votre environnement :

Copiez le fichier .env.example (s'il existe) ou créez un fichier .env à la racine du projet.

Remplissez-le avec vos configurations locales. Il doit contenir au minimum :

Code snippet

# Fichier .env
FLASK_ENV="development"
DEBUG=True
HOST="0.0.0.0"
PORT=5000

# URLs des services locaux
OLLAMA_BASE_URL="http://127.0.0.1:11434"
COMFYUI_SERVER="127.0.0.1:8188"
Configurez l'API YouTube :

Suivez les instructions de Google pour créer des identifiants API.

Placez votre fichier credentials.json dans astro_core/services/youtube/.

Exécutez le script d'authentification une première fois pour générer le token.json :

Bash

python astro_core/services/youtube/youtube_auth.py
Placez les assets :

Ajoutez vos images de référence pour les signes dans assets/images/ (ex: aries_image.jpg).

Ajoutez votre fichier de musique de fond dans assets/music/.

## Lancement de l'Application 🚀
Assurez-vous que vos serveurs Ollama et ComfyUI sont bien en cours d'exécution.

Depuis la racine du projet, lancez le serveur Flask :

Bash

python main.py
Ouvrez votre navigateur et allez à l'adresse http://127.0.0.1:5000 (ou le port que vous avez configuré).

## Scripts Utilitaires 🧹
Des scripts de maintenance sont disponibles dans le dossier scripts/. Exécutez-les depuis la racine du projet.

Nettoyer les fichiers générés et/ou débloquer les fichiers :

Bash

python scripts/purge_data.py
Le script vous proposera un menu pour choisir l'action à effectuer.

## Feuille de Route 🗺️
[ ] Améliorer l'orchestrateur pour une gestion plus intelligente des workflows.

[ ] Ajouter plus de templates de vidéo pour ComfyUI.

[ ] Mettre en place un système de comptes utilisateurs pour sauvegarder les thèmes astraux.

[ ] Optimiser les performances de la génération vidéo en lot.

[ ] Créer une documentation complète de l'API.

## Licence
Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
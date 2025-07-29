import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement du fichier .env
# Cela rend les variables de .env accessibles via os.environ
load_dotenv()

class Settings:
    """
    Configuration centralisée de l'application AstroGenAI.
    Lit les variables d'environnement et définit les chemins de manière dynamique.
    """
    # --- Configuration du Projet ---
    # Définit le dossier racine du projet (où se trouve ce fichier config.py)
    BASE_DIR = Path(__file__).resolve().parent

    # --- Configuration du Serveur Flask ---
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))

    # Authentification (désactivée par défaut)
    AUTH_ENABLED = False
    AUTH_USERNAME = "admin"
    AUTH_PASSWORD = "****"

    # --- Configuration des Services Externes ---
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    COMFYUI_SERVER = os.getenv("COMFYUI_SERVER", "127.0.0.1:8188")

    # --- Configuration des Modèles IA ---
    # Modèle pour la génération de texte (horoscopes)
    OLLAMA_TEXT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q8_0")
    # Modèle pour l'orchestration (plus puissant si possible)
    OLLAMA_ORCHESTRATOR_MODEL = os.getenv("OLLAMA_ORCHESTRATOR_MODEL", "llama3.1:8b-instruct-q8_0")
    # Modèle pour le chat (conversationnel)
    OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3:8b")
    OLLAMA_TIMEOUT = 10
    OLLAMA_CHAT_TIMEOUT = 60


    # --- Définition Dynamique des Chemins ---

    # Dossier du code source
    SOURCE_CODE_DIR = BASE_DIR / "astro_core"

    # Dossiers d'entrée (Assets)
    ASSETS_DIR = BASE_DIR / "assets"
    INPUT_IMAGES_DIR = ASSETS_DIR / "images" # Pour ControlNet
    MUSIC_DIR = ASSETS_DIR / "music"
    WORKFLOW_TEMPLATES_DIR = ASSETS_DIR / "workflow"

    # Dossiers de sortie (Output)
    OUTPUT_DIR = BASE_DIR / "output"
    GENERATED_AUDIO_DIR = OUTPUT_DIR / "generated_audio"
    GENERATED_VIDEOS_DIR = OUTPUT_DIR / "generated_video"
    FINAL_MONTAGE_DIR = OUTPUT_DIR / "final_montage"
    INDIVIDUAL_DIR = OUTPUT_DIR / "final_montage" / "individual"

    #Credentials
    YOUTUBE_CREDENTIALS_DIR = SOURCE_CODE_DIR / "services" / "youtube"


    # Dossiers Web (Flask)
    STATIC_DIR = BASE_DIR / "static"
    STATIC_CHARTS_DIR = STATIC_DIR / "charts"
    TEMPLATES_DIR = BASE_DIR / "templates"
    
    # Chemin vers la police pour le montage vidéo (IMPORTANT)
    FFMPEG_TIMEOUT = 300
    FFMPEG_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Instance unique de la configuration pour être importée dans toute l'application
settings = Settings()
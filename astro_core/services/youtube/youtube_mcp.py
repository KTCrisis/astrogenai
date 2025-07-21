
#!/usr/bin/env python3
"""
MCP YouTube Server - AstroGenAI
Service MCP complet pour l'upload automatique sur YouTube.
"""

import os
import sys
import datetime
import glob
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Dépendances Google API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Dépendance FastMCP
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️ FastMCP non disponible")

# Configuration des chemins
FINAL_MONTAGE_DIR = os.environ.get("VIDEO_MONTAGE_DIR", "final_montage")
INDIVIDUAL_DIR = os.path.join(FINAL_MONTAGE_DIR, "individual")
CREDENTIALS_DIR = os.environ.get("YOUTUBE_CREDENTIALS_DIR", "youtube_mcp")

# =============================================================================
# PARTIE 1 : MOTEUR D'UPLOAD 
# =============================================================================

@dataclass
class VideoMetadata:
    """Métadonnées d'une vidéo YouTube."""
    title: str
    description: str
    tags: list
    category_id: str = "22"  # People & Blogs par défaut
    privacy_status: str = "private"  # private, unlisted, public
    made_for_kids: bool = False

@dataclass
class UploadResult:
    """Résultat d'une tentative d'upload."""
    success: bool
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    title: str = ""
    error: Optional[str] = None
    upload_time: Optional[str] = None

class YouTubeUploader:
    """Gestionnaire d'upload YouTube pour AstroGenAI."""

    def __init__(self, credentials_path: str = CREDENTIALS_DIR):
        self.credentials_file = os.path.join(credentials_path, 'credentials.json')
        self.token_file = os.path.join(credentials_path, 'token.json')
        self.youtube_service = None
        self._authenticate()

    def _authenticate(self):
        """Authentification à l'API YouTube via le token."""
        try:
            if not os.path.exists(self.token_file):
                raise Exception(f"Token non trouvé à l'emplacement : {self.token_file}. Lancez d'abord le script d'authentification.")

            creds = Credentials.from_authorized_user_file(self.token_file)

            if not creds.valid:
                # Idéalement, il faudrait gérer le refresh ici, mais pour l'instant on demande de relancer l'auth.
                raise Exception("Token expiré ou invalide. Veuillez relancer l'authentification.")

            self.youtube_service = build('youtube', 'v3', credentials=creds)
            print("✅ Auth YouTube OK")

        except Exception as e:
            print(f"❌ Erreur d'authentification YouTube : {e}")
            self.youtube_service = None # S'assurer que le service n'est pas utilisable
            raise

    def create_astro_metadata(self, sign: str, date: Optional[str] = None, is_complete_video: bool = False) -> VideoMetadata:
        """Génère des métadonnées optimisées pour les vidéos d'horoscope."""
        if not date:
            date_obj = datetime.date.today()
        else:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()

        formatted_date = date_obj.strftime("%d/%m/%Y")

# =============================================================================
# METADATA VIDEO LONGUE
# =============================================================================
        if is_complete_video:
            title = f"🔮 Horoscope Complet du {formatted_date} - Tous les Signes Astrologiques | Prédictions AI"
            description = f"""🌟 Découvrez votre horoscope complet pour tous les signes du zodiaque pour le {formatted_date} !

Cette vidéo, entièrement générée par une intelligence artificielle, vous offre un guide astral quotidien pour naviguer les énergies cosmiques.

✨ DANS CETTE VIDÉO ✨
- Prédictions détaillées pour les 12 signes.
- Analyse des influences planétaires majeures du jour.
- Conseils pratiques et spirituels pour chaque signe.

🧠 NOTRE TECHNOLOGIE 🧠
- **Horoscopes** : Générés par des modèles de langage avancés (Ollama Llama3).
- **Calculs** : Positions planétaires réelles via Skyfield.
- **Visuels** : Constellations animées créées avec ComfyUI & AnimateDiff.
- **Voix & Sous-titres** : Synthèse vocale (gTTS) et transcription (Whisper AI).

Abonnez-vous pour ne manquer aucune prédiction !

#Horoscope #Astrologie #AstroGenAI #IA #HoroscopeComplet #Zodiaque #Prédictions #guidancespirituelle"""
            tags = ["horoscope", "astrologie", "horoscope complet", "tous les signes", "ia", "ai", "prédictions", "zodiaque", "guidance"]
            category_id = "24" # Entertainment
        else:
# =============================================================================
# METADATA SHORT VIDEO
# =============================================================================
            sign_names = {
                'aries': 'Bélier ♈', 'taurus': 'Taureau ♉', 'gemini': 'Gémeaux ♊',
                'cancer': 'Cancer ♋', 'leo': 'Lion ♌', 'virgo': 'Vierge ♍',
                'libra': 'Balance ♎', 'scorpio': 'Scorpion ♏', 'sagittarius': 'Sagittaire ♐',
                'capricorn': 'Capricorne ♑', 'aquarius': 'Verseau ♒', 'pisces': 'Poissons ♓'
            }
            sign_name = sign_names.get(sign.lower(), sign.title())
            title = f"🔮 Horoscope {sign_name} du {formatted_date} | Prédictions IA Personnalisées"
            description = f"""🌟 Découvrez votre horoscope personnalisé pour le signe du {sign_name} en date du {formatted_date} !

Laissez notre intelligence artificielle astrologique vous guider à travers les énergies cosmiques du jour.

#Horoscope #{sign.title()} #Astrologie #AstroGenAI #IA #PrédictionsQuotidiennes #{sign_name.split()[0]}"""
            tags = ["horoscope", "astrologie", f"horoscope {sign.lower()}", sign.lower(), "ia", "prédictions", "guidance", "zodiaque"]
            category_id = "22" # People & Blogs

        return VideoMetadata(title=title, description=description, tags=tags, category_id=category_id)

    def upload_video(self, video_path: str, metadata: VideoMetadata) -> UploadResult:
        """Upload une vidéo sur YouTube avec les métadonnées fournies."""
        if not self.youtube_service:
            return UploadResult(success=False, error="Service YouTube non authentifié.")
        if not os.path.exists(video_path):
            return UploadResult(success=False, error=f"Fichier vidéo non trouvé : {video_path}")

        try:
            print(f"📤 Démarrage de l'upload : {os.path.basename(video_path)}")
            print(f"📝 Titre : {metadata.title}")

            body = {
                'snippet': {
                    'title': metadata.title,
                    'description': metadata.description,
                    'tags': metadata.tags,
                    'categoryId': metadata.category_id
                },
                'status': {
                    'privacyStatus': metadata.privacy_status,
                    'madeForKids': metadata.made_for_kids
                }
            }

            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            request = self.youtube_service.videos().insert(part=','.join(body.keys()), body=body, media_body=media)

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Progression de l'upload : {int(status.progress() * 100)}%")

            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            print(f"✅ Upload réussi ! ID de la vidéo : {video_id}")
            print(f"🔗 URL : {video_url}")

            return UploadResult(
                success=True,
                video_id=video_id,
                video_url=video_url,
                title=metadata.title,
                upload_time=datetime.datetime.now().isoformat()
            )

        except HttpError as e:
            error_msg = f"Erreur HTTP YouTube : {e.resp.status} {e.content.decode('utf-8')}"
            print(f"❌ {error_msg}")
            return UploadResult(success=False, title=metadata.title, error=error_msg)
        except Exception as e:
            error_msg = f"Erreur inattendue pendant l'upload : {e}"
            print(f"❌ {error_msg}")
            return UploadResult(success=False, title=metadata.title, error=error_msg)

    def get_channel_info(self) -> Dict[str, Any]:
        """Récupère les informations de la chaîne YouTube authentifiée."""
        if not self.youtube_service:
            return {'success': False, 'error': "Service YouTube non authentifié."}
        try:
            request = self.youtube_service.channels().list(part='snippet,statistics', mine=True)
            response = request.execute()
            
            if response.get('items'):
                channel = response['items'][0]
                return {
                    'success': True,
                    'channel_id': channel['id'],
                    'title': channel['snippet']['title'],
                    'subscribers': channel['statistics'].get('subscriberCount', '0'),
                    'videos': channel['statistics'].get('videoCount', '0'),
                    'views': channel['statistics'].get('viewCount', '0')
                }
            return {'success': False, 'error': 'Aucune chaîne trouvée pour ce compte.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# =============================================================================
# PARTIE 2 : SERVEUR MCP
# =============================================================================

class YouTubeMCPServer:
    """Serveur MCP qui utilise le YouTubeUploader pour exposer des outils."""

    def __init__(self):
        try:
            self.uploader = YouTubeUploader()
        except Exception as e:
            print("Impossible d'initialiser le YouTubeMCPServer car l'uploader a échoué.")
            self.uploader = None
        
        self.signs_order = [
            'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
            'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
        ]
        self.sign_names = {sign: self.uploader.create_astro_metadata(sign).title.split(' ')[1] for sign in self.signs_order} if self.uploader else {}

    def _check_uploader(self):
        """Vérifie si l'uploader est disponible."""
        if not self.uploader:
            raise Exception("Le moteur d'upload YouTube n'a pas pu être initialisé.")

    def find_latest_video(self, directory: str, pattern: str) -> Optional[str]:
        """Trouve le fichier le plus récent correspondant à un pattern."""
        path_pattern = os.path.join(directory, pattern)
        files = glob.glob(path_pattern)
        return max(files, key=os.path.getctime) if files else None

    def get_available_videos(self) -> Dict[str, Any]:
        """Liste toutes les vidéos prêtes à être uploadées."""
        self._check_uploader()
        result = {"individual_videos": {}, "complete_video": None, "total_available": 0}

        for sign in self.signs_order:
            video_path = self.find_latest_video(INDIVIDUAL_DIR, f"{sign}_final_*.mp4")
            if video_path:
                result["individual_videos"][sign] = {
                    "path": video_path,
                    "filename": os.path.basename(video_path),
                    "size_mb": round(os.path.getsize(video_path) / (1024*1024), 2)
                }
                result["total_available"] += 1
        
        complete_video = self.find_latest_video(FINAL_MONTAGE_DIR, "horoscope_complet_*.mp4")
        if complete_video:
            result["complete_video"] = {
                "path": complete_video,
                "filename": os.path.basename(complete_video),
                "size_mb": round(os.path.getsize(complete_video) / (1024*1024), 2)
            }
        
        return result

    def upload_individual_video(self, sign: str, privacy: str = "private") -> Dict[str, Any]:
        """Prépare et upload la vidéo pour un signe."""
        self._check_uploader()
        video_path = self.find_latest_video(INDIVIDUAL_DIR, f"{sign}_final_*.mp4")
        if not video_path:
            return {"success": False, "error": f"Aucune vidéo finale trouvée pour {sign}."}

        metadata = self.uploader.create_astro_metadata(sign)
        metadata.privacy_status = privacy
        
        result = self.uploader.upload_video(video_path, metadata)
        return {"sign": sign, **result.__dict__}

    def upload_complete_horoscope(self, privacy: str = "private") -> Dict[str, Any]:
        """Prépare et upload la vidéo complète."""
        self._check_uploader()
        video_path = self.find_latest_video(FINAL_MONTAGE_DIR, "horoscope_complet_*.mp4")
        if not video_path:
            return {"success": False, "error": "Aucune vidéo complète trouvée."}

        metadata = self.uploader.create_astro_metadata("", is_complete_video=True)
        metadata.privacy_status = privacy
        
        result = self.uploader.upload_video(video_path, metadata)
        return {"type": "complete_horoscope", **result.__dict__}

    def get_youtube_status(self) -> Dict[str, Any]:
        """Retourne l'état de la connexion YouTube et des vidéos."""
        self._check_uploader()
        channel_info = self.uploader.get_channel_info()
        available_videos = self.get_available_videos()
        return {
            "success": channel_info['success'],
            "youtube_connected": channel_info['success'],
            "channel_info": channel_info,
            "available_videos": available_videos
        }

# =============================================================================
# INITIALISATION ET OUTILS MCP
# =============================================================================

# Instance globale du service
youtube_server = YouTubeMCPServer()

if FASTMCP_AVAILABLE and youtube_server.uploader:
    mcp = FastMCP("YouTubeServiceMCP")

    @mcp.tool()
    def get_status() -> dict:
        """Vérifie la connexion YouTube et liste les vidéos prêtes."""
        return youtube_server.get_youtube_status()

    @mcp.tool()
    def upload_sign_video(sign: str, privacy: str = "private") -> dict:
        """Upload la vidéo d'un signe. privacy: private, unlisted, ou public."""
        if sign not in youtube_server.signs_order:
            return {"success": False, "error": f"Signe invalide. Disponibles: {', '.join(youtube_server.signs_order)}"}
        return youtube_server.upload_individual_video(sign, privacy)
    
    @mcp.tool()
    def upload_complete_video(privacy: str = "private") -> dict:
        """Upload la vidéo complète. privacy: private, unlisted, ou public."""
        return youtube_server.upload_complete_horoscope(privacy)

    @mcp.tool()
    def upload_batch_videos(signs: Optional[List[str]] = None, privacy: str = "private") -> dict:
        """Upload en lot plusieurs vidéos. Si 'signs' est omis, tous les signes sont uploadés."""
        target_signs = signs if signs else youtube_server.signs_order
        results = [youtube_server.upload_individual_video(sign, privacy) for sign in target_signs]
        successful = sum(1 for r in results if r["success"])
        return {
            "summary": f"{successful}/{len(target_signs)} uploads réussis.",
            "total_requested": len(target_signs),
            "successful_uploads": successful,
            "failed_uploads": len(target_signs) - successful,
            "details": results
        }

# Point d'entrée pour tests en ligne de commande
if __name__ == "__main__":
    print("🎬 Service YouTube MCP - AstroGenAI")
    print("=" * 50)

    if not youtube_server.uploader:
        print("❌ Le service n'a pas pu démarrer. Vérifiez les erreurs d'authentification ci-dessus.")
        sys.exit(1)
        
    if not FASTMCP_AVAILABLE:
        print("❌ FastMCP non disponible. Le serveur ne peut pas démarrer. `pip install fastmcp`")
        print("ℹ️ Vous pouvez toujours utiliser les classes en mode module.")
    else:
        # Exécuter un test rapide si demandé
        if "--test" in sys.argv:
            print("\n🧪 Lancement des tests...")
            status = youtube_server.get_youtube_status()
            if status['success']:
                print(f"✅ Connexion réussie à la chaîne : {status['channel_info']['title']}")
                print(f"📊 Vidéos individuelles prêtes : {status['available_videos']['total_available']}")
                if status['available_videos']['complete_video']:
                    print("🎬 Vidéo complète prête.")
                else:
                    print("❓ Pas de vidéo complète trouvée.")
            else:
                print(f"❌ Test de statut échoué : {status.get('error')}")
        else:
            print("🚀 Démarrage du serveur FastMCP...")
            mcp.run()
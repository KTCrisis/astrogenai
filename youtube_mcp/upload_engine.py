#!/usr/bin/env python3
"""
Upload Engine - AstroGenAI YouTube Upload
Moteur d'upload vidéo avec métadonnées automatiques

Connexion à YouTube avec votre token existant
Recherche d'une vidéo test dans vos dossiers
Upload de la vidéo avec métadonnées automatiques
Affichage du lien YouTube

"""

import os
import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError



@dataclass
class VideoMetadata:
    """Métadonnées d'une vidéo"""
    title: str
    description: str
    tags: list
    category_id: str = "22"  # People & Blogs
    privacy_status: str = "private"  # private, unlisted, public
    made_for_kids: bool = False

@dataclass
class UploadResult:
    """Résultat d'un upload"""
    success: bool
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    title: str = ""
    error: Optional[str] = None
    upload_time: Optional[str] = None

class YouTubeUploader:
    """Gestionnaire d'upload YouTube pour AstroGenAI"""
    
    def __init__(self, credentials_file: str = '/home/fluxart/astroai_video/youtube_mcp/credentials.json', token_file: str = '/home/fluxart/astroai_video/youtube_mcp/token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.youtube_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authentification YouTube API"""
        try:
            if not os.path.exists(self.token_file):
                raise Exception("Token non trouvé. Lancez d'abord test_auth.py")
            
            # Charger credentials sauvegardés
            creds = Credentials.from_authorized_user_file(self.token_file)
            
            if not creds.valid:
                raise Exception("Token expiré. Relancez l'authentification")
            
            # Construire service YouTube
            self.youtube_service = build('youtube', 'v3', credentials=creds)
            print("✅ Service YouTube initialisé")
            
        except Exception as e:
            print(f"❌ Erreur authentification : {e}")
            raise
    
    def create_astro_metadata(self, sign: str, date: str = None) -> VideoMetadata:
        """Génère métadonnées automatiques pour horoscope"""
        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")
        
        # Noms des signes
        sign_names = {
            'aries': 'Bélier ♈', 'taurus': 'Taureau ♉', 'gemini': 'Gémeaux ♊',
            'cancer': 'Cancer ♋', 'leo': 'Lion ♌', 'virgo': 'Vierge ♍',
            'libra': 'Balance ♎', 'scorpio': 'Scorpion ♏', 'sagittarius': 'Sagittaire ♐',
            'capricorn': 'Capricorne ♑', 'aquarius': 'Verseau ♒', 'pisces': 'Poissons ♓'
        }
        
        sign_name = sign_names.get(sign.lower(), sign.title())
        formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        # Titre optimisé SEO
        title = f"🔮 Horoscope {sign_name} - {formatted_date} | Prédictions IA Personnalisées"
        
        # Description riche
        description = f"""🌟 Découvrez votre horoscope {sign_name} pour le {formatted_date} !

🤖 Généré par Intelligence Artificielle astrologique avancée
⭐ Prédictions personnalisées pour votre signe
🌙 Influences cosmiques et conseils pratiques
💫 Votre guide astral quotidien

📅 Dans cette vidéo :
- Prédictions spécifiques pour {sign_name}
- Influences planétaires du jour
- Conseils pratiques et spirituels
- Énergies cosmiques à anticiper

🔮 AstroGenAI - Votre intelligence artificielle astrologique
Abonnez-vous pour recevoir vos prédictions quotidiennes !

#Horoscope #Astrologie #{sign.title()} #Prédictions #IA #Voyance #Astres #Spiritualité #AstroGenAI"""

        # Tags optimisés
        tags = [
            "horoscope", "astrologie", f"{sign.lower()}", "prédictions", 
            "IA", "intelligence artificielle", "voyance", "astres", 
            "spiritualité", "cosmique", "planètes", f"{sign_name.split()[0].lower()}"
        ]
        
        return VideoMetadata(
            title=title,
            description=description,
            tags=tags,
            category_id="22",  # People & Blogs
            privacy_status="private"  # Commencer en privé pour tests
        )
    
    def upload_video(self, video_path: str, metadata: VideoMetadata) -> UploadResult:
        """Upload une vidéo sur YouTube"""
        if not os.path.exists(video_path):
            return UploadResult(
                success=False,
                error=f"Fichier vidéo non trouvé : {video_path}"
            )
        
        if not self.youtube_service:
            return UploadResult(
                success=False,
                error="Service YouTube non initialisé"
            )
        
        try:
            print(f"📤 Upload en cours : {os.path.basename(video_path)}")
            print(f"📝 Titre : {metadata.title}")
            
            # Préparer les métadonnées pour l'API
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
            
            # Préparer le fichier média
            media = MediaFileUpload(
                video_path,
                chunksize=-1,  # Upload en une fois pour petites vidéos
                resumable=True
            )
            
            # Lancer l'upload
            print("⬆️  Début de l'upload...")
            insert_request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Exécuter l'upload
            response = insert_request.execute()
            
            # Résultat de succès
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            upload_time = datetime.datetime.now().isoformat()
            
            print(f"✅ Upload réussi !")
            print(f"🎬 Video ID : {video_id}")
            print(f"🔗 URL : {video_url}")
            
            return UploadResult(
                success=True,
                video_id=video_id,
                video_url=video_url,
                title=metadata.title,
                upload_time=upload_time
            )
            
        except HttpError as e:
            error_msg = f"Erreur HTTP YouTube : {e}"
            print(f"❌ {error_msg}")
            
            return UploadResult(
                success=False,
                error=error_msg
            )
            
        except Exception as e:
            error_msg = f"Erreur upload : {e}"
            print(f"❌ {error_msg}")
            
            return UploadResult(
                success=False,
                error=error_msg
            )
    
    def upload_astro_video(self, video_path: str, sign: str, date: str = None) -> UploadResult:
        """Upload spécialisé pour vidéos d'horoscope"""
        # Générer métadonnées automatiques
        metadata = self.create_astro_metadata(sign, date)
        
        # Upload avec métadonnées
        return self.upload_video(video_path, metadata)
    
    def get_channel_info(self) -> Dict[str, Any]:
        """Récupère les informations de la chaîne"""
        try:
            request = self.youtube_service.channels().list(
                part='snippet,statistics',
                mine=True
            )
            response = request.execute()
            
            if response['items']:
                channel = response['items'][0]
                return {
                    'success': True,
                    'channel_id': channel['id'],
                    'title': channel['snippet']['title'],
                    'subscribers': channel['statistics'].get('subscriberCount', '0'),
                    'videos': channel['statistics'].get('videoCount', '0'),
                    'views': channel['statistics'].get('viewCount', '0')
                }
            else:
                return {'success': False, 'error': 'Chaîne non trouvée'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Test d'upload
def test_upload():
    """Test d'upload avec une vidéo exemple"""
    uploader = YouTubeUploader()
    
    # Informations chaîne
    channel_info = uploader.get_channel_info()
    if channel_info['success']:
        print("📺 Chaîne connectée :", channel_info['title'])
    
    # Rechercher une vidéo test
    test_video_paths = [
        "../final_montage/individual/aries_final_*.mp4",
        "../generated_videos/aries_*.mp4",
        "test_video.mp4"
    ]
    
    import glob
    test_video = None
    for pattern in test_video_paths:
        videos = glob.glob(pattern)
        if videos:
            test_video = videos[0]
            break
    
    if not test_video:
        print("❌ Aucune vidéo test trouvée")
        print("💡 Créez une vidéo avec le système existant d'abord")
        return
    
    print(f"🎬 Vidéo test trouvée : {test_video}")
    
    # Test upload
    result = uploader.upload_astro_video(test_video, "aries")
    
    if result.success:
        print("🎉 TEST D'UPLOAD RÉUSSI !")
        print(f"🔗 Vidéo YouTube : {result.video_url}")
    else:
        print(f"❌ Test échoué : {result.error}")

if __name__ == '__main__':
    print("🚀 AstroGenAI Upload Engine")
    print("=" * 40)
    test_upload()
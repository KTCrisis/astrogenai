# Fichier : tiktok_mcp.py (Nouveau fichier)

import os
import glob
import datetime
from typing import Optional, List
from tiktok_uploader.upload import upload_video
from config import settings # Importer la configuration pour les chemins

class TikTokUploader:
    """Gestionnaire d'upload pour TikTok."""

    def __init__(self):
        # L'authentification pour cette bibliothèque se fait via le sessionid du cookie.
        # C'est une information sensible à stocker dans votre .env
        self.session_id = os.getenv("TIKTOK_SESSION_ID")
        if not self.session_id:
            print("⚠️ AVERTISSEMENT: TIKTOK_SESSION_ID n'est pas défini dans le fichier .env. L'upload échouera.")

        # Utiliser les chemins définis dans config.py
        self.individual_dir = settings.FINAL_MONTAGE_DIR / "individual"
        self.signs_order = [
            'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
            'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
        ]
        self.sign_names = {
            'aries': 'Bélier ♈', 'taurus': 'Taureau ♉', 'gemini': 'Gémeaux ♊',
            'cancer': 'Cancer ♋', 'leo': 'Lion ♌', 'virgo': 'Vierge ♍',
            'libra': 'Balance ♎', 'scorpio': 'Scorpion ♏', 'sagittarius': 'Sagittaire ♐',
            'capricorn': 'Capricorne ♑', 'aquarius': 'Verseau ♒', 'pisces': 'Poissons ♓'
        }

    def _find_latest_video(self, sign: str) -> Optional[str]:
        """Trouve la vidéo finale la plus récente pour un signe."""
        path_pattern = str(self.individual_dir / f"{sign}_final_*.mp4")
        files = glob.glob(path_pattern)
        return max(files, key=os.path.getctime) if files else None

    def create_tiktok_metadata(self, sign: str) -> dict:
        """Crée le titre et les hashtags pour une vidéo TikTok."""
        sign_name = self.sign_names.get(sign.lower(), sign.title())
        date_str = datetime.date.today().strftime("%d/%m/%Y")

        title = f"🔮 Horoscope {sign_name} du {date_str}. #astrologie #horoscope #{sign.lower()} #guidance #ia #zodiaque"
        
        return {
            "title": title
        }

    def upload_sign_video(self, sign: str) -> dict:
        """Trouve et upload la vidéo d'un signe sur TikTok."""
        if not self.session_id:
            return {"success": False, "error": "Authentification TikTok non configurée (session_id manquant)."}

        video_path = self._find_latest_video(sign)
        if not video_path:
            return {"success": False, "error": f"Aucune vidéo finale trouvée pour {sign}."}

        metadata = self.create_tiktok_metadata(sign)
        
        try:
            print(f"📤 Démarrage de l'upload TikTok pour {sign}...")
            upload_video(
                video_path,
                description=metadata["title"],
                sessionid=self.session_id
            )
            print(f"✅ Upload TikTok pour {sign} réussi !")
            return {
                "success": True, 
                "sign": sign,
                "video_path": video_path,
                "title": metadata["title"]
            }
        except Exception as e:
            error_msg = f"Erreur lors de l'upload TikTok : {e}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

# Instance globale pour être importée
tiktok_server = TikTokUploader()
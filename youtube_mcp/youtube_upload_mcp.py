#!/usr/bin/env python3
"""
MCP YouTube Upload Server - AstroGenAI
Serveur MCP pour upload automatique sur YouTube
"""

import os
import sys
import datetime
import glob
from typing import Optional, List, Dict, Any
from pathlib import Path

# Import upload engine
from upload_engine import YouTubeUploader, UploadResult

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️ FastMCP non disponible")

# Configuration
FINAL_MONTAGE_DIR = "../final_montage"
INDIVIDUAL_DIR = f"{FINAL_MONTAGE_DIR}/individual"

class YouTubeMCPServer:
    """Serveur MCP pour uploads YouTube AstroGenAI"""
    
    def __init__(self):
        self.uploader = YouTubeUploader()
        self.signs_order = [
            'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
            'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
        ]
        
        self.sign_names = {
            'aries': 'Bélier', 'taurus': 'Taureau', 'gemini': 'Gémeaux',
            'cancer': 'Cancer', 'leo': 'Lion', 'virgo': 'Vierge',
            'libra': 'Balance', 'scorpio': 'Scorpion', 'sagittarius': 'Sagittaire',
            'capricorn': 'Capricorne', 'aquarius': 'Verseau', 'pisces': 'Poissons'
        }
    
    def find_latest_video(self, sign: str) -> Optional[str]:
        """Trouve la vidéo la plus récente pour un signe"""
        pattern = f"{INDIVIDUAL_DIR}/{sign}_final_*.mp4"
        videos = glob.glob(pattern)
        
        if not videos:
            return None
        
        # Retourner la plus récente
        return max(videos, key=os.path.getctime)
    
    def find_complete_video(self) -> Optional[str]:
        """Trouve la vidéo horoscope complète la plus récente"""
        pattern = f"{FINAL_MONTAGE_DIR}/horoscope_complet_*.mp4"
        videos = glob.glob(pattern)
        
        if not videos:
            return None
        
        return max(videos, key=os.path.getctime)
    
    def get_available_videos(self) -> Dict[str, Any]:
        """Liste toutes les vidéos disponibles pour upload"""
        result = {
            "individual_videos": {},
            "complete_video": None,
            "total_available": 0
        }
        
        # Vidéos individuelles
        for sign in self.signs_order:
            video_path = self.find_latest_video(sign)
            if video_path:
                result["individual_videos"][sign] = {
                    "path": video_path,
                    "filename": os.path.basename(video_path),
                    "size": os.path.getsize(video_path),
                    "modified": datetime.datetime.fromtimestamp(os.path.getmtime(video_path)).isoformat(),
                    "sign_name": self.sign_names.get(sign, sign.title())
                }
                result["total_available"] += 1
        
        # Vidéo complète
        complete_video = self.find_complete_video()
        if complete_video:
            result["complete_video"] = {
                "path": complete_video,
                "filename": os.path.basename(complete_video),
                "size": os.path.getsize(complete_video),
                "modified": datetime.datetime.fromtimestamp(os.path.getmtime(complete_video)).isoformat()
            }
        
        return result
    
    def upload_individual_video(self, sign: str, privacy: str = "private") -> Dict[str, Any]:
        """Upload vidéo individuelle d'un signe"""
        try:
            # Validation du signe
            if sign not in self.signs_order:
                return {
                    "success": False,
                    "error": f"Signe invalide: {sign}. Disponibles: {', '.join(self.signs_order)}"
                }
            
            # Trouver la vidéo
            video_path = self.find_latest_video(sign)
            if not video_path:
                return {
                    "success": False,
                    "error": f"Aucune vidéo trouvée pour {sign}"
                }
            
            # Créer métadonnées avec privacy personnalisé
            metadata = self.uploader.create_astro_metadata(sign)
            metadata.privacy_status = privacy
            
            # Upload
            result = self.uploader.upload_video(video_path, metadata)
            
            if result.success:
                return {
                    "success": True,
                    "video_id": result.video_id,
                    "video_url": result.video_url,
                    "title": result.title,
                    "sign": sign,
                    "sign_name": self.sign_names.get(sign, sign.title()),
                    "privacy": privacy,
                    "upload_time": result.upload_time,
                    "video_file": os.path.basename(video_path)
                }
            else:
                return {
                    "success": False,
                    "error": result.error,
                    "sign": sign
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur upload {sign}: {str(e)}"
            }
    
    def upload_batch_videos(self, signs: Optional[List[str]] = None, privacy: str = "private") -> Dict[str, Any]:
        """Upload en lot de plusieurs signes"""
        try:
            target_signs = signs if signs else self.signs_order
            results = []
            successful = 0
            failed = 0
            
            for sign in target_signs:
                print(f"📤 Upload {sign}...")
                result = self.upload_individual_video(sign, privacy)
                
                if result["success"]:
                    successful += 1
                    print(f"✅ {sign} uploadé: {result['video_url']}")
                else:
                    failed += 1
                    print(f"❌ {sign} échoué: {result['error']}")
                
                results.append(result)
            
            return {
                "success": True,
                "results": results,
                "total": len(target_signs),
                "successful": successful,
                "failed": failed,
                "summary": f"{successful}/{len(target_signs)} uploads réussis"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur upload batch: {str(e)}"
            }
    
    def get_youtube_status(self) -> Dict[str, Any]:
        """Statut de la connexion YouTube"""
        try:
            channel_info = self.uploader.get_channel_info()
            available_videos = self.get_available_videos()
            
            return {
                "success": True,
                "youtube_connected": channel_info.get("success", False),
                "channel_info": channel_info,
                "available_videos_count": available_videos["total_available"],
                "complete_video_available": available_videos["complete_video"] is not None,
                "individual_videos_available": list(available_videos["individual_videos"].keys())
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur statut YouTube: {str(e)}"
            }

# Initialisation serveur MCP
youtube_server = YouTubeMCPServer()

if FASTMCP_AVAILABLE:
    mcp = FastMCP("YouTubeUploadMCP")

    @mcp.tool()
    def get_youtube_status() -> dict:
        """
        Vérifie l'état de la connexion YouTube et des vidéos disponibles.
        
        Returns:
            Statut de la connexion et inventaire des vidéos
        """
        return youtube_server.get_youtube_status()

    @mcp.tool()
    def get_available_videos() -> dict:
        """
        Liste toutes les vidéos disponibles pour upload.
        
        Returns:
            Inventaire détaillé des vidéos individuelles et complètes
        """
        try:
            videos = youtube_server.get_available_videos()
            return {"success": True, "videos": videos}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def upload_sign_video(sign: str, privacy: str = "private") -> dict:
        """
        Upload la vidéo d'un signe spécifique sur YouTube.
        
        Args:
            sign: Nom du signe (aries, taurus, etc.)
            privacy: Statut de confidentialité (private, unlisted, public)
        
        Returns:
            Résultat de l'upload avec URL YouTube
        """
        return youtube_server.upload_individual_video(sign, privacy)

    @mcp.tool()
    def upload_batch_signs(signs: Optional[List[str]] = None, privacy: str = "private") -> dict:
        """
        Upload en lot de plusieurs signes sur YouTube.
        
        Args:
            signs: Liste des signes à uploader (par défaut: tous)
            privacy: Statut de confidentialité (private, unlisted, public)
        
        Returns:
            Résultats détaillés de tous les uploads
        """
        return youtube_server.upload_batch_videos(signs, privacy)

    @mcp.tool()
    def upload_complete_horoscope(privacy: str = "private") -> dict:
        """
        Upload la vidéo horoscope complète (12 signes) sur YouTube.
        
        Args:
            privacy: Statut de confidentialité (private, unlisted, public)
        
        Returns:
            Résultat de l'upload de la vidéo complète
        """
        try:
            complete_video = youtube_server.find_complete_video()
            if not complete_video:
                return {
                    "success": False,
                    "error": "Aucune vidéo horoscope complète trouvée"
                }
            
            # Métadonnées pour vidéo complète
            from upload_engine import VideoMetadata
            
            date = datetime.date.today().strftime("%d/%m/%Y")
            metadata = VideoMetadata(
                title=f"🔮 Horoscope Complet du Jour - {date} | 12 Signes IA",
                description=f"""🌟 Horoscope complet pour tous les signes du {date} !

🤖 Généré par Intelligence Artificielle astrologique
⭐ Prédictions pour les 12 signes du zodiaque
🌙 Influences cosmiques et conseils pratiques
💫 Votre guide astral quotidien complet

📅 Dans cette vidéo :
- Horoscope pour TOUS les signes
- Influences planétaires générales
- Conseils astrologiques du jour
- Énergies cosmiques collectives

🔮 AstroGenAI - Votre intelligence artificielle astrologique
Abonnez-vous pour vos prédictions quotidiennes !

#Horoscope #Astrologie #TousLesSignes #Prédictions #IA #AstroGenAI""",
                tags=["horoscope", "astrologie", "tous signes", "prédictions", "IA", "complet", "quotidien"],
                privacy_status=privacy
            )
            
            result = youtube_server.uploader.upload_video(complete_video, metadata)
            
            if result.success:
                return {
                    "success": True,
                    "video_id": result.video_id,
                    "video_url": result.video_url,
                    "title": result.title,
                    "privacy": privacy,
                    "upload_time": result.upload_time,
                    "video_file": os.path.basename(complete_video),
                    "type": "complete_horoscope"
                }
            else:
                return {"success": False, "error": result.error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_mcp_tools():
        """Test des outils MCP - Version Corrigée"""
        print("🧪 Test des outils MCP YouTube")
        print("=" * 40)
        
        # Test 1: Statut YouTube (appel direct à la classe)
        print("🔍 Test 1: Statut YouTube")
        status = youtube_server.get_youtube_status()
        print(f"✅ Connexion YouTube: {status.get('youtube_connected', False)}")
        if status.get('success'):
            channel_info = status.get('channel_info', {})
            print(f"📺 Chaîne: {channel_info.get('title', 'N/A')}")
            print(f"👥 Abonnés: {channel_info.get('subscribers', '0')}")
            print(f"📊 Vidéos disponibles: {status.get('available_videos_count', 0)}")
        
        # Test 2: Vidéos disponibles (appel direct à la classe)
        print("\n🔍 Test 2: Vidéos disponibles")
        videos = youtube_server.get_available_videos()
        print(f"📊 {videos['total_available']} vidéos individuelles trouvées")
        print(f"🎬 Vidéo complète: {'Oui' if videos['complete_video'] else 'Non'}")
        
        # Afficher quelques signes disponibles
        available_signs = list(videos['individual_videos'].keys())
        if available_signs:
            print(f"⭐ Signes disponibles: {', '.join(available_signs[:5])}")
            if len(available_signs) > 5:
                print(f"   ... et {len(available_signs) - 5} autres")
        
        # Test 3: Test upload simulé (juste validation)
        print("\n🔍 Test 3: Validation upload")
        if available_signs:
            test_sign = available_signs[0]
            video_path = youtube_server.find_latest_video(test_sign)
            if video_path and os.path.exists(video_path):
                print(f"✅ Vidéo prête pour upload: {test_sign}")
                print(f"📁 Fichier: {os.path.basename(video_path)}")
                print(f"📏 Taille: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
            else:
                print(f"❌ Vidéo introuvable pour {test_sign}")
        
        print("\n✅ Tests MCP terminés")
        print("\n💡 Pour upload réel:")
        print(f"   result = youtube_server.upload_individual_video('{available_signs[0] if available_signs else 'aries'}', 'private')")

if __name__ == "__main__":
    print("🎬 MCP YouTube Upload Server - AstroGenAI")
    print("=" * 50)
    
    if FASTMCP_AVAILABLE:
        print("🚀 Serveur FastMCP prêt")
        
        # Test optionnel
        if "--test" in sys.argv:
            test_mcp_tools()
        elif "--server" in sys.argv:
            print("🚀 Démarrage serveur MCP...")
            mcp.run()
        elif "--upload" in sys.argv:
            # Test d'upload réel
            if len(sys.argv) > 2:
                sign = sys.argv[2]
                print(f"📤 Test upload réel pour {sign}...")
                result = youtube_server.upload_individual_video(sign, "private")
                if result["success"]:
                    print(f"✅ Upload réussi: {result['video_url']}")
                else:
                    print(f"❌ Upload échoué: {result['error']}")
            else:
                print("Usage: python youtube_upload_mcp.py --upload <sign>")
        else:
            print("💡 Options disponibles:")
            print("   python youtube_upload_mcp.py --test              # Test des outils")
            print("   python youtube_upload_mcp.py --server            # Démarrer serveur")
            print("   python youtube_upload_mcp.py --upload aries      # Upload test")
            test_mcp_tools()
    else:
        print("❌ FastMCP non disponible")
        print("pip install fastmcp")
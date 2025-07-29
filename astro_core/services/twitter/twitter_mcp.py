#!/usr/bin/env python3
"""
MCP Twitter Server - AstroGenAI
Service MCP complet pour publication automatique sur Twitter
avec système de queue et timing intelligent
"""

import os
import sys
import datetime
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import time

# Dépendances Twitter
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    print("⚠️ Tweepy non disponible - pip install tweepy")

# Dépendance FastMCP
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️ FastMCP non disponible")

# Imports locaux
from .twitter_auth import TwitterAuthenticator
from .tweet_scheduler import TweetScheduler, TweetStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TweetResult:
    """Résultat d'une publication Twitter"""
    success: bool
    tweet_id: Optional[str] = None
    tweet_url: Optional[str] = None
    content: str = ""
    error: Optional[str] = None
    published_time: Optional[str] = None
    media_ids: Optional[List[str]] = None

class TwitterService:
    """Service principal pour publication Twitter"""
    
    def __init__(self):
        self.authenticator = TwitterAuthenticator()
        self.scheduler = TweetScheduler()
        self.api = None
        self.client = None
        
        # Métadonnées des signes pour templates
        self.sign_symbols = {
            'aries': '♈', 'taurus': '♉', 'gemini': '♊', 'cancer': '♋',
            'leo': '♌', 'virgo': '♍', 'libra': '♎', 'scorpio': '♏',
            'sagittarius': '♐', 'capricorn': '♑', 'aquarius': '♒', 'pisces': '♓'
        }
        
        self.sign_names = {
            'aries': 'Bélier', 'taurus': 'Taureau', 'gemini': 'Gémeaux',
            'cancer': 'Cancer', 'leo': 'Lion', 'virgo': 'Vierge',
            'libra': 'Balance', 'scorpio': 'Scorpion', 'sagittarius': 'Sagittaire',
            'capricorn': 'Capricorne', 'aquarius': 'Verseau', 'pisces': 'Poissons'
        }
        
        # Initialiser la connexion
        self._initialize_connection()
        
        # Démarrer le scheduler
        self.scheduler.start_scheduler()
    
    def _initialize_connection(self):
        """Initialise la connexion Twitter"""
        if not TWEEPY_AVAILABLE:
            logger.error("Tweepy non disponible")
            return False
        
        try:
            if self.authenticator.authenticate():
                self.api = self.authenticator.api
                self.client = self.authenticator.client
                logger.info("✅ Connexion Twitter initialisée")
                return True
            else:
                logger.error("❌ Échec authentification Twitter")
                return False
        except Exception as e:
            logger.error(f"Erreur initialisation Twitter: {e}")
            return False
    
    def create_tweet_content(self, sign: str, youtube_url: str = None, 
                           custom_message: str = None) -> str:
        """Crée le contenu du tweet avec template"""
        sign_name = self.sign_names.get(sign, sign.title())
        sign_symbol = self.sign_symbols.get(sign, '✨')
        today = datetime.date.today().strftime('%d/%m/%Y')
        
        if custom_message:
            base_content = custom_message
        else:
            base_content = f"🌟 Horoscope {sign_name} {sign_symbol} du {today}\n"
            base_content += "Découvrez vos prédictions astrologiques personnalisées !\n"
        
        if youtube_url:
            base_content += f"➡️ {youtube_url}\n"
        
        # Les hashtags seront ajoutés séparément pour respecter les limites
        return base_content.strip()
    
    def upload_media(self, image_path: str) -> Optional[str]:
        """Upload une image sur Twitter et retourne le media_id"""
        if not self.api or not os.path.exists(image_path):
            return None
        
        try:
            media = self.api.media_upload(image_path)
            logger.info(f"Image uploadée: {media.media_id}")
            return media.media_id
        except Exception as e:
            logger.error(f"Erreur upload image {image_path}: {e}")
            return None
    
    def publish_tweet_now(self, content: str, image_path: str = None, 
                         hashtags: List[str] = None) -> TweetResult:
        """Publie un tweet immédiatement"""
        if not self.api:
            return TweetResult(
                success=False,
                content=content,
                error="API Twitter non disponible"
            )
        
        try:
            # Préparer le contenu final
            final_content = content
            if hashtags:
                hashtag_str = " ".join(hashtags)
                # Vérifier la limite de 280 caractères
                if len(final_content + " " + hashtag_str) <= 280:
                    final_content += f"\n\n{hashtag_str}"
                else:
                    # Tronquer les hashtags si nécessaire
                    available_space = 280 - len(final_content) - 2
                    if available_space > 10:  # Au moins quelques hashtags
                        truncated_hashtags = hashtag_str[:available_space].rsplit(' ', 1)[0]
                        final_content += f"\n\n{truncated_hashtags}"
            
            # Upload de l'image si fournie
            media_ids = []
            if image_path and os.path.exists(image_path):
                media_id = self.upload_media(image_path)
                if media_id:
                    media_ids.append(media_id)
            
            # Publier le tweet
            if media_ids:
                tweet = self.api.update_status(
                    status=final_content,
                    media_ids=media_ids
                )
            else:
                tweet = self.api.update_status(status=final_content)
            
            # Construire l'URL du tweet
            user_id = tweet.user.screen_name
            tweet_url = f"https://twitter.com/{user_id}/status/{tweet.id}"
            
            result = TweetResult(
                success=True,
                tweet_id=str(tweet.id),
                tweet_url=tweet_url,
                content=final_content,
                published_time=datetime.datetime.now().isoformat(),
                media_ids=media_ids
            )
            
            logger.info(f"✅ Tweet publié: {tweet.id}")
            return result
            
        except tweepy.TooManyRequests:
            error_msg = "Limite de taux atteinte, retry plus tard"
            logger.error(error_msg)
            return TweetResult(success=False, content=content, error=error_msg)
            
        except tweepy.Forbidden as e:
            error_msg = f"Tweet interdit (contenu dupliqué?): {str(e)}"
            logger.error(error_msg)
            return TweetResult(success=False, content=content, error=error_msg)
            
        except Exception as e:
            error_msg = f"Erreur publication: {str(e)}"
            logger.error(error_msg)
            return TweetResult(success=False, content=content, error=error_msg)
    
    def schedule_tweet(self, sign: str, youtube_url: str = None, 
                      image_path: str = None, custom_message: str = None) -> str:
        """Programme un tweet dans la queue"""
        sign_name = self.sign_names.get(sign, sign.title())
        content = self.create_tweet_content(sign, youtube_url, custom_message)
        hashtags = self.scheduler._generate_hashtags(sign)
        
        task_id = self.scheduler.add_tweet_task(
            sign=sign,
            sign_name=sign_name,
            content=content,
            image_path=image_path,
            youtube_url=youtube_url,
            hashtags=hashtags
        )
        
        logger.info(f"Tweet programmé pour {sign_name}: {task_id}")
        return task_id
    
    def process_pending_tweets(self) -> List[Dict[str, Any]]:
        """Traite les tweets en attente de publication"""
        pending_tasks = self.scheduler.get_pending_tasks()
        results = []
        
        for task in pending_tasks:
            logger.info(f"Publication du tweet: {task.id}")
            
            result = self.publish_tweet_now(
                content=task.content,
                image_path=task.image_path,
                hashtags=task.hashtags
            )
            
            # Mettre à jour le statut dans la queue
            self.scheduler.mark_task_published(
                task_id=task.id,
                success=result.success,
                error_msg=result.error
            )
            
            results.append({
                "task_id": task.id,
                "sign": task.sign,
                "success": result.success,
                "tweet_url": result.tweet_url,
                "error": result.error
            })
        
        return results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Retourne l'état du service Twitter"""
        queue_status = self.scheduler.get_queue_status()
        
        # Test de connexion rapide
        twitter_connected = False
        account_info = {}
        
        if self.api:
            try:
                user = self.api.verify_credentials()
                twitter_connected = True
                account_info = {
                    "username": user.screen_name,
                    "name": user.name,
                    "followers": user.followers_count,
                    "tweets": user.statuses_count
                }
            except:
                twitter_connected = False
        
        return {
            "success": True,
            "twitter_connected": twitter_connected,
            "account_info": account_info,
            "queue_status": queue_status,
            "tweepy_available": TWEEPY_AVAILABLE,
            "scheduler_running": self.scheduler.running,
            "capabilities": [
                "immediate_publishing",
                "scheduled_publishing", 
                "media_upload",
                "hashtag_management",
                "queue_management"
            ]
        }
    
    def get_tweet_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retourne l'historique des tweets récents"""
        published_tasks = [
            task for task in self.scheduler.tasks 
            if task.status == TweetStatus.PUBLISHED
        ]
        
        # Trier par date de publication (plus récent en premier)
        published_tasks.sort(
            key=lambda t: t.published_time or t.created_time, 
            reverse=True
        )
        
        history = []
        for task in published_tasks[:limit]:
            history.append({
                "id": task.id,
                "sign": task.sign,
                "sign_name": task.sign_name,
                "content": task.content[:100] + "..." if len(task.content) > 100 else task.content,
                "published_time": task.published_time,
                "youtube_url": task.youtube_url,
                "hashtags": task.hashtags
            })
        
        return history
    
    def cleanup_service(self):
        """Nettoie le service avant fermeture"""
        self.scheduler.stop_scheduler()
        logger.info("Service Twitter nettoyé")

# =============================================================================
# INITIALISATION GLOBALE
# =============================================================================

# Instance globale du service
twitter_service = TwitterService()

# =============================================================================
# SERVEUR MCP
# =============================================================================

if FASTMCP_AVAILABLE:
    mcp = FastMCP("TwitterServiceMCP")

    @mcp.tool()
    def get_twitter_status() -> dict:
        """Vérifie l'état du service Twitter et de la queue"""
        try:
            return twitter_service.get_service_status()
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def publish_tweet_immediate(content: str, image_path: str = None, 
                               hashtags: List[str] = None) -> dict:
        """Publie un tweet immédiatement"""
        try:
            result = twitter_service.publish_tweet_now(content, image_path, hashtags)
            return {
                "success": result.success,
                "tweet_id": result.tweet_id,
                "tweet_url": result.tweet_url,
                "content": result.content,
                "error": result.error,
                "published_time": result.published_time
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def schedule_sign_tweet(sign: str, youtube_url: str = None, 
                           image_path: str = None, custom_message: str = None) -> dict:
        """Programme un tweet pour un signe astrologique"""
        try:
            task_id = twitter_service.schedule_tweet(sign, youtube_url, image_path, custom_message)
            return {
                "success": True,
                "task_id": task_id,
                "message": f"Tweet programmé pour {twitter_service.sign_names.get(sign, sign)}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def process_tweet_queue() -> dict:
        """Traite les tweets en attente dans la queue"""
        try:
            results = twitter_service.process_pending_tweets()
            successful = sum(1 for r in results if r["success"])
            
            return {
                "success": True,
                "processed": len(results),
                "successful": successful,
                "failed": len(results) - successful,
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_tweet_queue_status() -> dict:
        """Retourne l'état détaillé de la queue"""
        try:
            return {
                "success": True,
                "queue_status": twitter_service.scheduler.get_queue_status()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_tweet_history(limit: int = 10) -> dict:
        """Retourne l'historique des tweets publiés"""
        try:
            history = twitter_service.get_tweet_history(limit)
            return {
                "success": True,
                "history": history,
                "total_returned": len(history)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def cleanup_old_tweets(days: int = 7) -> dict:
        """Nettoie les anciennes tâches de la queue"""
        try:
            cleaned_count = twitter_service.scheduler.cleanup_old_tasks(days)
            return {
                "success": True,
                "cleaned_tasks": cleaned_count,
                "message": f"{cleaned_count} anciennes tâches supprimées"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_batch_schedule_from_youtube(youtube_uploads: List[Dict[str, str]]) -> dict:
        """Crée une planification batch depuis des uploads YouTube"""
        try:
            scheduled_tasks = []
            
            for upload in youtube_uploads:
                sign = upload.get("sign")
                youtube_url = upload.get("video_url") 
                image_path = upload.get("image_path")
                
                if sign and youtube_url:
                    task_id = twitter_service.schedule_tweet(
                        sign=sign,
                        youtube_url=youtube_url,
                        image_path=image_path
                    )
                    scheduled_tasks.append({
                        "sign": sign,
                        "task_id": task_id,
                        "youtube_url": youtube_url
                    })
            
            return {
                "success": True,
                "scheduled_count": len(scheduled_tasks),
                "tasks": scheduled_tasks,
                "message": f"{len(scheduled_tasks)} tweets programmés avec étalement automatique"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# =============================================================================
# CLASSE D'INTÉGRATION YOUTUBE
# =============================================================================

class YouTubeTwitterIntegration:
    """Intégration entre YouTube et Twitter pour publication automatique"""
    
    @staticmethod
    def auto_tweet_after_youtube_upload(youtube_result: Dict[str, Any], 
                                       image_path: str = None) -> Dict[str, Any]:
        """
        Fonction appelée automatiquement après un upload YouTube réussi
        
        Args:
            youtube_result: Résultat de l'upload YouTube
            image_path: Chemin vers l'image à inclure
        
        Returns:
            Résultat de la programmation Twitter
        """
        try:
            if not youtube_result.get("success"):
                return {"success": False, "error": "Upload YouTube échoué"}
            
            sign = youtube_result.get("sign")
            video_url = youtube_result.get("video_url")
            
            if not sign or not video_url:
                return {"success": False, "error": "Données YouTube incomplètes"}
            
            # Programmer le tweet
            task_id = twitter_service.schedule_tweet(
                sign=sign,
                youtube_url=video_url,
                image_path=image_path
            )
            
            logger.info(f"Tweet auto-programmé après upload YouTube: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "sign": sign,
                "message": f"Tweet programmé automatiquement pour {twitter_service.sign_names.get(sign, sign)}"
            }
            
        except Exception as e:
            logger.error(f"Erreur intégration YouTube-Twitter: {e}")
            return {"success": False, "error": str(e)}

# Instance d'intégration globale
youtube_twitter_integration = YouTubeTwitterIntegration()

# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    print("🐦" + "="*60)
    print("🐦 TWITTER SERVICE MCP - ASTROGENAI")
    print("🐦" + "="*60)
    
    # Vérification au démarrage
    status = twitter_service.get_service_status()
    
    print(f"📊 Configuration:")
    print(f"   • Scheduler: {'✅' if status['scheduler_running'] else '❌'}")
    print(f"   • Queue: {status['queue_status']['total_tasks']} tâches")
    
    print(f"📦 Dépendances:")
    print(f"   • Tweepy: {'✅' if status['tweepy_available'] else '❌'}")
    print(f"   • FastMCP: {'✅' if FASTMCP_AVAILABLE else '❌'}")
    print(f"   • Twitter API: {'✅' if status['twitter_connected'] else '❌'}")
    
    if status['twitter_connected']:
        account = status['account_info']
        print(f"   • Compte: @{account.get('username', 'N/A')}")
        print(f"   • Followers: {account.get('followers', 0):,}")
    
    print(f"🎯 Capacités:")
    for capability in status['capabilities']:
        print(f"   • {capability.replace('_', ' ').title()}")
    
    # Vérification queue
    queue_status = status['queue_status']
    if queue_status['next_scheduled']:
        next_time = datetime.datetime.fromisoformat(queue_status['next_scheduled'])
        print(f"⏰ Prochain tweet: {next_time.strftime('%d/%m/%Y à %H:%M')}")
    else:
        print("⏰ Aucun tweet programmé")
    
    # Avertissements
    if not status['tweepy_available']:
        print("⚠️  Tweepy non disponible - pip install tweepy")
    if not status['twitter_connected']:
        print("⚠️  Twitter non connecté - Vérifiez credentials.json")
    
    # Démarrage du serveur FastMCP
    if FASTMCP_AVAILABLE and status['twitter_connected']:
        print(f"🚀 Démarrage du serveur FastMCP...")
        print(f"🔧 Outils disponibles:")
        print(f"   • get_twitter_status")
        print(f"   • publish_tweet_immediate")
        print(f"   • schedule_sign_tweet")
        print(f"   • process_tweet_queue")
        print(f"   • get_tweet_history")
        print(f"   • create_batch_schedule_from_youtube")
        
        try:
            mcp.run()
        except KeyboardInterrupt:
            print("\n👋 Arrêt du service Twitter")
            twitter_service.cleanup_service()
    else:
        print("❌ Impossible de démarrer le serveur MCP")
        if not FASTMCP_AVAILABLE:
            print("💡 pip install fastmcp pour activer le serveur")
        if not status['twitter_connected']:
            print("💡 Configurez credentials.json et testez avec twitter_auth.py")
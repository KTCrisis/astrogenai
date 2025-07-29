#!/usr/bin/env python3
"""
Gestionnaire de queue et planification des tweets
Système de queue persistante pour étalement automatique des publications
"""

import json
import datetime
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TweetStatus(Enum):
    """États possibles d'un tweet dans la queue"""
    PENDING = "pending"
    SCHEDULED = "scheduled" 
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TweetTask:
    """Tâche de tweet dans la queue"""
    id: str
    sign: str
    sign_name: str
    content: str
    image_path: Optional[str]
    youtube_url: Optional[str]
    hashtags: List[str]
    scheduled_time: str  # ISO format
    created_time: str
    status: TweetStatus
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    published_time: Optional[str] = None

class TweetScheduler:
    """Gestionnaire de queue et planification des tweets"""
    
    def __init__(self, queue_file: Path = None):
        self.queue_file = queue_file or Path(__file__).parent / "tweet_queue.json"
        self.tasks: List[TweetTask] = []
        self.scheduler_thread = None
        self.running = False
        
        # Configuration du timing
        self.hour_interval = 1  # 1 tweet par heure
        self.publishing_hours = (9, 21)  # Publier entre 9h et 21h
        self.max_daily_tweets = 12  # Maximum par jour
        
        # Charger la queue existante
        self._load_queue()
    
    def _load_queue(self):
        """Charge la queue depuis le fichier JSON"""
        if not self.queue_file.exists():
            self.tasks = []
            return
        
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.tasks = []
            for task_data in data.get('tasks', []):
                task = TweetTask(**task_data)
                # Reconvertir le status depuis string
                task.status = TweetStatus(task_data['status'])
                self.tasks.append(task)
            
            logger.info(f"Queue chargée: {len(self.tasks)} tâches")
            
        except Exception as e:
            logger.error(f"Erreur chargement queue: {e}")
            self.tasks = []
    
    def _save_queue(self):
        """Sauvegarde la queue dans le fichier JSON"""
        try:
            data = {
                "last_updated": datetime.datetime.now().isoformat(),
                "total_tasks": len(self.tasks),
                "tasks": []
            }
            
            for task in self.tasks:
                task_dict = asdict(task)
                task_dict['status'] = task.status.value  # Convertir enum en string
                data['tasks'].append(task_dict)
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde queue: {e}")
    
    def add_tweet_task(self, sign: str, sign_name: str, content: str, 
                      image_path: str = None, youtube_url: str = None,
                      hashtags: List[str] = None) -> str:
        """Ajoute une nouvelle tâche de tweet à la queue"""
        
        # Générer un ID unique
        task_id = f"tweet_{sign}_{int(time.time())}"
        
        # Calculer le prochain créneau disponible
        scheduled_time = self._calculate_next_slot()
        
        # Hashtags par défaut
        if not hashtags:
            hashtags = self._generate_hashtags(sign)
        
        # Créer la tâche
        task = TweetTask(
            id=task_id,
            sign=sign,
            sign_name=sign_name,
            content=content,
            image_path=image_path,
            youtube_url=youtube_url,
            hashtags=hashtags,
            scheduled_time=scheduled_time.isoformat(),
            created_time=datetime.datetime.now().isoformat(),
            status=TweetStatus.SCHEDULED
        )
        
        self.tasks.append(task)
        self._save_queue()
        
        logger.info(f"Tâche ajoutée: {task_id} programmée pour {scheduled_time}")
        return task_id
    
    def _calculate_next_slot(self) -> datetime.datetime:
        """Calcule le prochain créneau de publication disponible"""
        now = datetime.datetime.now()
        
        # Trouver les créneaux déjà occupés
        scheduled_times = []
        for task in self.tasks:
            if task.status in [TweetStatus.SCHEDULED, TweetStatus.PENDING]:
                scheduled_times.append(datetime.datetime.fromisoformat(task.scheduled_time))
        
        # Commencer par la prochaine heure
        next_slot = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
        
        while True:
            # Vérifier si c'est dans les heures de publication
            if self.publishing_hours[0] <= next_slot.hour <= self.publishing_hours[1]:
                # Vérifier si le créneau est libre
                if next_slot not in scheduled_times:
                    return next_slot
            
            # Passer à l'heure suivante
            next_slot += datetime.timedelta(hours=1)
            
            # Éviter les boucles infinies (max 7 jours)
            if next_slot > now + datetime.timedelta(days=7):
                logger.warning("Aucun créneau libre trouvé dans les 7 prochains jours")
                return now + datetime.timedelta(hours=1)
    
    def _generate_hashtags(self, sign: str) -> List[str]:
        """Génère les hashtags automatiques pour un signe"""
        sign_hashtags = {
            'aries': ['#Bélier', '#Aries'],
            'taurus': ['#Taureau', '#Taurus'], 
            'gemini': ['#Gémeaux', '#Gemini'],
            'cancer': ['#Cancer'],
            'leo': ['#Lion', '#Leo'],
            'virgo': ['#Vierge', '#Virgo'],
            'libra': ['#Balance', '#Libra'],
            'scorpio': ['#Scorpion', '#Scorpio'],
            'sagittarius': ['#Sagittaire', '#Sagittarius'],
            'capricorn': ['#Capricorne', '#Capricorn'],
            'aquarius': ['#Verseau', '#Aquarius'],
            'pisces': ['#Poissons', '#Pisces']
        }
        
        base_hashtags = ['#Horoscope', '#Astrologie', '#IA', '#AstroGenAI']
        sign_specific = sign_hashtags.get(sign, [f'#{sign.title()}'])
        
        return base_hashtags + sign_specific
    
    def get_pending_tasks(self) -> List[TweetTask]:
        """Retourne les tâches prêtes à être publiées"""
        now = datetime.datetime.now()
        pending = []
        
        for task in self.tasks:
            if task.status == TweetStatus.SCHEDULED:
                scheduled_time = datetime.datetime.fromisoformat(task.scheduled_time)
                if scheduled_time <= now:
                    task.status = TweetStatus.PENDING
                    pending.append(task)
        
        if pending:
            self._save_queue()
        
        return pending
    
    def mark_task_published(self, task_id: str, success: bool = True, error_msg: str = None):
        """Marque une tâche comme publiée ou échouée"""
        for task in self.tasks:
            if task.id == task_id:
                if success:
                    task.status = TweetStatus.PUBLISHED
                    task.published_time = datetime.datetime.now().isoformat()
                    logger.info(f"Tâche {task_id} marquée comme publiée")
                else:
                    task.retry_count += 1
                    task.error_message = error_msg
                    
                    if task.retry_count >= task.max_retries:
                        task.status = TweetStatus.FAILED
                        logger.error(f"Tâche {task_id} échouée définitivement: {error_msg}")
                    else:
                        # Reprogrammer pour dans 30 minutes
                        retry_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
                        task.scheduled_time = retry_time.isoformat()
                        task.status = TweetStatus.SCHEDULED
                        logger.warning(f"Tâche {task_id} reprogrammée (tentative {task.retry_count})")
                
                self._save_queue()
                return
        
        logger.warning(f"Tâche {task_id} non trouvée pour mise à jour")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Retourne le statut de la queue"""
        status_counts = {}
        for status in TweetStatus:
            status_counts[status.value] = sum(1 for task in self.tasks if task.status == status)
        
        # Prochaine publication
        next_scheduled = None
        for task in self.tasks:
            if task.status == TweetStatus.SCHEDULED:
                scheduled_time = datetime.datetime.fromisoformat(task.scheduled_time)
                if not next_scheduled or scheduled_time < next_scheduled:
                    next_scheduled = scheduled_time
        
        return {
            "total_tasks": len(self.tasks),
            "status_breakdown": status_counts,
            "next_scheduled": next_scheduled.isoformat() if next_scheduled else None,
            "queue_file": str(self.queue_file),
            "last_updated": datetime.datetime.now().isoformat()
        }
    
    def cleanup_old_tasks(self, days_old: int = 7):
        """Nettoie les anciennes tâches"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
        
        initial_count = len(self.tasks)
        self.tasks = [
            task for task in self.tasks
            if (task.status not in [TweetStatus.PUBLISHED, TweetStatus.FAILED] or
                datetime.datetime.fromisoformat(task.created_time) > cutoff_date)
        ]
        
        cleaned_count = initial_count - len(self.tasks)
        if cleaned_count > 0:
            self._save_queue()
            logger.info(f"Nettoyage: {cleaned_count} anciennes tâches supprimées")
        
        return cleaned_count
    
    def start_scheduler(self):
        """Démarre le thread de planification"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler de tweets démarré")
    
    def stop_scheduler(self):
        """Arrête le scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler de tweets arrêté")
    
    def _scheduler_loop(self):
        """Boucle principale du scheduler"""
        while self.running:
            try:
                # Nettoyer périodiquement
                if datetime.datetime.now().hour == 3:  # 3h du matin
                    self.cleanup_old_tasks()
                
                # Cette boucle surveille juste la queue
                # La publication réelle se fait via l'appel externe
                time.sleep(60)  # Vérifier chaque minute
                
            except Exception as e:
                logger.error(f"Erreur dans scheduler loop: {e}")
                time.sleep(60)
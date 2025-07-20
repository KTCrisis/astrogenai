#!/usr/bin/env python3
"""
MCP Video Server avec architecture hybride
Serveur MCP pour création de vidéos d'horoscope avec synchronisation audio/texte
Peut être utilisé soit comme module importé, soit comme serveur MCP autonome
"""

import datetime
import logging
import os
import glob
import json
import subprocess
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import time
import shutil

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vérification des dépendances avec gestion gracieuse
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper non disponible. Installez avec: pip install openai-whisper")

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    logger.warning("FastMCP non disponible")

# =============================================================================
# CONFIGURATION ET DATACLASSES
# =============================================================================

@dataclass
class VideoConfig:
    """Configuration centralisée pour le générateur vidéo"""
    output_dir: str = "final_montage"
    video_input_dir: str = "generated_videos"
    audio_input_dir: str = "generated_audio"
    music_file: str = "music/Io.wav"
    whisper_model: str = "base"
    ffmpeg_timeout: int = 300
    max_retries: int = 3
    cleanup_days: int = 7

@dataclass
class TranscriptionData:
    """Données de transcription audio"""
    full_text: str
    word_timings: List[Dict[str, Union[str, float]]]
    duration: float
    word_count: int

@dataclass
class SynchronizedVideoResult:
    """Résultat de création vidéo synchronisée"""
    sign: str
    sign_name: str
    video_path: str
    transcription: TranscriptionData
    has_music: bool
    file_size: int
    generation_timestamp: str

@dataclass
class FullVideoResult:
    """Résultat de création vidéo complète"""
    video_path: str
    total_duration: float
    file_size: int
    clips_count: int
    signs_included: List[str]
    generation_timestamp: str

# =============================================================================
# CLASSE PRINCIPALE DU GÉNÉRATEUR VIDÉO
# =============================================================================

class VideoGenerator:
    """Générateur de vidéos avec synchronisation audio/texte - Architecture hybride"""
    
    def __init__(self, config: Optional[VideoConfig] = None):
        self.config = config if config is not None else VideoConfig()
        
        # Initialisation des dossiers
        self.output_dir = Path(self.config.output_dir)
        self.temp_dir = self.output_dir / "temp_clips"
        self.video_input_dir = Path(self.config.video_input_dir)
        self.audio_input_dir = Path(self.config.audio_input_dir)
        self.music_file = Path(self.config.music_file)
        self.individual_dir = self.output_dir / "individual"
    
        # Créer les dossiers nécessaires
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        self.individual_dir.mkdir(exist_ok=True)  

        # Ordre des signes astrologiques
        self.signs_order = [
            'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
            'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
        ]
        
        # Métadonnées des signes
        self.sign_names = {
            'aries': 'Bélier', 'taurus': 'Taureau', 'gemini': 'Gémeaux', 'cancer': 'Cancer',
            'leo': 'Lion', 'virgo': 'Vierge', 'libra': 'Balance', 'scorpio': 'Scorpion',
            'sagittarius': 'Sagittaire', 'capricorn': 'Capricorne', 'aquarius': 'Verseau', 'pisces': 'Poissons'
        }
        
        self.sign_symbols = {
            'aries': '♈', 'taurus': '♉', 'gemini': '♊', 'cancer': '♋', 'leo': '♌',
            'virgo': '♍', 'libra': '♎', 'scorpio': '♏', 'sagittarius': '♐',
            'capricorn': '♑', 'aquarius': '♒', 'pisces': '♓'
        }
        
        # Vérifier les dépendances système
        self._check_system_dependencies()
    
    def _check_system_dependencies(self) -> None:
        """Vérifie la disponibilité des dépendances système"""
        self.whisper_available = WHISPER_AVAILABLE
        self.ffmpeg_available = self._check_ffmpeg()
        
        if not self.whisper_available:
            logger.warning("Whisper non disponible - Transcription désactivée")
        if not self.ffmpeg_available:
            logger.error("ffmpeg non disponible - Génération vidéo impossible")
    
    def _check_ffmpeg(self) -> bool:
        """Vérifie si ffmpeg est disponible"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    # =============================================================================
    # MÉTHODES DE VALIDATION
    # =============================================================================
    
    def _validate_sign(self, sign: str) -> str:
        """Valide et normalise un signe astrologique"""
        if not sign:
            raise ValueError("Signe manquant")
        
        sign_lower = sign.lower().strip()
        if sign_lower not in self.sign_names:
            available = ", ".join(self.sign_names.keys())
            raise ValueError(f"Signe invalide '{sign}'. Disponibles: {available}")
        
        return sign_lower
    
    # =============================================================================
    # MÉTHODES UTILITAIRES
    # =============================================================================
    
    def _find_latest_assets(self, sign: str) -> Tuple[Optional[str], Optional[str]]:
        """Trouve les fichiers vidéo et audio les plus récents pour un signe"""
        try:
            video_pattern = str(self.video_input_dir / f"{sign}_*.mp4")
            audio_pattern = str(self.audio_input_dir / f"{sign}_*.mp3")
            
            video_files = glob.glob(video_pattern)
            audio_files = glob.glob(audio_pattern)
            
            latest_video = max(video_files, key=os.path.getctime) if video_files else None
            latest_audio = max(audio_files, key=os.path.getctime) if audio_files else None
            
            return latest_video, latest_audio
        except Exception as e:
            logger.error(f"Erreur recherche assets pour {sign}: {e}")
            return None, None
    
    def _get_file_duration(self, file_path: str) -> Optional[float]:
        """Obtient la durée d'un fichier média"""
        if not self.ffmpeg_available:
            return None
            
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Impossible d'obtenir la durée pour {file_path}: {e}")
            return None
    
    # =============================================================================
    # MÉTHODES DE TRANSCRIPTION
    # =============================================================================
    
    def _transcribe_audio_with_whisper(self, audio_path: str) -> Optional[TranscriptionData]:
        """Transcrit un fichier audio avec Whisper"""
        if not self.whisper_available:
            logger.warning("Whisper non disponible pour la transcription")
            return None
        
        logger.info(f"Transcription Whisper: {os.path.basename(audio_path)}")
        try:
            import whisper
            model = whisper.load_model(self.config.whisper_model)
            result = model.transcribe(audio_path, language="fr", word_timestamps=True)
            
            word_timings = []
            for segment in result.get("segments", []):
                for word_info in segment.get("words", []):
                    word_timings.append({
                        "word": word_info["word"].strip(),
                        "start": word_info["start"],
                        "end": word_info["end"]
                    })
            
            return TranscriptionData(
                full_text=result["text"],
                word_timings=word_timings,
                duration=result.get("duration", 0),
                word_count=len(word_timings)
            )
        except Exception as e:
            logger.error(f"Erreur transcription Whisper: {e}")
            return None
    
    # =============================================================================
    # MÉTHODES DE GÉNÉRATION VIDÉO
    # =============================================================================
    
    def _create_subtitle_filter(self, word_timings: List[Dict], sign: str) -> str:
        """Crée les filtres de sous-titres pour ffmpeg"""
        if not word_timings:
            return ""
        
        filters = []
        sign_name = self.sign_names.get(sign, sign.title())
        sign_symbol = self.sign_symbols.get(sign, '')
        
        # Titre du signe
        title_filter = (
            f"drawtext=text='♦{sign_name}♦':fontsize=40:fontcolor=silver:"
            "x=(w-text_w)/2:y=100:box=1:boxcolor=black@0.7:boxborderw=8"
        )
        filters.append(title_filter)
        
        # Symbole du signe
        if sign_symbol:
            symbol_filter = (
                f"drawtext=text='{sign_symbol}':fontsize=60:fontcolor=gold:"
                "x=(w-text_w)/2:y=180"
            )
            filters.append(symbol_filter)
        
        # Grouper les mots en phrases
        phrases = []
        current_phrase = []
        if word_timings:
            current_start = word_timings[0]["start"]
            for i, word in enumerate(word_timings):
                current_phrase.append(word["word"])
                
                if (len(current_phrase) >= 6 or 
                    word["word"].endswith(('.', '!', '?')) or 
                    i == len(word_timings) - 1):
                    
                    phrases.append({
                        "text": " ".join(current_phrase),
                        "start": current_start,
                        "end": word["end"]
                    })
                    current_phrase = []
                    if i < len(word_timings) - 1:
                        current_start = word_timings[i+1]["start"]
        
        # Créer les filtres pour chaque phrase
        for i, phrase in enumerate(phrases):
            clean_text = phrase['text'].replace("'", "").replace(":", " ").replace("\\", " ")
            y_pos = "h-200" if i % 2 == 0 else "h-150"
            
            phrase_filter = (
                f"drawtext=text='{clean_text}':fontsize=18:fontcolor=white:"
                f"x=(w-text_w)/2:y={y_pos}:box=1:boxcolor=black@0.7:boxborderw=5:"
                f"enable='between(t,{phrase['start']:.2f},{phrase['end']:.2f})'"
            )
            filters.append(phrase_filter)
        
        return ",".join(filters)
    
    def create_synchronized_video_for_sign(self, sign: str, add_music: bool = True) -> Optional[SynchronizedVideoResult]:
        """Crée une vidéo synchronisée pour un signe spécifique"""
        logger.info(f"Création vidéo synchronisée pour {sign}")
        
        if not self.whisper_available or not self.ffmpeg_available:
            logger.error("Dépendances manquantes (Whisper/ffmpeg)")
            return None
        
        try:
            # Validation du signe
            validated_sign = self._validate_sign(sign)
            
            # Recherche des assets
            video_path, audio_path = self._find_latest_assets(validated_sign)
            if not video_path or not audio_path:
                logger.error(f"Assets manquants pour {validated_sign}")
                return None
            
            logger.info(f"Vidéo: {os.path.basename(video_path)}")
            logger.info(f"Audio: {os.path.basename(audio_path)}")
            
            # Transcription
            transcription = self._transcribe_audio_with_whisper(audio_path)
            if not transcription:
                logger.error(f"Transcription échouée pour {validated_sign}")
                return None
            
            # Créer les sous-titres
            subtitle_filter = self._create_subtitle_filter(transcription.word_timings, validated_sign)
            
            # Durée audio
            audio_duration = self._get_file_duration(audio_path)
            if not audio_duration:
                logger.error(f"Impossible de déterminer la durée audio pour {validated_sign}")
                return None
            
            safe_duration = audio_duration + 1.0
            
            # Chemin de sortie
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_output_path = self.temp_dir / f"{validated_sign}_sync_{timestamp}.mp4"
            individual_output_path = self.individual_dir / f"{validated_sign}_final_{timestamp}.mp4"
    
            # Commande ffmpeg
            cmd = [
                'ffmpeg', '-y',
                '-stream_loop', '-1', '-i', video_path,  # Vidéo en boucle
                '-i', audio_path,                        # Audio voix
            ]
            
            if add_music and self.music_file.exists():
                cmd.extend(['-stream_loop', '-1', '-i', str(self.music_file)])  # Musique en boucle
                
                filter_complex = (
                    f"{subtitle_filter}[v_out];"
                    "[2:a]volume=0.4[a_music];"
                    "[1:a][a_music]amix=inputs=2:duration=longest[a_out]"
                )
                cmd.extend(['-filter_complex', filter_complex])
                cmd.extend(['-map', '[v_out]', '-map', '[a_out]'])
            else:
                cmd.extend(['-vf', subtitle_filter])
                cmd.extend(['-map', '0:v', '-map', '1:a'])
            
            cmd.extend([
                '-t', str(safe_duration),
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                '-c:a', 'aac', '-b:a', '192k',
                str(temp_output_path)
            ])
            
            # Exécution
            logger.info(f"Génération vidéo sync pour {validated_sign}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.ffmpeg_timeout)
            
            if result.returncode != 0:
                logger.error(f"Erreur ffmpeg: {result.stderr[:500]}")
                return None
            
            #Copier vers individual après succès ffmpeg
            try:
                shutil.copy2(temp_output_path, individual_output_path)
                logger.info(f"Vidéo copiée vers: {individual_output_path}")
            except Exception as e:
                logger.error(f"Erreur copie vers individual: {e}")
                # Continuer même si la copie échoue
   
            file_size = os.path.getsize(individual_output_path)  
            sign_name = self.sign_names.get(validated_sign, validated_sign.title())
            
            return SynchronizedVideoResult(
                sign=validated_sign,
                sign_name=sign_name,
                video_path=str(individual_output_path),
                transcription=transcription,
                has_music=add_music and self.music_file.exists(),
                file_size=file_size,
                generation_timestamp=datetime.datetime.now().isoformat()
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout génération vidéo pour {sign}")
            return None
        except Exception as e:
            logger.error(f"Erreur génération vidéo pour {sign}: {e}")
            return None
    
    def create_full_horoscope_video(self, signs: Optional[List[str]] = None) -> Optional[FullVideoResult]:
        """Crée la vidéo horoscope complète"""
        logger.info("Création vidéo horoscope complète")
        
        if not self.whisper_available or not self.ffmpeg_available:
            logger.error("Dépendances manquantes")
            return None
        
        try:
            signs = signs or self.signs_order
            synchronized_clips = []
            
            # Créer les clips synchronisés
            for sign in signs:
                # NOUVEAU : Chercher clip existant d'abord
                existing_videos = list(self.individual_dir.glob(f"{sign}_final_*.mp4"))
                
                if existing_videos:
                    # Utiliser le plus récent
                    latest_video = max(existing_videos, key=os.path.getctime)
                    logger.info(f"Utilisation clip existant: {latest_video.name}")
                    
                    # Copie temporaire pour assemblage
                    temp_assembly_path = self.temp_dir / f"{sign}_assembly_{datetime.datetime.now().strftime('%H%M%S')}.mp4"
                    shutil.copy2(latest_video, temp_assembly_path)
                    synchronized_clips.append(str(temp_assembly_path))
                    
                else:
                    # Seulement si aucun clip existant
                    logger.info(f"Aucun clip existant pour {sign}, génération...")
                    clip_result = self.create_synchronized_video_for_sign(sign)
                    if clip_result:
                        temp_assembly_path = self.temp_dir / f"{sign}_assembly_{datetime.datetime.now().strftime('%H%M%S')}.mp4"
                        shutil.copy2(clip_result.video_path, temp_assembly_path)
                        synchronized_clips.append(str(temp_assembly_path))
                    else:
                        logger.warning(f"Clip échoué pour {sign}")
            
            if not synchronized_clips:
                logger.error("Aucun clip généré")
                return None
            
            logger.info(f"Assemblage de {len(synchronized_clips)} clips")
            
            # Fichier de liste pour concaténation
            concat_file = self.output_dir / "concat_list.txt"
            with open(concat_file, 'w', encoding='utf-8') as f:
                for clip in synchronized_clips:
                    f.write(f"file '{os.path.abspath(clip)}'\n")
            
            # Vidéo finale
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = self.output_dir / f"horoscope_complet_{timestamp}.mp4"
            
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',
                str(final_path)
            ]
            
            logger.info("Assemblage final...")
            result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                logger.error(f"Erreur assemblage: {result.stderr}")
                return None
            
            for clip in synchronized_clips:
                try:
                    if "_assembly_" in clip and "temp_clips" in clip:  # NOUVEAU : condition stricte
                        os.remove(clip)
                        logger.debug(f"Supprimé fichier temporaire: {clip}")
                except Exception as e:
                    logger.warning(f"Erreur suppression {clip}: {e}")
            
            try:
                concat_file.unlink(missing_ok=True)
            except:
                pass
                
            # Résultat
            final_duration = self._get_file_duration(str(final_path))
            file_size = os.path.getsize(final_path)
            
            logger.info(f"✅ Vidéo finale créée: {final_path}")
            logger.info(f"Durée: {final_duration:.2f}s, Taille: {file_size/1024/1024:.1f}MB")
            
            return FullVideoResult(
                video_path=str(final_path),
                total_duration=final_duration or 0,
                file_size=file_size,
                clips_count=len(synchronized_clips),
                signs_included=signs,
                generation_timestamp=datetime.datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Erreur assemblage final: {e}")
            return None
    
    # =============================================================================
    # MÉTHODES D'ADMINISTRATION
    # =============================================================================
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retourne l'état du système de montage"""
        return {
            "whisper_available": self.whisper_available,
            "ffmpeg_available": self.ffmpeg_available,
            "fastmcp_available": FASTMCP_AVAILABLE,
            "config": asdict(self.config),
            "directories": {
                "output": str(self.output_dir),
                "video_input": str(self.video_input_dir),
                "audio_input": str(self.audio_input_dir),
                "temp": str(self.temp_dir),
                "individual": str(self.individual_dir) 
            },
            "music_available": self.music_file.exists(),
            "music_path": str(self.music_file),
            "supported_signs": list(self.sign_names.keys()),
            "signs_count": len(self.sign_names)
        }

    def get_assets_info(self) -> Dict[str, Any]:
        """Retourne les informations sur les assets disponibles"""
        assets = {}
        
        for sign in self.signs_order:
            video_path, audio_path = self._find_latest_assets(sign)
            assets[sign] = {
                "video_available": video_path is not None,
                "audio_available": audio_path is not None,
                "video_path": video_path,
                "audio_path": audio_path,
                "ready": video_path is not None and audio_path is not None
            }
        
        ready_count = sum(1 for info in assets.values() if info["ready"])
        
        return {
            "assets_by_sign": assets,
            "total_signs": len(self.signs_order),
            "ready_signs": ready_count,
            "completion_rate": ready_count / len(self.signs_order) if self.signs_order else 0
        }

    def get_individual_videos(self) -> Dict[str, Any]:
        """Retourne la liste des vidéos individuelles disponibles"""
        individual_videos = {}
        
        for sign in self.signs_order:
            pattern = self.individual_dir / f"{sign}_final_*.mp4"
            videos = list(self.individual_dir.glob(f"{sign}_final_*.mp4"))
            
            if videos:
                # Prendre la plus récente
                latest_video = max(videos, key=os.path.getctime)
                individual_videos[sign] = {
                    "path": str(latest_video),
                    "size": os.path.getsize(latest_video),
                    "created": datetime.datetime.fromtimestamp(os.path.getctime(latest_video)).isoformat(),
                    "sign_name": self.sign_names.get(sign, sign.title()),
                    "filename": latest_video.name
                }
            else:
                individual_videos[sign] = None
        
        return {
            "individual_videos": individual_videos,
            "available_count": len([v for v in individual_videos.values() if v is not None]),
            "total_signs": len(self.signs_order)
        }
# =============================================================================
# Fonction de Cleaning
# =============================================================================

    def cleanup_individual_videos(self, older_than_days: int = 7) -> int:
        """Nettoie les vidéos individuelles plus anciennes que X jours"""
        count = 0
        cutoff_time = time.time() - (older_than_days * 24 * 3600)
        
        try:
            for video_file in self.individual_dir.glob("*.mp4"):
                if os.path.getctime(video_file) < cutoff_time:
                    video_file.unlink()
                    count += 1
                    logger.info(f"Supprimé vidéo ancienne: {video_file.name}")
        except Exception as e:
            logger.error(f"Erreur nettoyage individual: {e}")
        
        return count 

    def cleanup_temporary_files(self) -> int:
        """Nettoie les fichiers temporaires"""
        count = 0
        try:
            for file_path in self.temp_dir.glob("*.mp4"):
                file_path.unlink()
                count += 1
            for file_path in self.output_dir.glob("concat_list.txt"):
                file_path.unlink()
                count += 1
        except Exception as e:
            logger.error(f"Erreur nettoyage: {e}")
        
        return count

# =============================================================================
# INITIALISATION GLOBALE POUR IMPORT DIRECT
# =============================================================================

# Configuration par défaut
config = VideoConfig()

# OBJET GLOBAL EXPORTABLE (comme astro_generator)
video_generator = VideoGenerator(config)

# =============================================================================
# SERVEUR MCP (OPTIONNEL)
# =============================================================================

if FASTMCP_AVAILABLE:
    mcp = FastMCP("VideoMCPServer")

    @mcp.tool()
    def get_montage_status() -> dict:
        """
        Vérifie l'état du serveur de montage.
        
        Returns:
            État détaillé du système de montage
        """
        try:
            status = video_generator.get_system_status()
            return {
                "success": True,
                "status": status
            }
        except Exception as e:
            logger.error(f"Erreur get_montage_status: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_synchronized_video(sign: str, add_music: bool = True) -> dict:
        """
        Crée une vidéo synchronisée pour un signe astrologique.
        
        Args:
            sign: Nom du signe (aries, taurus, etc.)
            add_music: Ajouter la musique de fond
        
        Returns:
            Résultat de la création vidéo
        """
        try:
            validated_sign = video_generator._validate_sign(sign)
            result = video_generator.create_synchronized_video_for_sign(validated_sign, add_music)
            
            if result:
                return {
                    "success": True,
                    "result": asdict(result),
                    "message": f"Vidéo synchronisée créée pour {result.sign_name}"
                }
            else:
                return {
                    "success": False,
                    "error": "Échec de la création vidéo"
                }
        
        except Exception as e:
            logger.error(f"Erreur create_synchronized_video: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_full_horoscope_video(signs: Optional[List[str]] = None) -> dict:
        """
        Crée la vidéo horoscope complète avec tous les signes.
        
        Args:
            signs: Liste des signes à inclure (optionnel, par défaut tous)
        
        Returns:
            Résultat de la création vidéo complète
        """
        try:
            result = video_generator.create_full_horoscope_video(signs)
            
            if result:
                return {
                    "success": True,
                    "result": asdict(result),
                    "message": f"Vidéo complète créée avec {result.clips_count} clips"
                }
            else:
                return {
                    "success": False,
                    "error": "Échec de la création vidéo complète"
                }
        
        except Exception as e:
            logger.error(f"Erreur create_full_horoscope_video: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_assets_info() -> dict:
        """
        Retourne les informations sur les assets disponibles.
        
        Returns:
            Informations détaillées sur les assets vidéo/audio
        """
        try:
            assets_info = video_generator.get_assets_info()
            return {
                "success": True,
                "assets": assets_info
            }
        except Exception as e:
            logger.error(f"Erreur get_assets_info: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def get_individual_videos() -> dict:
        """
        Retourne la liste des vidéos individuelles disponibles.
        
        Returns:
            Informations détaillées sur les vidéos par signe
        """
        try:
            videos_info = video_generator.get_individual_videos()
            return {
                "success": True,
                "videos": videos_info
            }
        except Exception as e:
            logger.error(f"Erreur get_individual_videos: {e}")
            return {"success": False, "error": str(e)}
    

    @mcp.tool()
    def cleanup_old_individual_videos(days: int = 7) -> dict:
        """
        Nettoie les vidéos individuelles anciennes.
        
        Args:
            days: Supprimer les fichiers plus anciens que X jours
        
        Returns:
            Nombre de fichiers supprimés
        """
        try:
            count = video_generator.cleanup_individual_videos(days)
            return {
                "success": True,
                "files_cleaned": count,
                "message": f"{count} vidéos individuelles supprimées"
            }
        except Exception as e:
            logger.error(f"Erreur cleanup_old_individual_videos: {e}")
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def cleanup_temp_files() -> dict:
        """
        Nettoie les fichiers temporaires de montage.
        
        Returns:
            Nombre de fichiers supprimés
        """
        try:
            count = video_generator.cleanup_temporary_files()
            return {
                "success": True,
                "files_cleaned": count,
                "message": f"{count} fichiers temporaires supprimés"
            }
        except Exception as e:
            logger.error(f"Erreur cleanup_temp_files: {e}")
            return {"success": False, "error": str(e)}

# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    print("🎬" + "="*60)
    print("🎬 VIDEO GENERATOR SERVER - VERSION HYBRIDE")
    print("🎬" + "="*60)
    
    # Vérification au démarrage
    status = video_generator.get_system_status()
    
    print(f"📊 Configuration:")
    print(f"   • Dossier sortie: {status['directories']['output']}")
    print(f"   • Dossier vidéos: {status['directories']['video_input']}")
    print(f"   • Dossier audios: {status['directories']['audio_input']}")
    print(f"   • Modèle Whisper: {config.whisper_model}")
    
    print(f"📦 Dépendances:")
    print(f"   • Whisper: {'✅' if status['whisper_available'] else '❌'}")
    print(f"   • ffmpeg: {'✅' if status['ffmpeg_available'] else '❌'}")
    print(f"   • FastMCP: {'✅' if status['fastmcp_available'] else '❌'}")
    print(f"   • Musique: {'✅' if status['music_available'] else '❌'}")
    
    print(f"🎯 Capacités:")
    print(f"   • {status['signs_count']} signes supportés")
    print(f"   • Transcription Whisper automatique")
    print(f"   • Sous-titres dynamiques")
    print(f"   • Mixage audio avec musique")
    print(f"   • Import direct ou serveur MCP")
    
    # Avertissements
    if not status['whisper_available']:
        print("⚠️  Whisper non disponible - pip install openai-whisper")
    if not status['ffmpeg_available']:
        print("⚠️  ffmpeg non disponible - Génération vidéo impossible")
    
    # Démarrage du serveur FastMCP si disponible
    if FASTMCP_AVAILABLE and "--mcp" in os.sys.argv:
        print(f"🚀 Démarrage du serveur FastMCP...")
        mcp.run()
    else:
        print("💡 Utilisation en mode module ou ajoutez --mcp pour le serveur")
        print("📄 Import disponible: from video_server_mcp import video_generator")
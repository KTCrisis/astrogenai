#!/usr/bin/env python3
"""
MCP ComfyUI Server avec FastMCP
Serveur MCP pour génération automatique de vidéos astro avec ComfyUI
Version complète avec correspondances de tous les signes
"""

import datetime
import logging
import json
import os
import random
import time
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import shutil
from tqdm import tqdm

# Imports pour ComfyUI
import requests
import websocket
import uuid
from fastmcp import FastMCP

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VideoSpecs:
    """Spécifications vidéo pour différents formats"""
    width: int
    height: int
    fps: int
    duration: int  # en secondes (nombre de frames)
    aspect_ratio: str
    platform: str
    batch_size: int

@dataclass
class ConstellationVideoResult:
    """Résultat de génération de vidéo constellation"""
    sign: str
    sign_name: str
    video_path: str
    prompt_used: str
    specs: VideoSpecs
    generation_timestamp: str
    file_size: int
    duration_seconds: float

class ComfyUIVideoGenerator:
    """Générateur de vidéos via ComfyUI"""
    
    def __init__(self, comfyui_server: str = "127.0.0.1:8188", output_dir: str = "generated_videos", images_dir: str = "images"):
        self.server_address = comfyui_server
        self.client_id = str(uuid.uuid4())
        self.output_dir = Path(output_dir)
        self.images_dir = Path(images_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Workflow de base avec ControlNet
        self.base_workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": "DreamShaper_8_pruned.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {
                    "title": "Load Checkpoint"
                }
            },
            "5": {
                "inputs": {
                    "width": 512,
                    "height": 960,
                    "batch_size": 16
                },
                "class_type": "EmptyLatentImage",
                "_meta": {
                    "title": "Empty Latent Image"
                }
            },
            "6": {
                "inputs": {
                    "seed": 886110862547056,
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["21", 0],
                    "positive": ["26", 0],
                    "negative": ["26", 1],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {
                    "title": "KSampler"
                }
            },
            "7": {
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["33", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {
                    "title": "VAE Decode"
                }
            },
            "16": {
                "inputs": {
                    "text": "blurry, low quality, human, duplicate, double, multiple subjects, split screen, divided, separated, mirrored, reflection, copies, twins, pairs, couple, text, watermark, signature, human figure, human visage, realistic photography, hyper realistic, cartoon, anime, vector art, blurry constellation, disconnected stars, incomplete constellation, scattered pattern, random dots, chaotic lines, unclear shape, deformed animal, modern frame, simple border, plain edges, minimalist design",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "Negative Prompt"
                }
            },
            "18": {
                "inputs": {
                    "prompts": "\"0\": \"cosmic deep gold starry void with swirling golden nebula clouds, scattered stellar points, infinite celestial atmosphere, dark mystical space, masterpiece, high quality\",\n\"8\": \"cosmic starry sky, mystical nebula background, stars connecting with luminous lines, constellation outline starting to form, delicate filigree borders beginning to manifest at image corners, masterpiece, high quality\",\n\"16\": \"complete constellation silhouette made of brilliant stars, clearly defined shape, Greek mythology cosmic art, ornate tarot card frame with intricate symbols, astrological decorations, and mystical borders completely surrounding the scene, fortune telling card aesthetic, masterpiece, high quality\"",
                    "interpolate_prompts": False,
                    "print_keyframes": 0,
                    "interpolation": "lerp",
                    "clip": ["1", 1]
                },
                "class_type": "ADE_PromptScheduling",
                "_meta": {
                    "title": "Prompt Scheduling"
                }
            },
            "21": {
                "inputs": {
                    "model_name": "mm_sd_v15_v2.ckpt",
                    "beta_schedule": "autoselect",
                    "model": ["1", 0]
                },
                "class_type": "ADE_AnimateDiffLoaderGen1",
                "_meta": {
                    "title": "AnimateDiff Loader"
                }
            },
            "22": {
                "inputs": {
                    "frame_rate": 8,
                    "loop_count": 0,
                    "filename_prefix": "constellation",
                    "format": "video/h264-mp4",
                    "pix_fmt": "yuv420p",
                    "crf": 19,
                    "save_metadata": True,
                    "pingpong": True,
                    "save_output": True,
                    "images": ["7", 0]
                },
                "class_type": "VHS_VideoCombine",
                "_meta": {
                    "title": "Video Combine"
                }
            },
            "25": {
                "inputs": {
                    "control_net_name": "control_v11p_sd15_scribble_fp16.safetensors"
                },
                "class_type": "ControlNetLoader",
                "_meta": {
                    "title": "ControlNet Loader"
                }
            },
            "26": {
                "inputs": {
                    "strength": 0.27,
                    "start_percent": 0.0,
                    "end_percent": 0.465,
                    "positive": ["18", 0],
                    "negative": ["16", 0],
                    "control_net": ["25", 0],
                    "image": ["32", 0]
                },
                "class_type": "ControlNetApplyAdvanced",
                "_meta": {
                    "title": "ControlNet Apply"
                }
            },
            "27": {
                "inputs": {
                    "image": "leo_image.jpg",
                    "upload": "image"
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "Load Reference Image"
                }
            },
            "32": {
                "inputs": {
                    "low_threshold": 0.3,
                    "high_threshold": 0.6,
                    "image": ["27", 0]
                },
                "class_type": "Canny",
                "_meta": {
                    "title": "Canny Edge Detection"
                }
            },
            "33": {
                "inputs": {
                    "vae_name": "vae-ft-mse-840000-ema-pruned.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {
                    "title": "VAE Loader"
                }
            }
        }
        
        # Formats vidéo disponibles
        self.video_formats = {
            "youtube_short": VideoSpecs(
                width=1080, height=1920, fps=8, duration=16, 
                aspect_ratio="9:16", platform="YouTube Shorts", batch_size=16
            ),
            "tiktok": VideoSpecs(
                width=1080, height=1920, fps=8, duration=16,
                aspect_ratio="9:16", platform="TikTok", batch_size=16
            ),
            "instagram_reel": VideoSpecs(
                width=1080, height=1920, fps=8, duration=16,
                aspect_ratio="9:16", platform="Instagram Reels", batch_size=16
            ),
            "square": VideoSpecs(
                width=1080, height=1080, fps=8, duration=16,
                aspect_ratio="1:1", platform="Instagram Post", batch_size=16
            ),
            "test": VideoSpecs(
                width=512, height=960, fps=8, duration=16,
                aspect_ratio="9:16", platform="Test", batch_size=16
            )
        }
        
        # Métadonnées complètes des signes avec correspondances précises
        self.sign_metadata = {
            "aries": {
                "name": "Bélier", 
                "animal": "ram", 
                "symbol": "♈", 
                "element": "Fire", 
                "colors": ["fiery red", "orange"], 
                "frame_color": "golden",
                "energy": "fire energy",
                "anatomic_details": "curved horns and powerful stance",
                "symbols": "fire symbols"
            },
            "taurus": {
                "name": "Taureau", 
                "animal": "bull", 
                "symbol": "♉", 
                "element": "Earth", 
                "colors": ["emerald green", "rose"], 
                "frame_color": "golden",
                "energy": "earth energy",
                "anatomic_details": "strong horns and stable stance",
                "symbols": "earth symbols"
            },
            "gemini": {
                "name": "Gémeaux", 
                "animal": "twins", 
                "symbol": "♊", 
                "element": "Air", 
                "colors": ["bright yellow", "silver"], 
                "frame_color": "silver",
                "energy": "air currents",
                "anatomic_details": "dual figures, intertwined forms, and mirrored poses",
                "symbols": "air symbols"
            },
            "cancer": {
                "name": "Cancer", 
                "animal": "crab", 
                "symbol": "♋", 
                "element": "Water", 
                "colors": ["silver", "pearl white"], 
                "frame_color": "silver",
                "energy": "lunar water energy",
                "anatomic_details": "distinct claws, shell, and segmented legs",
                "symbols": "lunar symbols"
            },
            "leo": {
                "name": "Lion",
                "animal": "lion", 
                "symbol": "♌", 
                "element": "Fire", 
                "colors": ["golden", "bright orange"], 
                "frame_color": "golden",
                "energy": "solar fire energy",
                "anatomic_details": "majestic mane, powerful stance, and regal posture",
                "symbols": "solar symbols"
            },
            "virgo": {
                "name": "Vierge", 
                "animal": "maiden", 
                "symbol": "♍", 
                "element": "Earth", 
                "colors": ["deep blue", "grey"], 
                "frame_color": "silver",
                "energy": "earth wisdom",
                "anatomic_details": "graceful figure, flowing robes, and wheat sheaf",
                "symbols": "earth symbols"
            },
            "libra": {
                "name": "Balance", 
                "animal": "scales", 
                "symbol": "♎", 
                "element": "Air", 
                "colors": ["soft blue", "pink"], 
                "frame_color": "golden",
                "energy": "harmonious air",
                "anatomic_details": "balanced scales, symmetrical design, and equilibrium",
                "symbols": "balance symbols"
            },
            "scorpio": {
                "name": "Scorpion", 
                "animal": "scorpion", 
                "symbol": "♏", 
                "element": "Water", 
                "colors": ["deep crimson", "black"], 
                "frame_color": "dark red",
                "energy": "intense water power",
                "anatomic_details": "curved tail, pincers, and segmented body",
                "symbols": "transformation symbols"
            },
            "sagittarius": {
                "name": "Sagittaire", 
                "animal": "centaur archer", 
                "symbol": "♐", 
                "element": "Fire", 
                "colors": ["royal purple", "turquoise"], 
                "frame_color": "golden",
                "energy": "adventurous fire",
                "anatomic_details": "bow and arrow, horse body, and human torso",
                "symbols": "adventure symbols"
            },
            "capricorn": {
                "name": "Capricorne",
                "animal": "mountain goat", 
                "symbol": "♑", 
                "element": "Earth", 
                "colors": ["dark brown", "charcoal"], 
                "frame_color": "bronze",
                "energy": "mountain earth",
                "anatomic_details": "curved horns, climbing stance, and sturdy build",
                "symbols": "mountain symbols"
            },
            "aquarius": {
                "name": "Verseau", 
                "animal": "water bearer", 
                "symbol": "♒", 
                "element": "Air", 
                "colors": ["electric blue", "silver"], 
                "frame_color": "electric blue",
                "energy": "electric air",
                "anatomic_details": "flowing water, vessel pouring, and ethereal form",
                "symbols": "innovation symbols"
            },
            "pisces": {
                "name": "Poissons", 
                "animal": "twin fish", 
                "symbol": "♓", 
                "element": "Water", 
                "colors": ["sea blue", "violet"], 
                "frame_color": "silver",
                "energy": "mystical water",
                "anatomic_details": "flowing fins, intertwined forms, and swimming motion",
                "symbols": "ocean symbols"
            }
        }
    
    def _get_url(self, endpoint: str) -> str:
        """Construit l'URL pour l'API ComfyUI"""
        return f"http://{self.server_address}/{endpoint}"
    
    def _get_ws_url(self) -> str:
        """Construit l'URL WebSocket pour ComfyUI"""
        return f"ws://{self.server_address}/ws?clientId={self.client_id}"
    
    def test_connection(self) -> bool:
        """Teste la connexion à ComfyUI"""
        try:
            response = requests.get(self._get_url("system_stats"), timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erreur connexion ComfyUI: {e}")
            return False
    
    def create_constellation_prompt(self, sign: str, custom_prompt: str = None) -> str:
        """Crée le prompt optimisé pour chaque constellation"""
        if custom_prompt:
            return custom_prompt
        
        sign_data = self.sign_metadata.get(sign, {})
        if not sign_data:
            return self._get_generic_prompt(sign)
        
        color_primary = sign_data["colors"][0]
        color_secondary = sign_data["colors"][1] if len(sign_data["colors"]) > 1 else sign_data["colors"][0]
        frame_color = sign_data["frame_color"]
        animal = sign_data["animal"]
        energy = sign_data["energy"]
        anatomic_details = sign_data["anatomic_details"]
        symbols = sign_data["symbols"]
        
#         prompt_v1 = ['''\"0\": \"cosmic {color_primary} starry sky with swirling {color_secondary} nebula background, scattered stellar points, celestial atmosphere, mystical {sign_data["element"].lower()} space, masterpiece, high quality\",
# \"4\": \"cosmic {color_primary} starry sky, {color_secondary} nebula background, constellation pattern forming, scattered stellar points, cosmic masterpiece, high quality\",
# \"8\": \"**moving cosmic {color_primary} starry sky**, {color_secondary} nebula background moving, stars connecting with cosmic {energy}, glowing {sign} constellation pattern forming, delicate {frame_color} filigree borders beginning to manifest at image corners, masterpiece, high quality\",
# \"12\": \"cosmic starry sky, **{color_secondary} nebula partially revealing constellation**, **stellar points pulsating**, delicate {frame_color} decorative elements beginning at corners, smooth morphing, masterpiece, high quality\",
# \"16\": \"cosmic starry sky with swirling {color_secondary} nebula background, **{animal} in greek mythology style with {anatomic_details}**, **intense glowing {color_primary} {energy}**, ornate {frame_color} tarot card frame with intricate {symbols}, astrological decorations borders completely surrounding the scene, fortune telling card aesthetic, masterpiece, high quality\"''']


        return f'''\"0\": \"cosmic {color_primary} starry sky with swirling {color_secondary} nebula background, scattered stellar points, celestial atmosphere, mystical {sign_data["element"].lower()} space, masterpiece, high quality\",
\"4\": \"cosmic {color_primary} starry sky, {color_secondary} nebula background, constellation pattern forming, scattered stellar points, cosmic masterpiece, high quality\",
\"8\": \"**moving cosmic {color_primary} starry sky**, {color_secondary} nebula background moving, stars connecting with cosmic {energy}, {sign} constellation pattern forming, delicate {frame_color} filigree borders beginning to manifest at image corners, masterpiece, high quality\",
\"12\": \"cosmic starry sky, **{color_secondary} nebula partially revealing constellation**, glowing {sign} constellation, **stellar points pulsating**, delicate {frame_color} decorative elements beginning at corners, smooth morphing, masterpiece, high quality\",
\"16\": \"cosmic starry sky with swirling {color_secondary} nebula background, **{animal} in greek mythology style with {anatomic_details}**, **intense glowing {color_primary} {energy}**, ornate {frame_color} tarot card frame with intricate {symbols}, astrological decorations borders completely surrounding the scene, fortune telling card aesthetic, masterpiece, high quality\"'''
    
    def _get_generic_prompt(self, sign: str) -> str:
        """Prompt générique de fallback"""
        return f'''\"0\": \"cosmic starry void with swirling nebula clouds, scattered stellar points, infinite celestial atmosphere, masterpiece, high quality\",
\"8\": \"cosmic starry sky, constellation pattern forming, stars connecting with luminous lines, masterpiece, high quality\",
\"16\": \"complete {sign} constellation, brilliant stars forming mythological shape, cosmic art, ornate tarot frame, masterpiece, high quality\"'''
    
    def prepare_workflow(self, sign: str, format_name: str = "test", 
                        custom_prompt: str = None, seed: int = None) -> Dict[str, Any]:
        """Prépare le workflow avec l'image de référence correspondante"""
        import copy
        workflow = copy.deepcopy(self.base_workflow)
        
        # Récupérer les spécifications du format
        specs = self.video_formats.get(format_name, self.video_formats["test"])
        
        # Configurer les dimensions
        workflow["5"]["inputs"]["width"] = specs.width
        workflow["5"]["inputs"]["height"] = specs.height
        workflow["5"]["inputs"]["batch_size"] = specs.batch_size
        

        best_seed =["886110862547056", "835635557728234", "86142623141374", "447541316895164"]
        # Configurer le seed
        if seed is None:
            seed = 447541316895164
            #seed = random.randint(0, 2**31-1)
        workflow["6"]["inputs"]["seed"] = seed
        
        # Configurer le frame rate
        workflow["22"]["inputs"]["frame_rate"] = specs.fps
        
        # Configurer le nom de fichier
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        workflow["22"]["inputs"]["filename_prefix"] = f"{sign}_{format_name}_{timestamp}"
        
        # Configurer l'image de référence
        image_filename = f"{sign}_image.jpg"
        workflow["27"]["inputs"]["image"] = image_filename
        
        # Vérifier que l'image existe
        image_path = self.images_dir / image_filename
        if not image_path.exists():
            logger.warning(f"⚠️  Image de référence non trouvée: {image_path}")
            # Utiliser une image par défaut ou lever une exception
            # workflow["27"]["inputs"]["image"] = "default_constellation.jpg"
        

        workflow["6"]["inputs"]["steps"] = 25
        workflow["6"]["inputs"]["cfg"] = 8.0
        workflow["6"]["inputs"]["sampler_name"] = "dpmpp_2m"
        workflow["6"]["inputs"]["scheduler"] = "karras"   

        # Configurer le prompt
        constellation_prompt = self.create_constellation_prompt(sign, custom_prompt)
        workflow["18"]["inputs"]["prompts"] = constellation_prompt
        
        # Ajuster la force du ControlNet selon le signe (certains nécessitent plus de contrôle)
        complex_signs = ["gemini", "scorpio", "capricorn", "aquarius", "pisces"]
        if sign in complex_signs:
            workflow["26"]["inputs"]["strength"] = 0.2
            workflow["26"]["inputs"]["start_percent"] = 0.0
            workflow["26"]["inputs"]["end_percent"] = 0.6
        else:
            workflow["26"]["inputs"]["strength"] = 0.2
            workflow["26"]["inputs"]["start_percent"] = 0.0
            workflow["26"]["inputs"]["end_percent"] = 0.4

        workflow["16"]["inputs"]["text"] = """blurry, low quality, human, duplicate, abrupt transition, sudden change, 
        discontinuous animation, jerky movement, static image, frozen frame, harsh cuts, 
        disconnected elements, scattered random dots, chaotic unconnected lines, 
        unclear nebula formation, incomplete transformation, text, watermark, signature"""

        # Vérifier la validité du workflow
        for node_id, node in workflow.items():
            if "class_type" not in node:
                logger.error(f"❌ Nœud {node_id} manque class_type")
                raise ValueError(f"Nœud {node_id} manque class_type")
            if "inputs" not in node:
                logger.error(f"❌ Nœud {node_id} manque inputs")
                raise ValueError(f"Nœud {node_id} manque inputs")
        
        return workflow
    
    def queue_prompt(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Met en file d'attente un workflow"""
        payload = {"prompt": workflow, "client_id": self.client_id}
        
        try:
            logger.info(f"🔍 Envoi du workflow avec {len(workflow)} nœuds")
            
            response = requests.post(self._get_url("prompt"), json=payload, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise en file d'attente: {e}")
            raise
    
    def wait_for_completion(self, prompt_id: str) -> bool:
        """Attend la fin de la génération via WebSocket avec barre de progression"""
        pbar = None
        ws = websocket.WebSocket()

        try:
            ws.connect(self._get_ws_url())

            while True:
                message = ws.recv()
                if isinstance(message, str):
                    data = json.loads(message)

                    if data.get('type') == 'progress' and data.get('data', {}).get('prompt_id') == prompt_id:
                        progress_data = data['data']
                        value = progress_data.get('value', 0)
                        max_val = progress_data.get('max', 1)

                        if pbar is None:
                            pbar = tqdm(total=max_val, unit=" steps", desc=f"🎨 Génération ComfyUI")

                        pbar.n = value
                        pbar.refresh()

                    elif data.get('type') == 'executing' and data.get('data', {}).get('prompt_id') == prompt_id:
                        execution_data = data.get('data', {})
                        if execution_data.get('node') is None:
                            if pbar:
                                pbar.n = pbar.total
                                pbar.refresh()
                            logger.info("✅ Génération terminée")
                            return True
                        else:
                            node_id = execution_data.get('node')
                            if pbar:
                                pbar.set_description(f"🎨 Génération ComfyUI (Nœud: {node_id})")

        except Exception as e:
            logger.error(f"Erreur WebSocket: {e}")
            return False
        finally:
            if pbar:
                pbar.close()
            if ws.connected:
                ws.close()
    
    def find_generated_video(self, prompt_id: str) -> Optional[str]:
        """Trouve la vidéo générée dans l'historique"""
        try:
            response = requests.get(self._get_url(f"history/{prompt_id}"))
            response.raise_for_status()
            history = response.json()
            
            if prompt_id not in history:
                logger.error(f"❌ Prompt ID {prompt_id} non trouvé dans l'historique")
                return None
            
            # Chercher dans les outputs
            outputs = history.get(prompt_id, {}).get("outputs", {})
            
            for node_id, node_output in outputs.items():
                # Chercher dans 'gifs' (VideoHelperSuite)
                if "gifs" in node_output:
                    for file_info in node_output["gifs"]:
                        filename = file_info.get("filename", "")
                        if filename.endswith(".mp4"):
                            subfolder = file_info.get("subfolder", "")
                            comfyui_output = "/home/fluxart/ComfyUI/output"
                            
                            if subfolder:
                                full_path = os.path.join(comfyui_output, subfolder, filename)
                            else:
                                full_path = os.path.join(comfyui_output, filename)
                            
                            if os.path.exists(full_path):
                                return full_path
            
            # Recherche par pattern de nom de fichier
            logger.info(f"🔍 Recherche par pattern...")
            comfyui_output = "/home/fluxart/ComfyUI/output"
            
            import glob
            mp4_files = glob.glob(os.path.join(comfyui_output, "*.mp4"))
            if mp4_files:
                latest_mp4 = max(mp4_files, key=os.path.getctime)
                file_time = os.path.getctime(latest_mp4)
                current_time = time.time()
                
                if current_time - file_time < 300:  # 5 minutes
                    return latest_mp4
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur recherche vidéo: {e}")
            return None
    
    def generate_constellation_video(self, sign: str, format_name: str = "test",
                                   custom_prompt: str = None, seed: int = None) -> Optional[ConstellationVideoResult]:
        """Génère une vidéo de constellation avec ControlNet"""
        
        logger.info(f"🎬 Génération vidéo pour {sign} (format: {format_name})")
        
        if not self.test_connection():
            logger.error("❌ Impossible de se connecter à ComfyUI")
            return None
        
        # Vérifier que l'image de référence existe
        image_path = self.images_dir / f"{sign}_image.jpg"
        if not image_path.exists():
            logger.error(f"❌ Image de référence manquante: {image_path}")
            return None
        
        try:
            # Préparer le workflow
            workflow = self.prepare_workflow(sign, format_name, custom_prompt, seed)
            
            # Mettre en file d'attente
            response = self.queue_prompt(workflow)
            prompt_id = response.get('prompt_id')
            
            if not prompt_id:
                logger.error("❌ Pas de prompt_id reçu")
                return None
            
            logger.info(f"✅ Prompt en file d'attente: {prompt_id}")
            
            # Attendre la fin de la génération
            if not self.wait_for_completion(prompt_id):
                logger.error("❌ Échec de la génération")
                return None
            
            # Attendre que les fichiers soient écrits
            time.sleep(2)
            
            # Trouver la vidéo générée
            video_path = self.find_generated_video(prompt_id)
            
            if not video_path:
                logger.error("❌ Vidéo générée non trouvée")
                return None
            
            # Copier vers notre dossier de sortie
            sign_data = self.sign_metadata.get(sign, {"name": sign.title()})
            final_filename = f"{sign}_{format_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            final_path = self.output_dir / final_filename
            
            shutil.copy2(video_path, final_path)
            
            # Obtenir les informations du fichier
            file_size = os.path.getsize(final_path)
            specs = self.video_formats.get(format_name, self.video_formats["test"])
            duration_seconds = specs.batch_size / specs.fps
            
            # Créer le résultat
            result = ConstellationVideoResult(
                sign=sign,
                sign_name=sign_data["name"],
                video_path=str(final_path),
                prompt_used=self.create_constellation_prompt(sign, custom_prompt),
                specs=specs,
                generation_timestamp=datetime.datetime.now().isoformat(),
                file_size=file_size,
                duration_seconds=duration_seconds
            )
            
            logger.info(f"✅ Vidéo générée: {final_path}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur génération vidéo: {e}")
            return None

# Initialisation du générateur
comfyui_generator = ComfyUIVideoGenerator()

# Création du serveur FastMCP
mcp = FastMCP("ComfyUI Video Generator")

@mcp.tool()
def get_comfyui_status() -> dict:
    """Vérifie l'état du générateur ComfyUI"""
    try:
        connected = comfyui_generator.test_connection()
        
        return {
            "success": True,
            "connected": connected,
            "server": comfyui_generator.server_address,
            "output_dir": str(comfyui_generator.output_dir),
            "images_dir": str(comfyui_generator.images_dir),
            "available_formats": list(comfyui_generator.video_formats.keys()),
            "supported_signs": list(comfyui_generator.sign_metadata.keys()),
            "workflow_ready": True
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_sign_correspondences() -> dict:
    """Retourne toutes les correspondances des signes"""
    try:
        return {
            "success": True,
            "correspondences": comfyui_generator.sign_metadata,
            "total_signs": len(comfyui_generator.sign_metadata)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def generate_constellation_video(sign: str, format_name: str = "test", 
                               custom_prompt: Optional[str] = None, 
                               seed: Optional[int] = 886110862547056) -> dict:
    """Génère une vidéo de constellation avec ControlNet"""
    try:
        if sign not in comfyui_generator.sign_metadata:
            return {
                "success": False,
                "error": f"Signe inconnu: {sign}",
                "available_signs": list(comfyui_generator.sign_metadata.keys())
            }
        
        if format_name not in comfyui_generator.video_formats:
            return {
                "success": False,
                "error": f"Format inconnu: {format_name}",
                "available_formats": list(comfyui_generator.video_formats.keys())
            }
        
        result = comfyui_generator.generate_constellation_video(
            sign=sign,
            format_name=format_name,
            custom_prompt=custom_prompt,
            seed=seed
        )
        
        if result:
            return {
                "success": True,
                "result": asdict(result),
                "message": f"Vidéo générée pour {result.sign_name}"
            }
        else:
            return {
                "success": False,
                "error": "Échec de la génération vidéo"
            }
    
    except Exception as e:
        logger.error(f"Erreur generate_constellation_video: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def generate_batch_constellation_videos(format_name: str = "test", 
                                      signs: Optional[List[str]] = None) -> dict:
    """Génère des vidéos pour plusieurs signes astrologiques"""
    try:
        if signs is None:
            signs = list(comfyui_generator.sign_metadata.keys())
        
        results = []
        successful = 0
        failed = 0
        
        for sign in signs:
            logger.info(f"🎬 Génération {sign} ({successful + failed + 1}/{len(signs)})")
            
            result = comfyui_generator.generate_constellation_video(
                sign=sign,
                format_name=format_name
            )
            
            if result:
                successful += 1
                results.append({
                    "sign": sign,
                    "success": True,
                    "result": asdict(result)
                })
            else:
                failed += 1
                results.append({
                    "sign": sign,
                    "success": False,
                    "error": "Génération échouée"
                })
        
        return {
            "success": True,
            "results": results,
            "total": len(signs),
            "successful": successful,
            "failed": failed,
            "format": format_name,
            "message": f"Génération terminée: {successful}/{len(signs)} réussies"
        }
    
    except Exception as e:
        logger.error(f"Erreur generate_batch_constellation_videos: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def preview_constellation_prompt(sign: str, custom_prompt: Optional[str] = None, seed: Optional[int] = 886110862547056) -> dict:
    """Prévisualise le prompt qui sera utilisé pour générer une constellation"""
    try:
        if sign not in comfyui_generator.sign_metadata:
            return {
                "success": False,
                "error": f"Signe inconnu: {sign}",
                "available_signs": list(comfyui_generator.sign_metadata.keys())
            }
        
        prompt = comfyui_generator.create_constellation_prompt(sign, custom_prompt)
        sign_data = comfyui_generator.sign_metadata[sign]
        final_seed = seed if seed is not None else 886110862547056
        
        return {
            "success": True,
            "sign": sign_data["name"],
            "symbol": sign_data["symbol"],
            "seed": final_seed,
            "prompt": prompt,
            "metadata": sign_data,
            "estimated_duration": "2-3 minutes",
            "image_reference": f"{sign}_image.jpg"
        }
    
    except Exception as e:
        logger.error(f"Erreur preview_constellation_prompt: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def check_reference_images() -> dict:
    """Vérifie la présence de toutes les images de référence"""
    try:
        missing_images = []
        existing_images = []
        
        for sign in comfyui_generator.sign_metadata.keys():
            image_filename = f"{sign}_image.jpg"
            image_path = comfyui_generator.images_dir / image_filename
            
            if image_path.exists():
                existing_images.append({
                    "sign": sign,
                    "filename": image_filename,
                    "path": str(image_path),
                    "size": os.path.getsize(image_path)
                })
            else:
                missing_images.append({
                    "sign": sign,
                    "filename": image_filename,
                    "expected_path": str(image_path)
                })
        
        return {
            "success": True,
            "images_dir": str(comfyui_generator.images_dir),
            "existing_images": existing_images,
            "missing_images": missing_images,
            "total_expected": len(comfyui_generator.sign_metadata),
            "total_existing": len(existing_images),
            "total_missing": len(missing_images),
            "all_present": len(missing_images) == 0
        }
    
    except Exception as e:
        logger.error(f"Erreur check_reference_images: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
def get_video_formats() -> dict:
    """Retourne tous les formats vidéo disponibles"""
    try:
        formats = {}
        for name, specs in comfyui_generator.video_formats.items():
            formats[name] = asdict(specs)
        
        return {
            "success": True,
            "formats": formats,
            "count": len(formats)
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def generate_specific_signs_batch(signs_list: List[str], format_name: str = "test") -> dict:
    """Génère des vidéos pour une liste spécifique de signes"""
    try:
        # Valider les signes
        invalid_signs = [sign for sign in signs_list if sign not in comfyui_generator.sign_metadata]
        if invalid_signs:
            return {
                "success": False,
                "error": f"Signes invalides: {', '.join(invalid_signs)}",
                "available_signs": list(comfyui_generator.sign_metadata.keys())
            }
        
        # Valider le format
        if format_name not in comfyui_generator.video_formats:
            return {
                "success": False,
                "error": f"Format invalide: {format_name}",
                "available_formats": list(comfyui_generator.video_formats.keys())
            }
        
        results = []
        successful = 0
        failed = 0
        
        for i, sign in enumerate(signs_list, 1):
            logger.info(f"🎬 Génération {sign} ({i}/{len(signs_list)})")
            
            result = comfyui_generator.generate_constellation_video(
                sign=sign,
                format_name=format_name
            )
            
            if result:
                successful += 1
                results.append({
                    "sign": sign,
                    "sign_name": result.sign_name,
                    "success": True,
                    "video_path": result.video_path,
                    "file_size": result.file_size,
                    "duration": result.duration_seconds
                })
            else:
                failed += 1
                results.append({
                    "sign": sign,
                    "success": False,
                    "error": "Génération échouée"
                })
        
        return {
            "success": True,
            "results": results,
            "total_requested": len(signs_list),
            "successful": successful,
            "failed": failed,
            "format": format_name,
            "message": f"Génération batch terminée: {successful}/{len(signs_list)} réussies"
        }
    
    except Exception as e:
        logger.error(f"Erreur generate_specific_signs_batch: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Vérification de ComfyUI au démarrage
    if comfyui_generator.test_connection():
        logger.info("🚀 Serveur FastMCP ComfyUI Video Generator démarré")
        logger.info(f"🎬 ComfyUI connecté: {comfyui_generator.server_address}")
        logger.info(f"📁 Dossier de sortie: {comfyui_generator.output_dir}")
        logger.info(f"🖼️  Dossier images: {comfyui_generator.images_dir}")
        logger.info(f"🎯 Formats disponibles: {list(comfyui_generator.video_formats.keys())}")
        logger.info(f"⭐ Signes supportés: {len(comfyui_generator.sign_metadata)} signes")
        
        # Vérifier les images de référence
        missing_count = 0
        for sign in comfyui_generator.sign_metadata.keys():
            image_path = comfyui_generator.images_dir / f"{sign}_image.jpg"
            if not image_path.exists():
                missing_count += 1
        
        if missing_count == 0:
            logger.info("✅ Toutes les images de référence sont présentes")
        else:
            logger.warning(f"⚠️  {missing_count} images de référence manquantes")
            
    else:
        logger.warning("⚠️  ComfyUI non disponible - Vérifiez que le serveur est démarré")
    
    # Démarrage du serveur FastMCP
    mcp.run()
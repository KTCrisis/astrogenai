#!/usr/bin/env python3
"""
=============================================================================
ASTRO GENERATOR MCP - INTERFACE WEB FLASK
=============================================================================
Interface web pour génération automatique d'horoscopes et vidéos astrales
Architecture modulaire avec serveurs MCP interconnectés
=============================================================================
"""

# =============================================================================
# IMPORTS ET DÉPENDANCES
# =============================================================================

# Core Python
import os
import sys
import json
import datetime
import asyncio
from functools import wraps
from pathlib import Path

from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import ollama

# Importer la configuration
from config import settings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# =============================================================================
# INITIALISATION DES SERVICES
# =============================================================================

def initialize_services():
    """
    Initialise et retourne les services disponibles dans un dictionnaire.
    """
    print("--- Initialisation des services ---")
    services = {
        'orchestrator': None,
        'astro_generator': None,
        'comfyui_generator': None,
        'video_generator': None,
        'youtube_service': None
    }
    try:
        from astro_core.orchestrator_mcp import workflow_orchestrator
        services['orchestrator'] = workflow_orchestrator
        print("✅ Orchestrator importé")
    except ImportError as e:
        print(f"⚠️  Orchestrator non disponible: {e}")

    try:
        from astro_core.services.astro_mcp import astro_generator
        services['astro_generator'] = astro_generator
        print("✅ Service Astro importé")
    except ImportError as e:
        print(f"❌ Erreur import Service Astro: {e}")
    
    try:
        from astro_core.services.comfyui_mcp import comfyui_generator
        services['comfyui_generator'] = comfyui_generator
        print("✅ Service ComfyUI importé")
    except ImportError as e:
        print(f"❌ Erreur import Service ComfyUI: {e}")
    
    try:
        from astro_core.services.video_mcp import video_generator
        services['video_generator'] = video_generator
        print("✅ Service Vidéo importé")
    except ImportError as e:
        print(f"❌ Erreur import Service Vidéo: {e}")

    try:
        from astro_core.services.youtube.youtube_mcp import youtube_server
        services['youtube_service'] = youtube_server
        print("✅ Service YouTube importé")
    except ImportError as e:
        print(f"❌ Erreur import Service YouTube: {e}")
    except Exception as e:
        print(f"❌ Erreur YouTube (authentification): {e}")

    try:
        from astro_core.services.tiktok.tiktok_mcp import tiktok_server
        services['tiktok_service'] = tiktok_server
        print("✅ Service TikTok importé")
    except ImportError as e:
        print(f"❌ Erreur import Service TikTok: {e}")
    except Exception as e:
        print(f"❌ Erreur Tiktok: {e}")

    print("--- Fin de l'initialisation ---")
    return services

# Initialisation centralisée des variables globales
SERVICES = initialize_services()
orchestrator = SERVICES.get('orchestrator')
astro_generator = SERVICES.get('astro_generator')
comfyui_generator = SERVICES.get('comfyui_generator')
video_generator = SERVICES.get('video_generator')
youtube_service = SERVICES.get('youtube_service')
tiktok_service = SERVICES.get('tiktok_service')

# =============================================================================
# INITIALISATION FLASK 
# =============================================================================
app = Flask(__name__,
            template_folder=settings.TEMPLATES_DIR,
            static_folder=settings.STATIC_DIR,
            static_url_path='/static')
# =============================================================================
# UTILITAIRES ET HELPERS
# =============================================================================

class OllamaClient:
    """Client unifié pour Ollama avec fallback automatique"""
    @staticmethod
    def make_request(endpoint, data=None, timeout=settings.OLLAMA_TIMEOUT):
        """Effectue une requête Ollama avec fallback"""
        url = f"{settings.OLLAMA_BASE_URL}/{endpoint}"
        
        try:
            # Méthode 1: Requests direct
            if data:
                response = requests.post(url, json=data, timeout=timeout)
            else:
                response = requests.get(url, timeout=timeout)
                
            if response.status_code == 200:
                return {'success': True, 'data': response.json()}
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            # Méthode 2: Fallback bibliothèque ollama
            try:
                if endpoint == "api/tags":
                    result = ollama.list()
                    return {'success': True, 'data': result}
                elif endpoint == "api/generate" and data:
                    # Adapter pour ollama.chat
                    chat_data = {
                        'model': data['model'],
                        'messages': [{'role': 'user', 'content': data['prompt']}],
                        'options': data.get('options', {})
                    }
                    result = ollama.chat(**chat_data)
                    return {'success': True, 'data': {'response': result['message']['content']}}
                else:
                    raise Exception("Endpoint non supporté en fallback")
            except Exception as ollama_error:
                return {'success': False, 'error': f"Requests: {str(e)}, Ollama: {str(ollama_error)}"}

class ValidationHelper:
    """Helpers pour validation des données"""
    
    @staticmethod
    def validate_sign(sign):
        """Valide un signe astrologique"""
        if not sign:
            raise ValueError("Signe manquant")
        return sign.lower().strip()
    
    @staticmethod
    def parse_date(date_str):
        """Parse une date string en objet date"""
        if not date_str:
            return None
        try:
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Format de date invalide: {date_str}")
    
    @staticmethod
    def validate_json_request(required_fields=None):
        """Valide une requête JSON"""
        data = request.json or {}
        
        if required_fields:
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                raise ValueError(f"Champs manquants: {', '.join(missing)}")
        
        return data

# =============================================================================
# DÉCORATEURS
# =============================================================================

def handle_api_errors(f):
    """Décorateur pour gestion centralisée des erreurs API"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(f):
                return await f(*args, **kwargs)
            else:
                return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400
        except Exception as e:
            print(f"❌ Erreur API {f.__name__}: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    return decorated_function

def require_auth(f):
    """Décorateur d'authentification (désactivé par défaut)"""
    @wraps(f)
    # Doit être async pour pouvoir utiliser await
    async def decorated_function(*args, **kwargs):
        if not settings.AUTH_ENABLED:
            return await f(*args, **kwargs) # Passe l'appel en l'attendant
            
        auth = request.authorization
        if not auth or not (auth.username == settings.AUTH_USERNAME and auth.password == settings.AUTH_PASSWORD):
            return '', 401, {'WWW-Authenticate': 'Basic realm="Astro Generator - Authentification requise"'}
        return await f(*args, **kwargs) # Passe l'appel en l'attendant
    return decorated_function

def require_service(service_name):
    """Décorateur pour vérifier la disponibilité d'un service"""
    def decorator(f):
        @wraps(f)
        # Doit être async pour pouvoir utiliser await
        async def decorated_function(*args, **kwargs):
            if not SERVICES.get(service_name, False):
                return jsonify({
                    "success": False,
                    "error": f"Service {service_name} non disponible"
                }), 503
            return await f(*args, **kwargs) # Passe l'appel en l'attendant
        return decorated_function
    return decorator

# =============================================================================
# INITIALISATION FLASK
# =============================================================================


app = Flask(__name__, 
           template_folder=settings.TEMPLATES_DIR, 
           static_folder=settings.STATIC_DIR,
           static_url_path='/static')

# =============================================================================
# SERVICES MÉTIER
# =============================================================================

class AstroService:
    """Service pour les opérations astrologiques"""
    
    @staticmethod
    async def call_astro_tool(tool_name: str, arguments: dict):
        """Interface unifiée pour appeler les outils astro"""
        if not astro_generator:
            raise Exception("Générateur d'horoscopes non disponible")
        
        # Dispatcher vers la bonne méthode
        method_map = {
            "generate_single_horoscope": AstroService._generate_single,
            "generate_daily_horoscopes": AstroService._generate_daily,
            "get_astral_context": AstroService._get_context,
            "get_sign_metadata": AstroService._get_metadata,
            "calculate_lunar_influence": AstroService._calculate_lunar
        }
        
        if tool_name not in method_map:
            raise ValueError(f"Outil inconnu: {tool_name}")
        
        return await method_map[tool_name](arguments)
    
    @staticmethod
    async def _generate_single(args):
        """Génère un horoscope individuel"""
        sign = ValidationHelper.validate_sign(args.get("sign"))
        date = ValidationHelper.parse_date(args.get("date"))
        generate_audio = args.get("generate_audio", False)
        
        horoscope_result, audio_path, audio_duration = await astro_generator.generate_single_horoscope(
            sign, date, generate_audio=generate_audio
        )
        
        result = {
            "success": True,
            "result": {
                "sign": horoscope_result.sign,
                "date": horoscope_result.date,
                "horoscope": horoscope_result.horoscope_text,
                "horoscope_text": horoscope_result.horoscope_text,
                "title_theme": horoscope_result.title_theme,
                "word_count": horoscope_result.word_count,
                "lunar_influence": horoscope_result.lunar_influence_score,
                "astral_context": {
                    "lunar_phase": horoscope_result.astral_context.lunar_phase,
                    "season": horoscope_result.astral_context.season,
                    "influential_planets": horoscope_result.astral_context.influential_planets
                }
            }
        }
        
        # Ajouter audio si généré
        if generate_audio:
            result["audio_path"] = audio_path
            result["audio_duration_seconds"] = audio_duration
        
        return result
    
    @staticmethod
    async def _generate_daily(args):
        """Génère tous les horoscopes quotidiens"""
        date = ValidationHelper.parse_date(args.get("date"))
        results = await astro_generator.generate_daily_horoscopes(date)
        
        formatted_results = {}
        for key, result in results.items():
            if hasattr(result, 'horoscope_text'):
                formatted_results[key] = {
                    "sign": result.sign,
                    "horoscope": result.horoscope_text,
                    "word_count": result.word_count,
                    "lunar_influence": result.lunar_influence_score
                }
            else:
                formatted_results[key] = {"error": str(result)}
        
        return {
            "success": True,
            "result": {
                "date": args.get("date") or datetime.date.today().strftime("%Y-%m-%d"),
                "horoscopes": formatted_results,
                "total_generated": len(formatted_results)
            }
        }
    
    @staticmethod
    async def _get_context(args):
        """Obtient le contexte astral"""
        date_str = args.get("date", datetime.date.today().strftime("%Y-%m-%d"))
        date = ValidationHelper.parse_date(date_str)
        context = astro_generator.get_astral_context(date)
        
        return {
            "success": True,
            "result": {
                "date": context.date,
                "day_of_week": context.day_of_week,
                "lunar_phase": context.lunar_phase,
                "season": context.season,
                "influential_planets": context.influential_planets,
                "seasonal_energy": context.seasonal_energy
            }
        }
    
    @staticmethod
    async def _get_metadata(args):
        """Obtient les métadonnées d'un signe"""
        sign = ValidationHelper.validate_sign(args.get("sign"))
        metadata = astro_generator.get_sign_metadata(sign)
        
        if not metadata:
            raise ValueError(f"Signe inconnu: {sign}")
        
        return {
            "success": True,
            "result": {
                "name": metadata.name,
                "dates": metadata.dates,
                "element": metadata.element,
                "ruling_planet": metadata.ruling_planet,
                "constellation": metadata.constellation,
                "traits": metadata.traits,
                "colors": metadata.colors,
                "stone": metadata.stone,
                "keywords": metadata.keywords,
                "compatible_signs": metadata.compatible_signs
            }
        }
    
    @staticmethod
    async def _calculate_lunar(args):
        """Calcule l'influence lunaire"""
        sign = ValidationHelper.validate_sign(args.get("sign"))
        date_str = args.get("date", datetime.date.today().strftime("%Y-%m-%d"))
        date = ValidationHelper.parse_date(date_str)
        
        influence = astro_generator.calculate_lunar_influence(sign, date)
        interpretation = "Faible" if influence < 0.5 else "Modérée" if influence < 0.8 else "Forte"
        
        return {
            "success": True,
            "result": {
                "sign": sign,
                "date": date_str,
                "lunar_influence_score": round(influence, 3),
                "interpretation": interpretation
            }
        }

class ComfyUIService:
    """Service pour les opérations ComfyUI"""
    
    @staticmethod
    def validate_sign_and_format(sign, format_name):
        """Valide signe et format pour ComfyUI"""
        if not comfyui_generator:
            raise Exception("ComfyUI non disponible")
        
        sign = ValidationHelper.validate_sign(sign)
        
        if sign not in comfyui_generator.sign_metadata:
            raise ValueError(f"Signe inconnu: {sign}")
        
        if format_name not in comfyui_generator.video_formats:
            raise ValueError(f"Format inconnu: {format_name}")
        
        return sign, format_name

class VideoService:
    """Service pour les opérations vidéo avec montage"""
    
    @staticmethod
    def validate_sign(sign):
        """Valide un signe pour le générateur vidéo"""
        if not video_generator:
            raise Exception("Video generator non disponible")
        
        return video_generator._validate_sign(sign)
    
    @staticmethod
    def create_synchronized_video(sign, add_music=True):
        """Crée une vidéo synchronisée pour un signe"""
        validated_sign = VideoService.validate_sign(sign)
        result = video_generator.create_synchronized_video_for_sign(validated_sign, add_music)
        return result
    
    @staticmethod
    def create_full_video(signs=None):
        """Crée la vidéo complète avec tous les signes"""
        if not SERVICES['video_generator']:
            raise Exception("Video generator non disponible")
        
        result = video_generator.create_full_horoscope_video(signs)
        return result
    
    @staticmethod
    def get_system_status():
        """Retourne l'état du système vidéo"""
        if not SERVICES['video_generator']:
            raise Exception("Video generator non disponible")
        
        return video_generator.get_system_status()
    
    @staticmethod
    def get_assets_info():
        """Retourne les informations sur les assets"""
        if not SERVICES['video_generator']:
            raise Exception("Video generator non disponible")
        
        return video_generator.get_assets_info()
    
    @staticmethod
    def cleanup_temp_files():
        """Nettoie les fichiers temporaires"""
        if not SERVICES['video_generator']:
            raise Exception("Video generator non disponible")
        
        return video_generator.cleanup_temporary_files()

# =============================================================================
# ENDPOINTS PRINCIPAUX
# =============================================================================

@app.route('/')
def index():
    """Page d'accueil principale"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir les fichiers statiques"""
    return send_from_directory(settings.STATIC_FOLDER, filename)

@app.route('/health')
@handle_api_errors
async def health_check():
    """Endpoint de santé pour monitoring"""
    # Test Ollama
    ollama_result = OllamaClient.make_request("api/tags", timeout=5)
    ollama_status = ollama_result['success']
    ollama_models = ollama_result.get('data', {}).get('models', []) if ollama_status else []
    
    # Test Astro Generator
    astro_status = False
    astro_error = None
    if astro_generator:
        try:
            today = datetime.date.today()
            context = astro_generator.get_astral_context(today)
            astro_status = context is not None
        except Exception as e:
            astro_error = str(e)
    else:
        astro_error = "Module non importé"
    
    # Test ComfyUI
    comfyui_status = False
    if comfyui_generator:
        try:
            comfyui_status = comfyui_generator.test_connection()
        except Exception:
            pass
    
    # Test Video Generator 
    video_status = False
    video_error = None
    if video_generator:
        try:
            video_status_data = video_generator.get_system_status()
            video_status = video_status_data['whisper_available'] and video_status_data['ffmpeg_available']
        except Exception as e:
            video_error = str(e)
    else:
        video_error = "Module non importé"

    # Test Orchestrator 
    orchestrator_status = False
    orchestrator_error = None
    if orchestrator:
        try:
            status = orchestrator.get_orchestrator_status()
            orchestrator_status = status['success'] and status['status']['ollama_available']
        except Exception as e:
            orchestrator_error = str(e)
    else:
        orchestrator_error = "Module non importé"
    
    overall_status = 'healthy' if (ollama_status and astro_status) else 'degraded'
    
    return jsonify({
        'flask': True,
        'services': {
            'ollama': {
                'status': ollama_status,
                'models': [m.get('name', 'unknown') for m in ollama_models],
                'count': len(ollama_models),
                'error': ollama_result.get('error') if not ollama_status else None
            },
            'astro': {
                'status': astro_status,
                'available': astro_generator is not None,
                'error': astro_error
            },
            'comfyui': {
                'status': comfyui_status,
                'available': comfyui_generator is not None
            },
            'video_generator': {
                'status': video_status,
                'available': video_generator is not None,
                'error': video_error
            },
            'orchestrator': {
                'status': orchestrator_status,
                'available': orchestrator is not None,
                'error': orchestrator_error,
                'capabilities': ['intelligent_planning', 'adaptive_execution', 'error_recovery'] if orchestrator_status else []
            }
        },
        'status': overall_status,
        'timestamp': datetime.datetime.now().isoformat(),
        'version': '2.1.0'
    })

# =============================================================================
# ROUTES POUR LES PAGES LÉGALES
# =============================================================================

@app.route('/terms-of-service')
def terms_page():
    """Sert la page des conditions d'utilisation."""
    return render_template('terms.html')

@app.route('/privacy-policy')
def privacy_page():
    """Sert la page de politique de confidentialité."""
    return render_template('privacy.html')

# =============================================================================
# API ENDPOINT AGENT ORCHESTRATOR
# =============================================================================

@app.route('/api/agent/status', methods=['GET'])
@handle_api_errors
async def api_agent_status():
    """État de l'agent orchestrateur intelligent"""
    if not orchestrator:
        return jsonify({
            "success": False,
            "error": "Orchestrateur non disponible",
            "available": False
        }), 503
    
    try:
        status = orchestrator.get_orchestrator_status()
        return jsonify({
            "success": True,
            "agent_available": True,
            "orchestrator_status": status,
            "capabilities": status["status"]["capabilities"],
            "active_workflows": status["status"]["active_workflows"],
            "performance_summary": {
                "workflows_processed": status["status"]["total_workflows_processed"],
                "success_rate": status["status"]["average_success_rate"]
            },
            "ready": status["status"]["ollama_available"]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/agent/intelligent_batch', methods=['POST'])
@handle_api_errors
@require_service('orchestrator')
async def api_intelligent_batch_generation():
    """Génération batch intelligente orchestrée par l'agent"""
    if not orchestrator:
        return jsonify({
            "success": False,
            "error": "Agent orchestrateur non disponible"
        }), 503
    
    data = ValidationHelper.validate_json_request()
    
    agent_request = {
        "workflow_type": "intelligent_batch_generation",
        "user_request": data,
        "services_available": {
            "astro_generator": SERVICES.get('astro_generator', False),
            "comfyui_generator": SERVICES.get('comfyui_generator', False), 
            "video_generator": SERVICES.get('video_generator', False),
            "youtube_service": SERVICES.get('youtube_service', False)
        },
        "signs": data.get('signs', [
            'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
            'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
        ]),
        "include_audio": data.get('include_audio', True),
        "include_video": data.get('include_video', True),
        "include_upload": data.get('include_upload', False),
        "format": data.get('format', 'youtube_short'),
        "optimization_goals": data.get('optimization_goals', ['quality', 'speed']),
        "constraints": {
            "max_execution_time": data.get('max_time', 3600),
            "resource_usage": data.get('resource_level', 'medium'),
            "quality_level": data.get('quality', 'high')
        }
    }
    
    try:
        plan = await orchestrator.create_intelligent_plan(agent_request)
        
        if not plan:
            return jsonify({
                "success": False,
                "error": "L'agent n'a pas pu créer de plan viable"
            }), 500
        
        execution_result = await orchestrator.execute_workflow_plan(plan)
        
        return jsonify({
            "success": True,
            "agent_analysis": {
                "strategy_chosen": plan.execution_strategy,
                "reasoning": "Plan optimisé par intelligence artificielle",
                "estimated_duration": plan.estimated_total_duration,
                "actual_duration": execution_result.execution_time,
                "efficiency_ratio": plan.estimated_total_duration / execution_result.execution_time if execution_result.execution_time > 0 else 1.0,
                "steps_planned": len(plan.steps),
                "optimization_goals": plan.optimization_goals
            },
            "execution_results": {
                "workflow_success": execution_result.success,
                "completed_steps": execution_result.completed_steps,
                "failed_steps": execution_result.failed_steps,
                "execution_time": execution_result.execution_time,
                "performance_metrics": execution_result.performance_metrics,
                "optimizations_applied": execution_result.optimizations_applied
            },
            "agent_insights": execution_result.agent_insights,
            "detailed_results": execution_result.results,
            "recommendations": {
                "performance_assessment": execution_result.agent_insights.get('performance_assessment', 'good'),
                "future_optimizations": execution_result.agent_insights.get('optimization_recommendations', []),
                "learning_points": execution_result.agent_insights.get('learning_points', [])
            },
            "workflow_id": plan.workflow_id,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur orchestrateur intelligent: {str(e)}",
            "fallback_available": True,
            "suggestion": "Utilisez le workflow standard en cas de problème"
        }), 500

@app.route('/api/agent/smart_single_generation', methods=['POST'])
@handle_api_errors
@require_service('astro_generator')
async def api_smart_single_generation():
    """Génération intelligente pour un signe avec adaptation contextuelle"""
    if not ORCHESTRATOR_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Agent non disponible"
        }), 503
    
    data = ValidationHelper.validate_json_request(['sign'])
    
    agent_request = {
        "workflow_type": "smart_single_generation",
        "target_sign": data['sign'],
        "date": data.get('date', datetime.date.today().strftime('%Y-%m-%d')),
        "include_audio": data.get('include_audio', True),
        "include_video": data.get('include_video', True),
        "format": data.get('format', 'youtube_short'),
        "quality_level": data.get('quality', 'high'),
        "context": {
            "user_preferences": data.get('preferences', {}),
            "system_load": "medium",  # À déterminer dynamiquement
            "urgency": data.get('urgency', 'normal'),
            "services_available": {
                "astro": SERVICES.get('astro_generator', False),
                "comfyui": SERVICES.get('comfyui_generator', False),
                "video": SERVICES.get('video_generator', False),
                "youtube": SERVICES.get('youtube_service', False),
                "tiktok": SERVICES.get('tiktok_service', False)

            }
        },
        "optimization_goals": data.get('optimization_goals', ['quality', 'personalization'])
    }
    
    try:
        plan = await orchestrator.create_intelligent_plan(agent_request)
        
        execution = await orchestrator.execute_workflow_plan(plan)
        
        return jsonify({
            "success": True,
            "sign": data['sign'],
            "sign_name": execution.results.get('astro_server', {}).get('sign', data['sign']),
            "agent_strategy": {
                "strategy_applied": plan.execution_strategy,
                "personalization_level": "high",
                "adaptation_reasoning": f"Stratégie {plan.execution_strategy} choisie pour optimiser {', '.join(plan.optimization_goals)}",
                "efficiency_optimizations": execution.optimizations_applied,
                "estimated_vs_actual": {
                    "estimated": plan.estimated_total_duration,
                    "actual": execution.execution_time
                }
            },
            "content_generated": {
                "horoscope_available": 'astro_server' in execution.results,
                "video_available": 'comfyui_server' in execution.results or 'video_server' in execution.results,
                "audio_available": execution.results.get('astro_server', {}).get('audio_generated', False),
                "services_used": list(execution.results.keys())
            },
            "quality_metrics": execution.performance_metrics,
            "agent_insights": {
                "performance_assessment": execution.agent_insights.get('performance_assessment', 'good'),
                "content_quality_estimated": "high" if execution.success else "medium",
                "improvements_suggested": execution.agent_insights.get('optimization_recommendations', []),
                "learning_for_next_time": execution.agent_insights.get('learning_points', [])
            },
            "execution_details": {
                "total_time": execution.execution_time,
                "steps_completed": len(execution.completed_steps),
                "steps_failed": len(execution.failed_steps),
                "efficiency_score": execution.performance_metrics.get('efficiency_score', 0.0),
                "success_rate": 1.0 if execution.success else 0.0
            },
            "raw_results": execution.results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur génération intelligente: {str(e)}",
            "fallback_available": True
        }), 500

@app.route('/api/agent/optimize_workflow', methods=['POST'])
@handle_api_errors
async def api_optimize_workflow():
    """Optimisation intelligente des workflows par l'agent"""
    if not ORCHESTRATOR_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Agent non disponible"
        }), 503
    
    data = ValidationHelper.validate_json_request()
    
    try:
        optimization_result = await orchestrator.optimize_existing_workflow(
            data.get('workflow_id', 'current_system'),
            data.get('optimization_goals', ['speed', 'quality', 'resource_efficiency'])
        )
        
        return jsonify({
            "success": True,
            "optimization_analysis": optimization_result,
            "current_system_assessment": optimization_result.get('current_plan', {}),
            "proposed_improvements": optimization_result.get('optimizations', {}),
            "expected_benefits": optimization_result.get('optimizations', {}).get('expected_improvements', {}),
            "implementation_priority": optimization_result.get('optimizations', {}).get('implementation_priority', 'medium'),
            "actionable_steps": optimization_result.get('optimizations', {}).get('recommendations', []),
            "estimated_impact": {
                "performance_gain": optimization_result.get('optimizations', {}).get('expected_improvements', {}).get('time_reduction', '0%'),
                "quality_improvement": optimization_result.get('optimizations', {}).get('expected_improvements', {}).get('quality_improvement', 'stable'),
                "resource_efficiency": optimization_result.get('optimizations', {}).get('expected_improvements', {}).get('resource_savings', 'stable')
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur optimisation: {str(e)}"
        }), 500

@app.route('/api/agent/performance_analysis', methods=['GET'])
@handle_api_errors
async def api_agent_performance_analysis():
    """Analyse de performance par l'agent"""
    if not ORCHESTRATOR_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "Agent non disponible"
        }), 503
    
    try:
        days = request.args.get('days', 7, type=int)
        
        analysis = await orchestrator.analyze_workflow_performance_method(days)
        
        return jsonify({
            "success": True,
            "analysis_period": f"{days} jours",
            "performance_insights": analysis,
            "key_metrics": analysis.get('raw_metrics', {}),
            "strategic_analysis": analysis.get('analysis', {}),
            "actionable_recommendations": analysis.get('analysis', {}).get('strategic_recommendations', []),
            "predicted_improvements": analysis.get('analysis', {}).get('predicted_improvements', ''),
            "trend_analysis": {
                "performance_trends": analysis.get('analysis', {}).get('performance_trends', ''),
                "bottlenecks": analysis.get('analysis', {}).get('bottlenecks_identified', []),
                "success_factors": analysis.get('analysis', {}).get('success_factors', [])
            },
            "next_steps": analysis.get('analysis', {}).get('optimization_opportunities', [])
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur analyse performance: {str(e)}"
        }), 500


# =============================================================================
# API ENDPOINTS - HOROSCOPES 
# =============================================================================

@app.route('/api/generate_single_horoscope', methods=['POST'])
@handle_api_errors
@require_service('astro_generator')
async def api_generate_single_horoscope():
    """Génère un horoscope pour un signe spécifique"""
    data = ValidationHelper.validate_json_request(['sign'])
    arguments = {
        "sign": data['sign'],
        "date": data.get('date'),
        "generate_audio": False
    }
    
    result = await AstroService.call_astro_tool("generate_single_horoscope", arguments)
    return jsonify(result)

@app.route('/api/generate_single_horoscope_with_audio', methods=['POST'])
@handle_api_errors
@require_service('astro_generator')
async def api_generate_single_horoscope_with_audio():
    """Génère un horoscope avec fichier audio TTS"""
    data = ValidationHelper.validate_json_request(['sign'])
    arguments = {
        "sign": data['sign'],
        "date": data.get('date'),
        "generate_audio": True
    }
    
    result = await AstroService.call_astro_tool("generate_single_horoscope", arguments)
    
    # Reformater pour compatibilité
    if result['success']:
        horoscope_data = result['result']
        return jsonify({
            "success": True,
            "horoscope": {
                "sign": horoscope_data['sign'],
                "date": horoscope_data['date'],
                "horoscope_text": horoscope_data['horoscope_text'],
                "word_count": horoscope_data['word_count']
            },
            "audio_path": result.get('audio_path'),
            "audio_duration_seconds": result.get('audio_duration_seconds')
        })
    
    return jsonify(result)

@app.route('/api/generate_daily_horoscopes', methods=['POST'])
@handle_api_errors
@require_service('astro_generator')
async def api_generate_daily_horoscopes():
    """Génère tous les horoscopes quotidiens"""
    data = ValidationHelper.validate_json_request()
    arguments = {"date": data.get('date')}
    
    result = await AstroService.call_astro_tool("generate_daily_horoscopes", arguments)
    return jsonify(result)

@app.route('/api/get_astral_context', methods=['POST'])
@handle_api_errors
@require_service('astro_generator')
async def api_get_astral_context():
    """Obtient le contexte astral pour une date"""
    data = ValidationHelper.validate_json_request()
    arguments = {"date": data.get('date')}
    
    result = await AstroService.call_astro_tool("get_astral_context", arguments)
    return jsonify(result)

@app.route('/api/calculate_lunar_influence', methods=['POST'])
@handle_api_errors
@require_service('astro_generator')
async def api_calculate_lunar_influence():
    """Calcule l'influence lunaire"""
    data = ValidationHelper.validate_json_request(['sign'])
    arguments = {
        "sign": data['sign'],
        "date": data.get('date')
    }
    
    result = await AstroService.call_astro_tool("calculate_lunar_influence", arguments)
    return jsonify(result)

@app.route('/api/get_sign_metadata', methods=['POST'])
@handle_api_errors
@require_service('astro_generator')
async def api_get_sign_metadata():
    """Obtient les métadonnées d'un signe"""
    data = ValidationHelper.validate_json_request(['sign'])
    arguments = {"sign": data['sign']}
    
    result = await AstroService.call_astro_tool("get_sign_metadata", arguments)
    return jsonify(result)

# =============================================================================
# API ENDPOINTS - ASTROCHART
# =============================================================================

@app.route('/api/astrochart/generate_image', methods=['POST'])
@handle_api_errors
@require_service('astro_generator')
async def api_generate_chart_image():
    """Génère une image de la carte du ciel via le générateur intégré."""
    data = request.json or {}
    date_str = data.get('date')

    try:
        # Import des dépendances nécessaires
        from astro_core.services.astrochart.astrochart_mcp import astro_calculator
        import datetime
        
        # Validation et parsing de la date
        if date_str:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = datetime.date.today()
        
        # Vérification que le générateur d'images est disponible
        if not hasattr(astro_generator, 'chart_generator') or astro_generator.chart_generator is None:
            raise Exception("Générateur d'images non disponible (Matplotlib requis)")
        
        # Calcul des positions planétaires (réutilisation des données existantes)
        positions = astro_calculator.calculate_positions(target_date)
        
        if not positions:
            raise Exception("Impossible de calculer les positions planétaires")
        
        # Génération de l'image directement via le générateur intégré
        chart_path = astro_generator.chart_generator.create_chart_from_positions(
            positions, target_date
        )
        
        if chart_path:
            relative_path = os.path.relpath(chart_path, settings.STATIC_DIR)
            web_path = f"/static/{relative_path.replace(os.sep, '/')}"
            result = {
                "success": True,
                "chart_image_path": web_path,
                "date": target_date.strftime('%Y-%m-%d'),
                "positions_count": len(positions),
                "message": f"Carte astrologique générée pour le {target_date.strftime('%d/%m/%Y')}"
            }
        else:
            result = {
                "success": False,
                "error": "Échec de la génération de l'image"
            }
        
        return jsonify(result)
        
    except ValueError as e:
        # Erreur de format de date
        raise Exception(f"Format de date invalide. Utilisez YYYY-MM-DD. Erreur: {str(e)}")
    except Exception as e:
        # Autres erreurs
        raise Exception(f"Erreur lors de la génération de la carte: {str(e)}")
        
# =============================================================================
# API ENDPOINTS - OLLAMA CHAT 
# =============================================================================

@app.route('/api/ollama/models', methods=['GET'])
@handle_api_errors
async def api_ollama_models():
    """Récupère la liste des modèles Ollama disponibles"""
    result = OllamaClient.make_request("api/tags")
    
    if result['success']:
        models = result['data'].get('models', [])
        return jsonify({
            "success": True,
            "models": models,
            "count": len(models)
        })
    else:
        return jsonify({
            "success": False,
            "error": f"Ollama non disponible: {result['error']}",
            "models": [],
            "suggestion": "Vérifiez qu'Ollama est démarré avec 'ollama serve'"
        }), 503

@app.route('/api/ollama/chat', methods=['POST'])
@handle_api_errors
async def api_ollama_chat():
    """Endpoint pour le chat avec Ollama"""
    data = ValidationHelper.validate_json_request(['message'])
    message = data['message'].strip()
    model = data.get('model', 'llama3:8b')
    
    if not message:
        raise ValueError("Message vide")
    
    # Prompt système pour l'astrologie
    astro_prompt = f"""Tu es un astrologue expert et bienveillant qui aide les gens avec leurs questions astrologiques.
Réponds de manière claire, positive et informative. Évite les prédictions trop précises.
Reste dans le domaine de l'astrologie et de la spiritualité.

Question: {message}

Réponse:"""
    
    request_data = {
        'model': model,
        'prompt': astro_prompt,
        'stream': False,
        'think': False,
        'options': {
            'temperature': 0.7,
            'top_p': 0.9,
            'num_predict': 2000
        }
    }
    
    result = OllamaClient.make_request("api/generate", request_data, settings.OLLAMA_CHAT_TIMEOUT)
    
    if result['success']:
        ai_response = result['data'].get('response', 'Erreur dans la réponse')
        return jsonify({
            "success": True,
            "response": ai_response,
            "model": model,
            "timestamp": datetime.datetime.now().isoformat()
        })
    else:
        error_msg = result['error']
        if "model" in error_msg.lower():
            error_msg = f"Modèle '{model}' non disponible. Vérifiez qu'il est installé avec 'ollama pull {model}'"
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            error_msg = "Impossible de se connecter à Ollama. Vérifiez qu'il est démarré avec 'ollama serve'"
        
        return jsonify({
            "success": False,
            "error": error_msg
        }), 503

# =============================================================================
# API ENDPOINTS - COMFYUI VIDÉO 
# =============================================================================

@app.route('/api/comfyui/status', methods=['GET'])
@handle_api_errors
@require_service('comfyui_generator')
async def api_comfyui_status():
    """Retourne l'état du générateur ComfyUI"""
    connected = comfyui_generator.test_connection()
    
    return jsonify({
        "success": True,
        "connected": connected,
        "server": comfyui_generator.server_address,
        "output_dir": str(comfyui_generator.output_dir),
        "available_formats": list(comfyui_generator.video_formats.keys()),
        "supported_signs": list(comfyui_generator.sign_metadata.keys()),
        "workflow_ready": True,
        "message": "ComfyUI opérationnel" if connected else "ComfyUI non connecté"
    })

@app.route('/api/comfyui/formats', methods=['GET'])
@handle_api_errors
@require_service('comfyui_generator')
async def api_comfyui_formats():
    """Retourne les formats vidéo disponibles"""
    formats = {}
    for name, specs in comfyui_generator.video_formats.items():
        formats[name] = {
            "width": specs.width,
            "height": specs.height,
            "fps": specs.fps,
            "duration": specs.duration,
            "aspect_ratio": specs.aspect_ratio,
            "platform": specs.platform,
            "batch_size": specs.batch_size
        }
    
    return jsonify({
        "success": True,
        "formats": formats,
        "count": len(formats)
    })

@app.route('/api/comfyui/generate_video', methods=['POST'])
@handle_api_errors
@require_service('comfyui_generator')
async def api_comfyui_generate_video():
    """Génère une vidéo de constellation avec ComfyUI"""
    data = ValidationHelper.validate_json_request(['sign'])
    
    sign, format_name = ComfyUIService.validate_sign_and_format(
        data['sign'], 
        data.get('format', 'test')
    )
    
    result = comfyui_generator.generate_constellation_video(
        sign=sign,
        format_name=format_name,
        custom_prompt=data.get('custom_prompt'),
        seed=data.get('seed')
    )
    
    if result:
        return jsonify({
            "success": True,
            "result": {
                "sign": result.sign,
                "sign_name": result.sign_name,
                "video_path": result.video_path,
                "file_size": result.file_size,
                "duration_seconds": result.duration_seconds,
                "specs": {
                    "width": result.specs.width,
                    "height": result.specs.height,
                    "fps": result.specs.fps,
                    "platform": result.specs.platform
                },
                "generation_timestamp": result.generation_timestamp
            },
            "message": f"Vidéo générée pour {result.sign_name}"
        })
    else:
        raise Exception("Échec de la génération vidéo")

@app.route('/api/comfyui/generate_batch', methods=['POST'])
@handle_api_errors
@require_service('comfyui_generator')
async def api_comfyui_generate_batch():
    """Génère des vidéos pour plusieurs signes"""
    data = ValidationHelper.validate_json_request()
    format_name = data.get('format', 'test')
    signs = data.get('signs') or list(comfyui_generator.sign_metadata.keys())
    
    results = []
    successful = 0
    failed = 0
    
    for sign in signs:
        try:
            result = comfyui_generator.generate_constellation_video(
                sign=sign,
                format_name=format_name
            )
            
            if result:
                successful += 1
                results.append({
                    "sign": sign,
                    "success": True,
                    "result": {
                        "sign_name": result.sign_name,
                        "video_path": result.video_path,
                        "file_size": result.file_size,
                        "duration_seconds": result.duration_seconds
                    }
                })
            else:
                failed += 1
                results.append({
                    "sign": sign,
                    "success": False,
                    "error": "Génération échouée"
                })
                
        except Exception as e:
            failed += 1
            results.append({
                "sign": sign,
                "success": False,
                "error": str(e)
            })
    
    return jsonify({
        "success": True,
        "results": results,
        "total": len(signs),
        "successful": successful,
        "failed": failed,
        "format": format_name,
        "message": f"Génération terminée: {successful}/{len(signs)} réussies"
    })

@app.route('/api/comfyui/preview_prompt', methods=['POST'])
@handle_api_errors
@require_service('comfyui_generator')
async def api_comfyui_preview_prompt():
    """Prévisualise le prompt qui sera utilisé"""
    data = ValidationHelper.validate_json_request(['sign'])
    
    sign = ValidationHelper.validate_sign(data['sign'])
    if sign not in comfyui_generator.sign_metadata:
        raise ValueError(f"Signe inconnu: {sign}")
    
    prompt = comfyui_generator.create_constellation_prompt(sign, data.get('custom_prompt'))
    sign_data = comfyui_generator.sign_metadata[sign]
    
    return jsonify({
        "success": True,
        "sign": sign_data["name"],
        "symbol": sign_data["symbol"],
        "prompt": prompt,
        "metadata": sign_data,
        "estimated_duration": "2-3 minutes"
    })

@app.route('/api/comfyui/download_video/<path:video_path>')
@handle_api_errors
@require_service('comfyui_generator')
async def api_comfyui_download_video(video_path):
    """Télécharge une vidéo générée"""
    # Sécurité : vérifier que le fichier est dans le dossier de sortie
    full_path = os.path.join(comfyui_generator.output_dir, video_path)
    
    if not os.path.exists(full_path):
        return jsonify({
            "success": False,
            "error": "Fichier non trouvé"
        }), 404
    
    # Vérifier que le fichier est bien dans le dossier autorisé
    if not os.path.abspath(full_path).startswith(os.path.abspath(comfyui_generator.output_dir)):
        return jsonify({
            "success": False,
            "error": "Accès non autorisé"
        }), 403
    
    return send_from_directory(
        comfyui_generator.output_dir,
        video_path,
        as_attachment=True
    )

# =============================================================================
# API ENDPOINTS - VIDÉO MONTAGE 
# =============================================================================

@app.route('/api/montage/status', methods=['GET'])
@handle_api_errors
@require_service('video_generator')
async def api_montage_status():
    """Retourne l'état du serveur de montage"""
    try:
        status = VideoService.get_system_status()
        return jsonify({
            "success": True,
            "status": {
                "whisper_available": status['whisper_available'],
                "ffmpeg_available": status['ffmpeg_available'],
                "music_available": status['music_available'],
                "directories": status['directories'],
                "music_path": status['music_path'],
                "supported_signs": status['supported_signs'],
                "signs_count": status['signs_count']
            },
            "ready": status['whisper_available'] and status['ffmpeg_available']
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/montage/create_single_video', methods=['POST'])
@handle_api_errors
@require_service('video_generator')
async def api_create_single_video():
    """Crée une vidéo synchronisée pour un signe"""
    try:
        data = ValidationHelper.validate_json_request(['sign'])
        sign = data['sign']
        add_music = data.get('add_music', True)
        
        result = VideoService.create_synchronized_video(sign, add_music)
        
        if result:
            return jsonify({
                "success": True,
                "result": {
                    "sign": result.sign,
                    "sign_name": result.sign_name,
                    "video_path": result.video_path,
                    "transcription": {
                        "full_text": result.transcription.full_text,
                        "duration": result.transcription.duration,
                        "word_count": result.transcription.word_count
                    },
                    "has_music": result.has_music,
                    "file_size": result.file_size,
                    "generation_timestamp": result.generation_timestamp
                },
                "message": f"Vidéo synchronisée créée pour {result.sign_name}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de la création vidéo"
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/montage/create_full_video', methods=['POST'])
@handle_api_errors
@require_service('video_generator')
async def api_create_full_video():
    """Crée la vidéo horoscope complète avec tous les signes"""
    try:
        data = ValidationHelper.validate_json_request()
        signs = data.get('signs')  # Optionnel, par défaut tous les signes
        
        result = VideoService.create_full_video(signs)
        
        if result:
            return jsonify({
                "success": True,
                "result": {
                    "video_path": result.video_path,
                    "total_duration": result.total_duration,
                    "file_size": result.file_size,
                    "clips_count": result.clips_count,
                    "signs_included": result.signs_included,
                    "generation_timestamp": result.generation_timestamp
                },
                "message": f"Vidéo complète créée avec {result.clips_count} clips"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de la création vidéo complète"
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/montage/assets', methods=['GET'])
@handle_api_errors
@require_service('video_generator')
async def api_montage_assets():
    """Informations sur les assets disponibles (vidéos/audio)"""
    try:
        assets_info = VideoService.get_assets_info()
        return jsonify({
            "success": True,
            "assets": assets_info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/montage/cleanup', methods=['POST'])
@handle_api_errors
@require_service('video_generator')
async def api_montage_cleanup():
    """Nettoie les fichiers temporaires de montage"""
    try:
        cleaned_count = VideoService.cleanup_temp_files()
        return jsonify({
            "success": True,
            "files_cleaned": cleaned_count,
            "message": f"{cleaned_count} fichiers temporaires supprimés"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/montage/download/<filename>')
@handle_api_errors
@require_service('video_generator')
async def api_download_montage(filename):
    """Télécharge une vidéo de montage"""
    try:
        # Vérifier que le fichier existe dans le dossier de sortie
        file_path = video_generator.output_dir / filename
        
        if not file_path.exists():
            return jsonify({
                "success": False,
                "error": "Fichier non trouvé"
            }), 404
        
        # Vérifier la sécurité du chemin
        if not str(file_path.resolve()).startswith(str(video_generator.output_dir.resolve())):
            return jsonify({
                "success": False,
                "error": "Accès non autorisé"
            }), 403
        
        return send_from_directory(
            video_generator.output_dir,
            filename,
            as_attachment=True
        )
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =============================================================================
# API ENDPOINTS - WORKFLOWS VIDEO INTÉGRÉS
# =============================================================================

async def _run_complete_sign_workflow(sign, date, format_name, add_music):
    """Logique du workflow complet pour un signe, pour être réutilisée."""
    results = {}
    
    # Étape 1: Générer horoscope avec audio
    if astro_generator:
        print(f"🎯 Étape 1: Génération horoscope + audio pour {sign}")
        horoscope_args = {
            "sign": sign,
            "date": date,
            "generate_audio": True
        }
        results['horoscope'] = await AstroService.call_astro_tool("generate_single_horoscope", horoscope_args)
    else:
        results['horoscope'] = {"success": False, "error": "Astro generator non disponible"}
    
    # Étape 2: Générer vidéo constellation avec ComfyUI
    if SERVICES['comfyui_generator']:
        print(f"🎬 Étape 2: Génération vidéo ComfyUI pour {sign}")
        validated_sign, validated_format = ComfyUIService.validate_sign_and_format(sign, format_name)
        comfyui_result = comfyui_generator.generate_constellation_video(
            sign=validated_sign,
            format_name=validated_format
        )
        if comfyui_result:
            results['comfyui_video'] = {
                "success": True,
                "video_path": comfyui_result.video_path,
                "specs": {
                    "width": comfyui_result.specs.width,
                    "height": comfyui_result.specs.height,
                    "fps": comfyui_result.specs.fps
                }
            }
        else:
            results['comfyui_video'] = {"success": False, "error": "Génération ComfyUI échouée"}
    else:
        results['comfyui_video'] = {"success": False, "error": "ComfyUI non disponible"}
    
    # Étape 3: Créer vidéo synchronisée avec montage
    if SERVICES['video_generator']:
        print(f"🎭 Étape 3: Montage synchronisé pour {sign}")
        montage_result = VideoService.create_synchronized_video(sign, add_music)
        if montage_result:
            results['synchronized_video'] = {
                "success": True,
                "video_path": montage_result.video_path,
                "transcription": {
                    "full_text": montage_result.transcription.full_text,
                    "duration": montage_result.transcription.duration,
                    "word_count": montage_result.transcription.word_count
                },
                "has_music": montage_result.has_music,
                "file_size": montage_result.file_size
            }
        else:
            results['synchronized_video'] = {"success": False, "error": "Montage synchronisé échoué"}
    else:
        results['synchronized_video'] = {"success": False, "error": "Video generator non disponible"}
   # Étape 4: Préparation des métadonnées YouTube
    if SERVICES['youtube_service']:
        print(f"📝 Étape 4: Préparation des métadonnées YouTube pour {sign}")
        theme_for_title = None
        if results.get('horoscope', {}).get('success'):
            horoscope_obj = results['horoscope'].get('result')
            if horoscope_obj:
                theme_for_title = horoscope_obj.get('title_theme')
            
        metadata = youtube_service.uploader.create_astro_metadata(
            sign=sign,
            date=date,
            title_theme=theme_for_title 
        )
        results['youtube_metadata'] = {
            "success": True,
            "title": metadata.title,
            "description": metadata.description
        }
        print(f"✅ Titre YouTube prévu : \"{metadata.title}\"")
          
    return results

@app.route('/api/workflow/complete_sign_generation', methods=['POST'])
@handle_api_errors
async def api_complete_sign_generation():
    """Workflow complet : Horoscope + Audio + Vidéo ComfyUI + Montage synchronisé"""
    data = ValidationHelper.validate_json_request(['sign'])
    sign = data['sign']
    date = data.get('date')
    format_name = data.get('format', 'youtube_short')
    add_music = data.get('add_music', True)
    
    try:
        results = await _run_complete_sign_workflow(sign, date, format_name, add_music)
        
        # Résumé
        successful_steps = sum(1 for r in results.values() if r.get('success', False))
        total_steps = len(results)
        
        return jsonify({
            "success": True,
            "sign": sign,
            "workflow_results": results,
            "summary": {
                "successful_steps": successful_steps,
                "total_steps": total_steps,
                "completion_rate": successful_steps / total_steps if total_steps > 0 else 0,
                "message": f"Workflow terminé: {successful_steps}/{total_steps} étapes réussies"
            },
            "generation_timestamp": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur workflow complet: {str(e)}"
        }), 500

@app.route('/api/workflow/batch_complete_generation', methods=['POST'])
@handle_api_errors
async def api_batch_complete_generation():
    """Workflow complet en lot pour tous les signes"""
    data = ValidationHelper.validate_json_request()
    signs = data.get('signs') or [
        'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
        'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
    ]
    date = data.get('date')
    format_name = data.get('format', 'youtube_short')
    add_music = data.get('add_music', True)
    
    try:
        batch_results = {}
        successful_signs = 0
        
        for sign in signs:
            print(f"🚀 Traitement du signe: {sign}")
            try:
                sign_results = await _run_complete_sign_workflow(sign, date, format_name, add_music)
                successful_steps = sum(1 for r in sign_results.values() if r.get('success', False))
                total_steps = len(sign_results)
                
                batch_results[sign] = {
                    "success": successful_steps == total_steps,
                    "details": sign_results,
                    "summary": {
                        "completion_rate": successful_steps / total_steps if total_steps > 0 else 0,
                    }
                }
                if successful_steps == total_steps:
                    successful_signs += 1
            except Exception as e:
                batch_results[sign] = {"success": False, "error": str(e)}
        
        final_video_result = None
        if SERVICES['video_generator'] and successful_signs > 0:
            print("🎞️ Assemblage final de la vidéo complète")
            try:
                final_video_result = VideoService.create_full_video(signs)
            except Exception as e:
                print(f"⚠️ Échec assemblage final: {e}")
        
        return jsonify({
            "success": True,
            "batch_results": batch_results,
            "final_video": {
                "success": final_video_result is not None,
                "video_path": final_video_result.video_path if final_video_result else None,
                "total_duration": final_video_result.total_duration if final_video_result else 0,
                "clips_count": final_video_result.clips_count if final_video_result else 0
            } if final_video_result else {"success": False, "error": "Assemblage final non disponible"},
            "summary": {
                "total_signs": len(signs),
                "successful_signs": successful_signs,
                "failed_signs": len(signs) - successful_signs,
                "success_rate": successful_signs / len(signs) if signs else 0,
                "message": f"Génération batch terminée: {successful_signs}/{len(signs)} signes traités avec succès"
            },
            "generation_timestamp": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur workflow batch: {str(e)}"
        }), 500
# =============================================================================
# API ENDPOINTS - YOUTUBE
# =============================================================================

@app.route('/api/youtube/status', methods=['GET'])
@handle_api_errors
@require_service('youtube_service')  
async def api_youtube_status():
    """Statut YouTube et vidéos disponibles"""
    try:
        status = youtube_service.get_youtube_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur statut YouTube: {str(e)}"
        }), 500

@app.route('/api/youtube/upload_sign/<sign>', methods=['POST'])
@handle_api_errors
@require_service('youtube_service')
async def api_upload_sign_youtube(sign):
    """Upload vidéo d'un signe sur YouTube"""
    try:
        data = ValidationHelper.validate_json_request()
        privacy = data.get('privacy', 'private')
        
        result = youtube_service.upload_individual_video(sign, privacy)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur upload YouTube: {str(e)}"
        }), 500

@app.route('/api/youtube/upload_batch', methods=['POST'])
@handle_api_errors
@require_service('youtube_service')
async def api_youtube_upload_batch():
    """Upload en lot sur YouTube"""
    try:
        data = ValidationHelper.validate_json_request()
        signs = data.get('signs')
        privacy = data.get('privacy', 'private')
        
        result = youtube_service.upload_batch_videos(signs, privacy)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur batch upload: {str(e)}"
        }), 500

@app.route('/api/youtube/available_videos', methods=['GET'])
@handle_api_errors
@require_service('youtube_service')
async def api_youtube_available_videos():
    """Liste des vidéos disponibles pour upload"""
    try:
        videos = youtube_service.get_available_videos()
        return jsonify({
            "success": True,
            "videos": videos
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur: {str(e)}"
        }), 500


# =============================================================================
# API ENDPOINTS - TIKTOK UPLOAD (NOUVELLE SECTION)
# =============================================================================

@app.route('/api/tiktok/upload_sign/<sign>', methods=['POST'])
@handle_api_errors
@require_service('tiktok_service')
async def api_upload_sign_tiktok(sign):
    """Upload la vidéo d'un signe sur TikTok."""
    try:
        # La logique d'upload est synchrone, nous l'exécutons dans un thread pour ne pas bloquer
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, tiktok_server.upload_sign_video, sign)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur upload TikTok: {str(e)}"
        }), 500

# =============================================================================
# AI SIGN GENERATION
# =============================================================================

@app.route('/api/workflow/intelligent_complete_sign_generation', methods=['POST'])
@handle_api_errors
async def api_intelligent_complete_sign_generation():
    """Version intelligente du workflow complet pour un signe"""
    if ORCHESTRATOR_AVAILABLE:
        # Utiliser l'agent intelligent
        return await api_smart_single_generation()
    else:
        # Fallback vers votre méthode existante
        return await api_complete_sign_generation()

@app.route('/api/workflow/intelligent_batch_complete_generation', methods=['POST'])
@handle_api_errors
async def api_intelligent_batch_complete_generation():
    """Version intelligente du workflow batch"""
    if ORCHESTRATOR_AVAILABLE:
        # Utiliser l'agent intelligent
        return await api_intelligent_batch_generation()
    else:
        # Fallback vers votre méthode existante
        return await api_batch_complete_generation()

# =============================================================================
# FONCTIONS UTILITAIRES DE DÉMARRAGE
# =============================================================================

def print_startup_banner():
    """Affiche la bannière de démarrage"""
    print("=" * 70)
    print("🌟 DÉMARRAGE ASTRO GENERATOR MCP v2.2")
    print("=" * 70)
    print(f"🌐 Interface web: http://127.0.0.1:{settings.PORT}/")
    print(f"🔐 Authentification: {'Activée' if settings.AUTH_ENABLED else 'Désactivée'}")
    print("📁 Structure:")
    print(f"   • Templates: {settings.TEMPLATES_DIR}/")
    print(f"   • Statiques: {settings.STATIC_DIR}/")
    print("")

def check_services_health():
    """Vérifie l'état des services au démarrage"""
    print("🚀 Vérification des services...")
    print("")
    # Vérification Astro Generator
    print("🧠 ORCHESTRATOR:")
    if orchestrator:  # ✅ Utilisez SERVICES
        try:
            status = orchestrator.get_orchestrator_status()
            orchestrator_status = status['success'] and status['status']['ollama_available']
            if orchestrator_status:
                print(f"   ✅ Opérationnel - {len(status['status']['capabilities'])} capacités")
                print(f"   🤖 Workflows traités: {status['status']['total_workflows_processed']}")
            else:
                print(f"   ⚠️  Problème: Ollama requis non disponible")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print("   ❌ Non disponible")

    # Vérification Astro Generator
    print("📊 ASTRO GENERATOR:")
    if astro_generator:
        try:
            today = datetime.date.today()
            context = astro_generator.get_astral_context(today)
            print(f"   ✅ Opérationnel - Phase lunaire: {context.lunar_phase}")
        except Exception as e:
            print(f"   ⚠️  Problème: {e}")
    else:
        print("   ❌ Non disponible")
    
    # Vérification Ollama
    print("🤖 OLLAMA:")
    try:
        result = OllamaClient.make_request("api/tags", timeout=5)
        if result['success']:
            models = result['data'].get('models', [])
            model_count = len(models)
            if model_count > 0:
                print(f"   ✅ Opérationnel - {model_count} modèles disponibles")
                for model in models[:3]:
                    print(f"      • {model.get('name', 'unknown')}")
                if model_count > 3:
                    print(f"      ... et {model_count - 3} autres")
            else:
                print("   ⚠️  Aucun modèle installé")
        else:
            raise Exception(result['error'])
    except Exception as e:
        print(f"   ❌ Problème: {e}")
        print("   💡 Vérifiez qu'Ollama est démarré: ollama serve")
    
    # Vérification ComfyUI
    print("🎬 COMFYUI:")
    if comfyui_generator:
        try:
            connected = comfyui_generator.test_connection()
            if connected:
                formats_count = len(comfyui_generator.video_formats)
                signs_count = len(comfyui_generator.sign_metadata)
                print(f"   ✅ Opérationnel - {formats_count} formats, {signs_count} signes")
                print(f"   🖥️  Serveur: {comfyui_generator.server_address}")
            else:
                print("   ⚠️  Serveur non connecté")
        except Exception as e:
            print(f"   ❌ Problème: {e}")
    else:
        print("   ❌ Non disponible")
    
    # Vérification Video Generator
    print("🎭 VIDEO GENERATOR (MONTAGE):")
    if video_generator:
        try:
            status = video_generator.get_system_status()
            whisper_ok = status['whisper_available']
            ffmpeg_ok = status['ffmpeg_available']
            music_ok = status['music_available']
            
            if whisper_ok and ffmpeg_ok:
                print(f"   ✅ Opérationnel - Whisper: ✅, ffmpeg: ✅, Musique: {'✅' if music_ok else '❌'}")
                print(f"   📁 Dossier sortie: {status['directories']['output']}")
                print(f"   🎯 {status['signs_count']} signes supportés")
            else:
                print(f"   ⚠️  Dépendances manquantes - Whisper: {'✅' if whisper_ok else '❌'}, ffmpeg: {'✅' if ffmpeg_ok else '❌'}")
        except Exception as e:
            print(f"   ❌ Problème: {e}")
    else:
        print("   ❌ Non disponible")
    
    # Vérification YouTube MCP
    print("📤 YOUTUBE MCP:")
    if youtube_service:
        try:
            status = youtube_service.get_youtube_status()
            if status['success'] and status['youtube_connected']:
                channel_info = status['channel_info']
                print(f"   ✅ Connecté - Chaîne: {channel_info.get('title', 'N/A')}")
                print(f"   👥 Abonnés: {channel_info.get('subscribers', '0')}")
                print(f"   📊 Vidéos prêtes à l'upload: {status['available_videos']['total_available']}")
                print(f"   🆔 Channel ID: {channel_info.get('channel_id', 'N/A')[:15]}...")
            else:
                print(f"   ⚠️  Connexion YouTube échouée: {status.get('error', 'Erreur inconnue')}")
        except Exception as e:
            print(f"   ❌ Problème: {e}")
    else:
        print("   ❌ Non disponible")
    
    print("")

def print_service_summary():
    """Affiche le résumé des services"""
    services_status = []
    
    if astro_generator:
        services_status.append("✅ Horoscopes")
    else:
        services_status.append("❌ Horoscopes")
    
    # Test Ollama rapide
    try:
        result = OllamaClient.make_request("api/tags", timeout=2)
        if result['success']:
            services_status.append("✅ Chat IA")
        else:
            services_status.append("❌ Chat IA")
    except:
        services_status.append("❌ Chat IA")
    
    if comfyui_generator:
        try:
            if comfyui_generator.test_connection():
                services_status.append("✅ Vidéos ComfyUI")
            else:
                services_status.append("⚠️  Vidéos ComfyUI")
        except:
            services_status.append("❌ Vidéos ComfyUI")
    else:
        services_status.append("❌ Vidéos ComfyUI")
    
    # Statut du générateur vidéo
    if video_generator:
        try:
            status = video_generator.get_system_status()
            if status['whisper_available'] and status['ffmpeg_available']:
                services_status.append("✅ Montage Vidéo")
            else:
                services_status.append("⚠️  Montage Vidéo")
        except:
            services_status.append("❌ Montage Vidéo")
    else:
        services_status.append("❌ Montage Vidéo")
    
    # Statut YouTube MCP
    if youtube_service:
        try:
            status = youtube_service.get_youtube_status()
            if status['success'] and status['youtube_connected']:
                services_status.append("✅ YouTube Upload")
            else:
                # Affiche l'erreur renvoyée par le service si la connexion a échoué
                error_msg = status.get('error', 'Erreur inconnue')
                services_status.append(f"⚠️  YouTube Upload ({error_msg})")
        except Exception as e:
            # Affiche l'erreur exacte si une exception se produit
            services_status.append(f"❌ YouTube Upload (Exception: {e})")

    print("📋 SERVICES DISPONIBLES:")
    for status in services_status:
        print(f"   {status}")
    
    # Conseils selon l'état
    if "❌" in " ".join(services_status):
        print("")
        print("💡 CONSEILS:")
        if "❌ Horoscopes" in services_status:
            print("   • Vérifiez astro_server_mcp.py")
        if "❌ Chat IA" in services_status:
            print("   • Démarrez Ollama: ollama serve")
        if "❌ Vidéos ComfyUI" in services_status:
            print("   • Vérifiez ComfyUI sur port 8188")
        if "❌ Montage Vidéo" in services_status:
            print("   • pip install openai-whisper")
            print("   • Installez ffmpeg")
        if "❌ YouTube Upload" in services_status:
            print("   • Vérifiez le dossier youtube/")
            print("   • Vérifiez credentials YouTube API")

def print_api_endpoints():
    """Affiche la liste des endpoints API disponibles"""
    print("")
    print("🔌 ENDPOINTS API:")
    
    endpoints = [
        ("GET", "/health", "État du système"),
        
        ("POST", "/api/generate_single_horoscope", "Horoscope individuel"),
        ("POST", "/api/generate_daily_horoscopes", "Horoscopes quotidiens"),
        ("POST", "/api/get_astral_context", "Contexte astral"),

        ("GET", "/api/ollama/models", "Modèles Ollama"),
        ("POST", "/api/ollama/chat", "Chat IA"),

        ("GET", "/api/comfyui/status", "État ComfyUI"),
        ("POST", "/api/comfyui/generate_video", "Génération vidéo"),
        ("POST", "/api/comfyui/generate_batch", "Génération batch"),

        ("GET", "/api/montage/status", "État montage vidéo"),
        ("POST", "/api/montage/create_single_video", "Vidéo synchronisée"),
        ("POST", "/api/montage/create_full_video", "Vidéo complète"),
        ("POST", "/api/workflow/complete_sign_generation", "Workflow complet"),
        ("POST", "/api/workflow/batch_complete_generation", "Workflow batch"),

        ("GET", "/api/youtube/status", "Statut YouTube"),
        ("POST", "/api/youtube/upload_sign/<sign>", "Upload signe YouTube"),
        ("POST", "/api/youtube/upload_batch", "Upload batch YouTube"),
        ("GET", "/api/youtube/available_videos", "Vidéos disponibles")
    ]
    
    for method, endpoint, description in endpoints:
        print(f"   {method:4} {endpoint:45} - {description}")

# =============================================================================
# GESTIONNAIRES D'ERREURS GLOBAUX
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    """Gestionnaire 404 personnalisé"""
    return jsonify({
        "success": False,
        "error": "Endpoint non trouvé",
        "suggestion": "Vérifiez l'URL et la méthode HTTP"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Gestionnaire 405 personnalisé"""
    return jsonify({
        "success": False,
        "error": "Méthode HTTP non autorisée",
        "suggestion": f"Méthodes autorisées: {', '.join(error.valid_methods)}"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire 500 personnalisé"""
    return jsonify({
        "success": False,
        "error": "Erreur interne du serveur",
        "suggestion": "Consultez les logs pour plus de détails"
    }), 500

@app.errorhandler(503)
def service_unavailable(error):
    """Gestionnaire 503 personnalisé"""
    return jsonify({
        "success": False,
        "error": "Service temporairement indisponible",
        "suggestion": "Vérifiez l'état des services avec /health"
    }), 503

# =============================================================================
# MIDDLEWARE ET HOOKS
# =============================================================================

@app.before_request
def before_request():
    """Hook exécuté avant chaque requête"""
    # Log des requêtes API uniquement
    if request.path.startswith('/api/'):
        print(f"🔄 {request.method} {request.path} - {request.remote_addr}")

@app.after_request
def after_request(response):
    """Hook exécuté après chaque requête"""
    # Headers de sécurité
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # CORS pour développement (à désactiver en production)
    if settings.DEBUG:
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response

# =============================================================================
# COMMANDES CLI (pour administration)
# =============================================================================

def cli_test_services():
    """Commande CLI pour tester tous les services"""
    print("🧪 Test des services en mode CLI...")
    
    # Test santé
    try:
        with app.test_client() as client:
            response = client.get('/health')
            data = response.get_json()
            
            print(f"Status: {data['status']}")
            for service, info in data['services'].items():
                status = "✅" if info['status'] else "❌"
                print(f"{service}: {status}")
                
    except Exception as e:
        print(f"❌ Erreur test: {e}")

def cli_show_settings():
    """Affiche la configuration actuelle"""
    print("⚙️  CONFIGURATION ACTUELLE:")
    print(f"   Host: {settings.HOST}")
    print(f"   Port: {settings.PORT}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Auth: {settings.AUTH_ENABLED}")
    print(f"   Ollama: {settings.OLLAMA_BASE_URL}")
    print(f"   Templates: {settings.TEMPLATE_DIR}")
    print(f"   Static: {settings.STATIC_FOLDER}")

# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================

def main():
    """Fonction principale de démarrage"""
    # Affichage startup
    print_startup_banner()
    check_services_health()
    print_service_summary()
    
    if settings.DEBUG:
        print_api_endpoints()
    
    print("")
    print("=" * 70)
    print("🚀 SERVEUR FLASK DÉMARRÉ AVEC MONTAGE VIDÉO")
    print("=" * 70)
    
    # Arguments CLI
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            cli_test_services()
            return
        elif command == "config":
            cli_show_config()
            return
        elif command == "help":
            print("Commandes disponibles:")
            print("  python app.py test    - Teste tous les services")
            print("  python app.py config  - Affiche la configuration")
            print("  python app.py help    - Affiche cette aide")
            return
    
    # Démarrage du serveur Flask
    try:
        app.run(
            host=settings.HOST,
            port=settings.PORT,
            debug=settings.DEBUG,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n👋 Arrêt du serveur Flask")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

# =============================================================================
# DOCUMENTATION API
# =============================================================================

"""
ENDPOINTS DISPONIBLES:

🏠 ROUTES PRINCIPALES:
GET  /                              - Interface web principale
GET  /static/<filename>             - Fichiers statiques
GET  /health                        - État du système

🤖 AI ORCHESTRATOR:
POST /api/agent/intelligent_batch                 - Batch intelligent IA
POST /api/agent/smart_single_generation           - Génération IA adaptative
GET  /api/agent/status                            - État agent orchestrateur

📊 HOROSCOPES:
POST /api/generate_single_horoscope          - Horoscope individuel
POST /api/generate_single_horoscope_with_audio - Horoscope + audio
POST /api/generate_daily_horoscopes          - Tous les horoscopes du jour
POST /api/get_astral_context                 - Contexte astral
POST /api/calculate_lunar_influence          - Influence lunaire
POST /api/get_sign_metadata                  - Métadonnées signe

🤖 CHAT IA:
GET  /api/ollama/models             - Liste des modèles Ollama
POST /api/ollama/chat               - Chat avec IA astrologique

🎬 VIDÉOS COMFYUI:
GET  /api/comfyui/status            - État ComfyUI
GET  /api/comfyui/formats           - Formats vidéo disponibles
POST /api/comfyui/generate_video    - Génération vidéo constellation
POST /api/comfyui/generate_batch    - Génération batch
POST /api/comfyui/preview_prompt    - Prévisualisation prompt
GET  /api/comfyui/download_video/<path> - Téléchargement vidéo

🎭 MONTAGE VIDÉO:
GET  /api/montage/status            - État du système de montage
POST /api/montage/create_single_video - Vidéo synchronisée (1 signe)
POST /api/montage/create_full_video - Vidéo complète (tous signes)
GET  /api/montage/assets            - Informations sur les assets
POST /api/montage/cleanup           - Nettoyage fichiers temporaires
GET  /api/montage/download/<filename> - Téléchargement vidéo montée

🚀 WORKFLOWS INTÉGRÉS:
POST /api/workflow/complete_sign_generation - Workflow complet (1 signe)
     • Horoscope + Audio + Vidéo ComfyUI + Montage synchronisé
POST /api/workflow/batch_complete_generation - Workflow batch (tous signes)
     • Pipeline complet pour tous les signes + assemblage final

AUTHENTIFICATION:
- Désactivée par défaut (settings.AUTH_ENABLED = False)
- Activable via configuration pour production

FORMATS DE DONNÉES:
- Toutes les réponses en JSON
- Structure standard: {"success": bool, "result|error": data}
- Codes HTTP appropriés (200, 400, 500, 503)

GESTION D'ERREURS:
- Validation centralisée des données
- Messages d'erreur explicites
- Fallbacks automatiques (Ollama)
- Monitoring avec /health

NOUVEAUTÉS v2.1:
✅ Intégration complète du montage vidéo
✅ Workflows automatisés bout-en-bout
✅ Service VideoService pour abstraction
✅ Endpoints dédiés au montage
✅ Pipeline complet : Horoscope → Audio → Vidéo → Montage
✅ Génération batch optimisée
✅ Gestion des assets et nettoyage
✅ Interface unifiée pour tous les générateurs

ARCHITECTURE:
Flask App → Services (Astro, ComfyUI, Video) → Générateurs MCP
         ↓
    Import direct des modules (pas de réseau)
         ↓  
    Méthodes natives Python (pas d'API calls)

DÉPENDANCES:
- astro_server_mcp.py (obligatoire)
- video_server_mcp.py (optionel)
- comfyui_server_mcp.py (optionnel)
- Ollama (optionnel)
- Whisper (optionnel, pour transcription)
- ffmpeg (obligatoire pour montage)
"""
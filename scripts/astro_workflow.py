#!/usr/bin/env python3
"""
AstroGen Workflow Complet - Pipeline automatisé CORRIGÉ
Génération complète : AstroChart → Horoscopes → Vidéos → Upload
"""

import asyncio
import datetime
import sys
import os
from pathlib import Path
import subprocess
import time
import requests
from typing import Optional
import argparse

# python -m scripts.astro_workflow
def setup_imports():
    """Configure les chemins d'import et importe les modules"""
    print("🔧 Configuration des imports...")
    
    services = {}
    
    try:
        from astro_core.services.astro_mcp import astro_generator
        services['astro'] = astro_generator
        print("✅ Astro Generator importé")
    except ImportError as e:
        print(f"❌ Astro Generator: {e}")
        sys.exit(1)
    
    try:
        from astro_core.services.comfyui_mcp import comfyui_generator
        services['comfyui'] = comfyui_generator
        print("✅ ComfyUI Generator importé")
    except ImportError as e:
        print(f"❌ ComfyUI Generator: {e}")
        sys.exit(1)
    
    try:
        from astro_core.services.video_mcp import video_generator
        services['video'] = video_generator
        print("✅ Video Generator importé")
    except ImportError as e:
        print(f"❌ Video Generator: {e}")
        sys.exit(1)
    
    try:
        from astro_core.services.youtube.youtube_mcp import youtube_server
        services['youtube'] = youtube_server
        print("✅ YouTube Server importé")
    except ImportError as e:
        print(f"❌ YouTube Server: {e}")
        sys.exit(1)
    
    try:
        from astro_core.services.astrochart.astrochart_mcp import astro_calculator
        services['astrochart'] = astro_calculator
        print("✅ AstroChart Calculator importé")
    except ImportError as e:
        print(f"❌ AstroChart Calculator: {e}")
        sys.exit(1)
    
    return services

def auto_start_services():
    """Démarre automatiquement les services externes"""

    print("🚀 Démarrage automatique des services...")
    
    # 1. Vérifier/Démarrer Ollama
    print("🤖 Vérification Ollama...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        print("✅ Ollama déjà démarré")
    except:
        print("🔄 Démarrage Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        print("✅ Ollama démarré")
    
    # 2. Vérifier/Démarrer ComfyUI
    print("🎬 Vérification ComfyUI...")
    try:
        response = requests.get("http://localhost:8188/system_stats", timeout=3)
        print("✅ ComfyUI déjà démarré")
    except:
        print("🔄 Recherche de ComfyUI...")
        comfyui_paths = [
            os.path.expanduser("~/ComfyUI"),
            "/opt/ComfyUI",
            "./ComfyUI",
            "../ComfyUI"
        ]
        
        comfyui_found = False
        for path in comfyui_paths:
            if os.path.exists(os.path.join(path, "main.py")):
                print(f"🔄 Démarrage ComfyUI depuis {path}...")
                subprocess.Popen(
                    ["python", "main.py"], 
                    cwd=path,
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                time.sleep(5)
                comfyui_found = True
                print("✅ ComfyUI démarré")
                break
        
        if not comfyui_found:
            print("❌ ComfyUI non trouvé. Chemins testés:")
            for path in comfyui_paths:
                print(f"  - {path}")
            print("💡 Installez ComfyUI ou ajustez le chemin")

def check_services_availability(services):
    """Vérifie que tous les services sont opérationnels"""
    print("🔍 Vérification des services...")
    
    # Test Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        print(f"🤖 Ollama: {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"❌ Ollama: {e}")
    
    # Test ComfyUI
    try:
        connected = services['comfyui'].test_connection()
        print(f"🎬 ComfyUI: {'✅' if connected else '❌'}")
    except Exception as e:
        print(f"❌ ComfyUI: {e}")
    
    # Test YouTube Auth
    try:
        status = services['youtube'].get_youtube_status()
        youtube_ok = status['success'] and status['youtube_connected']
        print(f"📤 YouTube: {'✅' if youtube_ok else '❌'}")
        if not youtube_ok:
            print("💡 Configurez YouTube API credentials")
    except Exception as e:
        print(f"❌ YouTube: {e}")
    
    # Test Video Generator
    try:
        status = services['video'].get_system_status()
        video_ok = status['whisper_available'] and status['ffmpeg_available']
        print(f"🎭 Video Generator: {'✅' if video_ok else '❌'}")
        if not video_ok:
            print("💡 Installez: pip install openai-whisper + ffmpeg")
    except Exception as e:
        print(f"❌ Video Generator: {e}")

def step1_generate_astrochart(services, date):
    """Génère les positions planétaires pour la date"""
    print("🌟 ÉTAPE 1: Génération AstroChart...")
    
    astro_calculator = services['astrochart']
    
    chart_data = astro_calculator.generate_chart_data(date)
    positions = astro_calculator.calculate_positions(date)
    aspects = astro_calculator.calculate_aspects(positions)
    
    return {
        "chart_data": chart_data,
        "positions": positions,
        "aspects": aspects,
        "lunar_phase": chart_data.moon_phase
    }

async def step2_generate_horoscopes(services, astrochart_data, signs, date):
    """Génère horoscopes + audio pour tous les signes"""
    print("📝 ÉTAPE 2: Génération Horoscopes + Audio...")
    
    astro_generator = services['astro']
    results = {}
    
    for sign in signs:
        print(f"  ⭐ Génération {sign}...")
        
        # Générer horoscope avec audio
        horoscope_result, audio_path, audio_duration = await astro_generator.generate_single_horoscope(
            sign, 
            date, 
            generate_audio=True
        )
        
        results[sign] = {
            "horoscope": horoscope_result,
            "audio_path": audio_path,
            "audio_duration": audio_duration
        }
    
    return results

def step3_generate_videos(services, signs, format_name="youtube_short"):
    """Génère les vidéos de constellations"""
    print("🎬 ÉTAPE 3: Génération Vidéos ComfyUI...")
    
    comfyui_generator = services['comfyui']
    video_results = {}
    
    for sign in signs:
        print(f"  🎯 Vidéo {sign}...")
        
        result = comfyui_generator.generate_constellation_video(
            sign=sign,
            format_name=format_name
        )
        
        video_results[sign] = result
    
    return video_results

def step4_create_montage(services, signs):
    """Crée les montages synchronisés pour chaque signe"""
    print("🎭 ÉTAPE 4: Montage Synchronisé...")
    
    video_generator = services['video']
    montage_results = {}
    
    for sign in signs:
        print(f"  🎵 Montage {sign}...")
        
        result = video_generator.create_synchronized_video_for_sign(
            sign, 
            add_music=True
        )
        
        montage_results[sign] = result
    
    return montage_results

def step5_create_complete_video(services, signs):
    """Assemble la vidéo horoscope complète"""
    print("🎞️ ÉTAPE 5: Assemblage Vidéo Complète...")
    
    video_generator = services['video']
    complete_video = video_generator.create_full_horoscope_video(signs)
    return complete_video

def step6_upload_youtube(services, signs, date, horoscopes, astrochart_data, 
                         upload_batch=True, upload_complete=True, privacy="public"):
    """Upload sur YouTube en fonction des flags."""
    print("📤 ÉTAPE 6: Upload YouTube...")
    youtube_server = services['youtube']
    date_str = date.strftime('%Y-%m-%d')

    if upload_batch:
        print("   📺 Upload batch des signes...")
        youtube_server.upload_batch_videos(
            signs=signs,
            privacy=privacy,
            horoscopes_data=horoscopes,
            date=date_str
        )
    
    if upload_complete:
        print("   🎬 Upload vidéo complète...")
        astral_context = {"lunar_phase": astrochart_data["chart_data"].moon_phase}
        youtube_server.upload_complete_horoscope(
            privacy=privacy, 
            date=date_str,
            astral_context=astral_context
        )

async def run_complete_workflow(services, target_date, mode='full', sign=None, no_upload=False):
    """Workflow complet et modulable selon le mode choisi."""
    print(f"🚀 DÉMARRAGE WORKFLOW (Mode: {mode})")
    print("=" * 50)
    
    all_signs = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                 'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces']
    
    if mode == 'single_sign':
        signs = [sign]
        upload_batch = not no_upload
        upload_complete = False
    elif mode == 'all_signs':
        signs = all_signs
        upload_batch = not no_upload
        upload_complete = False
    elif mode == 'complete_only':
        signs = all_signs
        upload_batch = False
        upload_complete = not no_upload
    else: # mode 'full'
        signs = all_signs
        upload_batch = not no_upload
        upload_complete = not no_upload

    try:
        astrochart = step1_generate_astrochart(services, target_date)
        horoscopes = await step2_generate_horoscopes(services, astrochart, signs, target_date)
        videos = step3_generate_videos(services, signs)
        montages = step4_create_montage(services, signs)   

        if mode in ['full', 'complete_only']:
            step5_create_complete_video(services, signs)
            
        if not no_upload:
            step6_upload_youtube(services, signs, target_date, horoscopes, astrochart, 
                                 upload_batch=upload_batch, upload_complete=upload_complete)
        else:
            print("📤 ÉTAPE 6: Upload YouTube ignoré.")
            
        print("\n✅ WORKFLOW TERMINÉ !")
        
    except Exception as e:
        print(f"❌ ERREUR WORKFLOW: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Point d'entrée avec vérifications"""
    print("🔧 INITIALISATION ASTROGEN WORKFLOW")
    print("=" * 40)
    
    parser = argparse.ArgumentParser(description="Lance le workflow complet ou partiel d'AstroGen.")
    
    # --- Groupe pour la sélection de la date ---
    date_group = parser.add_argument_group('Options de date')
    date_group.add_argument("--date", help="Date de génération (YYYY-MM-DD). Défaut: aujourd'hui.")
    date_group.add_argument("--demain", action="store_true", help="Raccourci pour générer pour demain.")
    # --- Groupe pour le mode d'exécution ---
    mode_group = parser.add_argument_group('Modes d\'exécution')
    mode_group.add_argument("--signe", help="Génère et upload UNIQUEMENT pour un seul signe (ex: aries).")
    mode_group.add_argument("--tous-les-signes", action="store_true", help="Génère et upload les 12 vidéos individuelles (sans la vidéo complète).")
    mode_group.add_argument("--video-complete", action="store_true", help="Génère tout, mais upload UNIQUEMENT la vidéo complète.")
    # --- Option pour désactiver l'upload ---
    parser.add_argument("--no-upload", action="store_true", help="Génère tous les fichiers sans rien uploader sur YouTube.")

    args = parser.parse_args()

    # Déterminer la date cible en fonction des arguments
    target_date = datetime.date.today()
    if args.demain:
        target_date = datetime.date.today() + datetime.timedelta(days=1)
        print(f"🎯 Cible : Demain ({target_date.strftime('%Y-%m-%d')})")
    elif args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, '%Y-%m-%d').date()
            print(f"🎯 Cible : Date spécifiée ({target_date.strftime('%Y-%m-%d')})")
        except ValueError:
            print(f"❌ Format de date invalide : '{args.date}'. Utilisez YYYY-MM-DD.")
            sys.exit(1)
    else:
        print(f"🎯 Cible : Aujourd'hui ({target_date.strftime('%Y-%m-%d')})")

    mode = 'full'
    signe_specifique = None
    if args.signe:
        mode = 'single_sign'
        signe_specifique = args.signe.lower()
        print(f"🚀 Mode : Signe unique ({signe_specifique})")
    elif args.tous_les_signes:
        mode = 'all_signs'
        print("🚀 Mode : Tous les signes (vidéos individuelles)")
    elif args.video_complete:
        mode = 'complete_only'
        print("🚀 Mode : Vidéo complète uniquement")
    else:
        print("🚀 Mode : Workflow complet (par défaut)")

    if args.no_upload:
        print("🚫 Upload sur YouTube désactivé.")

    # Option auto-start des services
    auto_start = input("🤖 Démarrer automatiquement Ollama et ComfyUI ? (y/N): ")
    if auto_start.lower() == 'y':
        auto_start_services()
    
    # Setup imports avec chemins corrects
    services = setup_imports()
    
    # Vérifications des services
    check_services_availability(services)
    
    # Demander confirmation
    print("\n" + "="*40)
    response = input("✅ Continuer le workflow ? (y/N): ")
    if response.lower() != 'y':
        print("❌ Workflow annulé par l'utilisateur")
        sys.exit(0)
    
    # Lancement du workflow async
    print("\n🚀 LANCEMENT DU WORKFLOW...")
    asyncio.run(run_complete_workflow(
        services=services,
        target_date=target_date,
        mode=mode,
        sign=signe_specifique,
        no_upload=args.no_upload)
    )

if __name__ == "__main__":
    main()
import asyncio
import datetime
import sys
import os
from pathlib import Path

# Permet au script de trouver vos modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_server_mcp import VideoGenerator

# --- CONFIGURATION DES ASSETS ---
# Modifiez ces chemins si vos dossiers sont différents
AUDIO_DIR = "generated_audio"
VIDEO_DIR = "generated_videos"
CHART_DIR = "static/charts"
# --------------------------------

async def find_latest_file(directory: str, pattern: str) -> str:
    """Trouve le fichier le plus récent correspondant à un pattern."""
    path = Path(directory)
    files = list(path.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Aucun fichier trouvé pour le pattern '{pattern}' dans '{directory}'")
    return str(max(files, key=os.path.getctime))

async def run_assembly_test():
    """
    Lance le test d'assemblage de la vidéo Hub.
    """
    print("🚀 Démarrage du test d'assemblage de la vidéo Hub...")
    
    video_gen = VideoGenerator()

    try:
        # --- ÉTAPES PRÉLIMINAIRES (RAPIDES) ---
        print("\n1. Localisation des assets pré-générés...")

        # 1. Trouver le fichier audio du Hub
        hub_audio_path = await find_latest_file(AUDIO_DIR, "hub_weekly_*.mp3")
        print(f"   🔊 Audio trouvé : {hub_audio_path}")

        # 2. Transcrire l'audio pour obtenir les timestamps (c'est rapide)
        print("   🎤 Transcription de l'audio avec Whisper...")
        transcription_data = video_gen._transcribe_audio_with_whisper(hub_audio_path)
        if not transcription_data:
            raise Exception("La transcription a échoué. Assurez-vous que Whisper est installé.")
        print(f"   ✅ Transcription terminée ({transcription_data.word_count} mots).")

        # 3. Construire le dictionnaire d'assets visuels
        print("   🖼️  Construction de la liste des assets visuels...")
        visual_assets = {}
        for sign in video_gen.signs_order:
            visual_assets[sign] = await find_latest_file(VIDEO_DIR, f"{sign}_*.mp4")
        
        visual_assets['astro_chart'] = await find_latest_file(CHART_DIR, "astro_chart_*.png")
        print(f"   ✅ {len(visual_assets)} assets visuels localisés.")

        # --- APPEL DE LA FONCTION À TESTER ---
        print("\n2. Lancement de la fonction d'assemblage `create_hub_video`...")
        final_result = await video_gen.create_hub_video(
            audio_path=hub_audio_path,
            transcription_data=transcription_data,
            visual_assets=visual_assets
        )
        
        # --- RÉSULTATS ---
        if final_result:
            print("\n✅ Test d'assemblage terminé avec succès !")
            print("-" * 50)
            print(f"🎥 Vidéo Hub finale créée : {final_result.video_path}")
            print(f"   Durée : {final_result.total_duration:.2f} secondes")
            print(f"   Taille : {final_result.file_size / (1024*1024):.2f} MB")
        else:
            print("\n❌ L'assemblage de la vidéo a échoué. Vérifiez les logs ci-dessus.")

    except FileNotFoundError as e:
        print(f"\n❌ ERREUR : Un fichier nécessaire est manquant.")
        print(f"   {e}")
        print("   Veuillez exécuter les scripts de génération (comfyui, hub_weekly) au moins une fois.")
    except Exception as e:
        print(f"\n❌ Le test a échoué : {e}")

if __name__ == "__main__":
    asyncio.run(run_assembly_test())
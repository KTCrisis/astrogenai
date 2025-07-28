import asyncio
import datetime
import sys
import os

#launch with python -m scripts.weekly_hub
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

async def run_test(services):
    """
    Fonction principale pour lancer le test de génération hebdomadaire.
    """
    print("🚀 Démarrage du test de génération du Hub hebdomadaire...")
    
    # Instancier votre générateur
    astro_generator = services['astro']
    
    # Définir la période de test (par exemple, la semaine actuelle)
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    print(f"🗓️  Période analysée : du {start_of_week} au {end_of_week}")
    print("-" * 50)
    
    try:
        # Appeler directement la fonction
        script_text, audio_path, audio_duration = await astro_generator.generate_weekly_summary(
            start_date=start_of_week, 
            end_date=end_of_week
        )
        
        print("\n✅ Test terminé avec succès !")
        print("-" * 50)
        
        # Afficher les résultats
        print("\n📝 === Début du Script Généré (Extrait) ===")
        #print(script_text[:800] + "...")
        print(script_text)
        print("=== Fin du Script Généré ===\n")
        
        print(f"🔊 Fichier audio généré : {audio_path}")
        print(f"⏳ Durée de l'audio : {audio_duration:.2f} secondes")
        
    except Exception as e:
        print(f"\n❌ Le test a échoué : {e}")

if __name__ == "__main__":
    services = setup_imports()
    asyncio.run(run_test(services=services))
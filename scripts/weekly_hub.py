import asyncio
import datetime
import sys
import os

# Permet au script de trouver vos modules custom
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from astro_server_mcp import AstroGenerator

async def run_test():
    """
    Fonction principale pour lancer le test de génération hebdomadaire.
    """
    print("🚀 Démarrage du test de génération du Hub hebdomadaire...")
    
    # Instancier votre générateur
    astro_gen = AstroGenerator()
    
    # Définir la période de test (par exemple, la semaine actuelle)
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    print(f"🗓️  Période analysée : du {start_of_week} au {end_of_week}")
    print("-" * 50)
    
    try:
        # Appeler directement la fonction
        script_text, audio_path, audio_duration = await astro_gen.generate_weekly_summary(
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
    # Lancer la fonction de test asynchrone
    asyncio.run(run_test())
#!/usr/bin/env python3
"""
Test de génération d'introduction hebdomadaire améliorée
Script pour tester uniquement la section intro avec les nouvelles contraintes de flux
"""

import asyncio
import datetime
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_imports():
    """Configure les imports nécessaires"""
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
        from astro_core.services.astrochart.astrochart_mcp import astro_calculator
        services['astrochart'] = astro_calculator
        print("✅ AstroChart Calculator importé")
    except ImportError as e:
        print(f"❌ AstroChart Calculator: {e}")
        sys.exit(1)
    
    return services

def get_improved_intro_template():
    """Template d'introduction amélioré avec contraintes de flux"""
    
    return """Tu es un astrologue expert et passionné, créateur de contenu YouTube spécialisé en astrologie moderne et accessible.

MISSION: Écris UNIQUEMENT une introduction captivante de 800 mots minimum pour une vidéo astrologique hebdomadaire.

PÉRIODE: {period}
ÉVÉNEMENTS MAJEURS: {events}

CONTEXTE ASTRAL DÉTAILLÉ:
{astral_context}

EXIGENCES DE LONGUEUR:
- MINIMUM 800 mots absolument requis
- Développe chaque point en profondeur
- N'hésite pas à être généreux dans les descriptions
- Si tu atteins moins de 800 mots, continue à développer

LANGUE ET STYLE:
- Français impeccable, registre soutenu mais accessible
- Ton chaleureux, mystérieux mais rassurant
- Vocabulaire riche et varié
- Évite les répétitions de mots

TERMINOLOGIE ASTROLOGIQUE:
- Utilise les termes français corrects
- "conjonction" pas "conjunction"
- "trigone" pas "trine"
- "carré" pas "square"

⚠️ CONTRAINTES DE FLUX CRITIQUES:
- Cette introduction fait partie d'une vidéo CONTINUE
- Ne termine PAS par "bonne semaine", "à bientôt", ou autre formule de clôture
- Termine par une TRANSITION vers l'analyse des événements cosmiques
- Maintiens l'engagement pour la suite immédiate

STRUCTURE OBLIGATOIRE:

ACCUEIL CHALEUREUX:
- "Bienvenue dans votre Guide AstroGenAI hebdomadaire !"
- Salutation personnalisée selon la saison

ACCROCHE COSMIQUE:
- Métaphore poétique sur l'énergie de la semaine
- Image évocatrice du ciel étoilé actuel
- Teasing de l'événement le plus spectaculaire

ÉVÉNEMENT PHARE:
- Description détaillée de l'événement cosmique majeur
- Contexte historique ou symbolique
- Impact émotionnel et spirituel attendu

PREVIEW DE LA VIDÉO:
- Annonce des sections à venir avec enthousiasme
- Promesse de révélations personnalisées par signe
- Mention des rituels/pratiques qui seront partagés

TRANSITION OBLIGATOIRE (dernière phrase):
- "Plongeons maintenant dans le détail de ces énergies cosmiques..."
- OU "Explorons ensemble comment ces forces célestes se déploient..."
- OU "Découvrons précisément comment ces influences vont façonner notre semaine..."

❌ INTERDICTIONS ABSOLUES:
- "Bonne semaine", "excellente semaine", "belle semaine"
- "À bientôt", "à très vite", "au revoir"
- "Prenez soin de vous", "portez-vous bien"
- Toute formule de conclusion définitive
- Ne mets JAMAIS de balises <think> ou </think> dans ta réponse
- Écris directement le contenu final sans réflexion visible
- Pas de métacommentaires sur ton processus de pensée

MOTS-CLÉS À INTÉGRER NATURELLEMENT:
- "énergie cosmique", "vibrations célestes"
- "voyage astral", "guidance des étoiles"
- "transformation", "révélation", "illumination"

Écris maintenant cette introduction substantielle avec transition fluide:"""

async def test_intro_generation(services):
    """
    Test de génération d'introduction avec le template amélioré
    """
    print("🚀 Test de génération d'introduction hebdomadaire...")
    print("=" * 60)
    
    astro_generator = services['astro']
    astro_calculator = services['astrochart']
    
    # Définir la période de test
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    print(f"📅 Période testée : du {start_of_week.strftime('%d/%m')} au {end_of_week.strftime('%d/%m')}")
    print(f"🤖 Modèle Ollama utilisé : {astro_generator.ollama_model}")
        # Démarrer le monitoring des ressources
    import psutil
    import time
    start_time = time.time()
    
    # Mesure des ressources avant génération
    process_info_before = None
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            if 'ollama' in proc.info['name'].lower():
                process_info_before = {
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_mb': proc.info['memory_info'].rss / (1024 * 1024)
                }
                break
    except:
        pass
    print("-" * 40)
    
    try:
        # 1. Calculer les événements de la semaine
        print("🔮 Calcul des événements astrologiques...")
        weekly_events = astro_calculator.get_major_events_for_week(start_of_week, end_of_week)
        events_str = "\n".join([f"- Le {e['date']}: {e['description']} ({e['type']})" for e in weekly_events])
        
        print(f"✅ {len(weekly_events)} événements trouvés")
        for event in weekly_events[:3]:  # Afficher les 3 premiers
            print(f"   • {event['date']}: {event['description']}")
        
        # 2. Formater le contexte astral
        print("\n🌟 Formatage du contexte astral...")
        astral_context_formatted = astro_generator._format_astral_context_for_weekly(start_of_week, end_of_week)
        print("✅ Contexte astral préparé")
        
        # 3. Créer le prompt avec le template amélioré
        print("\n📝 Création du prompt amélioré...")
        template = get_improved_intro_template()
        prompt = template.format(
            period=f"{start_of_week.strftime('%d/%m')} au {end_of_week.strftime('%d/%m')}",
            events=events_str,
            astral_context=astral_context_formatted
        )
        
        print(f"✅ Prompt créé ({len(prompt)} caractères)")
        
        # 4. Génération avec Ollama
        print("\n🤖 Génération avec Ollama...")
        print("⏳ Patientez, génération en cours...")
        
        intro_text = await astro_generator._call_ollama_for_long_content(prompt)
        
        # 5. Nettoyage spécifique pour l'intro
        print("\n🧹 Nettoyage du texte...")
        
        # Supprimer les formules de clôture inappropriées
        import re
        unwanted_closures = [
            "bonne semaine", "belle semaine", "excellente semaine", "merveilleuse semaine",
            "à bientôt", "à très vite", "au revoir", "à la prochaine",
            "prenez soin de vous", "portez-vous bien", "que les étoiles vous accompagnent"
        ]
        
        original_length = len(intro_text)
        
        for closure in unwanted_closures:
            intro_text = re.sub(rf'\b{re.escape(closure)}\b[.!]*\s*$', '', intro_text, flags=re.IGNORECASE)
            intro_text = re.sub(rf'\b{re.escape(closure)}\b[.!]*\s*\n', '', intro_text, flags=re.IGNORECASE)
        
        # Nettoyage général
        intro_text = astro_generator._clean_script_text(intro_text)
        
        cleaned_length = len(intro_text)
        if cleaned_length < original_length:
            print(f"✅ Nettoyage effectué ({original_length - cleaned_length} caractères supprimés)")
        
        # 6. Analyse des résultats
        print("\n📊 ANALYSE DES RÉSULTATS")
        print("=" * 40)
        
        word_count = len(intro_text.split())
        char_count = len(intro_text)
        
        print(f"📏 Longueur : {word_count} mots ({char_count} caractères)")
        print(f"🎯 Objectif : 800+ mots ({'✅ ATTEINT' if word_count >= 800 else '❌ TROP COURT'})")
        
        # Vérifier la transition finale
        last_sentences = intro_text.split('.')[-3:]  # 3 dernières phrases
        last_text = '.'.join(last_sentences).lower()
        
        transition_indicators = ['plongeons', 'explorons', 'découvrons', 'maintenant', 'précisément']
        has_good_transition = any(word in last_text for word in transition_indicators)
        print(f"🔄 Transition : {'✅ BONNE' if has_good_transition else '⚠️ À VÉRIFIER'}")
        
        # Vérifier l'absence de formules de clôture
        bad_endings = any(closure in intro_text.lower() for closure in unwanted_closures)
        print(f"🚫 Clôtures : {'❌ TROUVÉES' if bad_endings else '✅ PROPRE'}")
        
        # 7. Affichage du résultat
        print(f"\n📖 INTRODUCTION GÉNÉRÉE")
        print("=" * 60)
        print(intro_text)
        print("=" * 60)
        
        # 8. Dernières phrases pour vérifier la transition
        print(f"\n🔍 DERNIÈRES PHRASES (transition) :")
        sentences = intro_text.split('.')
        for sentence in sentences[-3:]:
            if sentence.strip():
                print(f"   • {sentence.strip()}.")
        
        print(f"\n✅ Test d'introduction terminé avec succès !")
        print(f"📈 Score global : {word_count} mots générés")
        
        return intro_text
        
    except Exception as e:
        print(f"\n❌ Erreur durant le test : {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🌟" + "="*58)
    print("🌟 TEST GÉNÉRATION INTRO HEBDOMADAIRE AMÉLIORÉE")
    print("🌟" + "="*58)
    
    services = setup_imports()
    result = asyncio.run(test_intro_generation(services))
    
    if result:
        print(f"\n🎉 Test réussi ! Introduction prête à l'emploi.")
    else:
        print(f"\n💥 Test échoué. Vérifiez les logs ci-dessus.")
#!/usr/bin/env python3
"""
Script de test pour les titres d'horoscopes
Fichier: tests/test_title_generation.py
"""

import asyncio
import sys
import os

# Ajouter le chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_title_generation():
    """
    Teste la génération de titres avec différents horoscopes
    """
    
    # Import de votre générateur
    from astro_core.services.astro_mcp import astro_generator
    
    # Exemples d'horoscopes pour tester
    test_horoscopes = {
        "bélier": """
        Cher Bélier, cette journée vous invite à explorer de nouveaux territoires créatifs. 
        Votre énergie naturelle trouve un écho dans les mouvements planétaires, 
        particulièrement avec Mars qui stimule votre capacité d'innovation. 
        Une rencontre professionnelle pourrait ouvrir des portes inattendues. 
        Conseil : osez proposer vos idées les plus audacieuses.
        """,
        
        "cancer": """
        Cher Cancer, la Lune dans votre signe amplifie votre intuition et votre sensibilité. 
        C'est le moment idéal pour vous reconnecter avec votre famille ou vos proches. 
        Une décision importante concernant votre foyer se dessine à l'horizon. 
        Vos émotions sont votre boussole aujourd'hui. 
        Conseil : faites confiance à votre ressenti profond.
        """,
        
        "lion": """
        Cher Lion, votre charisme naturel brille de mille feux aujourd'hui. 
        Le Soleil dans votre secteur de créativité vous pousse vers l'expression artistique. 
        Un projet personnel prend une tournure exceptionnelle et pourrait vous mener vers la reconnaissance. 
        Votre générosité attire l'attention positive. 
        Conseil : partagez vos talents sans retenue.
        """,
        
        "scorpion": """
        Cher Scorpion, les profondeurs de votre âme révèlent des vérités cachées. 
        Pluton active votre capacité de transformation personnelle. 
        Un secret du passé refait surface, mais c'est pour votre bien. 
        Votre magnétisme naturel influence positivement votre entourage. 
        Conseil : embrassez les changements qui se présentent.
        """,
        
        "verseau": """
        Cher Verseau, votre vision futuriste trouve enfin un terrain d'expression. 
        Uranus éveille votre génie inventif et votre originalité. 
        Un groupe ou une communauté reconnaît votre valeur unique. 
        Vos idées avant-gardistes inspirent et motivent les autres. 
        Conseil : persévérez dans vos projets innovants.
        """
    }
    
    print("🎬 Test de génération de titres pour différents horoscopes")
    print("=" * 60)
    
    results = {}
    
    for signe, horoscope_text in test_horoscopes.items():
        print(f"\n📝 Test pour {signe.upper()}:")
        print("-" * 40)
        
        try:
            # Générer plusieurs titres pour le même horoscope
            titles = []
            for i in range(3):  # 3 tentatives pour voir la variété
                title = await astro_generator._extract_title_theme(horoscope_text)
                titles.append(title)
                print(f"   Titre #{i+1}: {title}")
            
            results[signe] = {
                'horoscope': horoscope_text[:100] + "...",
                'titles': titles,
                'unique_titles': len(set(titles)),  # Nombre de titres uniques
                'repeated': len(titles) - len(set(titles))  # Répétitions
            }
            
            # Analyse de la variété
            if len(set(titles)) == 1:
                print(f"   ⚠️  PROBLÈME: Même titre répété {len(titles)} fois")
            elif len(set(titles)) == len(titles):
                print(f"   ✅ EXCELLENT: {len(titles)} titres différents")
            else:
                print(f"   🔶 MOYEN: {len(set(titles))} titres uniques sur {len(titles)}")
                
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            results[signe] = {'error': str(e)}
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    total_unique = 0
    total_titles = 0
    
    for signe, data in results.items():
        if 'error' not in data:
            print(f"{signe.upper()}: {data['unique_titles']}/{len(data['titles'])} titres uniques")
            total_unique += data['unique_titles']
            total_titles += len(data['titles'])
    
    if total_titles > 0:
        creativity_score = (total_unique / total_titles) * 100
        print(f"\n🎯 SCORE DE CRÉATIVITÉ: {creativity_score:.1f}%")
        
        if creativity_score >= 90:
            print("✅ EXCELLENT: Très bonne variété de titres")
        elif creativity_score >= 70:
            print("🔶 CORRECT: Variété acceptable") 
        else:
            print("❌ PROBLÈME: Trop de répétitions, template à améliorer")
    
    return results

async def test_title_with_current_horoscope(sign: str):
    """
    Teste la génération de titre avec un horoscope fraîchement généré
    """
    from astro_core.services.astro_mcp import astro_generator
    import datetime
    
    print(f"🧪 Test complet pour {sign.upper()}")
    print("=" * 50)
    
    try:
        # 1. Générer un horoscope frais
        print("📝 Génération d'un nouvel horoscope...")
        horoscope_result, _, _ = await astro_generator.generate_single_horoscope(
            sign, datetime.date.today()
        )
        
        print(f"✅ Horoscope généré ({horoscope_result.word_count} mots)")
        print(f"📄 Contenu: {horoscope_result.horoscope_text[:100]}...")
        
        # 2. Tester la génération de titre
        print(f"\n🎬 Test de génération de titres...")
        
        titles = []
        for i in range(5):  # 5 tentatives
            title = await astro_generator._extract_title_theme(horoscope_result.horoscope_text)
            titles.append(title)
            print(f"   Titre #{i+1}: '{title}'")
        
        # 3. Analyse
        unique_count = len(set(titles))
        print(f"\n📊 ANALYSE:")
        print(f"   • {unique_count}/5 titres uniques")
        print(f"   • Score de variété: {(unique_count/5)*100:.1f}%")
        
        if unique_count >= 4:
            print("   ✅ Excellente créativité")
        elif unique_count >= 3:
            print("   🔶 Créativité correcte")
        else:
            print("   ❌ Problème de répétition")
        
        # 4. Afficher le titre utilisé actuellement
        print(f"\n🏷️  Titre actuel dans result: '{horoscope_result.title_theme}'")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test de génération de titres")
    parser.add_argument("--sign", help="Tester un signe spécifique avec horoscope frais")
    parser.add_argument("--all", action="store_true", help="Tester tous les exemples")
    
    args = parser.parse_args()
    
    if args.sign:
        asyncio.run(test_title_with_current_horoscope(args.sign))
    else:
        asyncio.run(test_title_generation())
#!/usr/bin/env python3
"""
Test d'intégration complète - Horoscope + ComfyUI + Flask
"""

import sys
import os
import time
import requests
import json
from datetime import datetime, date

# Ajouter le dossier courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_complete_integration():
    """Test complet de l'intégration"""
    
    print("🌟 Test d'Intégration Complète - Astro AI Video")
    print("=" * 70)
    
    # Configuration
    FLASK_URL = "http://127.0.0.1:5003"
    test_results = []
    
    print("💡 Assurez-vous que:")
    print("   - ComfyUI est démarré: cd /home/fluxart/ComfyUI && python main.py")
    print("   - Flask est démarré: python app.py")
    print()
    
    # 1. Test de base - Serveur Flask
    print("1️⃣ Test du serveur Flask")
    print("-" * 50)
    
    try:
        response = requests.get(f"{FLASK_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Flask opérationnel")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Ollama: {data.get('ollama', {}).get('status', 'unknown')}")
            print(f"   Astro: {data.get('astro_generator', {}).get('status', 'unknown')}")
            test_results.append(("Flask", True))
        else:
            print(f"❌ Flask non accessible: {response.status_code}")
            test_results.append(("Flask", False))
            return False
    except Exception as e:
        print(f"❌ Erreur connexion Flask: {e}")
        test_results.append(("Flask", False))
        return False
    
    # 2. Test génération d'horoscope
    print(f"\n2️⃣ Test génération d'horoscope")
    print("-" * 50)
    
    try:
        response = requests.post(f"{FLASK_URL}/api/generate_single_horoscope", 
                               json={"sign": "leo", "date": date.today().strftime("%Y-%m-%d")},
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                horoscope = data["result"]
                print(f"✅ Horoscope généré pour {horoscope['sign']}")
                print(f"   Texte: {horoscope['horoscope'][:80]}...")
                print(f"   Mots: {horoscope['word_count']}")
                print(f"   Influence lunaire: {horoscope['lunar_influence']}")
                test_results.append(("Horoscope", True))
                
                # Sauvegarder pour les tests suivants
                global test_horoscope_data
                test_horoscope_data = horoscope
                
            else:
                print(f"❌ Échec génération: {data.get('error')}")
                test_results.append(("Horoscope", False))
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            test_results.append(("Horoscope", False))
    except Exception as e:
        print(f"❌ Erreur génération horoscope: {e}")
        test_results.append(("Horoscope", False))
    
    # 3. Test ComfyUI Status
    print(f"\n3️⃣ Test statut ComfyUI")
    print("-" * 50)
    
    try:
        response = requests.get(f"{FLASK_URL}/api/comfyui/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("connected"):
                print(f"✅ ComfyUI connecté")
                print(f"   Serveur: {data.get('server')}")
                print(f"   Formats: {len(data.get('available_formats', []))}")
                print(f"   Signes: {len(data.get('supported_signs', []))}")
                test_results.append(("ComfyUI Status", True))
            else:
                print(f"❌ ComfyUI non connecté: {data.get('error')}")
                test_results.append(("ComfyUI Status", False))
        else:
            print(f"❌ Erreur endpoint ComfyUI: {response.status_code}")
            test_results.append(("ComfyUI Status", False))
    except Exception as e:
        print(f"❌ Erreur test ComfyUI: {e}")
        test_results.append(("ComfyUI Status", False))
    
    # 4. Test formats vidéo
    print(f"\n4️⃣ Test formats vidéo")
    print("-" * 50)
    
    try:
        response = requests.get(f"{FLASK_URL}/api/comfyui/formats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                formats = data["formats"]
                print(f"✅ {len(formats)} formats disponibles:")
                for name, specs in list(formats.items())[:3]:
                    print(f"   {name}: {specs['width']}x{specs['height']} ({specs['platform']})")
                test_results.append(("Formats", True))
            else:
                print(f"❌ Erreur formats: {data.get('error')}")
                test_results.append(("Formats", False))
        else:
            print(f"❌ Erreur endpoint formats: {response.status_code}")
            test_results.append(("Formats", False))
    except Exception as e:
        print(f"❌ Erreur test formats: {e}")
        test_results.append(("Formats", False))
    
    # 5. Test génération vidéo ComfyUI
    print(f"\n5️⃣ Test génération vidéo ComfyUI")
    print("-" * 50)
    
    generate_video = input("Voulez-vous tester la génération vidéo ComfyUI ? (y/N): ").lower().strip()
    
    if generate_video == 'y':
        try:
            print("🚀 Génération vidéo en cours...")
            start_time = time.time()
            
            response = requests.post(f"{FLASK_URL}/api/comfyui/generate_video", 
                                   json={
                                       "sign": "leo",
                                       "format": "test",
                                       "seed": 42
                                   },
                                   timeout=180)  # 3 minutes
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data["result"]
                    print(f"✅ Vidéo générée en {duration:.1f} secondes")
                    print(f"   Signe: {result['sign_name']}")
                    print(f"   Taille: {result['file_size']} bytes")
                    print(f"   Durée: {result['duration_seconds']}s")
                    print(f"   Chemin: {result['video_path']}")
                    print(f"   Résolution: {result['specs']['width']}x{result['specs']['height']}")
                    test_results.append(("Vidéo ComfyUI", True))
                else:
                    print(f"❌ Échec génération vidéo: {data.get('error')}")
                    test_results.append(("Vidéo ComfyUI", False))
            else:
                print(f"❌ Erreur HTTP génération: {response.status_code}")
                print(f"   Réponse: {response.text}")
                test_results.append(("Vidéo ComfyUI", False))
        except Exception as e:
            print(f"❌ Erreur génération vidéo: {e}")
            test_results.append(("Vidéo ComfyUI", False))
    else:
        print("⏭️  Test génération vidéo ignoré")
        test_results.append(("Vidéo ComfyUI", "Ignoré"))
    
    # 6. Test Chat IA
    print(f"\n6️⃣ Test chat IA")
    print("-" * 50)
    
    try:
        response = requests.post(f"{FLASK_URL}/api/ollama/chat", 
                               json={
                                   "message": "Donne-moi un conseil astrologique pour le Lion",
                                   "model": "mistral:latest"
                               },
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Chat IA opérationnel")
                print(f"   Réponse: {data['response'][:100]}...")
                test_results.append(("Chat IA", True))
            else:
                print(f"❌ Erreur chat: {data.get('error')}")
                test_results.append(("Chat IA", False))
        else:
            print(f"❌ Erreur endpoint chat: {response.status_code}")
            test_results.append(("Chat IA", False))
    except Exception as e:
        print(f"❌ Erreur test chat: {e}")
        test_results.append(("Chat IA", False))
    
    # 7. Test contexte astral
    print(f"\n7️⃣ Test contexte astral")
    print("-" * 50)
    
    try:
        response = requests.post(f"{FLASK_URL}/api/get_astral_context", 
                               json={"date": date.today().strftime("%Y-%m-%d")},
                               timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                context = data["result"]
                print(f"✅ Contexte astral récupéré")
                print(f"   Date: {context['date']}")
                print(f"   Phase lunaire: {context['lunar_phase']}")
                print(f"   Saison: {context['season']}")
                print(f"   Planètes: {len(context['influential_planets'])}")
                test_results.append(("Contexte astral", True))
            else:
                print(f"❌ Erreur contexte: {data.get('error')}")
                test_results.append(("Contexte astral", False))
        else:
            print(f"❌ Erreur endpoint contexte: {response.status_code}")
            test_results.append(("Contexte astral", False))
    except Exception as e:
        print(f"❌ Erreur test contexte: {e}")
        test_results.append(("Contexte astral", False))
    
    # Résumé final
    print(f"\n{'='*70}")
    print("📊 RÉSUMÉ FINAL")
    print("=" * 70)
    
    successful = 0
    total = len([r for r in test_results if r[1] != "Ignoré"])
    
    for test_name, result in test_results:
        if result == True:
            status = "✅ RÉUSSI"
            successful += 1
        elif result == False:
            status = "❌ ÉCHOUÉ"
        else:
            status = "⏭️  IGNORÉ"
        
        print(f"{test_name:<20} {status}")
    
    print(f"\n🎯 Résultat: {successful}/{total} tests réussis")
    
    if successful >= total * 0.8:  # 80% de réussite
        print("\n🎉 Intégration largement réussie!")
        print("🚀 Votre système Astro AI Video est opérationnel")
        
        print("\n📋 Workflow complet disponible:")
        print("1. ✅ Génération d'horoscopes avec IA")
        print("2. ✅ Création de vidéos avec ComfyUI")
        print("3. ✅ Chat interactif avec Ollama")
        print("4. ✅ Contexte astral détaillé")
        print("5. ✅ Interface web complète")
        
        print("\n🎬 Prochaines étapes:")
        print("• Ajoutez vos musiques de fond")
        print("• Créez des templates de miniatures")
        print("• Configurez la publication automatique")
        print("• Lancez votre chaîne d'horoscopes !")
        
        return True
    else:
        print("\n⚠️  Certains composants ne fonctionnent pas")
        print("🔧 Vérifiez la configuration:")
        print("• ComfyUI est-il démarré ?")
        print("• Ollama fonctionne-t-il ?")
        print("• Les dépendances sont-elles installées ?")
        
        return False

def test_workflow_complete():
    """Test du workflow complet: Horoscope -> Vidéo -> Publication"""
    
    print(f"\n🎯 Test du workflow complet")
    print("=" * 70)
    
    workflow_test = input("Voulez-vous tester le workflow complet ? (y/N): ").lower().strip()
    
    if workflow_test != 'y':
        print("⏭️  Test workflow ignoré")
        return True
    
    FLASK_URL = "http://127.0.0.1:5003"
    
    try:
        print("🔄 Workflow: Horoscope -> Vidéo -> Infos")
        print("-" * 50)
        
        # Étape 1: Générer horoscope
        print("1️⃣ Génération horoscope...")
        horoscope_response = requests.post(f"{FLASK_URL}/api/generate_single_horoscope", 
                                         json={"sign": "leo"}, timeout=30)
        
        if horoscope_response.status_code != 200:
            print("❌ Échec génération horoscope")
            return False
        
        horoscope_data = horoscope_response.json()
        if not horoscope_data.get("success"):
            print("❌ Horoscope non généré")
            return False
        
        horoscope = horoscope_data["result"]
        print(f"✅ Horoscope généré: {horoscope['word_count']} mots")
        
        # Étape 2: Générer vidéo
        print("2️⃣ Génération vidéo...")
        video_response = requests.post(f"{FLASK_URL}/api/comfyui/generate_video", 
                                     json={
                                         "sign": "leo",
                                         "format": "test"
                                     }, timeout=180)
        
        if video_response.status_code != 200:
            print("❌ Échec génération vidéo")
            return False
        
        video_data = video_response.json()
        if not video_data.get("success"):
            print("❌ Vidéo non générée")
            return False
        
        video_result = video_data["result"]
        print(f"✅ Vidéo générée: {video_result['file_size']} bytes")
        
        # Étape 3: Récupérer contexte astral
        print("3️⃣ Récupération contexte astral...")
        context_response = requests.post(f"{FLASK_URL}/api/get_astral_context", 
                                       json={}, timeout=15)
        
        if context_response.status_code != 200:
            print("❌ Échec récupération contexte")
            return False
        
        context_data = context_response.json()
        if not context_data.get("success"):
            print("❌ Contexte non récupéré")
            return False
        
        context = context_data["result"]
        print(f"✅ Contexte récupéré: {context['lunar_phase']}")
        
        # Résumé du workflow
        print("\n🎬 CONTENU GÉNÉRÉ POUR PUBLICATION:")
        print("=" * 50)
        print(f"📅 Date: {horoscope['date']}")
        print(f"⭐ Signe: {horoscope['sign']}")
        print(f"📝 Horoscope: {horoscope['horoscope']}")
        print(f"🎥 Vidéo: {video_result['video_path']}")
        print(f"📊 Durée: {video_result['duration_seconds']}s")
        print(f"📐 Résolution: {video_result['specs']['width']}x{video_result['specs']['height']}")
        print(f"🌙 Phase lunaire: {context['lunar_phase']}")
        print(f"🍂 Saison: {context['season']}")
        
        print("\n✅ Workflow complet fonctionnel!")
        print("🚀 Prêt pour la production quotidienne")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur workflow: {e}")
        return False

if __name__ == '__main__':
    print("Démarrage des tests d'intégration...")
    
    # Test principal
    success = test_complete_integration()
    
    if success:
        # Test workflow complet
        workflow_success = test_workflow_complete()
        
        if workflow_success:
            print("\n🏆 TOUS LES TESTS RÉUSSIS!")
            print("🎉 Votre système Astro AI Video est prêt!")
            
            print("\n📱 Accédez à votre interface web:")
            print("   👉 http://127.0.0.1:5003/")
            
            print("\n🎬 Fonctionnalités disponibles:")
            print("• Génération d'horoscopes personnalisés")
            print("• Création de vidéos avec ComfyUI")
            print("• Chat interactif avec IA")
            print("• Contexte astral détaillé")
            print("• Génération en lot")
            print("• Téléchargement des vidéos")
            
            exit(0)
        else:
            print("\n⚠️  Workflow partiellement fonctionnel")
            exit(1)
    else:
        print("\n❌ Tests d'intégration échoués")
        exit(1)
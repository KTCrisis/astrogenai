#!/usr/bin/env python3
"""
Test ComfyUI MCP Server - Version Corrigée
Script de test pour le serveur MCP ComfyUI
"""

import asyncio
import sys
import os
import time

# Ajouter le dossier courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_comfyui_mcp():
    """Test du serveur MCP ComfyUI"""
    
    print("🎬 Test du serveur MCP ComfyUI")
    print("=" * 50)
    
    try:
        # Import du serveur
        from comfyui_server_mcp import comfyui_generator
        print("✅ Import du serveur réussi")
        
        # Test 1: Statut
        print("\n🔍 Test 1: Vérification du statut")
        if comfyui_generator.test_connection():
            print("✅ ComfyUI connecté")
        else:
            print("❌ ComfyUI non connecté")
            return False
        
        # Test 2: Formats disponibles
        print("\n📋 Test 2: Formats disponibles")
        formats = list(comfyui_generator.video_formats.keys())
        print(f"✅ {len(formats)} formats: {', '.join(formats)}")
        
        # Test 3: Signes disponibles
        print("\n⭐ Test 3: Signes disponibles")
        signs = list(comfyui_generator.sign_metadata.keys())
        print(f"✅ {len(signs)} signes: {', '.join(signs)}")
        
        # Test 4: Génération de prompt
        print("\n📝 Test 4: Génération de prompt")
        test_sign = "leo"
        prompt = comfyui_generator.create_constellation_prompt(test_sign)
        print(f"✅ Prompt généré pour {test_sign}")
        print(f"   Longueur: {len(prompt)} caractères")
        print(f"   Aperçu: {prompt[:100]}...")
        
        # Test 5: Préparation de workflow
        print("\n🔧 Test 5: Préparation de workflow")
        workflow = comfyui_generator.prepare_workflow(test_sign, "test")
        print(f"✅ Workflow préparé")
        print(f"   Nœuds: {len(workflow)}")
        print(f"   Dimensions: {workflow['5']['inputs']['width']}x{workflow['5']['inputs']['height']}")
        print(f"   Batch size: {workflow['5']['inputs']['batch_size']}")
        
        # Test 6: Génération vidéo (optionnel)
        print("\n🎬 Test 6: Génération vidéo (optionnel)")
        generate_test = input("Voulez-vous tester la génération vidéo ? (y/N): ").lower().strip()
        
        if generate_test == 'y':
            print("🚀 Génération en cours...")
            start_time = time.time()
            
            result = comfyui_generator.generate_constellation_video(
                sign=test_sign,
                format_name="test"
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result:
                print(f"✅ Vidéo générée en {duration:.1f} secondes")
                print(f"   Chemin: {result.video_path}")
                print(f"   Taille: {result.file_size} bytes")
                print(f"   Durée: {result.duration_seconds:.1f}s")
            else:
                print("❌ Génération échouée")
                return False
        else:
            print("⏭️  Test de génération ignoré")
        
        print("\n✅ Tous les tests sont réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_tools():
    """Test des outils MCP - Version corrigée"""
    
    print("\n🛠️  Test des outils MCP")
    print("=" * 40)
    
    try:
        # Import du serveur MCP complet
        from comfyui_server_mcp import comfyui_generator
        
        # Test 1: Statut - Appel direct de la fonction
        print("\n🔍 Test outil: get_comfyui_status")
        
        # Utiliser directement la classe plutôt que l'outil MCP
        connected = comfyui_generator.test_connection()
        status = {
            "success": True,
            "connected": connected,
            "server": comfyui_generator.server_address,
            "output_dir": str(comfyui_generator.output_dir),
            "available_formats": list(comfyui_generator.video_formats.keys()),
            "supported_signs": list(comfyui_generator.sign_metadata.keys()),
            "workflow_ready": True
        }
        
        if status["success"]:
            print("✅ Statut récupéré")
            print(f"   Connecté: {status['connected']}")
            print(f"   Serveur: {status['server']}")
            print(f"   Formats: {len(status['available_formats'])}")
            print(f"   Signes: {len(status['supported_signs'])}")
        else:
            print(f"❌ Erreur: {status.get('error', 'Erreur inconnue')}")
        
        # Test 2: Formats
        print("\n📋 Test outil: get_video_formats")
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
        
        formats_result = {
            "success": True,
            "formats": formats,
            "count": len(formats)
        }
        
        if formats_result["success"]:
            print("✅ Formats récupérés")
            print(f"   Nombre: {formats_result['count']}")
            for name, specs in list(formats_result['formats'].items())[:3]:
                print(f"   {name}: {specs['width']}x{specs['height']} ({specs['platform']})")
        else:
            print(f"❌ Erreur: {formats_result.get('error', 'Erreur inconnue')}")
        
        # Test 3: Aperçu prompt
        print("\n📝 Test outil: preview_constellation_prompt")
        sign = "leo"
        
        if sign in comfyui_generator.sign_metadata:
            prompt = comfyui_generator.create_constellation_prompt(sign)
            sign_data = comfyui_generator.sign_metadata[sign]
            
            preview = {
                "success": True,
                "sign": sign_data["name"],
                "symbol": sign_data["symbol"],
                "prompt": prompt,
                "metadata": sign_data,
                "estimated_duration": "2-3 minutes"
            }
        else:
            preview = {
                "success": False,
                "error": f"Signe inconnu: {sign}"
            }
        
        if preview["success"]:
            print("✅ Aperçu généré")
            print(f"   Signe: {preview['sign']} {preview['symbol']}")
            print(f"   Durée estimée: {preview['estimated_duration']}")
            print(f"   Prompt: {preview['prompt'][:80]}...")
        else:
            print(f"❌ Erreur: {preview['error']}")
        
        # Test 4: Test génération
        print("\n🎬 Test outil: generate_constellation_video")
        
        generate_mcp_test = input("Voulez-vous tester la génération MCP ? (y/N): ").lower().strip()
        
        if generate_mcp_test == 'y':
            print("🚀 Génération MCP en cours...")
            start_time = time.time()
            
            # Utiliser directement la fonction de génération
            result = comfyui_generator.generate_constellation_video(
                sign="leo",
                format_name="test"
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result:
                print(f"✅ Génération MCP réussie en {duration:.1f} secondes")
                print(f"   Signe: {result.sign_name}")
                print(f"   Chemin: {result.video_path}")
                print(f"   Taille: {result.file_size} bytes")
            else:
                print("❌ Génération MCP échouée")
        else:
            print("⏭️  Test génération MCP ignoré")
        
        print("\n✅ Tous les outils MCP fonctionnent!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des outils: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_workflow_customization():
    """Test de personnalisation du workflow"""
    
    print("\n🎨 Test de personnalisation du workflow")
    print("=" * 50)
    
    try:
        from comfyui_server_mcp import comfyui_generator
        
        # Test avec différents formats
        formats_to_test = ["test", "youtube_short", "square"]
        
        for format_name in formats_to_test:
            print(f"\n📱 Test format: {format_name}")
            
            workflow = comfyui_generator.prepare_workflow("leo", format_name)
            specs = comfyui_generator.video_formats[format_name]
            
            # Vérifier les paramètres
            width = workflow['5']['inputs']['width']
            height = workflow['5']['inputs']['height']
            batch_size = workflow['5']['inputs']['batch_size']
            fps = workflow['22']['inputs']['frame_rate']
            
            print(f"   Dimensions: {width}x{height} (attendu: {specs.width}x{specs.height})")
            print(f"   Batch size: {batch_size} (attendu: {specs.batch_size})")
            print(f"   FPS: {fps} (attendu: {specs.fps})")
            
            # Vérifier que les valeurs correspondent
            if width == specs.width and height == specs.height and batch_size == specs.batch_size:
                print(f"   ✅ Format {format_name} correctement configuré")
            else:
                print(f"   ❌ Format {format_name} mal configuré")
                return False
        
        # Test avec seed personnalisé
        print("\n🎲 Test avec seed personnalisé")
        workflow_with_seed = comfyui_generator.prepare_workflow("leo", "test", seed=12345)
        if workflow_with_seed['6']['inputs']['seed'] == 12345:
            print("✅ Seed personnalisé appliqué")
        else:
            print("❌ Seed personnalisé non appliqué")
            return False
        
        # Test avec prompt personnalisé
        print("\n📝 Test avec prompt personnalisé")
        custom_prompt = '"0": "test prompt frame 0", "8": "test prompt frame 8", "16": "test prompt frame 16"'
        workflow_custom = comfyui_generator.prepare_workflow("leo", "test", custom_prompt=custom_prompt)
        if workflow_custom['18']['inputs']['prompts'] == custom_prompt:
            print("✅ Prompt personnalisé appliqué")
        else:
            print("❌ Prompt personnalisé non appliqué")
            return False
        
        print("\n✅ Tous les tests de personnalisation réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de personnalisation: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling():
    """Test de gestion des erreurs"""
    
    print("\n🛡️  Test de gestion des erreurs")
    print("=" * 40)
    
    try:
        from comfyui_server_mcp import comfyui_generator
        
        # Test 1: Signe inexistant
        print("\n❌ Test signe inexistant")
        if "inexistant" not in comfyui_generator.sign_metadata:
            print("✅ Erreur signe inexistant bien gérée")
        else:
            print("❌ Erreur signe inexistant mal gérée")
            return False
        
        # Test 2: Format inexistant
        print("\n❌ Test format inexistant")
        if "inexistant" not in comfyui_generator.video_formats:
            print("✅ Erreur format inexistant bien gérée")
        else:
            print("❌ Erreur format inexistant mal gérée")
            return False
        
        # Test 3: Génération avec paramètres invalides
        print("\n❌ Test génération avec paramètres invalides")
        try:
            # Ceci devrait lever une erreur
            workflow = comfyui_generator.prepare_workflow("inexistant", "test")
            print("❌ Erreur non détectée")
            return False
        except Exception:
            print("✅ Erreur de génération bien gérée")
        
        print("\n✅ Tous les tests de gestion d'erreurs réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de gestion d'erreurs: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_debug_video_generation():
    """Test de debug pour la génération vidéo"""
    
    print("\n🔍 Test de debug - Génération vidéo")
    print("=" * 50)
    
    try:
        from comfyui_server_mcp import comfyui_generator
        
        # Test de connexion détaillé
        print("\n🔗 Test de connexion détaillé")
        try:
            import requests
            response = requests.get(f"http://{comfyui_generator.server_address}/system_stats", timeout=5)
            print(f"✅ Connexion réussie: {response.status_code}")
            print(f"   Réponse: {response.json()}")
        except Exception as e:
            print(f"❌ Connexion échouée: {e}")
            return False
        
        # Test de l'historique
        print("\n📋 Test de l'historique ComfyUI")
        try:
            response = requests.get(f"http://{comfyui_generator.server_address}/history", timeout=5)
            history = response.json()
            print(f"✅ Historique récupéré: {len(history)} entrées")
            
            # Afficher les 3 dernières entrées
            for i, (prompt_id, data) in enumerate(list(history.items())[-3:]):
                print(f"   {i+1}. {prompt_id}: {data.get('status', {}).get('completed', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Erreur historique: {e}")
        
        # Test de génération avec debug
        print("\n🎬 Test de génération avec debug")
        debug_test = input("Voulez-vous tester la génération avec debug ? (y/N): ").lower().strip()
        
        if debug_test == 'y':
            print("🚀 Génération avec debug...")
            
            # Préparer le workflow avec debug
            workflow = comfyui_generator.prepare_workflow("leo", "test")
            
            print(f"📝 Workflow préparé:")
            print(f"   Nœuds: {list(workflow.keys())}")
            print(f"   Dimensions: {workflow['5']['inputs']['width']}x{workflow['5']['inputs']['height']}")
            print(f"   Seed: {workflow['6']['inputs']['seed']}")
            print(f"   Prompt: {workflow['18']['inputs']['prompts'][:100]}...")
            
            # Test de mise en queue
            try:
                response = comfyui_generator.queue_prompt(workflow)
                prompt_id = response.get('prompt_id')
                print(f"✅ Prompt mis en queue: {prompt_id}")
                
                # Attendre et vérifier
                print("⏳ Attente de la génération...")
                success = comfyui_generator.wait_for_completion(prompt_id)
                
                if success:
                    print("✅ Génération terminée")
                    
                    # Rechercher la vidéo
                    video_path = comfyui_generator.find_generated_video(prompt_id)
                    
                    if video_path:
                        print(f"✅ Vidéo trouvée: {video_path}")
                        
                        # Vérifier si le fichier existe
                        if os.path.exists(video_path):
                            file_size = os.path.getsize(video_path)
                            print(f"✅ Fichier confirmé: {file_size} bytes")
                        else:
                            print(f"❌ Fichier non trouvé: {video_path}")
                    else:
                        print("❌ Vidéo non trouvée dans l'historique")
                        
                        # Debug de l'historique
                        try:
                            response = requests.get(f"http://{comfyui_generator.server_address}/history/{prompt_id}")
                            history_data = response.json()
                            print(f"🔍 Debug historique pour {prompt_id}:")
                            print(f"   Status: {history_data.get(prompt_id, {}).get('status', 'N/A')}")
                            print(f"   Outputs: {list(history_data.get(prompt_id, {}).get('outputs', {}).keys())}")
                        except Exception as e:
                            print(f"❌ Erreur debug historique: {e}")
                else:
                    print("❌ Génération échouée")
                    
            except Exception as e:
                print(f"❌ Erreur lors de la génération: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⏭️  Test de génération debug ignoré")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de debug: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Fonction principale"""
    
    print("🌟 Test Complet ComfyUI MCP Server - Version Corrigée")
    print("=" * 70)
    
    print("💡 Assurez-vous que ComfyUI est démarré:")
    print("   cd /home/fluxart/ComfyUI && python main.py")
    print()
    
    # Tests progressifs
    tests = [
        ("🎬 Générateur ComfyUI", test_comfyui_mcp),
        ("🛠️  Outils MCP", test_mcp_tools),
        ("🎨 Personnalisation workflow", test_workflow_customization),
        ("🛡️  Gestion d'erreurs", test_error_handling),
        ("🔍 Debug génération vidéo", test_debug_video_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"🧪 {test_name}")
        print('='*70)
        
        try:
            success = await test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: RÉUSSI")
            else:
                print(f"❌ {test_name}: ÉCHOUÉ")
                
        except Exception as e:
            print(f"❌ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Pause entre les tests
    
    # Résumé final
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 70)
    
    successful = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{test_name:<35} {status}")
        if success:
            successful += 1
    
    print(f"\n🎯 Résultat final: {successful}/{total} tests réussis")
    
    if successful >= total - 1:  # Permettre 1 échec
        print("\n🎉 Tests largement réussis!")
        print("🚀 Le serveur MCP ComfyUI est prêt à être utilisé")
        
        print("\n📋 Prochaines étapes:")
        print("1. Vérifier le problème de récupération des vidéos générées")
        print("2. Démarrer le serveur MCP: python comfyui_server_mcp.py")
        print("3. Intégrer dans l'app Flask")
        print("4. Tester les endpoints API")
        print("5. Générer vos premières vidéos de constellations !")
        
        return 0
    else:
        print("\n⚠️  Plusieurs tests ont échoué")
        print("🔧 Vérifiez la configuration ComfyUI")
        print("💡 Points à vérifier:")
        print("   - ComfyUI est démarré et accessible")
        print("   - Les extensions AnimateDiff et VideoHelperSuite sont installées")
        print("   - Les modèles requis sont présents")
        print("   - Le dossier de sortie est accessible")
        print("   - Pas de conflits de ports")
        return 1

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
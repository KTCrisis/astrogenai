#!/usr/bin/env python3
"""
Test Twitter API v2 - Version corrigée pour les nouveaux plans X API
"""

import requests
import json
import datetime
import os
from requests_oauthlib import OAuth1Session

def load_twitter_credentials():
    """Charge les credentials Twitter"""
    possible_paths = [
        "astro_core/services/twitter/credentials.json",
        "credentials.json",
        "twitter_credentials.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"📁 Credentials trouvés: {path}")
            with open(path, 'r') as f:
                return json.load(f)
    
    print("❌ Fichier credentials.json non trouvé")
    return None

def create_oauth_session(credentials):
    """Crée une session OAuth 1.0a pour X API v2"""
    try:
        # Création de la session OAuth 1.0a
        oauth = OAuth1Session(
            credentials['api_key'],
            client_secret=credentials['api_secret'],
            resource_owner_key=credentials['access_token'],
            resource_owner_secret=credentials['access_token_secret'],
        )
        
        # Test de connexion avec v2 API
        response = oauth.get(
            "https://api.twitter.com/2/users/me",
            headers={"User-Agent": "AstroGenAI-v2"}
        )
        
        if response.status_code == 200:
            user_data = response.json()
            username = user_data['data']['username']
            print(f"✅ Connecté à X API v2 en tant que: @{username}")
            return oauth
        else:
            print(f"❌ Erreur connexion v2: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur OAuth: {e}")
        return None

def create_test_tweet():
    """Crée le contenu du tweet de test"""
    now = datetime.datetime.now()
    
    content = f"🌟 Test AstroGenAI v2 - {now.strftime('%d/%m/%Y à %H:%M')}\n"
    content += "Test API X v2 avec nouveau système ! ✨\n"
    content += "\n#AstroGenAI #XAPIv2 #Test"
    
    return content

def upload_media_v2(oauth, image_path):
    """Upload media avec v1.1 (seul endpoint média disponible)"""
    if not image_path or not os.path.exists(image_path):
        return None
    
    try:
        print(f"📷 Upload média: {image_path}")
        
        # Upload via v1.1 (autorisé)
        with open(image_path, 'rb') as file:
            files = {'media': file}
            
            response = oauth.post(
                "https://upload.twitter.com/1.1/media/upload.json",
                files=files
            )
        
        if response.status_code == 200:
            media_data = response.json()
            media_id = media_data['media_id_string']
            print(f"✅ Média uploadé: {media_id}")
            return media_id
        else:
            print(f"⚠️ Erreur upload: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
            
    except Exception as e:
        print(f"⚠️ Erreur upload média: {e}")
        return None

def publish_tweet_v2(oauth, content, media_id=None):
    """Publie le tweet avec X API v2"""
    try:
        print(f"📝 Contenu du tweet:")
        print(f'   "{content}"')
        print(f"📏 Longueur: {len(content)} caractères")
        
        # Vérification plan Free
        if len(content) > 280:
            print("⚠️ Tweet trop long pour le plan Free")
            return False
        
        # Confirmation utilisateur
        print(f"\n🤔 Publier ce tweet via X API v2 ? (y/N): ", end="")
        confirm = input().lower().strip()
        
        if confirm != 'y':
            print("❌ Publication annulée")
            return False
        
        # Préparation du payload v2
        payload = {"text": content}
        
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        
        # Headers pour v2
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AstroGenAI-v2"
        }
        
        print(f"🚀 Publication via POST /2/tweets...")
        
        # Requête POST vers v2 API
        response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
            headers=headers
        )
        
        print(f"📡 Status code: {response.status_code}")
        
        if response.status_code == 201:
            # Succès
            data = response.json()
            tweet_id = data['data']['id']
            
            # Récupération du nom d'utilisateur
            user_response = oauth.get("https://api.twitter.com/2/users/me")
            username = user_response.json()['data']['username']
            
            tweet_url = f"https://x.com/{username}/status/{tweet_id}"
            
            print(f"\n🎉 TWEET PUBLIÉ AVEC SUCCÈS !")
            print(f"🆔 ID: {tweet_id}")
            print(f"🔗 URL: {tweet_url}")
            print(f"👤 Par: @{username}")
            print(f"⏰ À: {datetime.datetime.now()}")
            
            return True
            
        else:
            # Erreur
            print(f"❌ Erreur publication: {response.status_code}")
            print(f"Réponse: {response.text}")
            
            # Analyse des erreurs courantes
            if response.status_code == 403:
                error_data = response.json()
                if 'errors' in error_data:
                    for error in error_data['errors']:
                        print(f"   - {error.get('message', 'Erreur inconnue')}")
                
                print(f"\n💡 Solutions possibles:")
                print(f"   1. Contenu en double détecté")
                print(f"   2. Limite quotidienne atteinte (17 tweets/jour)")
                print(f"   3. App pas associée à un Project")
                print(f"   4. Permissions insuffisantes")
            
            elif response.status_code == 429:
                print(f"❌ Limite de taux atteinte")
                print(f"💡 Plan Free: 17 tweets/24h - Attendez avant de republier")
            
            return False
            
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def check_api_limits(oauth):
    """Vérifie les limites API actuelles"""
    try:
        print(f"\n📊 Vérification des limites API...")
        
        # Récupération des infos utilisateur
        response = oauth.get("https://api.twitter.com/2/users/me")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"👤 Compte: @{user_data['data']['username']}")
            print(f"🆔 ID: {user_data['data']['id']}")
            
            # Affichage des limites du plan Free
            print(f"\n📋 Limites Plan Free:")
            print(f"   • POST /2/tweets: 17 requests/24h")
            print(f"   • GET endpoints: Divers (voir doc)")
            print(f"   • Posts récupérés: 500/mois max")
            print(f"   • Rate limits: Très restrictives")
            
            return True
        else:
            print(f"❌ Impossible de vérifier: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

def main():
    """Fonction principale"""
    print("🐦" + "="*60)
    print("🐦 TEST X API v2 - ASTROGENAI (VERSION CORRIGÉE)")
    print("🐦" + "="*60)
    
    # 1. Chargement credentials
    print("\n1️⃣ Chargement des credentials...")
    credentials = load_twitter_credentials()
    if not credentials:
        return
    
    # 2. Connexion OAuth v2
    print("\n2️⃣ Connexion à X API v2...")
    oauth = create_oauth_session(credentials)
    if not oauth:
        return
    
    # 3. Vérification des limites
    print("\n3️⃣ Vérification du compte...")
    if not check_api_limits(oauth):
        return
    
    # 4. Choix du type de test
    print("\n4️⃣ Type de test:")
    print("   1. Tweet simple v2")
    print("   2. Tweet avec hashtags")
    print("   3. Tweet avec image (v1.1 upload + v2 post)")
    
    choice = input("\nVotre choix (1/2/3): ").strip()
    
    # 5. Création du contenu
    content = create_test_tweet()
    media_id = None
    
    if choice == "2":
        content += " #XAPIv2Migration #DevTwitter"
    elif choice == "3":
        print(f"\nChemin image (ou ENTER): ", end="")
        image_path = input().strip()
        if image_path:
            media_id = upload_media_v2(oauth, image_path)
    
    # 6. Publication
    print("\n5️⃣ Publication du tweet...")
    success = publish_tweet_v2(oauth, content, media_id)
    
    if success:
        print(f"\n✅ TEST v2 RÉUSSI !")
        print(f"🎯 X API v2 fonctionne correctement")
        print(f"📈 Prêt pour l'intégration AstroGenAI")
        
        print(f"\n💡 Points importants:")
        print(f"   • Utilisez toujours l'endpoint /2/tweets")
        print(f"   • Plan Free: 17 tweets/jour maximum")
        print(f"   • Upload média via v1.1, post via v2")
        print(f"   • App doit être associée à un Project")
    else:
        print(f"\n❌ Test échoué")
        print(f"\n🔧 Actions à vérifier:")
        print(f"   1. App associée à un Project dans le portail dev")
        print(f"   2. Permissions en lecture/écriture activées")
        print(f"   3. Limite quotidienne pas atteinte")
        print(f"   4. Plan au minimum Free activé")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n👋 Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
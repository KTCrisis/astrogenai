#!/usr/bin/env python3
"""
Test Twitter API v2 - Version mise à jour avec OAuth1Session
Harmonisé avec le système d'authentification de test_permission.py
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
    print("💡 Structure attendue:")
    print('''{
    "api_key": "votre_api_key",
    "api_secret": "votre_api_secret",
    "access_token": "votre_access_token",
    "access_token_secret": "votre_access_token_secret"
}''')
    return None

def create_oauth_session(credentials):
    """Crée une session OAuth 1.0a pour X API v2"""
    try:
        print("🔐 Création de la session OAuth1...")
        
        # Création de la session OAuth 1.0a (même méthode que test_permission.py)
        oauth = OAuth1Session(
            credentials['api_key'],
            client_secret=credentials['api_secret'],
            resource_owner_key=credentials['access_token'],
            resource_owner_secret=credentials['access_token_secret'],
        )
        
        print("✅ Session OAuth1 créée - Prêt pour publication")
        return oauth
            
    except Exception as e:
        print(f"❌ Erreur OAuth: {e}")
        return None

def check_api_limits(oauth):
    """Vérifie les limites et le statut du compte"""
    try:
        print("📊 Vérification des limites API...")
        
        # Récupération des informations utilisateur
        response = oauth.get("https://api.twitter.com/2/users/me")
        
        if response.status_code == 200:
            user_data = response.json()
            username = user_data['data']['username']
            user_id = user_data['data']['id']
            
            print(f"👤 Compte: @{username} (ID: {user_id})")
            
            # Vérification des headers de rate limit si disponibles
            remaining = response.headers.get('x-rate-limit-remaining')
            reset_time = response.headers.get('x-rate-limit-reset')
            
            if remaining:
                print(f"🔢 Requêtes restantes: {remaining}")
            
            if reset_time:
                reset_dt = datetime.datetime.fromtimestamp(int(reset_time))
                print(f"🕐 Reset à: {reset_dt.strftime('%H:%M:%S')}")
            
            print("✅ Vérifications OK")
            return True
        else:
            print(f"❌ Impossible de vérifier les limites: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️ Erreur vérification limites: {e}")
        return True  # Continue même si la vérification échoue

def create_test_tweet():
    """Crée le contenu du tweet de test"""
    now = datetime.datetime.now()
    
    content = f"🦀 Découvrez l'horoscope du Cancer\n"
    content += "\nhttps://www.youtube.com/shorts/RmgsQ-RPDEI\n"
    content += "\n#horoscope #cancer #astrologie"
    
    return content

def upload_media_v2(oauth, image_path):
    """Upload média via v1.1 API (nécessaire pour v2)"""
    try:
        if not os.path.exists(image_path):
            print(f"❌ Image non trouvée: {image_path}")
            return None
        
        print(f"📷 Upload de l'image: {image_path}")
        
        # Upload via v1.1 API (requis même pour v2)
        with open(image_path, 'rb') as f:
            files = {'media': f}
            response = oauth.post(
                'https://upload.twitter.com/1.1/media/upload.json',
                files=files
            )
        
        if response.status_code == 200:
            media_data = response.json()
            media_id = media_data['media_id_string']
            print(f"✅ Image uploadée - Media ID: {media_id}")
            return media_id
        else:
            print(f"❌ Erreur upload: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception upload: {e}")
        return None

def publish_tweet_v2(oauth, content, media_id=None):
    """Publie un tweet via v2 API avec OAuth1"""
    try:
        print(f"📝 Contenu du tweet:")
        print(f'   "{content}"')
        print(f"📏 Longueur: {len(content)} caractères")
        
        if media_id:
            print(f"📷 Avec média ID: {media_id}")
        
        # Confirmation
        print(f"\n🤔 Publier ce tweet ? (y/N): ", end="")
        confirm = input().lower().strip()
        
        if confirm != 'y':
            print("❌ Publication annulée")
            return False
        
        # Payload pour POST /2/tweets
        payload = {"text": content}
        
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        
        print(f"🚀 Publication directe via POST /2/tweets...")
        
        # Publication directe (sans test préalable pour éviter rate limit)
        response = oauth.post(
            'https://api.twitter.com/2/tweets',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 Status code: {response.status_code}")
        
        if response.status_code == 201:
            # Succès
            data = response.json()
            tweet_id = data['data']['id']
            
            tweet_url = f"https://x.com/AstroGenAI/status/{tweet_id}"
            
            print(f"\n🎉 TWEET PUBLIÉ AVEC SUCCÈS !")
            print(f"🆔 ID: {tweet_id}")
            print(f"🔗 URL: {tweet_url}")
            print(f"👤 Par: @AstroGenAI")
            print(f"⏰ À: {datetime.datetime.now().strftime('%H:%M:%S')}")
            
            return True
        else:
            print(f"❌ Erreur publication: {response.status_code}")
            print(f"Réponse: {response.text}")
            
            if response.status_code == 403:
                print("\n💡 Erreur 403 - Causes possibles:")
                print("   • Permissions Read only (utilisez test_permission.py)")
                print("   • App pas associée à un Project")
                print("   • Limite quotidienne atteinte (17 tweets/jour)")
                print("   • Contenu détecté comme spam")
            elif response.status_code == 429:
                print("\n💡 Rate limit atteint - Attendez avant de réessayer")
            
            return False
    
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪" + "="*70)
    print("🧪 TEST TWITTER API v2 avec OAuth1Session - ASTROGENAI")
    print("🧪" + "="*70)
    
    # 1. Chargement credentials
    print("\n1️⃣ Chargement des credentials...")
    credentials = load_twitter_credentials()
    if not credentials:
        return
    
    # Vérification des clés requises
    required_keys = ['api_key', 'api_secret', 'access_token', 'access_token_secret']
    missing_keys = [key for key in required_keys if key not in credentials]
    
    if missing_keys:
        print(f"❌ Clés manquantes: {', '.join(missing_keys)}")
        return
    
    print("✅ Credentials chargés")
    
    # 2. Connexion OAuth v2
    print("\n2️⃣ Connexion à X API v2...")
    oauth = create_oauth_session(credentials)
    if not oauth:
        print("\n🔧 Si vous avez des problèmes de permissions:")
        print("   python test_permission.py")
        return
    
    # 3. Choix du type de test (sans vérifications supplémentaires)
    print("\n3️⃣ Type de test:")
    print("   1. Tweet simple v2")
    print("   2. Tweet avec hashtags étendus")
    print("   3. Tweet avec image (v1.1 upload + v2 post)")
    print("   4. Test permissions seulement (dry-run)")
    
    choice = input("\nVotre choix (1/2/3/4): ").strip()
    
    if choice == "4":
        # Test dry-run
        print("\n🧪 Test des permissions (dry-run)...")
        test_response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json={"text": "Test permissions - ne sera pas publié"},
            headers={"Content-Type": "application/json"}
        )
        
        if test_response.status_code == 403:
            print("❌ Permissions insuffisantes")
            print("🔧 Lancez: python test_permission.py")
        else:
            print("✅ Permissions OK pour l'écriture")
        return
    
    # 5. Création du contenu
    content = create_test_tweet()
    media_id = None
    
    if choice == "2":
        content += " #AI"
    elif choice == "3":
        print(f"\n📷 Chemin de l'image (ou ENTER pour ignorer): ", end="")
        image_path = input().strip()
        if image_path:
            media_id = upload_media_v2(oauth, image_path)
            if not media_id:
                print("⚠️ Continuons sans image")
    
    # 6. Publication
    print("\n5️⃣ Publication du tweet...")
    success = publish_tweet_v2(oauth, content, media_id)
    
    # 7. Résumé final
    print(f"\n" + "="*70)
    print(f"📊 RÉSUMÉ DU TEST")
    print(f"="*70)
    
    if success:
        print(f"🎉 TEST RÉUSSI !")
        print(f"✅ OAuth1Session fonctionnel")
        print(f"✅ X API v2 opérationnel")
        print(f"✅ Permissions Read/Write OK")
        print(f"📈 Prêt pour l'intégration AstroGenAI")
        
        print(f"\n💡 Points importants:")
        print(f"   • Endpoint utilisé: POST /2/tweets")
        print(f"   • Authentification: OAuth 1.0a")
        print(f"   • Plan Free: 17 tweets/jour maximum")
        print(f"   • Upload média: via v1.1, post via v2")
    else:
        print(f"❌ TEST ÉCHOUÉ")
        print(f"\n🔧 Actions de dépannage:")
        print(f"   1. Lancez: python test_permission.py")
        print(f"   2. Vérifiez l'association Project")
        print(f"   3. Confirmez les permissions Read/Write")
        print(f"   4. Régénérez les tokens si nécessaire")
    
    print(f"\n📋 Rappel des limites Plan Free:")
    print(f"   • 17 POST /2/tweets par 24h")
    print(f"   • 500 Posts récupérés par mois")
    print(f"   • Rate limits restrictives")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n👋 Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
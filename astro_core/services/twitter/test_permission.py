#!/usr/bin/env python3
"""
Debug version pour diagnostiquer le problème 403 paradoxal
"""

import requests
import json
import os
from requests_oauthlib import OAuth1Session

def load_twitter_credentials():
    """Charge les credentials Twitter"""
    possible_paths = [
        "astro_core/services/twitter/credentials.json",
        "credentials.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    return None

def debug_write_permissions(credentials):
    """Debug approfondi des permissions d'écriture"""
    try:
        oauth = OAuth1Session(
            credentials['api_key'],
            client_secret=credentials['api_secret'],
            resource_owner_key=credentials['access_token'],
            resource_owner_secret=credentials['access_token_secret'],
        )
        
        print("🔍 DEBUG - Test d'écriture approfondi...")
        
        # 1. Test avec contenu minimal
        print("\n1️⃣ Test avec contenu minimal...")
        minimal_payload = {"text": "Test"}
        
        response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json=minimal_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📡 Status: {response.status_code}")
        print(f"📋 Headers rate limit:")
        for header, value in response.headers.items():
            if 'rate-limit' in header.lower() or 'limit' in header.lower():
                print(f"   {header}: {value}")
        
        print(f"📄 Réponse complète:")
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except:
            print(f"   {response.text}")
        
        # 2. Test avec rate limit info
        print(f"\n2️⃣ Vérification rate limits...")
        rate_limit_response = oauth.get("https://api.twitter.com/1.1/application/rate_limit_status.json")
        
        if rate_limit_response.status_code == 200:
            rate_data = rate_limit_response.json()
            
            # Chercher les limites pour POST tweets
            if 'resources' in rate_data:
                tweets_limits = rate_data['resources'].get('tweets', {})
                for endpoint, limit_info in tweets_limits.items():
                    if 'post' in endpoint or 'tweets' in endpoint:
                        print(f"📊 {endpoint}:")
                        print(f"   Limit: {limit_info.get('limit', 'N/A')}")
                        print(f"   Remaining: {limit_info.get('remaining', 'N/A')}")
                        print(f"   Reset: {limit_info.get('reset', 'N/A')}")
        
        # 3. Test de vérification compte
        print(f"\n3️⃣ Vérification statut du compte...")
        user_response = oauth.get("https://api.twitter.com/2/users/me?user.fields=public_metrics")
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print(f"👤 Compte: @{user_data['data']['username']}")
            
            metrics = user_data['data'].get('public_metrics', {})
            print(f"📊 Tweets count: {metrics.get('tweet_count', 'N/A')}")
            print(f"📊 Followers: {metrics.get('followers_count', 'N/A')}")
        
        # 4. Test différents contenus
        print(f"\n4️⃣ Test de différents contenus...")
        
        # test_contents = [
        #     "Hello world",
        #     "Test AstroGenAI",
        #     "🌟 Test",
        #     "Test sans hashtags ni liens"
        # ]
        
        # for i, content in enumerate(test_contents, 1):
        #     print(f"\n   Test {i}: '{content}'")
        #     test_payload = {"text": content}
            
        #     test_response = oauth.post(
        #         "https://api.twitter.com/2/tweets",
        #         json=test_payload,
        #         headers={"Content-Type": "application/json"}
        #     )
            
        #     print(f"   Status: {test_response.status_code}")
            
        #     if test_response.status_code != 403:
        #         print(f"   ✅ Ce contenu passe !")
        #         print(f"   Réponse: {test_response.text[:100]}...")
        #         break
        #     else:
        #         try:
        #             error_data = test_response.json()
        #             print(f"   ❌ Erreur: {error_data.get('detail', 'Inconnue')}")
        #         except:
        #             print(f"   ❌ Erreur: {test_response.text}")
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur debug: {e}")
        return False

def main():
    """Fonction principale de debug"""
    print("🐛" + "="*70)
    print("🐛 DEBUG PERMISSIONS TWITTER API")
    print("🐛" + "="*70)
    
    credentials = load_twitter_credentials()
    if not credentials:
        print("❌ Credentials non trouvés")
        return
    
    debug_write_permissions(credentials)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n👋 Debug interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
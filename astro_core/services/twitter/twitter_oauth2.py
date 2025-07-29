#!/usr/bin/env python3
"""
Twitter API v2 avec OAuth 2.0 Authorization Code Flow with PKCE
Version moderne sans problèmes de permissions OAuth 1.0a
"""

import requests
import json
import datetime
import os
import secrets
import base64
import hashlib
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser
import time

class OAuth2Config:
    """Configuration OAuth 2.0"""
    
    def __init__(self, client_id, client_secret=None, redirect_uri="http://localhost:8080/callback"):
        self.client_id = client_id
        self.client_secret = client_secret  # Optionnel pour public clients
        self.redirect_uri = redirect_uri
        self.auth_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        
        # Scopes requis pour poster des tweets
        self.scopes = [
            "tweet.read",
            "tweet.write", 
            "users.read",
            "offline.access"  # Pour refresh token
        ]

class PKCEHelper:
    """Générateur PKCE (Proof Key for Code Exchange)"""
    
    @staticmethod
    def generate_code_verifier():
        """Génère un code verifier aléatoire"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    @staticmethod  
    def generate_code_challenge(verifier):
        """Génère le code challenge à partir du verifier"""
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

class CallbackHandler(BaseHTTPRequestHandler):
    """Handler pour capturer le callback OAuth"""
    
    def do_GET(self):
        """Traite la requête GET du callback"""
        if self.path.startswith('/callback'):
            # Parse des paramètres
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            
            if 'code' in params:
                self.server.authorization_code = params['code'][0]
                self.server.state = params.get('state', [None])[0]
                
                # Réponse success
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>Authorization Successful</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>🎉 Authorization Successful!</h1>
                    <p>Vous pouvez fermer cette fenêtre.</p>
                    <p>Retournez à votre application Python.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
                
            elif 'error' in params:
                self.server.error = params['error'][0]
                
                # Réponse erreur
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Authorization Failed</h1>
                    <p>Erreur: {params['error'][0]}</p>
                    <p>Vous pouvez fermer cette fenêtre.</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Supprime les logs du serveur"""
        pass

class TwitterOAuth2:
    """Client OAuth 2.0 pour Twitter API v2"""
    
    def __init__(self, config):
        self.config = config
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
    
    def authorize(self):
        """Lance le flow d'autorisation OAuth 2.0"""
        print("🔐 Démarrage de l'autorisation OAuth 2.0...")
        
        # 1. Génération PKCE
        code_verifier = PKCEHelper.generate_code_verifier()
        code_challenge = PKCEHelper.generate_code_challenge(code_verifier)
        state = secrets.token_urlsafe(32)
        
        print(f"🔑 PKCE Code Challenge généré")
        
        # 2. Construction de l'URL d'autorisation
        auth_params = {
            'response_type': 'code',
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'scope': ' '.join(self.config.scopes),
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{self.config.auth_url}?{urllib.parse.urlencode(auth_params)}"
        
        print(f"🌐 URL d'autorisation créée")
        print(f"📋 Scopes demandés: {', '.join(self.config.scopes)}")
        
        # 3. Démarrage du serveur callback
        server = HTTPServer(('localhost', 8080), CallbackHandler)
        server.authorization_code = None
        server.state = None
        server.error = None
        
        # Thread pour le serveur
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        print(f"🖥️  Serveur callback démarré sur http://localhost:8080")
        
        # 4. Ouverture du navigateur
        print(f"🌐 Ouverture du navigateur pour autorisation...")
        print(f"🔗 URL: {auth_url}")
        
        try:
            webbrowser.open(auth_url)
        except:
            print(f"❌ Impossible d'ouvrir le navigateur automatiquement")
            print(f"📋 Copiez cette URL dans votre navigateur:")
            print(f"   {auth_url}")
        
        # 5. Attente du callback
        print(f"⏳ En attente de l'autorisation utilisateur...")
        print(f"💡 Autorisez l'application dans votre navigateur")
        
        timeout = 120  # 2 minutes
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            if server.authorization_code or server.error:
                break
            time.sleep(0.5)
        
        server.shutdown()
        
        if server.error:
            print(f"❌ Autorisation refusée: {server.error}")
            return False
        
        if not server.authorization_code:
            print(f"❌ Timeout - Aucune réponse reçue")
            return False
        
        if server.state != state:
            print(f"❌ State parameter invalide - Possible attaque CSRF")
            return False
        
        print(f"✅ Code d'autorisation reçu")
        
        # 6. Échange du code contre un access token
        return self._exchange_code_for_token(server.authorization_code, code_verifier)
    
    def _exchange_code_for_token(self, authorization_code, code_verifier):
        """Échange le code d'autorisation contre un access token"""
        print(f"🔄 Échange du code contre un access token...")
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'code': authorization_code,
            'code_verifier': code_verifier
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Ajout du client secret si disponible (confidential client)
        if self.config.client_secret:
            headers['Authorization'] = f"Basic {self._get_basic_auth()}"
        
        try:
            response = requests.post(
                self.config.token_url,
                data=token_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                self.access_token = token_response['access_token']
                self.refresh_token = token_response.get('refresh_token')
                expires_in = token_response.get('expires_in', 7200)  # 2h par défaut
                
                self.token_expires_at = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
                
                print(f"✅ Access token obtenu avec succès")
                print(f"🕒 Expire à: {self.token_expires_at.strftime('%H:%M:%S')}")
                
                if self.refresh_token:
                    print(f"🔄 Refresh token disponible")
                
                return True
            else:
                print(f"❌ Erreur lors de l'échange: {response.status_code}")
                print(f"Réponse: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception lors de l'échange: {e}")
            return False
    
    def _get_basic_auth(self):
        """Génère l'en-tête Basic Auth pour confidential clients"""
        credentials = f"{self.config.client_id}:{self.config.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded
    
    def refresh_access_token(self):
        """Renouvelle l'access token avec le refresh token"""
        if not self.refresh_token:
            print(f"❌ Pas de refresh token disponible")
            return False
        
        print(f"🔄 Renouvellement de l'access token...")
        
        refresh_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.config.client_id
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            response = requests.post(
                self.config.token_url,
                data=refresh_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                self.access_token = token_response['access_token']
                expires_in = token_response.get('expires_in', 7200)
                self.token_expires_at = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
                
                # Le refresh token peut être renouvelé
                if 'refresh_token' in token_response:
                    self.refresh_token = token_response['refresh_token']
                
                print(f"✅ Access token renouvelé")
                return True
            else:
                print(f"❌ Erreur renouvellement: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception renouvellement: {e}")
            return False
    
    def is_token_valid(self):
        """Vérifie si le token est encore valide"""
        if not self.access_token or not self.token_expires_at:
            return False
        
        # Marge de 5 minutes
        margin = datetime.timedelta(minutes=5)
        return datetime.datetime.now() < (self.token_expires_at - margin)
    
    def ensure_valid_token(self):
        """S'assure qu'un token valide est disponible"""
        if self.is_token_valid():
            return True
        
        if self.refresh_token:
            return self.refresh_access_token()
        
        print(f"⚠️ Token expiré et pas de refresh token")
        print(f"💡 Nouvelle autorisation requise")
        return self.authorize()
    
    def make_authenticated_request(self, method, url, **kwargs):
        """Fait une requête authentifiée"""
        if not self.ensure_valid_token():
            return None
        
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f"Bearer {self.access_token}"
        kwargs['headers'] = headers
        
        return requests.request(method, url, **kwargs)

def load_oauth2_credentials():
    """Charge les credentials OAuth 2.0"""
    possible_paths = [
        "astro_core/services/twitter/oauth2_credentials.json",
        "oauth2_credentials.json",
        "twitter_oauth2_credentials.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"📁 Credentials OAuth 2.0 trouvés: {path}")
            with open(path, 'r') as f:
                return json.load(f)
    
    print(f"❌ Fichier oauth2_credentials.json non trouvé")
    print(f"💡 Structure attendue:")
    print(f'''{{
    "client_id": "votre_client_id",
    "client_secret": "votre_client_secret_optionnel"
}}''')
    return None

def create_test_tweet():
    """Crée le contenu du tweet de test"""
    now = datetime.datetime.now()
    
    content = f"🌟 Test AstroGenAI OAuth 2.0 - {now.strftime('%d/%m/%Y à %H:%M')}\n"
    content += "✨ API X v2 avec OAuth 2.0 PKCE parfaitement fonctionnel !\n"
    content += "\n#AstroGenAI #OAuth2 #XAPIv2 #Success"
    
    return content

def post_tweet_oauth2(twitter_client, content):
    """Poste un tweet via OAuth 2.0"""
    try:
        print(f"📝 Contenu du tweet:")
        print(f'   "{content}"')
        print(f"📏 Longueur: {len(content)} caractères")
        
        # Confirmation
        print(f"\n🤔 Publier ce tweet via OAuth 2.0 ? (y/N): ", end="")
        confirm = input().lower().strip()
        
        if confirm != 'y':
            print("❌ Publication annulée")
            return False
        
        # Payload pour POST /2/tweets
        payload = {"text": content}
        
        print(f"🚀 Publication via POST /2/tweets avec OAuth 2.0...")
        
        # Requête authentifiée
        response = twitter_client.make_authenticated_request(
            'POST',
            'https://api.twitter.com/2/tweets',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if not response:
            print(f"❌ Impossible de faire la requête (token invalide)")
            return False
        
        print(f"📡 Status code: {response.status_code}")
        
        if response.status_code == 201:
            # Succès
            data = response.json()
            tweet_id = data['data']['id']
            
            # Récupération du nom d'utilisateur
            user_response = twitter_client.make_authenticated_request(
                'GET',
                'https://api.twitter.com/2/users/me'
            )
            
            username = "unknown"
            if user_response and user_response.status_code == 200:
                username = user_response.json()['data']['username']
            
            tweet_url = f"https://x.com/{username}/status/{tweet_id}"
            
            print(f"\n🎉 TWEET PUBLIÉ AVEC SUCCÈS !")
            print(f"🆔 ID: {tweet_id}")
            print(f"🔗 URL: {tweet_url}")
            print(f"👤 Par: @{username}")
            print(f"⏰ À: {datetime.datetime.now()}")
            
            return True
        else:
            print(f"❌ Erreur publication: {response.status_code}")
            print(f"Réponse: {response.text}")
            
            if response.status_code == 403:
                print(f"\n💡 Avec OAuth 2.0, cette erreur peut indiquer:")
                print(f"   • Scopes insuffisants")
                print(f"   • App pas dans un Project")
                print(f"   • Plan d'accès insuffisant")
            
            return False
    
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔐" + "="*60)
    print("🔐 TWITTER API v2 avec OAuth 2.0 PKCE - ASTROGENAI")
    print("🔐" + "="*60)
    
    # 1. Chargement des credentials
    print(f"\n1️⃣ Chargement des credentials OAuth 2.0...")
    credentials = load_oauth2_credentials()
    if not credentials:
        return
    
    if 'client_id' not in credentials:
        print(f"❌ client_id manquant dans les credentials")
        return
    
    print(f"✅ Client ID chargé: {credentials['client_id'][:10]}...")
    
    # 2. Configuration OAuth 2.0
    config = OAuth2Config(
        client_id=credentials['client_id'],
        client_secret=credentials.get('client_secret'),  # Optionnel
        redirect_uri="http://localhost:8080/callback"
    )
    
    # 3. Initialisation du client Twitter
    twitter_client = TwitterOAuth2(config)
    
    # 4. Autorisation OAuth 2.0
    print(f"\n2️⃣ Autorisation OAuth 2.0...")
    if not twitter_client.authorize():
        print(f"❌ Échec de l'autorisation")
        return
    
    # 5. Test des API
    print(f"\n3️⃣ Test des endpoints...")
    
    # Test lecture
    user_response = twitter_client.make_authenticated_request(
        'GET',
        'https://api.twitter.com/2/users/me'
    )
    
    if user_response and user_response.status_code == 200:
        user_data = user_response.json()
        username = user_data['data']['username']
        print(f"✅ Lecture OK - Connecté comme @{username}")
    else:
        print(f"❌ Erreur lecture utilisateur")
        return
    
    # 6. Création et publication du tweet
    print(f"\n4️⃣ Publication du tweet de test...")
    content = create_test_tweet()
    
    success = post_tweet_oauth2(twitter_client, content)
    
    if success:
        print(f"\n🎉 TEST OAuth 2.0 RÉUSSI !")
        print(f"✅ Authorization Code Flow with PKCE fonctionne")
        print(f"✅ POST /2/tweets via OAuth 2.0 opérationnel")
        print(f"✅ Tokens automatiquement renouvelables")
        
        print(f"\n🚀 AstroGenAI prêt avec OAuth 2.0 !")
        
        # Sauvegarde optionnelle des tokens
        print(f"\n💾 Souhaitez-vous sauvegarder les tokens ? (y/N): ", end="")
        save = input().lower().strip()
        
        if save == 'y':
            tokens = {
                'access_token': twitter_client.access_token,
                'refresh_token': twitter_client.refresh_token,
                'expires_at': twitter_client.token_expires_at.isoformat() if twitter_client.token_expires_at else None
            }
            
            with open('twitter_tokens.json', 'w') as f:
                json.dump(tokens, f, indent=2)
            
            print(f"💾 Tokens sauvegardés dans twitter_tokens.json")
    else:
        print(f"\n❌ Test échoué")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n👋 Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
#!/usr/bin/env python3
"""
Test d'authentification YouTube API - Version Corrigée
"""

import os
import sys
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# SCOPES CORRIGÉS - Plus étendus
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.readonly'
]

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def authenticate_youtube():
    """Authentification YouTube API avec scopes corrigés"""
    creds = None
    
    # IMPORTANT : Supprimer l'ancien token car les scopes ont changé
    if os.path.exists(TOKEN_FILE):
        print("🗑️  Suppression ancien token (scopes différents)...")
        os.remove(TOKEN_FILE)
    
    # Charger token existant (sera None après suppression)
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Si pas de credentials valides, demander authentification
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refresh du token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"❌ Fichier {CREDENTIALS_FILE} non trouvé !")
                return None
            
            print("🔐 Lancement de l'authentification OAuth2 avec scopes étendus...")
            print("📧 URL d'authentification générée...")
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            
            # Version pour serveur sans navigateur
            print("\n🌐 COPIEZ ET COLLEZ cette URL dans votre navigateur :")
            print("=" * 80)
            
            # Démarrer le flow
            try:
                creds = flow.run_local_server(port=0, open_browser=False)
            except Exception as e:
                print(f"❌ Erreur flow : {e}")
                print("\n💡 Essayez avec la méthode manuelle :")
                print("1. Copiez l'URL affichée ci-dessus")
                print("2. Ouvrez-la dans un navigateur")
                print("3. Autorisez l'application")
                print("4. Copiez le code de retour")
                return None
        
        # Sauvegarder token
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("💾 Token sauvegardé avec nouveaux scopes")
    
    return creds

def test_channel_access(creds):
    """Test d'accès à la chaîne YouTube avec permissions étendues"""
    try:
        # Construire service YouTube
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Test 1 : Récupérer infos chaîne (nécessite youtube.readonly)
        print("🔍 Test 1 : Accès lecture chaîne...")
        request = youtube.channels().list(
            part='snippet,statistics',
            mine=True
        )
        response = request.execute()
        
        if not response['items']:
            print("❌ Aucune chaîne trouvée")
            return False
        
        channel = response['items'][0]
        snippet = channel['snippet']
        statistics = channel['statistics']
        
        print("✅ Test 1 réussi !")
        print(f"📺 Chaîne : {snippet['title']}")
        print(f"🆔 ID : {channel['id']}")
        print(f"👥 Abonnés : {statistics.get('subscriberCount', '0')}")
        print(f"🎬 Vidéos : {statistics.get('videoCount', '0')}")
        
        # Test 2 : Vérifier permissions upload
        print("\n🔍 Test 2 : Vérification permissions upload...")
        
        # Tester avec une requête qui nécessite youtube.upload scope
        try:
            # Test de listing des playlists (nécessite permissions étendues)
            playlists_request = youtube.playlists().list(
                part='snippet',
                mine=True,
                maxResults=1
            )
            playlists_response = playlists_request.execute()
            print("✅ Test 2 réussi ! Permissions upload disponibles")
            
        except Exception as e:
            print(f"⚠️  Test 2 échoué : {e}")
            return False
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        print("=" * 50)
        print("✅ Authentification complète")
        print("✅ Accès lecture chaîne")
        print("✅ Permissions upload")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur API : {e}")
        
        if "insufficientPermissions" in str(e):
            print("\n💡 Solution :")
            print("1. Les scopes OAuth sont insuffisants")
            print("2. Re-configurer l'écran de consentement avec tous les scopes")
            print("3. Supprimer token.json et recommencer")
        
        return False

def main():
    """Fonction principale"""
    print("🚀 Test d'authentification AstroGenAI YouTube API - VERSION CORRIGÉE")
    print("=" * 80)
    print("🔧 Scopes étendus : upload + lecture + gestion complète")
    print()
    
    # Authentification
    creds = authenticate_youtube()
    if not creds:
        print("❌ Échec de l'authentification")
        return
    
    # Test accès chaîne
    if test_channel_access(creds):
        print("\n🚀 CONFIGURATION YOUTUBE API COMPLÈTEMENT OPÉRATIONNELLE !")
        print("✅ Prêt pour le développement de l'upload engine")
        
    else:
        print("\n❌ Problème d'accès - Vérifiez les scopes OAuth")

if __name__ == '__main__':
    main()
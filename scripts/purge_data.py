# Fichier: scripts/purge_data.py (Version fusionnée)

import os
import sys
from pathlib import Path

# --- CONFIGURATION ---

# Rend le fichier config.py accessible depuis le sous-dossier /scripts
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

try:
    from config import settings
    CONFIG_LOADED = True
except ImportError:
    CONFIG_LOADED = False

# --- FONCTION 1 : NETTOYAGE DES DONNÉES GÉNÉRÉES ---

def purge_generated_files():
    """
    Trouve et supprime les fichiers générés (audios, vidéos, montages).
    """
    if not CONFIG_LOADED:
        print("❌ Configuration non chargée. Annulation du nettoyage des données.")
        return

    print("\n--- 1. Nettoyage des Données Générées ---")
    
    target_dirs = [
        settings.GENERATED_AUDIO_DIR,
        settings.GENERATED_VIDEOS_DIR,
        settings.FINAL_MONTAGE_DIR,
        Path.home() / "ComfyUI" / "output",
    ]
    
    signs = [
        'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
        'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
    ]
    other_patterns = ["transition.mp4", "concat_list.txt", "liste_sync.txt"]

    confirm = input("Voulez-vous supprimer tous les audios/vidéos générés ? (y/N) : ")
    if confirm.lower() != 'y':
        print("Opération annulée.")
        return

    total_deleted = 0
    all_patterns = other_patterns + [f"{sign}*" for sign in signs]

    for dir_path in target_dirs:
        if not dir_path.is_dir():
            continue
        
        print(f"\n🧹 Nettoyage de : {dir_path}")
        deleted_in_dir = 0
        for pattern in all_patterns:
            for file_path in dir_path.rglob(pattern):
                try:
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_in_dir += 1
                except Exception as e:
                    print(f"  ❌ Erreur sur {file_path.name}: {e}")
        
        print(f"  ✅ {deleted_in_dir} fichier(s) supprimé(s).")
        total_deleted += deleted_in_dir
    
    print(f"\n--- Nettoyage des données terminé : {total_deleted} fichier(s) au total. ---")

# --- FONCTION 2 : DÉBLOCAGE DES FICHIERS DU PROJET ---

def unblock_project_files():
    """
    Supprime tous les fichiers ':Zone.Identifier' du projet.
    """
    print("\n--- 2. Déblocage des Fichiers du Projet (Suppression des Zone.Identifier) ---")
    
    files_to_unblock = list(project_root.rglob('*:Zone.Identifier'))

    if not files_to_unblock:
        print("✅ Aucun fichier bloqué ('Zone.Identifier') trouvé.")
        return

    print(f" Trouvé {len(files_to_unblock)} fichier(s) à débloquer.")
    confirm = input("Voulez-vous supprimer ces étiquettes de sécurité ? (y/N) : ")
    if confirm.lower() != 'y':
        print("Opération annulée.")
        return

    deleted_count = 0
    for file_path in files_to_unblock:
        try:
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"  ❌ Erreur sur {file_path.name}: {e}")
            
    print(f"\n--- Déblocage terminé : {deleted_count} fichier(s) débloqué(s). ---")

# --- MENU PRINCIPAL ---

def main():
    """
    Affiche un menu pour choisir l'action de nettoyage.
    """
    if not CONFIG_LOADED:
        print("❌ Erreur: Impossible de charger 'config.py'.")
        print("Assurez-vous que le script est dans un sous-dossier du projet.")
        return
        
    while True:
        print("\n" + "="*40)
        print("🔧 Menu de Nettoyage du Projet AstroGenAI 🔧")
        print("="*40)
        print("1. Purger les données générées (audios, vidéos, etc.)")
        print("2. Débloquer les fichiers du projet (supprimer les Zone.Identifier)")
        print("3. Tout faire (Purger ET Débloquer)")
        print("q. Quitter")
        
        choice = input("\nVotre choix : ")
        
        if choice == '1':
            purge_generated_files()
        elif choice == '2':
            unblock_project_files()
        elif choice == '3':
            purge_generated_files()
            unblock_project_files()
        elif choice.lower() == 'q':
            print("👋 Au revoir !")
            break
        else:
            print("❌ Choix invalide, veuillez réessayer.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script de build pour créer l'exécutable Windows du launcher Illama
Version 2.0.5 - Avec support Quick Wins
Exécute ce script sur Windows avec: python build_exe.py
"""

import subprocess
import sys
import os

def build():
    # Mettre à jour installer.iss avec la version depuis launcher.py
    print("[INFO] Mise à jour de installer.iss avec la version depuis launcher.py...")
    result = subprocess.run([sys.executable, "update_version.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print("[WARNING] Impossible de mettre à jour installer.iss automatiquement")
        print("[INFO] Assure-toi que la version dans installer.iss correspond à la version dans launcher.py")
    else:
        print(result.stdout)
    print()
    
    # Installer PyInstaller si nécessaire
    print("[INFO] Installation de PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])
    
    # Vérifier quels modules Quick Wins sont présents
    quick_wins_modules = []
    if os.path.exists("config_secure.py"):
        quick_wins_modules.append("config_secure.py")
    if os.path.exists("logger_config.py"):
        quick_wins_modules.append("logger_config.py")
    if os.path.exists("download_manager.py"):
        quick_wins_modules.append("download_manager.py")
    
    # Commande PyInstaller de base
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=IllamaLauncher",
        "--onefile",           # Un seul fichier exe
        "--windowed",          # Pas de console
        "--clean",
        "--noconfirm",
    ]
    
    # Ajouter l'icône si disponible
    if os.path.exists("icon.ico"):
        cmd.extend([
            "--icon=icon.ico",
            "--add-data=icon.ico;.",
        ])
    
    # Ajouter les modules Quick Wins comme hidden imports
    if quick_wins_modules:
        print(f"[INFO] Modules Quick Wins détectés: {', '.join(quick_wins_modules)}")
        for module in quick_wins_modules:
            module_name = module.replace('.py', '')
            cmd.extend(["--hidden-import", module_name])
    
    # Ajouter le fichier principal
    cmd.append("launcher.py")
    
    print("\n[INFO] Commande PyInstaller:")
    print(" ".join(cmd))
    print("\n[INFO] Building IllamaLauncher.exe...")
    print("[INFO] Ceci peut prendre quelques minutes...\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ [SUCCESS] Build terminé avec succès!")
        print(f"📦 L'exécutable se trouve dans: dist/IllamaLauncher.exe")
        print(f"📁 Dossier de travail PyInstaller: build/")
        print(f"📄 Spec file: IllamaLauncher.spec")
        
        if quick_wins_modules:
            print(f"\n⭐ Modules Quick Wins inclus:")
            for module in quick_wins_modules:
                print(f"   - {module}")
    else:
        print("\n❌ [ERROR] Le build a échoué!")
        print("Vérifie les erreurs ci-dessus.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(build())


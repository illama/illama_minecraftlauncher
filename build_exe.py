#!/usr/bin/env python3
"""
Script de build pour créer l'exécutable Windows du launcher Illama
Exécute ce script sur Windows avec: python build_exe.py
"""

import subprocess
import sys
import os

def build():
    # Installer PyInstaller si nécessaire
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"])
    
    # Commande PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=IllamaLauncher",
        "--onefile",           # Un seul fichier exe
        "--windowed",          # Pas de console
        "--icon=icon.ico",     # Icône (si disponible)
        "--add-data=icon.ico;.",  # Inclure l'icône
        "--clean",
        "--noconfirm",
        "launcher.py"
    ]
    
    # Si pas d'icône, enlever les options d'icône
    if not os.path.exists("icon.ico"):
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name=IllamaLauncher",
            "--onefile",
            "--windowed",
            "--clean",
            "--noconfirm",
            "launcher.py"
        ]
    
    print("Building IllamaLauncher.exe...")
    subprocess.run(cmd)
    print("\nDone! L'exécutable se trouve dans le dossier 'dist/'")

if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""
Script pour mettre à jour la version dans installer.iss depuis launcher.py
"""

import re
import sys

def update_installer_version():
    """Met à jour la version dans installer.iss depuis launcher.py"""
    try:
        # Lire la version depuis launcher.py
        with open("launcher.py", "r", encoding="utf-8") as f:
            launcher_content = f.read()
        
        # Extraire la version
        version_match = re.search(r'LAUNCHER_VERSION\s*=\s*"([^"]+)"', launcher_content)
        if not version_match:
            print("[ERREUR] Impossible de trouver LAUNCHER_VERSION dans launcher.py")
            return False
        
        version = version_match.group(1)
        print(f"[INFO] Version détectée: {version}")
        
        # Lire installer.iss
        with open("installer.iss", "r", encoding="utf-8") as f:
            installer_content = f.read()
        
        # Mettre à jour la version
        new_content = re.sub(
            r'#define MyAppVersion "[^"]+"',
            f'#define MyAppVersion "{version}"',
            installer_content
        )
        
        # Écrire le fichier mis à jour
        with open("installer.iss", "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print(f"[OK] installer.iss mis à jour avec la version {version}")
        return True
        
    except FileNotFoundError as e:
        print(f"[ERREUR] Fichier non trouvé: {e}")
        return False
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la mise à jour: {e}")
        return False

if __name__ == "__main__":
    success = update_installer_version()
    sys.exit(0 if success else 1)


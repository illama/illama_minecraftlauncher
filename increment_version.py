#!/usr/bin/env python3
"""
Script pour incrémenter automatiquement la version du launcher
Utilisation: python increment_version.py
"""

import re
from pathlib import Path

def increment_version(version: str) -> str:
    """Incrémente la version automatiquement
    Format: X.Y.Z
    - Z incrémente jusqu'à 9, puis Y incrémente et Z revient à 0
    - Y incrémente jusqu'à 9, puis X incrémente et Y revient à 0
    Exemples: 1.0.2 -> 1.0.3, 1.0.9 -> 1.1.0, 1.9.9 -> 2.0.0
    """
    try:
        parts = version.split('.')
        if len(parts) != 3:
            return version
        
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2])
        
        # Incrémenter le patch
        patch += 1
        
        # Si patch > 9, incrémenter minor et remettre patch à 0
        if patch > 9:
            patch = 0
            minor += 1
            
            # Si minor > 9, incrémenter major et remettre minor à 0
            if minor > 9:
                minor = 0
                major += 1
        
        return f"{major}.{minor}.{patch}"
    except:
        return version

def update_version_in_file(file_path: Path, old_version: str, new_version: str):
    """Met à jour la version dans le fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remplacer toutes les occurrences de l'ancienne version
        content = content.replace(f'LAUNCHER_VERSION = "{old_version}"', f'LAUNCHER_VERSION = "{new_version}"')
        content = content.replace(f'LAUNCHER_VERSION = \'{old_version}\'', f'LAUNCHER_VERSION = \'{new_version}\'')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour: {e}")
        return False

def get_current_version(file_path: Path) -> str:
    """Extrait la version actuelle du fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if 'LAUNCHER_VERSION' in line:
                    # Chercher le pattern LAUNCHER_VERSION = "X.Y.Z"
                    match = re.search(r'LAUNCHER_VERSION\s*=\s*["\']([\d.]+)["\']', line)
                    if match:
                        return match.group(1)
    except Exception as e:
        print(f"Erreur lors de la lecture: {e}")
    return None

if __name__ == "__main__":
    launcher_file = Path("launcher.py")
    
    if not launcher_file.exists():
        print("Erreur: launcher.py introuvable!")
        exit(1)
    
    current_version = get_current_version(launcher_file)
    
    if not current_version:
        print("Erreur: Impossible de trouver LAUNCHER_VERSION dans launcher.py")
        exit(1)
    
    new_version = increment_version(current_version)
    
    print(f"Version actuelle: {current_version}")
    print(f"Nouvelle version: {new_version}")
    
    if update_version_in_file(launcher_file, current_version, new_version):
        print(f"[OK] Version mise a jour de {current_version} a {new_version}")
    else:
        print("[ERREUR] Erreur lors de la mise a jour")
        exit(1)


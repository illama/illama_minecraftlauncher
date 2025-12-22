"""
Configuration sécurisée pour Illama Launcher
Gère le chargement des secrets depuis .env et la validation
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Charger le fichier .env s'il existe
load_dotenv()

class Config:
    """Configuration centralisée et sécurisée"""
    
    # === VERSION ===
    LAUNCHER_VERSION = "2.0.4"
    MIN_REQUIRED_VERSION = "1.0.0"
    
    # === SECRETS (depuis .env) ===
    @staticmethod
    def get_drive_api_key() -> str:
        """Récupère la clé API Google Drive"""
        key = os.getenv('DRIVE_API_KEY')
        if not key:
            raise ValueError(
                "DRIVE_API_KEY manquant ! "
                "Crée un fichier .env à partir de .env.example"
            )
        return key
    
    @staticmethod
    def get_drive_folder_id() -> str:
        """Récupère l'ID du dossier Google Drive"""
        folder_id = os.getenv('DRIVE_FOLDER_ID')
        if not folder_id:
            raise ValueError(
                "DRIVE_FOLDER_ID manquant ! "
                "Crée un fichier .env à partir de .env.example"
            )
        return folder_id
    
    @staticmethod
    def get_github_token() -> str:
        """Récupère le token GitHub (optionnel si repo public)"""
        return os.getenv('GITHUB_TOKEN', '')
    
    @staticmethod
    def get_ms_client_id() -> str:
        """Récupère le Microsoft Client ID"""
        return os.getenv('MS_CLIENT_ID', '6a3728d6-27a3-4180-99bb-479895b8f88e')
    
    @staticmethod
    def verify_admin_password(password: str) -> bool:
        """
        Vérifie le mot de passe admin de manière sécurisée
        Utilise un hash SHA-256 au lieu du mot de passe en clair
        """
        admin_hash = os.getenv('ADMIN_PASSWORD_HASH')
        
        # Fallback : si pas de hash dans .env, utiliser l'ancien système
        # (À SUPPRIMER en production !)
        if not admin_hash:
            print("[SECURITY WARNING] Utilisation du mot de passe en clair !")
            plain_password = os.getenv('ADMIN_PASSWORD', 'Swap!72!')
            return password == plain_password
        
        # Vérification sécurisée avec hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == admin_hash
    
    # === SERVEUR ===
    SERVER_ADDRESS = os.getenv('SERVER_ADDRESS', 'illama.duckdns.org')
    SERVER_NAME = os.getenv('SERVER_NAME', 'Illama Server')
    
    # === BACKEND ===
    BACKEND_URL = os.getenv('BACKEND_URL', '')
    
    # === GITHUB ===
    GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER', 'illama')
    GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME', 'illama_minecraftlauncher')
    
    @property
    def github_releases_url(self) -> str:
        """URL de l'API GitHub pour les releases"""
        return f"https://api.github.com/repos/{self.GITHUB_REPO_OWNER}/{self.GITHUB_REPO_NAME}/releases/latest"
    
    # === DÉVELOPPEMENT ===
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    @classmethod
    def validate(cls) -> bool:
        """
        Valide que toutes les configurations essentielles sont présentes
        Retourne True si OK, sinon raise une exception explicite
        """
        errors = []
        
        try:
            cls.get_drive_api_key()
        except ValueError as e:
            errors.append(str(e))
        
        try:
            cls.get_drive_folder_id()
        except ValueError as e:
            errors.append(str(e))
        
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(
                f"Configuration invalide :\n{error_msg}\n\n"
                "Instructions :\n"
                "1. Copie .env.example vers .env\n"
                "2. Remplis les valeurs dans .env\n"
                "3. Relance le launcher"
            )
        
        return True


def generate_admin_password_hash(password: str) -> str:
    """
    Utilitaire pour générer un hash de mot de passe admin
    Usage: python config_secure.py --generate-hash "mon_mot_de_passe"
    """
    return hashlib.sha256(password.encode()).hexdigest()


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    # Si lancé en ligne de commande pour générer un hash
    if len(sys.argv) > 2 and sys.argv[1] == '--generate-hash':
        password = sys.argv[2]
        hash_value = generate_admin_password_hash(password)
        print(f"\nHash SHA-256 pour le mot de passe:")
        print(f"{hash_value}")
        print(f"\nAjoute cette ligne dans ton fichier .env:")
        print(f"ADMIN_PASSWORD_HASH={hash_value}")
    else:
        # Test de validation
        try:
            Config.validate()
            print("✅ Configuration valide !")
            print(f"Version du launcher: {Config.LAUNCHER_VERSION}")
            print(f"Serveur: {Config.SERVER_NAME} ({Config.SERVER_ADDRESS})")
            print(f"Mode debug: {Config.DEBUG}")
        except ValueError as e:
            print(f"❌ Erreur de configuration:\n{e}")
            sys.exit(1)

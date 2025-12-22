"""
Guide d'intégration des Quick Wins dans launcher.py
====================================================

Ce fichier explique comment intégrer les nouveaux modules dans ton launcher existant.

ÉTAPE 1 : Installer les dépendances
====================================

pip install -r requirements.txt


ÉTAPE 2 : Créer le fichier .env
================================

1. Copie .env.example vers .env
2. Remplis les valeurs avec tes vrais secrets
3. Génère un hash pour le mot de passe admin :

   python config_secure.py --generate-hash "ton_mot_de_passe"


ÉTAPE 3 : Intégrer le système de logging
=========================================

Au début de launcher.py, remplace les print() par le logger :

# ANCIEN CODE :
print("[Info] Téléchargement en cours...")

# NOUVEAU CODE :
from logger_config import get_logger
logger = get_logger()
logger.info("Téléchargement en cours...")


ÉTAPE 4 : Utiliser la configuration sécurisée
==============================================

Remplace les constantes hardcodées :

# ANCIEN CODE :
DRIVE_API_KEY = "AIzaSyDM0KvOtyFluGO6-P9YJdcUyB73bZxir2k"
ADMIN_PASSWORD = "Swap!72!"

# NOUVEAU CODE :
from config_secure import Config

# Valider la configuration au démarrage
try:
    Config.validate()
except ValueError as e:
    messagebox.showerror("Erreur de configuration", str(e))
    sys.exit(1)

# Utiliser les valeurs
DRIVE_API_KEY = Config.get_drive_api_key()
DRIVE_FOLDER_ID = Config.get_drive_folder_id()

# Pour vérifier le mot de passe admin
def check_admin_password(password):
    return Config.verify_admin_password(password)


ÉTAPE 5 : Utiliser le download manager robuste
===============================================

Dans la classe GoogleDriveSync, remplace la logique de téléchargement :

# ANCIEN CODE dans GoogleDriveSync :
def download_file(self, file_info):
    # ... code existant avec urllib ...

# NOUVEAU CODE :
from download_manager import DownloadManager, RetryPolicy

class GoogleDriveSync:
    def __init__(self, ...):
        # ...
        self.download_manager = DownloadManager(
            retry_policy=RetryPolicy(
                max_retries=self.config.get('download_retries', 3)
            ),
            timeout=self.config.get('download_timeout', 180),
            chunk_size=self.config.get('download_chunk_size', 32768)
        )
    
    def download_file(self, file_info, progress_callback=None):
        url = file_info['url']
        dest = Path(file_info['path'])
        expected_hash = file_info.get('sha256')  # Utilise SHA-256 maintenant !
        
        result = self.download_manager.download_file(
            url=url,
            dest=dest,
            expected_hash=expected_hash,
            hash_algorithm='sha256',  # Plus sûr que MD5
            progress_callback=progress_callback
        )
        
        if not result.success:
            logger.error(f"Échec du téléchargement : {result.error}")
            return False
        
        return True


ÉTAPE 6 : Ajouter le logging dans les fonctions critiques
==========================================================

Ajoute des logs dans les fonctions importantes :

def sync_mods(self):
    logger.info("=== Début de la synchronisation ===")
    try:
        # ... ton code ...
        logger.info("Synchronisation terminée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation", exc_info=True)
        raise

def launch_minecraft(self):
    logger.info("Lancement de Minecraft...")
    try:
        # ... ton code ...
        logger.info("Minecraft lancé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors du lancement", exc_info=True)
        raise


ÉTAPE 7 : Nettoyer les anciens logs au démarrage
=================================================

Au début de la fonction main() ou __init__ de LauncherGUI :

from logger_config import LauncherLogger

# Nettoyer les logs de plus de 7 jours
LauncherLogger.cleanup_old_logs(days_to_keep=7)


ÉTAPE 8 : Rebuild et test
==========================

1. Teste d'abord en mode dev :
   python launcher.py

2. Si tout fonctionne, build l'exe :
   BUILD_LAUNCHER.bat

3. Teste l'exe compilé

4. Vérifie les logs dans :
   %LOCALAPPDATA%\IllamaLauncher\logs\


EXEMPLE COMPLET D'INTÉGRATION
==============================
"""

# Exemple de code à ajouter au début de launcher.py :

# ========== IMPORTS (après les imports existants) ==========
from config_secure import Config
from logger_config import get_logger
from download_manager import DownloadManager, RetryPolicy

# ========== CONFIGURATION (remplacer les constantes) ==========
# Valider la config au démarrage
try:
    Config.validate()
    logger = get_logger(log_level=Config.LOG_LEVEL)
    logger.info(f"Illama Launcher v{Config.LAUNCHER_VERSION} démarré")
except ValueError as e:
    # Si pas de logger encore disponible, utiliser print
    print(f"ERREUR: {e}")
    if 'tk' in sys.modules:  # Si tkinter est déjà importé
        messagebox.showerror("Configuration invalide", str(e))
    sys.exit(1)

# Utiliser les valeurs depuis Config
DRIVE_API_KEY = Config.get_drive_api_key()
DRIVE_FOLDER_ID = Config.get_drive_folder_id()
LAUNCHER_VERSION = Config.LAUNCHER_VERSION
SERVER_ADDRESS = Config.SERVER_ADDRESS
SERVER_NAME = Config.SERVER_NAME

# ========== FONCTION EXEMPLE : Vérification admin ==========
def verify_admin_password():
    """Vérifie le mot de passe admin de manière sécurisée"""
    password = simpledialog.askstring(
        "Mot de passe Admin",
        "Entre le mot de passe administrateur:",
        show='*'
    )
    
    if not password:
        return False
    
    if Config.verify_admin_password(password):
        logger.info("Authentification admin réussie")
        return True
    else:
        logger.warning("Tentative d'authentification admin échouée")
        messagebox.showerror("Erreur", "Mot de passe incorrect")
        return False

# ========== LOGS DANS LES FONCTIONS EXISTANTES ==========
# Exemple : dans la fonction de synchronisation
def sync_mods(self):
    logger.info("Début de la synchronisation des mods")
    logger.debug(f"Config: drive_folder_id={DRIVE_FOLDER_ID}")
    
    try:
        # ... ton code de sync existant ...
        logger.info(f"Synchronisation terminée : {len(mods)} mods traités")
    except Exception as e:
        logger.error("Erreur lors de la synchronisation", exc_info=True)
        messagebox.showerror("Erreur", f"Synchronisation échouée: {e}")

"""
NOTES IMPORTANTES :
===================

1. NE PAS supprimer l'ancien code immédiatement
   - Garde une copie de launcher.py avant modifications
   - Intègre progressivement les nouveaux modules
   - Teste après chaque changement

2. Ordre de priorité d'intégration :
   - Logging (facile, très utile)
   - Configuration sécurisée (.env)
   - Download manager (améliore la robustesse)

3. SHA-256 vs MD5 :
   - Commence à utiliser SHA-256 pour les nouveaux fichiers
   - Garde la compatibilité MD5 pour l'ancien code
   - Migre progressivement

4. Logs :
   - Les logs sont dans %LOCALAPPDATA%\IllamaLauncher\logs\
   - Vérifier régulièrement pour détecter les problèmes

5. Build :
   - Après intégration, teste bien en mode dev
   - Build l'exe seulement quand tout fonctionne
   - Garde l'ancien exe comme backup

CHECKLIST FINALE :
==================
[ ] .env créé et rempli
[ ] requirements.txt installé
[ ] Logging intégré dans les fonctions principales
[ ] Configuration sécurisée utilisée
[ ] Tests en mode dev (python launcher.py)
[ ] Build de l'exe (BUILD_LAUNCHER.bat)
[ ] Tests de l'exe compilé
[ ] Vérification des logs
[ ] Commit et push (sans .env !)
"""

if __name__ == "__main__":
    print(__doc__)

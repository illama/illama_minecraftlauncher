"""
Système de logging professionnel pour Illama Launcher
Gère les logs console, fichier, et erreurs critiques
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

# Créer le dossier de logs s'il n'existe pas
LOG_DIR = Path.home() / 'AppData' / 'Local' / 'IllamaLauncher' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

class ColoredFormatter(logging.Formatter):
    """Formatter avec couleurs pour la console"""
    
    # Codes couleurs ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        # Ajouter la couleur selon le niveau
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        return super().format(record)


class LauncherLogger:
    """Gestionnaire de logging centralisé"""
    
    def __init__(
        self,
        name: str = 'illama_launcher',
        log_level: str = 'INFO',
        max_file_size_mb: int = 10,
        backup_count: int = 5
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Éviter les doublons de handlers
        if self.logger.handlers:
            return
        
        # Format détaillé pour fichier
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Format simple pour console
        console_formatter = ColoredFormatter(
            '%(levelname)-8s | %(message)s'
        )
        
        # === HANDLER 1: Fichier rotatif (logs normaux) ===
        log_file = LOG_DIR / f'launcher_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # === HANDLER 2: Fichier séparé pour les erreurs ===
        error_log_file = LOG_DIR / f'errors_{datetime.now().strftime("%Y%m%d")}.log'
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
        
        # === HANDLER 3: Console (seulement en mode debug) ===
        if log_level.upper() == 'DEBUG':
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        self.logger.info(f"=== Illama Launcher démarré ===")
        self.logger.info(f"Logs sauvegardés dans: {LOG_DIR}")
    
    def get_logger(self) -> logging.Logger:
        """Retourne l'instance du logger"""
        return self.logger
    
    @staticmethod
    def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
        """
        Log une exception avec son contexte complet
        
        Args:
            logger: Instance du logger
            exception: L'exception à logger
            context: Contexte additionnel (ex: "Lors de la synchronisation")
        """
        logger.error(
            f"{context}\n"
            f"Type: {type(exception).__name__}\n"
            f"Message: {str(exception)}",
            exc_info=True
        )
    
    @staticmethod
    def cleanup_old_logs(days_to_keep: int = 7):
        """
        Nettoie les anciens fichiers de logs
        
        Args:
            days_to_keep: Nombre de jours de logs à conserver
        """
        if not LOG_DIR.exists():
            return
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        deleted_count = 0
        for log_file in LOG_DIR.glob('*.log*'):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
            except Exception as e:
                print(f"Erreur lors du nettoyage de {log_file}: {e}")
        
        if deleted_count > 0:
            print(f"[Cleanup] {deleted_count} ancien(s) fichier(s) de logs supprimé(s)")


# === INSTANCE GLOBALE (Singleton pattern) ===
_logger_instance: Optional[LauncherLogger] = None

def get_logger(
    name: str = 'illama_launcher',
    log_level: str = 'INFO'
) -> logging.Logger:
    """
    Récupère l'instance du logger (Singleton)
    
    Usage:
        from logger_config import get_logger
        logger = get_logger()
        logger.info("Message de log")
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = LauncherLogger(name, log_level)
    
    return _logger_instance.get_logger()


# === DÉCORATEURS UTILITAIRES ===
def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Décorateur pour logger automatiquement les appels de fonction
    
    Usage:
        @log_function_call()
        def ma_fonction(arg1, arg2):
            ...
    """
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or get_logger()
            log.debug(f"→ Appel de {func.__name__} avec args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                log.debug(f"← {func.__name__} terminé avec succès")
                return result
            except Exception as e:
                log.error(f"✗ Erreur dans {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    # Configuration du logger
    logger = get_logger(log_level='DEBUG')
    
    # Tests
    logger.debug("Ceci est un message de debug")
    logger.info("Ceci est un message d'info")
    logger.warning("Ceci est un warning")
    logger.error("Ceci est une erreur")
    
    # Test d'exception
    try:
        raise ValueError("Erreur de test")
    except Exception as e:
        LauncherLogger.log_exception(logger, e, "Test d'exception")
    
    # Test du décorateur
    @log_function_call()
    def test_function(x, y):
        return x + y
    
    test_function(5, 3)
    
    # Nettoyage des vieux logs
    LauncherLogger.cleanup_old_logs(days_to_keep=7)
    
    print(f"\n✅ Tests terminés. Vérifie les logs dans: {LOG_DIR}")

"""
Module de téléchargement robuste avec retry intelligent et validation
Améliore la fiabilité des téléchargements de mods
"""

import time
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from logger_config import get_logger

logger = get_logger()


@dataclass
class DownloadResult:
    """Résultat d'un téléchargement"""
    success: bool
    filepath: Optional[Path] = None
    error: Optional[str] = None
    bytes_downloaded: int = 0
    duration_seconds: float = 0.0
    attempts: int = 0
    sha256_hash: Optional[str] = None


class RetryPolicy:
    """Politique de retry pour les téléchargements"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """
        Calcule le délai avant le prochain retry (exponential backoff)
        
        Args:
            attempt: Numéro de la tentative (0, 1, 2, ...)
        
        Returns:
            Délai en secondes
        """
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)


class DownloadManager:
    """Gestionnaire de téléchargements avec retry et validation"""
    
    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        timeout: int = 180,
        chunk_size: int = 32768,
        user_agent: str = "IllamaLauncher/2.0"
    ):
        self.retry_policy = retry_policy or RetryPolicy()
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.user_agent = user_agent
    
    def download_file(
        self,
        url: str,
        dest: Path,
        expected_hash: Optional[str] = None,
        hash_algorithm: str = 'sha256',
        progress_callback: Optional[Callable[[int, int], None]] = None,
        resume: bool = True
    ) -> DownloadResult:
        """
        Télécharge un fichier avec retry automatique et validation
        
        Args:
            url: URL du fichier à télécharger
            dest: Chemin de destination
            expected_hash: Hash attendu pour validation (optionnel)
            hash_algorithm: Algorithme de hash ('sha256' recommandé, 'md5' legacy)
            progress_callback: Fonction callback(bytes_downloaded, total_bytes)
            resume: Permettre la reprise de téléchargement
        
        Returns:
            DownloadResult avec les détails du téléchargement
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                result = self._attempt_download(
                    url, dest, progress_callback, resume
                )
                
                # Valider le hash si fourni
                if expected_hash and result.success:
                    calculated_hash = self._calculate_hash(dest, hash_algorithm)
                    result.sha256_hash = calculated_hash
                    
                    if calculated_hash != expected_hash.lower():
                        logger.error(
                            f"Hash mismatch pour {dest.name}\n"
                            f"Attendu: {expected_hash}\n"
                            f"Reçu: {calculated_hash}"
                        )
                        dest.unlink(missing_ok=True)
                        result.success = False
                        result.error = "Hash mismatch"
                        raise ValueError("Hash validation failed")
                
                # Succès !
                result.duration_seconds = time.time() - start_time
                result.attempts = attempt + 1
                logger.info(
                    f"✓ Téléchargement réussi: {dest.name} "
                    f"({result.bytes_downloaded:,} octets, "
                    f"{result.duration_seconds:.1f}s, "
                    f"{result.attempts} tentative(s))"
                )
                return result
                
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Tentative {attempt + 1}/{self.retry_policy.max_retries + 1} échouée "
                    f"pour {dest.name}: {e}"
                )
                
                # Si ce n'est pas la dernière tentative, attendre avant de retry
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.get_delay(attempt)
                    logger.debug(f"Attente de {delay:.1f}s avant retry...")
                    time.sleep(delay)
                else:
                    # Dernière tentative échouée
                    logger.error(
                        f"✗ Échec définitif après {attempt + 1} tentatives: {dest.name}"
                    )
        
        # Toutes les tentatives ont échoué
        return DownloadResult(
            success=False,
            error=last_error,
            duration_seconds=time.time() - start_time,
            attempts=self.retry_policy.max_retries + 1
        )
    
    def _attempt_download(
        self,
        url: str,
        dest: Path,
        progress_callback: Optional[Callable[[int, int], None]],
        resume: bool
    ) -> DownloadResult:
        """
        Tente un téléchargement (une seule tentative)
        """
        # Créer le dossier parent si nécessaire
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Préparer la requête
        headers = {'User-Agent': self.user_agent}
        
        # Support de la reprise si le fichier existe partiellement
        start_byte = 0
        if resume and dest.exists():
            start_byte = dest.stat().st_size
            headers['Range'] = f'bytes={start_byte}-'
            logger.debug(f"Reprise du téléchargement à partir de {start_byte:,} octets")
        
        request = urllib.request.Request(url, headers=headers)
        
        # Ouvrir la connexion
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            
            # Si reprise, ajuster la taille totale
            if start_byte > 0:
                total_size += start_byte
            
            # Mode d'écriture (append si reprise, sinon write)
            mode = 'ab' if resume and start_byte > 0 else 'wb'
            
            bytes_downloaded = start_byte
            
            with open(dest, mode) as f:
                while True:
                    chunk = response.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    
                    # Callback de progression
                    if progress_callback:
                        progress_callback(bytes_downloaded, total_size)
        
        return DownloadResult(
            success=True,
            filepath=dest,
            bytes_downloaded=bytes_downloaded
        )
    
    @staticmethod
    def _calculate_hash(filepath: Path, algorithm: str = 'sha256') -> str:
        """
        Calcule le hash d'un fichier
        
        Args:
            filepath: Chemin du fichier
            algorithm: 'sha256' (recommandé) ou 'md5' (legacy)
        
        Returns:
            Hash en hexadécimal (lowercase)
        """
        hash_obj = hashlib.new(algorithm)
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def verify_file_integrity(
        filepath: Path,
        expected_hash: str,
        algorithm: str = 'sha256'
    ) -> bool:
        """
        Vérifie l'intégrité d'un fichier déjà téléchargé
        
        Args:
            filepath: Chemin du fichier
            expected_hash: Hash attendu
            algorithm: Algorithme de hash
        
        Returns:
            True si le hash correspond, False sinon
        """
        if not filepath.exists():
            return False
        
        calculated = DownloadManager._calculate_hash(filepath, algorithm)
        return calculated == expected_hash.lower()


# === FONCTIONS UTILITAIRES ===

def download_with_retry(
    url: str,
    dest: Path,
    expected_hash: Optional[str] = None,
    max_retries: int = 3,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> DownloadResult:
    """
    Fonction helper simple pour télécharger avec retry
    
    Usage:
        result = download_with_retry(
            "https://example.com/mod.jar",
            Path("mods/mod.jar"),
            expected_hash="abc123...",
            max_retries=3
        )
        if result.success:
            print("Téléchargement réussi !")
    """
    manager = DownloadManager(
        retry_policy=RetryPolicy(max_retries=max_retries)
    )
    return manager.download_file(url, dest, expected_hash, progress_callback=progress_callback)


def calculate_file_hash(filepath: Path, algorithm: str = 'sha256') -> str:
    """
    Calcule le hash d'un fichier (fonction standalone)
    
    Usage:
        hash_value = calculate_file_hash(Path("mod.jar"))
    """
    return DownloadManager._calculate_hash(filepath, algorithm)


# === EXEMPLE D'UTILISATION ===
if __name__ == "__main__":
    import sys
    
    # Test du système de téléchargement
    test_url = "https://www.google.com/robots.txt"
    test_dest = Path("test_download.txt")
    
    def progress(downloaded, total):
        if total > 0:
            percent = (downloaded / total) * 100
            print(f"\rProgression: {percent:.1f}% ({downloaded:,} / {total:,} octets)", end='')
    
    print(f"Test de téléchargement depuis: {test_url}")
    result = download_with_retry(
        test_url,
        test_dest,
        max_retries=2,
        progress_callback=progress
    )
    
    print()  # Nouvelle ligne après la barre de progression
    
    if result.success:
        print(f"✅ Succès !")
        print(f"   Fichier: {result.filepath}")
        print(f"   Taille: {result.bytes_downloaded:,} octets")
        print(f"   Durée: {result.duration_seconds:.2f}s")
        print(f"   Hash: {result.sha256_hash}")
        
        # Nettoyage
        test_dest.unlink(missing_ok=True)
    else:
        print(f"❌ Échec: {result.error}")
        sys.exit(1)

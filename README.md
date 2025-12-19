# Illama Launcher

Launcher Minecraft personnalisé pour le serveur Illama avec synchronisation automatique des mods via Google Drive.

## Fonctionnalités

- Synchronisation automatique des mods depuis Google Drive
- Connexion Microsoft/Mojang obligatoire (vérifie la licence Minecraft)
- Configuration RAM, résolution, etc.
- Support Prism Launcher uniquement
- Installation automatique de Prism Launcher
- Interface moderne et simple

## Pour les joueurs

### Installation

1. Télécharge et exécute `IllamaLauncher_Setup.exe`
2. Suis les instructions d'installation
3. Lance "Illama Launcher" depuis le menu Démarrer ou le Bureau

### Première utilisation

1. Connecte-toi avec ton compte Microsoft (celui de Minecraft)
2. Choisis ta version de Minecraft et Forge
3. Si Prism Launcher n'est pas installé, clique sur "Installer Prism Launcher"
4. Clique sur "JOUER" - les mods se synchronisent automatiquement!

## Pour les développeurs

### Créer l'installateur

1. **Prérequis:**
   - Python 3.8+ (https://www.python.org/downloads/)
   - Inno Setup 6 (https://jrsoftware.org/isdl.php)

2. **Build automatique:**
   ```
   Double-clique sur BUILD.bat
   ```

3. **Build manuel:**
   ```bash
   pip install pyinstaller
   pyinstaller --name=IllamaLauncher --onefile --windowed --clean launcher.py
   ```
   Puis compile `installer.iss` avec Inno Setup.

### Structure

```
minecraft-sync-launcher/
├── launcher.py                    # Code principal
├── BUILD.bat                      # Script de build automatique
├── build_exe.py                   # Script Python de build
├── installer.iss                  # Script Inno Setup
├── COMMENT_CREER_INSTALLATEUR.md  # Instructions détaillées
└── README.md                      # Ce fichier
```

### Configuration Admin

- **Mot de passe admin:** `illama2024` (modifiable dans le code)
- **Clé API Google Drive:** Intégrée dans le code
- **ID dossier Drive:** Intégré dans le code

Pour modifier ces paramètres, édite les variables au début de `launcher.py`:
```python
DRIVE_API_KEY = "ta_cle_api"
DRIVE_FOLDER_ID = "id_du_dossier"
ADMIN_PASSWORD = "ton_mot_de_passe"
```

## Licence

Usage privé pour le serveur Illama.

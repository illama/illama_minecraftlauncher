# 🎮 Illama Launcher

> **Launcher Minecraft professionnel avec synchronisation automatique des mods depuis Google Drive**

[![Version](https://img.shields.io/badge/version-2.0.4-green.svg)](https://github.com/illama/illama_minecraftlauncher/releases)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Utilisation](#-utilisation)
- [Développement](#-développement)
- [Build & Distribution](#-build--distribution)
- [Dépannage](#-dépannage)
- [Contribution](#-contribution)

---

## ✨ Fonctionnalités

### 🔄 Synchronisation intelligente
- ✅ Téléchargement automatique des mods depuis Google Drive
- ✅ Vérification d'intégrité SHA-256
- ✅ Reprise de téléchargement en cas d'échec
- ✅ Retry automatique avec exponential backoff
- ✅ Détection des mods obsolètes et nettoyage

### 🎯 Gestion de Minecraft
- ✅ Support de Prism Launcher
- ✅ Création automatique d'instances
- ✅ Gestion des versions Minecraft & Forge
- ✅ Configuration optimale de la RAM
- ✅ Détection automatique de Java

### 🔐 Authentification Microsoft
- ✅ Login via compte Microsoft/Xbox
- ✅ Gestion automatique des tokens
- ✅ Refresh automatique de la session

### 🎨 Interface moderne
- ✅ Interface sombre type GitHub/Discord
- ✅ Animations fluides
- ✅ Barre de progression en temps réel
- ✅ System tray avec icône
- ✅ Support multi-résolutions

### 🛡️ Sécurité
- ✅ Gestion sécurisée des secrets (fichier .env)
- ✅ Hash des mots de passe admin
- ✅ Validation des téléchargements
- ✅ Logs complets pour audit

---

## 📦 Installation

### Pour les utilisateurs

1. **Télécharge l'installateur**
   ```
   IllamaLauncher_Setup.exe
   ```

2. **Lance l'installateur et suis les instructions**

3. **Premier lancement**
   - Le launcher te guidera à travers la configuration initiale
   - Connecte-toi avec ton compte Microsoft
   - Choisis ta version de Minecraft
   - Le launcher va créer une instance Prism automatiquement

### Pour les développeurs

1. **Clone le repository**
   ```bash
   git clone https://github.com/illama/illama_minecraftlauncher.git
   cd illama_minecraftlauncher
   ```

2. **Crée un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Installe les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure les secrets**
   ```bash
   cp .env.example .env
   # Édite .env et remplis tes clés API
   ```

5. **Lance le launcher**
   ```bash
   python launcher.py
   ```

---

## ⚙️ Configuration

### Fichier `.env`

Le fichier `.env` contient les secrets et configurations sensibles. **Ne jamais le commiter dans Git !**

```bash
# Copie le fichier exemple
cp .env.example .env

# Édite avec tes valeurs
nano .env  # ou notepad .env sur Windows
```

**Variables importantes :**

```env
# Google Drive API
DRIVE_API_KEY=ta_clé_api_google_drive
DRIVE_FOLDER_ID=id_du_dossier_avec_les_mods

# GitHub (pour les mises à jour)
GITHUB_TOKEN=ton_token_github  # Optionnel si repo public

# Admin Password (hash SHA-256)
ADMIN_PASSWORD_HASH=hash_sha256_du_mot_de_passe
```

### Générer un hash de mot de passe admin

```bash
python config_secure.py --generate-hash "ton_mot_de_passe"
```

Copie le hash généré dans `.env` :
```env
ADMIN_PASSWORD_HASH=abc123def456...
```

---

## 🚀 Utilisation

### Lancement rapide

1. **Lance IllamaLauncher.exe**
2. **Première utilisation** : Suis l'assistant de configuration
3. **Synchronisation** : Clique sur "Synchroniser les mods"
4. **Jouer** : Clique sur "Lancer Minecraft"

### Mode Admin

Pour accéder aux fonctionnalités d'administration :

1. Clique sur l'icône ⚙️ en haut à droite
2. Entre le mot de passe admin
3. Tu peux maintenant :
   - Uploader des mods
   - Supprimer des mods
   - Gérer les fichiers

### Logs

Les logs sont automatiquement sauvegardés dans :
```
%LOCALAPPDATA%\IllamaLauncher\logs\
```

- `launcher_YYYYMMDD.log` : Logs normaux
- `errors_YYYYMMDD.log` : Erreurs uniquement

---

## 🛠️ Développement

### Structure du projet

```
illama-launcher/
├── launcher.py              # Code principal (à refactoriser)
├── config_secure.py         # Gestion sécurisée de la config
├── logger_config.py         # Système de logging
├── download_manager.py      # Téléchargements robustes
├── requirements.txt         # Dépendances Python
├── .env.example            # Template de configuration
├── BUILD_LAUNCHER.bat      # Script de build Windows
├── installer.iss           # Configuration Inno Setup
└── README.md               # Ce fichier
```

### Tests

```bash
# Lancer les tests (à implémenter)
pytest tests/

# Avec couverture
pytest --cov=src tests/
```

### Formatage du code

```bash
# Formater avec Black
black launcher.py

# Linter avec Flake8
flake8 launcher.py
```

---

## 📦 Build & Distribution

### Build de l'exécutable

**Windows :**
```bash
# Méthode 1 : Script automatique
BUILD_LAUNCHER.bat

# Méthode 2 : Commande manuelle
python -m PyInstaller --name=IllamaLauncher --onefile --windowed --clean launcher.py
```

L'exécutable sera créé dans `dist/IllamaLauncher.exe`

### Création de l'installateur

1. **Installe Inno Setup**
   - Télécharge depuis : https://jrsoftware.org/isdl.php
   - Installe-le

2. **Build l'installateur**
   ```bash
   BUILD_LAUNCHER.bat
   ```
   
   Ou manuellement :
   ```bash
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```

3. **L'installateur sera créé dans**
   ```
   installer_output/IllamaLauncher_Setup.exe
   ```

### Release sur GitHub

1. **Tag la version**
   ```bash
   git tag -a v2.0.4 -m "Version 2.0.4"
   git push origin v2.0.4
   ```

2. **Crée une release sur GitHub**
   - Upload `IllamaLauncher_Setup.exe`
   - Upload `IllamaLauncher.exe` (version portable)
   - Ajoute les notes de version

---

## 🔧 Dépannage

### Erreur : "DRIVE_API_KEY manquant"
**Solution :** Crée un fichier `.env` à partir de `.env.example` et remplis les valeurs.

### Erreur : "Failed to execute script"
**Solution :** Vérifie que toutes les dépendances sont installées :
```bash
pip install -r requirements.txt
```

### Prism Launcher non détecté
**Solution :** Installe Prism Launcher depuis : https://prismlauncher.org/download/

### Téléchargement des mods échoue
**Solutions :**
1. Vérifie ta connexion internet
2. Vérifie que l'API Google Drive est accessible
3. Consulte les logs dans `%LOCALAPPDATA%\IllamaLauncher\logs\`

### Mods non chargés dans Minecraft
**Solutions :**
1. Vérifie que l'instance Prism est correctement configurée
2. Relance la synchronisation
3. Vérifie la version de Minecraft/Forge

---

## 🤝 Contribution

Les contributions sont les bienvenues !

### Comment contribuer

1. **Fork le projet**
2. **Crée une branche** (`git checkout -b feature/AmazingFeature`)
3. **Commit tes changements** (`git commit -m 'Add AmazingFeature'`)
4. **Push vers la branche** (`git push origin feature/AmazingFeature`)
5. **Ouvre une Pull Request**

### Guidelines

- Utilise Black pour le formatage
- Ajoute des tests pour les nouvelles fonctionnalités
- Mets à jour la documentation
- Respecte le style de code existant

---

## 📝 TODO / Roadmap

### Version 2.1
- [ ] Refactoriser le code en modules séparés
- [ ] Implémenter des tests unitaires
- [ ] Ajouter support de profils multiples
- [ ] Mode hors ligne

### Version 2.2
- [ ] Migration vers CustomTkinter
- [ ] Discord Rich Presence
- [ ] Statistiques de jeu
- [ ] Backup automatique des saves

### Version 3.0
- [ ] Support de Fabric en plus de Forge
- [ ] Interface web (optionnelle)
- [ ] Serveur backend pour analytics
- [ ] Multi-langue (FR/EN)

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👨‍💻 Auteur

**Illama Team**
- GitHub: [@illama](https://github.com/illama)
- Serveur: illama.duckdns.org

---

## 🙏 Remerciements

- [Prism Launcher](https://prismlauncher.org/) pour leur excellent launcher
- [Forge](https://files.minecraftforge.net/) pour le mod loader
- La communauté Minecraft pour les mods

---

## 📞 Support

**Besoin d'aide ?**
- 📧 Email : [ton_email@example.com]
- 💬 Discord : [Lien vers ton Discord]
- 🐛 Issues : [GitHub Issues](https://github.com/illama/illama_minecraftlauncher/issues)

---

<div align="center">

**Fait avec ❤️ pour la communauté Minecraft**

⭐ **N'oublie pas de star le projet si tu l'aimes !** ⭐

</div>

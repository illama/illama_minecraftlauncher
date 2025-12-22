@echo off
REM ========================================
REM Installation automatique Illama Launcher
REM Version 2.0.5 - Quick Wins intégrés
REM ========================================

echo.
echo ========================================
echo   INSTALLATION ILLAMA LAUNCHER v2.0.5
echo ========================================
echo.

REM Vérifier Python
echo [1/4] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo.
    echo Installe Python depuis: https://www.python.org/downloads/
    echo N'oublie pas de cocher "Add Python to PATH" pendant l'installation
    pause
    exit /b 1
)
python --version
echo.

REM Installer les dépendances
echo [2/4] Installation des dependances...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation des dependances
    pause
    exit /b 1
)
echo.

REM Créer .env si n'existe pas
echo [3/4] Configuration...
if not exist .env (
    echo Creation du fichier .env depuis le template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edite le fichier .env avec tes vraies cles API
    echo Utilise: notepad .env
    echo.
) else (
    echo Fichier .env existe deja - OK
)
echo.

REM Test du launcher
echo [4/4] Test du launcher...
echo Lancement de launcher.py en mode test...
timeout /t 2 >nul
python launcher.py --version >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] Le launcher a rencontre une erreur au demarrage
    echo Consulte les logs dans: %LOCALAPPDATA%\IllamaLauncher\logs\
) else (
    echo Launcher OK
)
echo.

echo ========================================
echo   INSTALLATION TERMINEE !
echo ========================================
echo.
echo Prochaines etapes:
echo 1. Edite .env avec tes vraies cles: notepad .env
echo 2. Genere ton mot de passe admin: python admin_password_tool.py
echo 3. Lance le launcher: python launcher.py
echo.
echo Documentation complete dans README.md et QUICK_START.md
echo.

pause

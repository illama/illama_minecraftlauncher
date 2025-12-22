@echo off
echo ========================================
echo   Verification et Rebuild COMPLET
echo ========================================
echo.

:: Vérifier quel fichier launcher est présent
echo [VERIFICATION] Fichiers launcher trouves:
if exist "launcher.py" echo  - launcher.py
if exist "launcher_v5_final.py" echo  - launcher_v5_final.py
if exist "launcher_autoconnect.py" echo  - launcher_autoconnect.py
echo.

:: Déterminer quel fichier utiliser
set LAUNCHER_FILE=
if exist "launcher.py" set LAUNCHER_FILE=launcher.py
if exist "launcher_v5_final.py" set LAUNCHER_FILE=launcher_v5_final.py

if not defined LAUNCHER_FILE (
    echo [ERREUR] Aucun fichier launcher trouve!
    echo Place launcher.py dans ce dossier.
    pause
    exit /b 1
)

echo [INFO] Fichier a compiler: %LAUNCHER_FILE%
echo.

:: Vérifier que le fichier contient les corrections essentielles
echo [VERIFICATION] Verification du contenu de %LAUNCHER_FILE%...
findstr /C:"gc.collect()" %LAUNCHER_FILE% >nul
if errorlevel 1 (
    echo [ERREUR] %LAUNCHER_FILE% ne contient pas la correction gc.collect^(^)
    echo.
    echo IMPORTANT: Ce fichier ne contient pas toutes les corrections!
    echo L'erreur _MEI* va probablement persister.
    echo.
    echo Telecharge le fichier launcher.py corrige ou lance quand meme?
    echo.
    echo Appuie sur une touche pour compiler quand meme...
    echo Ou CTRL+C pour annuler et telecharger le bon fichier.
    pause >nul
) else (
    echo [OK] Correction gc.collect^(^) presente
)
echo.

findstr /C:"sys.exit(0)" %LAUNCHER_FILE% >nul
if errorlevel 1 (
    echo [WARNING] %LAUNCHER_FILE% ne contient pas sys.exit^(0^)
    echo Certaines corrections peuvent manquer.
    echo.
) else (
    echo [OK] Correction sys.exit^(0^) presente
)
echo.

:: Vérifier Python
py --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERREUR] Python non trouve!
        pause
        exit /b 1
    )
    set PYTHON=python
) else (
    set PYTHON=py
)
echo [INFO] Python trouve: %PYTHON%
echo.

:: NETTOYAGE COMPLET
echo ========================================
echo   NETTOYAGE COMPLET
echo ========================================
echo.

echo [1/6] Suppression de build/...
if exist build rmdir /s /q build
echo [OK]

echo [2/6] Suppression de dist/...
if exist dist rmdir /s /q dist
echo [OK]

echo [3/6] Suppression des fichiers .spec...
if exist *.spec del /q *.spec
echo [OK]

echo [4/6] Suppression de __pycache__...
if exist __pycache__ rmdir /s /q __pycache__
echo [OK]

echo [5/6] Nettoyage du cache PyInstaller...
if exist "%LOCALAPPDATA%\pyinstaller" rmdir /s /q "%LOCALAPPDATA%\pyinstaller"
echo [OK]

echo [6/6] Nettoyage des anciens .exe...
if exist "IllamaLauncher.exe" del /q "IllamaLauncher.exe"
if exist "launcher.exe" del /q "launcher.exe"
echo [OK]
echo.

:: INSTALLATION DES DEPENDANCES
echo ========================================
echo   INSTALLATION DEPENDANCES
echo ========================================
echo.
%PYTHON% -m pip install --upgrade pip -q
%PYTHON% -m pip install pyinstaller pystray pillow -q
echo [OK] Dependances installees
echo.

:: COMPILATION
echo ========================================
echo   COMPILATION
echo ========================================
echo.
echo [INFO] Compilation de %LAUNCHER_FILE% avec --clean...
echo [INFO] Cela peut prendre 1-2 minutes...
echo.

%PYTHON% -m PyInstaller --name=IllamaLauncher --onefile --windowed --clean --noconfirm %LAUNCHER_FILE%

if not exist "dist\IllamaLauncher.exe" (
    echo.
    echo [ERREUR] La compilation a echoue!
    echo Verifie les erreurs ci-dessus.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   COMPILATION REUSSIE!
echo ========================================
echo.
echo [OK] Executable cree: dist\IllamaLauncher.exe
echo.

:: Vérifier la taille du fichier
for %%A in ("dist\IllamaLauncher.exe") do set filesize=%%~zA
if %filesize% LSS 20000000 (
    echo [WARNING] Le fichier exe semble petit ^(%filesize% octets^)
    echo.
)

:: Afficher les informations
echo ========================================
echo   INFORMATIONS
echo ========================================
echo.
echo Fichier source: %LAUNCHER_FILE%
echo Fichier compile: dist\IllamaLauncher.exe
for %%A in ("dist\IllamaLauncher.exe") do echo Taille: %%~zA octets
echo.

:: Vérifier les corrections
findstr /C:"gc.collect()" %LAUNCHER_FILE% >nul
if errorlevel 1 (
    echo [WARNING] Ce build ne contient PAS la correction gc.collect^(^)
    echo L'erreur _MEI* va probablement apparaitre!
    echo Telecharge le fichier launcher.py corrige.
    echo.
) else (
    echo [OK] Ce build inclut la correction erreur _MEI*
)

findstr /C:"sys.exit(0)" %LAUNCHER_FILE% >nul
if errorlevel 1 (
    echo [WARNING] Ce build ne contient PAS la correction sys.exit^(0^)
    echo.
) else (
    echo [OK] Ce build inclut toutes les corrections
)
echo.

:: Proposer de créer l'installateur
echo ========================================
echo   CREATION INSTALLATEUR
echo ========================================
echo.

set INNO=
if exist "%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe" set INNO=%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe
if exist "%PROGRAMFILES%\Inno Setup 6\ISCC.exe" set INNO=%PROGRAMFILES%\Inno Setup 6\ISCC.exe

if not defined INNO (
    echo [WARNING] Inno Setup n'est pas installe!
    echo.
    echo Pour creer l'installateur Setup.exe:
    echo 1. Telecharge Inno Setup: https://jrsoftware.org/isdl.php
    echo 2. Installe-le
    echo 3. Relance ce script
    echo.
    echo Pour l'instant, tu peux distribuer: dist\IllamaLauncher.exe
    echo.
    goto skip_installer
)

if not exist "installer.iss" (
    echo [WARNING] Fichier installer.iss non trouve!
    echo L'installateur ne peut pas etre cree sans ce fichier.
    echo.
    echo Tu peux distribuer directement: dist\IllamaLauncher.exe
    echo.
    goto skip_installer
)

echo [INFO] Inno Setup trouve!
echo [INFO] Creation de l'installateur...
echo.

:: Mettre à jour la version si update_version.py existe
if exist "update_version.py" (
    echo [INFO] Mise a jour de la version dans installer.iss...
    %PYTHON% update_version.py
    if errorlevel 1 (
        echo [WARNING] Impossible de mettre a jour la version automatiquement
    )
    echo.
)

:: Créer l'installateur
"%INNO%" installer.iss

if exist "installer_output\IllamaLauncher_Setup.exe" (
    echo.
    echo ========================================
    echo   INSTALLATEUR CREE!
    echo ========================================
    echo.
    echo [OK] Installateur: installer_output\IllamaLauncher_Setup.exe
    for %%A in ("installer_output\IllamaLauncher_Setup.exe") do echo [OK] Taille: %%~zA octets
    echo.
    echo Tu peux maintenant distribuer:
    echo  - installer_output\IllamaLauncher_Setup.exe (RECOMMANDE^)
    echo  - ou dist\IllamaLauncher.exe (portable^)
    echo.
) else (
    echo.
    echo [ERREUR] L'installateur n'a pas ete cree!
    echo Verifie les erreurs ci-dessus.
    echo.
    echo Tu peux distribuer directement: dist\IllamaLauncher.exe
    echo.
)

:skip_installer

echo ========================================
echo   TERMINÉ!
echo ========================================
echo.

:: Afficher les fichiers créés
echo Fichiers crees:
if exist "dist\IllamaLauncher.exe" (
    echo  [X] dist\IllamaLauncher.exe
    for %%A in ("dist\IllamaLauncher.exe") do echo      Taille: %%~zA octets
)
if exist "installer_output\IllamaLauncher_Setup.exe" (
    echo  [X] installer_output\IllamaLauncher_Setup.exe
    for %%A in ("installer_output\IllamaLauncher_Setup.exe") do echo      Taille: %%~zA octets
)
echo.

echo Prochaines etapes:
echo  1. Teste dist\IllamaLauncher.exe
echo  2. Verifie qu'il n'y a PLUS d'erreur _MEI* a la fermeture
if exist "installer_output\IllamaLauncher_Setup.exe" (
    echo  3. Distribue installer_output\IllamaLauncher_Setup.exe
) else (
    echo  3. Distribue dist\IllamaLauncher.exe (ou installe Inno Setup pour creer le Setup)
)
echo.
pause

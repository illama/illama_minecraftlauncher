@echo off
echo ========================================
echo   Build Illama Launcher Installer
echo ========================================
echo.

:: Vérifier Python avec le lanceur py (Windows)
py --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERREUR] Python n'est pas installe!
        echo.
        echo Telecharge Python depuis: https://www.python.org/downloads/
        echo IMPORTANT: Coche "Add Python to PATH" pendant l'installation!
        echo.
        pause
        exit /b 1
    )
    set PYTHON=python
) else (
    set PYTHON=py
)

echo [INFO] Python trouve: %PYTHON%
echo.

echo [0/3] Installation de PyInstaller...
%PYTHON% -m pip install pyinstaller pystray pillow -q
if errorlevel 1 (
    echo [WARNING] Certaines dependances optionnelles n'ont pas pu etre installees
    %PYTHON% -m pip install pyinstaller -q
)

echo [1/3] Creation de l'executable...
%PYTHON% -m PyInstaller --name=IllamaLauncher --onefile --windowed --clean --noconfirm launcher.py

if not exist "dist\IllamaLauncher.exe" (
    echo [ERREUR] La creation de l'executable a echoue!
    pause
    exit /b 1
)

echo.
echo [OK] Executable cree: dist\IllamaLauncher.exe
echo.

:: Vérifier Inno Setup
set INNO=
if exist "%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe" set INNO=%PROGRAMFILES(X86)%\Inno Setup 6\ISCC.exe
if exist "%PROGRAMFILES%\Inno Setup 6\ISCC.exe" set INNO=%PROGRAMFILES%\Inno Setup 6\ISCC.exe

if defined INNO (
    echo [2/3] Creation de l'installateur avec Inno Setup...
    "%INNO%" installer.iss
    echo.
    echo ========================================
    echo   BUILD TERMINE!
    echo ========================================
    echo.
    if exist "installer_output\IllamaLauncher_Setup.exe" (
        echo Installateur cree: installer_output\IllamaLauncher_Setup.exe
        echo.
        echo Tu peux distribuer ce fichier a tes clients!
    )
) else (
    echo [INFO] Inno Setup n'est pas installe.
    echo.
    echo Pour creer l'installateur:
    echo 1. Telecharge Inno Setup: https://jrsoftware.org/isdl.php
    echo 2. Installe-le
    echo 3. Relance BUILD.bat
    echo.
    echo OU distribue directement: dist\IllamaLauncher.exe
)

echo.
pause

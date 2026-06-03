@echo off
chcp 65001 >nul
title Build MailCentPro Windows

echo.
echo ╔══════════════════════════════════════════════╗
echo ║   Build MailCent Pro — Windows              ║
echo ╚══════════════════════════════════════════════╝
echo.

REM ── Python ────────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌  Python introuvable.
    echo.
    echo     Téléchargez Python 3.11+ sur https://www.python.org/downloads/
    echo     Cochez bien "Add Python to PATH" lors de l'installation.
    echo.
    pause
    exit /b 1
)
echo ✅  Python :
python --version
echo.

REM ── Dépendances ───────────────────────────────────────────────────────────
echo 📦  Installation des dépendances...
pip install --quiet --upgrade pip
pip install --quiet PySide6 pyinstaller
if errorlevel 1 (
    echo ❌  Échec installation des dépendances.
    pause
    exit /b 1
)
echo ✅  Dépendances installées.
echo.

REM ── Nettoyage préalable ───────────────────────────────────────────────────
if exist build     rmdir /S /Q build
if exist dist      rmdir /S /Q dist
if exist MailCentPro-Windows.zip del /Q MailCentPro-Windows.zip

REM ── Compilation ───────────────────────────────────────────────────────────
echo 🔨  Compilation (peut prendre 2-3 minutes)...
echo.
python -m PyInstaller mailcentpro.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ❌  Compilation échouée — vérifiez les erreurs ci-dessus.
    pause
    exit /b 1
)

REM ── Dossier data/ vide ────────────────────────────────────────────────────
if not exist "dist\MailCentPro\data" mkdir "dist\MailCentPro\data"
if exist "data\eleves_exemple.csv" copy /Y "data\eleves_exemple.csv" "dist\MailCentPro\data\" >nul

REM ── Archive zip ───────────────────────────────────────────────────────────
echo.
echo 📦  Création de l'archive...
cd dist
powershell -Command "Compress-Archive -Path 'MailCentPro' -DestinationPath '..\MailCentPro-Windows.zip' -Force"
cd ..

if not exist "MailCentPro-Windows.zip" (
    echo ❌  Création du zip échouée.
    pause
    exit /b 1
)

REM ── Nettoyage ─────────────────────────────────────────────────────────────
rmdir /S /Q build >nul 2>&1
rmdir /S /Q dist  >nul 2>&1

echo.
echo ╔══════════════════════════════════════════════╗
echo ║   ✅  Build terminé !                        ║
echo ║                                              ║
echo ║   → MailCentPro-Windows.zip                  ║
echo ║                                              ║
echo ║   Distribution :                             ║
echo ║   1. Envoyer le .zip à l'utilisateur         ║
echo ║   2. Extraire                                ║
echo ║   3. Double-cliquer MailCentPro.exe          ║
echo ╚══════════════════════════════════════════════╝
echo.
pause

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
pip install --quiet PySide6 pyinstaller pyarmor
if errorlevel 1 (
    echo ❌  Échec installation des dépendances.
    pause
    exit /b 1
)
echo ✅  Dépendances installées.
echo.

REM ── Nettoyage préalable ───────────────────────────────────────────────────
if exist build              rmdir /S /Q build
if exist dist               rmdir /S /Q dist
if exist pyarmor_dist       rmdir /S /Q pyarmor_dist
if exist MailCentPro-Windows.zip del /Q MailCentPro-Windows.zip

REM ── Protection PyArmor ────────────────────────────────────────────────────
echo 🔒  Protection du code source...
pyarmor gen -O pyarmor_dist mailcentpro.py
if errorlevel 1 (
    echo ❌  Protection PyArmor échouée.
    pause
    exit /b 1
)

echo import glob, os > _patch_spec.py
echo dirs = sorted(glob.glob("pyarmor_dist/pyarmor_runtime_*")) >> _patch_spec.py
echo rname = os.path.basename(dirs[0]) if dirs else "pyarmor_runtime_0" >> _patch_spec.py
echo txt = open("mailcentpro.spec").read() >> _patch_spec.py
echo txt = txt.replace('["mailcentpro.py"]', '["pyarmor_dist/mailcentpro.py"]') >> _patch_spec.py
echo txt = txt.replace('pathex=[],', 'pathex=["pyarmor_dist"],') >> _patch_spec.py
echo txt = txt.replace('"PySide6.QtCore"', '"' + rname + '", "PySide6.QtCore"') >> _patch_spec.py
echo open("mailcentpro_protected.spec", "w").write(txt) >> _patch_spec.py
python _patch_spec.py
del _patch_spec.py
echo ✅  Code source protégé.
echo.

REM ── Compilation ───────────────────────────────────────────────────────────
echo 🔨  Compilation (peut prendre 2-3 minutes)...
echo.
python -m PyInstaller mailcentpro_protected.spec --clean --noconfirm

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
rmdir /S /Q build             >nul 2>&1
rmdir /S /Q dist              >nul 2>&1
rmdir /S /Q pyarmor_dist      >nul 2>&1
if exist mailcentpro_protected.spec del /Q mailcentpro_protected.spec >nul 2>&1

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

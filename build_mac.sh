#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  build_mac.sh — Génère MailCentPro-Mac.zip
#  Résultat : un .app bundle autonome, aucune installation requise.
#  Taille estimée : ~50-80 MB (zip)
#  Prérequis : macOS 12+, Xcode Command Line Tools
# ─────────────────────────────────────────────────────────────────
set -e
cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Build MailCent Pro — macOS                 ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Python ────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "❌  python3 introuvable."
    echo "    Installez via Homebrew : brew install python3"
    exit 1
fi
echo "✅  $(python3 --version)"

# ── Dépendances ───────────────────────────────────────────────────
echo ""
echo "📦  Installation des dépendances..."
pip3 install --quiet --upgrade pip
pip3 install --quiet PySide6 pyinstaller "pyarmor<8"

# ── Nettoyage préalable ───────────────────────────────────────────
rm -rf build dist pyarmor_dist MailCentPro-Mac.zip

# ── Protection PyArmor ────────────────────────────────────────────
echo ""
echo "🔒  Protection du code source..."
pyarmor obfuscate --output pyarmor_dist mailcentpro.py

python3 - <<'PYEOF'
import os
txt = open("mailcentpro.spec").read()
txt = txt.replace('["mailcentpro.py"]', '["pyarmor_dist/mailcentpro.py"]')
txt = txt.replace('pathex=[],', 'pathex=["pyarmor_dist"],')
txt = txt.replace('"PySide6.QtCore"', '"pytransform", "PySide6.QtCore"')
open("mailcentpro_protected.spec", "w").write(txt)
PYEOF
echo "✅  Code source protégé."

# ── Spec Mac (crée un .app bundle) ────────────────────────────────
# On génère un spec temporaire adapté macOS par-dessus le spec protégé
python3 - <<'PYEOF'
content = open("mailcentpro_protected.spec").read()

# Remplacer COLLECT par BUNDLE pour créer un .app macOS
collect_block = """
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MailCentPro",
)
"""
bundle_block = """
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MailCentPro",
)

app = BUNDLE(
    coll,
    name="MailCentPro.app",
    bundle_identifier="fr.mailcentpro.app",
    info_plist={
        "NSHighResolutionCapable": True,
        "CFBundleShortVersionString": "2.0",
        "LSMinimumSystemVersion": "12.0",
    },
)
"""
content = content.replace(collect_block.strip(), bundle_block.strip())
open("mailcentpro_mac.spec", "w").write(content)
print("Spec macOS généré.")
PYEOF

# ── Compilation ───────────────────────────────────────────────────
echo ""
echo "🔨  Compilation (peut prendre 2-3 minutes)..."
python3 -m PyInstaller mailcentpro_mac.spec --clean --noconfirm
rm -f mailcentpro_mac.spec

# ── Vérification ──────────────────────────────────────────────────
if [ ! -d "dist/MailCentPro.app" ]; then
    echo "❌  Compilation échouée — vérifiez les erreurs ci-dessus."
    exit 1
fi

# ── Dossier data/ à côté du .app ─────────────────────────────────
mkdir -p dist/data
cp -n data/eleves_exemple.csv dist/data/ 2>/dev/null || true

# ── Dossier de distribution ───────────────────────────────────────
mkdir -p dist/MailCentPro-Mac
mv dist/MailCentPro.app dist/MailCentPro-Mac/
mv dist/data              dist/MailCentPro-Mac/

# ── Archive zip ───────────────────────────────────────────────────
echo ""
echo "📦  Création de l'archive..."
cd dist
zip -r "../MailCentPro-Mac.zip" MailCentPro-Mac/
cd ..

SIZE=$(du -sh MailCentPro-Mac.zip | cut -f1)
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅  Build terminé !                        ║"
echo "║                                              ║"
echo "║   → MailCentPro-Mac.zip (${SIZE})                ║"
echo "║                                              ║"
echo "║   Distribution :                             ║"
echo "║   1. Envoyer le .zip à l'utilisateur         ║"
echo "║   2. Extraire                                ║"
echo "║   3. Double-cliquer MailCentPro.app          ║"
echo "║                                              ║"
echo "║   ⚠  Notarisation Apple recommandée          ║"
echo "║      pour éviter le blocage Gatekeeper       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Nettoyage
rm -rf build dist pyarmor_dist mailcentpro_protected.spec

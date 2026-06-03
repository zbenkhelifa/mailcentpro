#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  build_linux.sh — Génère MailCentPro-Linux.zip
#  Résultat : un dossier autonome, aucune installation requise.
#  Taille estimée : ~40-70 MB (zip)
# ─────────────────────────────────────────────────────────────────
set -e
cd "$(dirname "$0")"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Build MailCent Pro — Linux                 ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Python ────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "❌  python3 introuvable. Installez-le : sudo apt install python3 python3-pip"
    exit 1
fi
echo "✅  $(python3 --version)"

# ── Dépendances ───────────────────────────────────────────────────
echo ""
echo "📦  Installation des dépendances..."
pip3 install --quiet --upgrade pip
pip3 install --quiet PySide6 pyinstaller

# ── Nettoyage préalable ───────────────────────────────────────────
rm -rf build dist MailCentPro-Linux.zip

# ── Compilation ───────────────────────────────────────────────────
echo ""
echo "🔨  Compilation (peut prendre 1-2 minutes)..."
python3 -m PyInstaller mailcentpro.spec --clean --noconfirm

# ── Vérification ──────────────────────────────────────────────────
if [ ! -f "dist/MailCentPro/MailCentPro" ]; then
    echo "❌  Compilation échouée — vérifiez les erreurs ci-dessus."
    exit 1
fi

# ── Dossier data/ vide ────────────────────────────────────────────
mkdir -p dist/MailCentPro/data
cp -n data/eleves_exemple.csv dist/MailCentPro/data/ 2>/dev/null || true

# ── Rendre l'exécutable... exécutable ────────────────────────────
chmod +x dist/MailCentPro/MailCentPro

# ── Archive zip ───────────────────────────────────────────────────
echo ""
echo "📦  Création de l'archive..."
cd dist
zip -r "../MailCentPro-Linux.zip" MailCentPro/
cd ..

SIZE=$(du -sh MailCentPro-Linux.zip | cut -f1)
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅  Build terminé !                        ║"
echo "║                                              ║"
echo "║   → MailCentPro-Linux.zip (${SIZE})              ║"
echo "║                                              ║"
echo "║   Distribution :                             ║"
echo "║   1. Envoyer le .zip à l'utilisateur         ║"
echo "║   2. Extraire                                ║"
echo "║   3. Lancer : ./MailCentPro/MailCentPro      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Nettoyage build intermédiaire
rm -rf build dist

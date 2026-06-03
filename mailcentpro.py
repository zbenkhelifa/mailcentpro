#!/usr/bin/env python3
"""MailCent Pro — PySide6 dark/light edition"""

import csv, hashlib, json, os, smtplib, socket, ssl, sys, threading, time
import urllib.error, urllib.request
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QDialog, QFileDialog,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSpinBox,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_FILE  = os.path.join(os.path.dirname(__file__), "config.json")
LICENCE_FILE = os.path.join(os.path.dirname(__file__), ".licence")
SUPABASE_VERIFY_URL = "https://tcexvmzfesnbhfjcgrnz.supabase.co/functions/v1/verifier-licence"

# ── Business logic ────────────────────────────────────────────────────────────

def get_machine_id():
    raw = socket.gethostname() + os.environ.get("USERNAME", "") + os.environ.get("USER", "")
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def verifier_licence(cle: str) -> dict:
    payload = json.dumps({"cle": cle, "machine_id": get_machine_id()}).encode()
    req = urllib.request.Request(
        SUPABASE_VERIFY_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except Exception:
            return {"valide": False, "message": f"Erreur serveur ({e.code})."}
    except Exception as e:
        return {"valide": False, "message": f"Impossible de contacter le serveur : {e}"}

def lire_licence_locale() -> str | None:
    if os.path.exists(LICENCE_FILE):
        with open(LICENCE_FILE, "r") as f:
            return f.read().strip() or None
    return None

def sauver_licence_locale(cle: str):
    with open(LICENCE_FILE, "w") as f:
        f.write(cle.strip())

def build_html(design):
    org     = design.get("org_nom", "Mon Organisation")
    slogan  = design.get("org_slogan", "")
    couleur = design.get("header_couleur", "#1e3a5f")
    message = design.get("message", "")
    boutons = design.get("boutons", [])
    footer  = design.get("footer", "Cordialement")

    if message.strip():
        if design.get("html_mode", False):
            message_html = message
        else:
            lignes = message.replace("\r\n", "\n").split("\n")
            message_html = (
                '<p style="margin:0 0 24px;font-size:15px;color:#555;line-height:1.7;">'
                + "<br>".join(lignes) + "</p>"
            )
    else:
        message_html = ""

    boutons_html = ""
    if boutons:
        rows = ""
        for i, b in enumerate(boutons):
            margin = "0 6px 12px" if i < len(boutons) - 1 else "0 6px"
            rows += f"""
              <tr><td align="center" style="padding:{margin};">
                <a href="{b['url']}" style="display:inline-block;background:{b['couleur']};
                   color:#ffffff;text-decoration:none;padding:14px 28px;border-radius:8px;
                   font-size:14px;font-weight:600;width:220px;text-align:center;box-sizing:border-box;">
                  {b['texte']}
                </a>
              </td></tr>"""
        boutons_html = (
            f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">'
            f'{rows}</table>'
        )

    slogan_html = (
        f'<p style="margin:6px 0 0;color:#a8c4e0;font-size:14px;">{slogan}</p>'
        if slogan.strip() else ""
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:{couleur};padding:32px 40px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;letter-spacing:-0.5px;">{org}</h1>
            {slogan_html}
          </td>
        </tr>
        <tr><td style="padding:36px 40px;">{message_html}{boutons_html}</td></tr>
        <tr>
          <td style="background:#f0f4f8;padding:20px 40px;text-align:center;border-top:1px solid #e8ecf0;">
            <p style="margin:0;font-size:12px;color:#aaa;">{footer}</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

DEFAULT_DESIGN = {
    "org_nom":        "Mon Organisation",
    "org_slogan":     "",
    "header_couleur": "#1e3a5f",
    "message":        "",
    "boutons":        [{"texte": "Accéder à la plateforme", "url": "https://votre-site.fr", "couleur": "#1e3a5f"}],
    "footer":         "Cordialement",
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "smtp_host": "", "smtp_port": "587", "smtp_user": "", "smtp_password": "",
        "smtp_tls": True, "delai": "3", "pause_tous_les": "0", "pause_duree": "30",
        "objet": "Message", "csv_path": "", "email_col": "", "pdf_dir": "", "design": DEFAULT_DESIGN,
        "dark_mode": True,
    }

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def load_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

# ── Stylesheets ───────────────────────────────────────────────────────────────
DARK_STYLE = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #313244;
    background: #1e1e2e;
    border-radius: 0 8px 8px 8px;
    top: -1px;
}
QTabBar::tab {
    background: #181825;
    color: #6c7086;
    padding: 10px 22px;
    border: 1px solid transparent;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #1e1e2e;
    color: #cdd6f4;
    border-color: #313244;
    border-bottom: 1px solid #1e1e2e;
}
QTabBar::tab:hover:!selected { background: #24273a; color: #cdd6f4; }
QLineEdit, QSpinBox {
    background: #2a2b3d;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 7px 11px;
    color: #cdd6f4;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QSpinBox:focus { border-color: #2563eb; }
QLineEdit:read-only { background: #1e1e2e; color: #6c7086; }
QComboBox {
    background: #2a2b3d;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 7px 11px;
    color: #cdd6f4;
}
QComboBox:focus { border-color: #2563eb; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #2a2b3d;
    border: 1px solid #45475a;
    color: #cdd6f4;
    selection-background-color: #2563eb;
    padding: 4px;
}
QTextEdit {
    background: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 8px;
    color: #cdd6f4;
    selection-background-color: #2563eb;
}
QTextEdit:focus { border-color: #2563eb; }
QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    font-weight: 700;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #89b4fa;
    background: #1e1e2e;
}
QCheckBox { color: #cdd6f4; spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 2px solid #585b70;
    background: #2a2b3d;
}
QCheckBox::indicator:checked { background: #2563eb; border-color: #2563eb; }
QCheckBox::indicator:hover { border-color: #2563eb; }
QProgressBar {
    background: #313244;
    border-radius: 5px;
    border: none;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #7c3aed);
    border-radius: 5px;
}
QScrollBar:vertical {
    background: #1e1e2e; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical { background: #45475a; border-radius: 4px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #1e1e2e; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #45475a; border-radius: 4px; min-width: 24px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QLabel { color: #cdd6f4; }
QMessageBox { background: #2a2b3d; }
QMessageBox QLabel { color: #cdd6f4; }
QPushButton { min-height: 32px; border-radius: 6px; border: none; font-weight: 600; }
"""

LIGHT_STYLE = """
QWidget {
    background-color: #f5f5f5;
    color: #1f2937;
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #d1d5db;
    background: #f5f5f5;
    border-radius: 0 8px 8px 8px;
    top: -1px;
}
QTabBar::tab {
    background: #e5e7eb;
    color: #6b7280;
    padding: 10px 22px;
    border: 1px solid transparent;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #f5f5f5;
    color: #1f2937;
    border-color: #d1d5db;
    border-bottom: 1px solid #f5f5f5;
}
QTabBar::tab:hover:!selected { background: #dde1e7; color: #1f2937; }
QLineEdit, QSpinBox {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 7px 11px;
    color: #1f2937;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QSpinBox:focus { border-color: #2563eb; }
QLineEdit:read-only { background: #f0f2f5; color: #9ca3af; }
QComboBox {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 7px 11px;
    color: #1f2937;
}
QComboBox:focus { border-color: #2563eb; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d1d5db;
    color: #1f2937;
    selection-background-color: #2563eb;
    padding: 4px;
}
QTextEdit {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 8px;
    color: #1f2937;
    selection-background-color: #2563eb;
}
QTextEdit:focus { border-color: #2563eb; }
QGroupBox {
    border: 1px solid #d1d5db;
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    font-weight: 700;
    color: #2563eb;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #2563eb;
    background: #f5f5f5;
}
QCheckBox { color: #1f2937; spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 2px solid #d1d5db;
    background: #ffffff;
}
QCheckBox::indicator:checked { background: #2563eb; border-color: #2563eb; }
QCheckBox::indicator:hover { border-color: #2563eb; }
QProgressBar {
    background: #e5e7eb;
    border-radius: 5px;
    border: none;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #7c3aed);
    border-radius: 5px;
}
QScrollBar:vertical {
    background: #f5f5f5; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical { background: #d1d5db; border-radius: 4px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #9ca3af; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #f5f5f5; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #d1d5db; border-radius: 4px; min-width: 24px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QLabel { color: #1f2937; }
QMessageBox { background: #ffffff; }
QMessageBox QLabel { color: #1f2937; }
QPushButton { min-height: 32px; border-radius: 6px; border: none; font-weight: 600; }
"""

# Couleurs spécifiques aux widgets avec style inline, par thème
_DARK = {
    "header_bg":     "#181825",
    "header_border": "#313244",
    "logo_color":    "#cdd6f4",
    "ver_color":     "#45475a",
    "scroll_bg":     "#1e1e2e",
    "log_bg":        "#11111b",
    "log_border":    "#313244",
    "muted":         "#a6adc8",
    "dim":           "#45475a",
    "dim2":          "#6c7086",
    "accent":        "#89b4fa",
    "btn_sec":       ("#2e2e42", "#3a3a52", "#a6adc8"),
    "btn_dis_bg":    "#313244",
    "btn_dis_fg":    "#6c7086",
    "rm_normal":     "background: #2e1a1a; color: #f38ba8;",
    "rm_hover":      "background: #dc2626; color: white;",
    "swatch_border": "#45475a",
    "html_bg":       "#11111b",
    "html_color":    "#cdd6f4",
    "log_colors":    {
        "INFO": "#a6adc8", "OK": "#a6e3a1",
        "ERR": "#f38ba8", "WARN": "#f9e2af", "START": "#89b4fa",
    },
}

_LIGHT = {
    "header_bg":     "#ffffff",
    "header_border": "#e5e7eb",
    "logo_color":    "#1f2937",
    "ver_color":     "#9ca3af",
    "scroll_bg":     "#f5f5f5",
    "log_bg":        "#f8fafc",
    "log_border":    "#e5e7eb",
    "muted":         "#374151",
    "dim":           "#6b7280",
    "dim2":          "#6b7280",
    "accent":        "#2563eb",
    "btn_sec":       ("#e5e7eb", "#d1d5db", "#374151"),
    "btn_dis_bg":    "#e5e7eb",
    "btn_dis_fg":    "#9ca3af",
    "rm_normal":     "background: #fee2e2; color: #dc2626;",
    "rm_hover":      "background: #dc2626; color: white;",
    "swatch_border": "#d1d5db",
    "html_bg":       "#f8fafc",
    "html_color":    "#1f2937",
    "log_colors":    {
        "INFO": "#6b7280", "OK": "#16a34a",
        "ERR": "#dc2626", "WARN": "#b45309", "START": "#2563eb",
    },
}

# ── Cross-thread signals ──────────────────────────────────────────────────────
class Signals(QObject):
    log_append      = Signal(str, str)
    progress_update = Signal(int, int)
    send_finished   = Signal(int, int, list, list)
    smtp_test_ok    = Signal()
    smtp_test_err   = Signal(str)
    lic_valid       = Signal(str)
    lic_invalid     = Signal(str)
    lic_offline     = Signal()


# ── Activation dialog ─────────────────────────────────────────────────────────
class ActivationDialog(QDialog):
    on_activated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sig = Signals()
        self._sig.lic_valid.connect(self._on_valid)
        self._sig.lic_invalid.connect(self._on_invalid)
        self.setWindowTitle("Activation — MailCent Pro")
        self.setFixedSize(480, 310)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        bar = QWidget()
        bar.setFixedHeight(6)
        bar.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #7c3aed);")
        root.addWidget(bar)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setSpacing(14)
        bl.setContentsMargins(44, 30, 44, 30)
        root.addWidget(body)

        title = QLabel("🔑  Activation de l'application")
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        title.setAlignment(Qt.AlignCenter)
        bl.addWidget(title)

        hint = QLabel("Saisissez votre clé de licence\n(format : ENVOI-XXXX-XXXX-XXXX)")
        hint.setStyleSheet("font-size: 12px;")
        hint.setAlignment(Qt.AlignCenter)
        bl.addWidget(hint)

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("ENVOI-XXXX-XXXX-XXXX")
        self._key_input.setAlignment(Qt.AlignCenter)
        self._key_input.setStyleSheet(
            "font-size: 15px; font-family: 'Courier New', monospace; "
            "letter-spacing: 2px; padding: 10px; border-radius: 8px;")
        self._key_input.returnPressed.connect(self._activate)
        bl.addWidget(self._key_input)

        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet("font-size: 13px; min-height: 18px;")
        bl.addWidget(self._status)

        self._btn = QPushButton("Activer")
        self._btn.setFixedHeight(44)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2563eb,stop:1 #7c3aed);
                color: white; border-radius: 8px; font-size: 14px; font-weight: 700;
            }
            QPushButton:hover { background: #1d4ed8; }
            QPushButton:disabled { opacity: 0.5; }
        """)
        self._btn.clicked.connect(self._activate)
        bl.addWidget(self._btn)

        contact = QLabel("Pour obtenir une licence : codeappli09@gmail.com")
        contact.setStyleSheet("font-size: 11px;")
        contact.setAlignment(Qt.AlignCenter)
        bl.addWidget(contact)

    def _activate(self):
        cle = self._key_input.text().strip().upper()
        if not cle:
            self._status.setText("Veuillez saisir une clé.")
            self._status.setStyleSheet("color: #f38ba8; font-size: 13px;")
            return
        self._btn.setEnabled(False)
        self._btn.setText("Vérification...")
        self._status.setText("Connexion au serveur...")
        self._status.setStyleSheet("font-size: 13px;")
        sig = self._sig

        def _do():
            result = verifier_licence(cle)
            if result.get("valide"):
                sauver_licence_locale(cle)
                sig.lic_valid.emit(result.get("client_nom", ""))
            else:
                sig.lic_invalid.emit(result.get("message", "Clé invalide."))

        threading.Thread(target=_do, daemon=True).start()

    def _on_valid(self, client_nom):
        self._status.setText(f"✅  Activé — Bienvenue, {client_nom} !")
        self._status.setStyleSheet("color: #a6e3a1; font-size: 13px;")
        QTimer.singleShot(1200, lambda: [self.accept(), self.on_activated.emit()])

    def _on_invalid(self, msg):
        self._btn.setEnabled(True)
        self._btn.setText("Activer")
        self._status.setText(f"❌  {msg}")
        self._status.setStyleSheet("color: #f38ba8; font-size: 13px;")


# ── Main application ──────────────────────────────────────────────────────────
class App(QMainWindow):

    _BTN_CONFIGS = {
        "primary":   ("#2563eb", "#1d4ed8", "#fff"),
        "danger":    ("#dc2626", "#b91c1c", "#fff"),
        "success":   ("#16a34a", "#15803d", "#fff"),
    }

    _LOG_ICONS = {
        "INFO": "ℹ", "OK": "✅", "ERR": "❌", "WARN": "⚠", "START": "🚀",
    }

    def __init__(self):
        super().__init__()
        self.cfg          = load_config()
        self._dark_mode   = self.cfg.get("dark_mode", True)
        self._stop_flag   = False
        self._sending     = False
        self._boutons     = []
        self._sig         = Signals()
        self._themed_widgets = []   # list of (widget, fn) where fn(colors) -> style str
        self._secondary_btns = []   # secondary buttons to re-style on theme change
        self._connect_signals()
        self._build_ui()
        self._apply_theme(self._dark_mode)
        self._lock_ui()
        QTimer.singleShot(200, self._check_licence)

    # ── Signals ───────────────────────────────────────────────────────────────

    def _connect_signals(self):
        self._sig.log_append.connect(self._do_log)
        self._sig.progress_update.connect(self._do_progress)
        self._sig.send_finished.connect(self._do_send_finished)
        self._sig.smtp_test_ok.connect(self._on_smtp_ok)
        self._sig.smtp_test_err.connect(self._on_smtp_err)

    def _on_smtp_ok(self):
        self._do_log("Connexion SMTP réussie ✔", "OK")
        QMessageBox.information(self, "Succès", "Connexion SMTP réussie !")

    def _on_smtp_err(self, msg):
        self._do_log(f"Échec connexion : {msg}", "ERR")
        QMessageBox.critical(self, "Erreur SMTP", f"Connexion échouée :\n{msg}")

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        self._apply_theme(not self._dark_mode)
        self.cfg["dark_mode"] = self._dark_mode
        save_config(self.cfg)

    def _apply_theme(self, dark: bool):
        self._dark_mode = dark
        c = _DARK if dark else _LIGHT
        QApplication.instance().setStyleSheet(DARK_STYLE if dark else LIGHT_STYLE)

        # Header
        self._header_widget.setStyleSheet(
            f"background: {c['header_bg']}; border-bottom: 1px solid {c['header_border']};")
        self._logo_lbl.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {c['logo_color']}; background: transparent;")
        self._ver_lbl.setStyleSheet(
            f"color: {c['ver_color']}; font-size: 12px; background: transparent;")
        self._theme_btn.setText("☀  Clair" if dark else "🌙  Sombre")
        self._theme_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {c['ver_color']}; "
            f"border: 1px solid {c['header_border']}; border-radius: 6px; "
            f"padding: 4px 10px; font-size: 12px; min-height: 26px; }}"
            f"QPushButton:hover {{ background: {c['header_border']}; }}"
        )

        # Design tab scroll area
        self._design_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: {c['scroll_bg']}; }}")
        self._design_inner.setStyleSheet(f"background: {c['scroll_bg']};")

        # Log tab
        self._log_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {c['log_bg']};
                border: 1px solid {c['log_border']};
                border-radius: 8px;
                font-family: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", monospace;
                font-size: 12px;
                padding: 10px;
            }}
        """)

        # Generic themed widgets
        for widget, style_fn in self._themed_widgets:
            widget.setStyleSheet(style_fn(c))

        # Secondary buttons
        bg, bg_h, fg = c["btn_sec"]
        dis_bg, dis_fg = c["btn_dis_bg"], c["btn_dis_fg"]
        sec_style = (
            f"QPushButton {{ background: {bg}; color: {fg}; border: none; border-radius: 6px; "
            f"padding: 8px 16px; font-weight: 600; font-size: 13px; min-height: 32px; }}"
            f"QPushButton:hover {{ background: {bg_h}; }}"
            f"QPushButton:pressed {{ background: {bg_h}; }}"
            f"QPushButton:disabled {{ background: {dis_bg}; color: {dis_fg}; }}"
        )
        for btn in self._secondary_btns:
            btn.setStyleSheet(sec_style)

        # Bouton-row rm buttons
        for entry in self._boutons:
            if "rm" in entry:
                entry["rm"].setStyleSheet(
                    f"QPushButton {{ {c['rm_normal']} border-radius: 4px; font-weight: 700; }}"
                    f"QPushButton:hover {{ {c['rm_hover']} }}"
                )
            if "swatch" in entry:
                entry["swatch"].setStyleSheet(
                    f"background: {entry['couleur']}; border-radius: 4px; "
                    f"border: 1px solid {c['swatch_border']};"
                )

        # Log colors
        self._LOG_COLORS = c["log_colors"]

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("MailCent Pro")
        self.setMinimumSize(880, 700)
        self.resize(960, 760)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QWidget()
        header.setFixedHeight(56)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        logo = QLabel("MailCent <span style='color:#2563eb;'>Pro</span>")
        logo.setTextFormat(Qt.RichText)
        hl.addWidget(logo)
        hl.addStretch()
        ver = QLabel("v2.0")
        hl.addWidget(ver)
        hl.addSpacing(12)
        self._theme_btn = QPushButton("☀  Clair")
        self._theme_btn.setCursor(Qt.PointingHandCursor)
        self._theme_btn.clicked.connect(self._toggle_theme)
        hl.addWidget(self._theme_btn)
        root.addWidget(header)
        self._header_widget = header
        self._logo_lbl = logo
        self._ver_lbl = ver

        # Loading label (shown while checking licence)
        self._loading_lbl = QLabel("Vérification de la licence...")
        self._loading_lbl.setAlignment(Qt.AlignCenter)
        self._themed_widgets.append(
            (self._loading_lbl, lambda c: f"color: {c['dim']}; font-size: 14px;"))
        root.addWidget(self._loading_lbl, 1)

        # Tabs (hidden until licence validated)
        self._tabs_wrapper = QWidget()
        tl = QVBoxLayout(self._tabs_wrapper)
        tl.setContentsMargins(12, 12, 12, 12)
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        tl.addWidget(self._tabs)
        root.addWidget(self._tabs_wrapper, 1)

        self._tab_config = QWidget()
        self._tab_design = QWidget()
        self._tab_envoi  = QWidget()
        self._tab_log    = QWidget()

        self._tabs.addTab(self._tab_config, "⚙  Configuration")
        self._tabs.addTab(self._tab_design, "🎨  Design email")
        self._tabs.addTab(self._tab_envoi,  "📤  Envoi")
        self._tabs.addTab(self._tab_log,    "📋  Log")

        self._build_tab_config()
        self._build_tab_design()
        self._build_tab_envoi()
        self._build_tab_log()

    # ── Tab: Configuration ────────────────────────────────────────────────────

    def _build_tab_config(self):
        layout = QVBoxLayout(self._tab_config)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        smtp_grp = QGroupBox("Serveur SMTP")
        sg = QVBoxLayout(smtp_grp)
        sg.setSpacing(8)

        self._smtp_inputs = {}
        for label, key, secret in [
            ("Hôte SMTP",    "smtp_host",     False),
            ("Port",         "smtp_port",     False),
            ("Utilisateur",  "smtp_user",     False),
            ("Mot de passe", "smtp_password", True),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label + " :")
            lbl.setFixedWidth(130)
            self._themed_widgets.append((lbl, lambda c: f"color: {c['muted']};"))
            inp = QLineEdit()
            if secret:
                inp.setEchoMode(QLineEdit.Password)
            self._smtp_inputs[key] = inp
            row.addWidget(lbl)
            row.addWidget(inp)
            sg.addLayout(row)

        tls_row = QHBoxLayout()
        lbl_tls = QLabel("Sécurité :")
        lbl_tls.setFixedWidth(130)
        self._themed_widgets.append((lbl_tls, lambda c: f"color: {c['muted']};"))
        self._tls_check = QCheckBox("Utiliser TLS (STARTTLS)")
        tls_row.addWidget(lbl_tls)
        tls_row.addWidget(self._tls_check)
        tls_row.addStretch()
        sg.addLayout(tls_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addWidget(self._mk_btn("💾  Sauvegarder", self._save_config, "success"))
        btn_row.addWidget(self._mk_btn("🔌  Tester la connexion", self._test_smtp))
        btn_row.addStretch()
        sg.addLayout(btn_row)
        layout.addWidget(smtp_grp)

        opt_grp = QGroupBox("Options d'envoi")
        ol = QHBoxLayout(opt_grp)
        ol.setSpacing(10)
        lbl_d = QLabel("Délai entre envois :")
        self._themed_widgets.append((lbl_d, lambda c: f"color: {c['muted']};"))
        ol.addWidget(lbl_d)
        self._delai_spin = QSpinBox()
        self._delai_spin.setRange(1, 30)
        self._delai_spin.setValue(3)
        self._delai_spin.setFixedWidth(72)
        ol.addWidget(self._delai_spin)
        hint_d = QLabel("s  ·")
        self._themed_widgets.append((hint_d, lambda c: f"color: {c['dim']}; font-size: 12px;"))
        ol.addWidget(hint_d)

        lbl_p = QLabel("Pause de")
        self._themed_widgets.append((lbl_p, lambda c: f"color: {c['muted']};"))
        ol.addWidget(lbl_p)
        self._pause_duree_spin = QSpinBox()
        self._pause_duree_spin.setRange(1, 300)
        self._pause_duree_spin.setValue(30)
        self._pause_duree_spin.setFixedWidth(72)
        ol.addWidget(self._pause_duree_spin)
        lbl_p2 = QLabel("s  tous les")
        self._themed_widgets.append((lbl_p2, lambda c: f"color: {c['muted']};"))
        ol.addWidget(lbl_p2)
        self._pause_tous_les_spin = QSpinBox()
        self._pause_tous_les_spin.setRange(0, 500)
        self._pause_tous_les_spin.setValue(0)
        self._pause_tous_les_spin.setFixedWidth(72)
        self._pause_tous_les_spin.setSpecialValueText("désactivé")
        ol.addWidget(self._pause_tous_les_spin)
        hint_p = QLabel("envois  (0 = désactivé)")
        self._themed_widgets.append((hint_p, lambda c: f"color: {c['dim']}; font-size: 12px;"))
        ol.addWidget(hint_p)
        ol.addStretch()
        layout.addWidget(opt_grp)
        layout.addStretch()

    # ── Tab: Design ───────────────────────────────────────────────────────────

    def _build_tab_design(self):
        outer = QVBoxLayout(self._tab_design)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        outer.addWidget(scroll)
        self._design_scroll = scroll

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(12)
        scroll.setWidget(inner)
        self._design_inner = inner

        # Identity
        id_grp = QGroupBox("Identité")
        il = QVBoxLayout(id_grp)
        il.setSpacing(8)
        self._dv = {}
        for label, key in [("Nom organisation :", "org_nom"), ("Slogan (optionnel) :", "org_slogan")]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(160)
            self._themed_widgets.append((lbl, lambda c: f"color: {c['muted']};"))
            inp = QLineEdit()
            self._dv[key] = inp
            row.addWidget(lbl)
            row.addWidget(inp)
            il.addLayout(row)

        color_row = QHBoxLayout()
        lbl_c = QLabel("Couleur header :")
        lbl_c.setFixedWidth(160)
        self._themed_widgets.append((lbl_c, lambda c: f"color: {c['muted']};"))
        self._header_color_inp = QLineEdit()
        self._header_color_inp.setFixedWidth(90)
        self._header_color_inp.setText("#1e3a5f")
        self._header_color_inp.textChanged.connect(self._update_color_swatch)
        self._header_swatch = QPushButton()
        self._header_swatch.setFixedSize(32, 32)
        self._header_swatch.setCursor(Qt.PointingHandCursor)
        self._header_swatch.clicked.connect(self._pick_header_color)
        color_row.addWidget(lbl_c)
        color_row.addWidget(self._header_color_inp)
        color_row.addWidget(self._header_swatch)
        color_row.addStretch()
        il.addLayout(color_row)
        layout.addWidget(id_grp)

        # Message
        msg_grp = QGroupBox("Message")
        ml = QVBoxLayout(msg_grp)
        ml.setSpacing(6)
        hint_row = QHBoxLayout()
        self._lbl_hint = QLabel(
            "Corps du mail. Utilisez {colonne} pour insérer une valeur du CSV.")
        self._themed_widgets.append(
            (self._lbl_hint, lambda c: f"color: {c['dim2']}; font-size: 12px;"))
        hint_row.addWidget(self._lbl_hint)
        hint_row.addStretch()
        self._html_check = QCheckBox("Mode HTML")
        self._themed_widgets.append(
            (self._html_check, lambda c: f"font-weight: 700; color: {c['accent']};"))
        self._html_check.toggled.connect(self._toggle_html_mode)
        hint_row.addWidget(self._html_check)
        ml.addLayout(hint_row)
        self._msg_edit = QTextEdit()
        self._msg_edit.setMinimumHeight(130)
        ml.addWidget(self._msg_edit)
        self._lbl_cols = QLabel("Chargez un CSV pour voir les variables disponibles.")
        self._themed_widgets.append(
            (self._lbl_cols, lambda c: f"color: {c['dim']}; font-size: 11px;"))
        ml.addWidget(self._lbl_cols)
        layout.addWidget(msg_grp)

        # Boutons
        btn_grp = QGroupBox("Boutons")
        self._btn_grp_layout = QVBoxLayout(btn_grp)
        self._btn_grp_layout.setSpacing(6)
        hint_b = QLabel("Ajoutez jusqu'à 4 boutons (liens) dans le mail.")
        self._themed_widgets.append(
            (hint_b, lambda c: f"color: {c['dim2']}; font-size: 12px;"))
        self._btn_grp_layout.addWidget(hint_b)
        self._bouton_rows_container = QWidget()
        self._bouton_rows_container.setStyleSheet("background: transparent;")
        self._bouton_rows_layout = QVBoxLayout(self._bouton_rows_container)
        self._bouton_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._bouton_rows_layout.setSpacing(4)
        self._btn_grp_layout.addWidget(self._bouton_rows_container)
        add_b = self._mk_btn("+ Ajouter un bouton", self._add_bouton_row, "success")
        add_b.setFixedWidth(180)
        self._btn_grp_layout.addWidget(add_b)
        layout.addWidget(btn_grp)

        # Footer
        foot_grp = QGroupBox("Pied de mail")
        fl = QHBoxLayout(foot_grp)
        fl.setSpacing(8)
        lbl_f = QLabel("Texte footer :")
        lbl_f.setFixedWidth(130)
        self._themed_widgets.append((lbl_f, lambda c: f"color: {c['muted']};"))
        self._dv["footer"] = QLineEdit()
        fl.addWidget(lbl_f)
        fl.addWidget(self._dv["footer"])
        layout.addWidget(foot_grp)

        prev = self._mk_btn("👁  Aperçu du mail (HTML)", self._preview_html)
        prev.setFixedWidth(240)
        layout.addWidget(prev, alignment=Qt.AlignCenter)

    # ── Tab: Envoi ────────────────────────────────────────────────────────────

    def _build_tab_envoi(self):
        layout = QVBoxLayout(self._tab_envoi)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # CSV
        csv_grp = QGroupBox("Fichier destinataires (CSV)")
        cl = QVBoxLayout(csv_grp)
        cl.setSpacing(8)
        r1 = QHBoxLayout()
        self._csv_input = QLineEdit()
        self._csv_input.setReadOnly(True)
        self._csv_input.setPlaceholderText("Aucun fichier sélectionné...")
        r1.addWidget(self._csv_input)
        b_csv = self._mk_btn("📂  Parcourir", self._browse_csv, "secondary")
        b_csv.setFixedWidth(130)
        r1.addWidget(b_csv)
        cl.addLayout(r1)
        self._lbl_count = QLabel("")
        self._lbl_count.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        cl.addWidget(self._lbl_count)
        r2 = QHBoxLayout()
        lbl_ec = QLabel("Colonne email :")
        lbl_ec.setFixedWidth(120)
        self._themed_widgets.append((lbl_ec, lambda c: f"color: {c['muted']};"))
        self._email_col_combo = QComboBox()
        self._email_col_combo.setFixedWidth(200)
        r2.addWidget(lbl_ec)
        r2.addWidget(self._email_col_combo)
        r2.addStretch()
        cl.addLayout(r2)
        layout.addWidget(csv_grp)

        # Objet
        subj_grp = QGroupBox("Objet du mail")
        sl = QHBoxLayout(subj_grp)
        lbl_s = QLabel("Objet :")
        lbl_s.setFixedWidth(60)
        self._themed_widgets.append((lbl_s, lambda c: f"color: {c['muted']};"))
        self._objet_input = QLineEdit()
        sl.addWidget(lbl_s)
        sl.addWidget(self._objet_input)
        layout.addWidget(subj_grp)

        # PDF
        pdf_grp = QGroupBox("Fichiers PDF à joindre (optionnel)")
        pl = QVBoxLayout(pdf_grp)
        pl.setSpacing(6)
        hint_p = QLabel(
            "Nommez les PDF : Prenom_Nom.pdf, Nom_Prenom.pdf ou email.pdf — correspondance automatique.")
        self._themed_widgets.append(
            (hint_p, lambda c: f"color: {c['dim2']}; font-size: 12px;"))
        pl.addWidget(hint_p)
        rp = QHBoxLayout()
        self._pdf_dir_input = QLineEdit()
        self._pdf_dir_input.setReadOnly(True)
        self._pdf_dir_input.setPlaceholderText("Aucun dossier sélectionné...")
        rp.addWidget(self._pdf_dir_input)
        b_pdf = self._mk_btn("📂  Dossier", self._browse_pdf_dir, "secondary")
        b_pdf.setFixedWidth(120)
        rp.addWidget(b_pdf)
        pl.addLayout(rp)
        self._lbl_pdf = QLabel("Aucun dossier sélectionné.")
        self._themed_widgets.append(
            (self._lbl_pdf, lambda c: f"color: {c['dim']}; font-size: 12px;"))
        pl.addWidget(self._lbl_pdf)
        layout.addWidget(pdf_grp)

        # Design info
        d_grp = QGroupBox("Design utilisé")
        dl = QHBoxLayout(d_grp)
        info = QLabel("Le mail sera envoyé avec le design configuré dans l'onglet 🎨 Design email.")
        self._themed_widgets.append((info, lambda c: f"color: {c['muted']};"))
        prev2 = self._mk_btn("👁  Aperçu avant envoi", self._preview_html, "secondary")
        dl.addWidget(info)
        dl.addStretch()
        dl.addWidget(prev2)
        layout.addWidget(d_grp)

        self._progress = QProgressBar()
        self._progress.setFixedHeight(10)
        self._progress.setValue(0)
        layout.addWidget(self._progress)
        self._lbl_progress = QLabel("")
        self._lbl_progress.setAlignment(Qt.AlignCenter)
        self._themed_widgets.append(
            (self._lbl_progress, lambda c: f"color: {c['dim2']}; font-size: 12px;"))
        layout.addWidget(self._lbl_progress)

        send_row = QHBoxLayout()
        send_row.setSpacing(10)
        self._btn_send = self._mk_btn("🚀  Lancer l'envoi", self._start_send)
        self._btn_send.setFixedWidth(180)
        self._btn_stop = self._mk_btn("⛔  Arrêter", self._stop_send, "danger")
        self._btn_stop.setFixedWidth(140)
        self._btn_stop.setEnabled(False)
        send_row.addStretch()
        send_row.addWidget(self._btn_send)
        send_row.addWidget(self._btn_stop)
        send_row.addStretch()
        layout.addLayout(send_row)
        layout.addStretch()

    # ── Tab: Log ──────────────────────────────────────────────────────────────

    def _build_tab_log(self):
        layout = QVBoxLayout(self._tab_log)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self._log_edit = QTextEdit()
        self._log_edit.setReadOnly(True)
        layout.addWidget(self._log_edit, 1)
        br = QHBoxLayout()
        br.setSpacing(8)
        br.addStretch()
        br.addWidget(self._mk_btn("🗑  Effacer le log", self._clear_log, "secondary"))
        br.addWidget(self._mk_btn("💾  Exporter le log", self._export_log, "success"))
        br.addStretch()
        layout.addLayout(br)

    # ── Button factory ────────────────────────────────────────────────────────

    def _mk_btn(self, text, callback, type_="primary"):
        if type_ == "secondary":
            c = _DARK if self._dark_mode else _LIGHT
            bg, bg_h, fg = c["btn_sec"]
            dis_bg, dis_fg = c["btn_dis_bg"], c["btn_dis_fg"]
        else:
            bg, bg_h, fg = self._BTN_CONFIGS.get(type_, self._BTN_CONFIGS["primary"])
            dis_bg, dis_fg = "#313244", "#6c7086"
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg}; color: {fg};
                border: none; border-radius: 6px;
                padding: 8px 16px; font-weight: 600; font-size: 13px; min-height: 32px;
            }}
            QPushButton:hover {{ background: {bg_h}; }}
            QPushButton:pressed {{ background: {bg_h}; }}
            QPushButton:disabled {{ background: {dis_bg}; color: {dis_fg}; }}
        """)
        if type_ == "secondary":
            self._secondary_btns.append(btn)
        return btn

    # ── Licence ───────────────────────────────────────────────────────────────

    def _lock_ui(self):
        self._tabs_wrapper.hide()
        self._loading_lbl.show()

    def _unlock_ui(self):
        self._loading_lbl.hide()
        self._tabs_wrapper.show()
        self._load_fields()

    def _check_licence(self):
        cle = lire_licence_locale()
        if not cle:
            self._show_activation()
            return

        sig = self._sig
        sig.lic_valid.connect(lambda _: self._unlock_ui(), Qt.ConnectionType.SingleShotConnection)
        sig.lic_offline.connect(self._unlock_ui, Qt.ConnectionType.SingleShotConnection)
        sig.lic_invalid.connect(self._on_licence_revoked, Qt.ConnectionType.SingleShotConnection)

        def _do():
            result = verifier_licence(cle)
            if result.get("valide"):
                sig.lic_valid.emit(result.get("client_nom", ""))
            elif "Impossible de contacter" in result.get("message", ""):
                sig.lic_offline.emit()
            else:
                sig.lic_invalid.emit(result.get("message", "Licence invalide."))

        threading.Thread(target=_do, daemon=True).start()

    def _on_licence_revoked(self, msg):
        if os.path.exists(LICENCE_FILE):
            os.remove(LICENCE_FILE)
        QMessageBox.critical(self, "Licence invalide",
                             f"{msg}\n\nVeuillez entrer une nouvelle clé.")
        self._show_activation()

    def _show_activation(self):
        dlg = ActivationDialog(self)
        dlg.on_activated.connect(self._unlock_ui)
        dlg.exec()

    # ── Load / collect ────────────────────────────────────────────────────────

    def _load_fields(self):
        for key, inp in self._smtp_inputs.items():
            inp.setText(str(self.cfg.get(key, "")))
        self._tls_check.setChecked(self.cfg.get("smtp_tls", True))
        self._delai_spin.setValue(int(self.cfg.get("delai", 3)))
        self._pause_tous_les_spin.setValue(int(self.cfg.get("pause_tous_les", 0)))
        self._pause_duree_spin.setValue(int(self.cfg.get("pause_duree", 30)))
        self._csv_input.setText(self.cfg.get("csv_path", ""))
        self._objet_input.setText(self.cfg.get("objet", "Message"))

        pdf_dir = self.cfg.get("pdf_dir", "")
        self._pdf_dir_input.setText(pdf_dir)
        if pdf_dir:
            self._update_pdf_count()

        d = self.cfg.get("design", DEFAULT_DESIGN)
        self._dv["org_nom"].setText(d.get("org_nom", ""))
        self._dv["org_slogan"].setText(d.get("org_slogan", ""))
        self._dv["footer"].setText(d.get("footer", "Cordialement"))
        couleur = d.get("header_couleur", "#1e3a5f")
        self._header_color_inp.setText(couleur)
        c = _DARK if self._dark_mode else _LIGHT
        self._header_swatch.setStyleSheet(
            f"background: {couleur}; border-radius: 4px; border: 1px solid {c['swatch_border']};")
        self._msg_edit.setPlainText(d.get("message", ""))
        self._html_check.setChecked(d.get("html_mode", False))
        for b in d.get("boutons", []):
            self._add_bouton_row(b.get("texte", ""), b.get("url", ""), b.get("couleur", "#1e3a5f"))

        if self.cfg.get("csv_path"):
            self._update_count()

    def _collect_config(self):
        for key, inp in self._smtp_inputs.items():
            self.cfg[key] = inp.text().strip()
        self.cfg["smtp_tls"]  = self._tls_check.isChecked()
        self.cfg["delai"]          = str(self._delai_spin.value())
        self.cfg["pause_tous_les"] = str(self._pause_tous_les_spin.value())
        self.cfg["pause_duree"]    = str(self._pause_duree_spin.value())
        self.cfg["csv_path"]  = self._csv_input.text()
        self.cfg["objet"]     = self._objet_input.text().strip()
        self.cfg["email_col"] = self._email_col_combo.currentText()
        self.cfg["pdf_dir"]   = self._pdf_dir_input.text()
        self.cfg["design"]    = self._collect_design()

    def _save_config(self):
        self._collect_config()
        save_config(self.cfg)
        self._do_log("Configuration sauvegardée.", "OK")
        QMessageBox.information(self, "Sauvegardé", "Configuration sauvegardée avec succès.")

    # ── Design helpers ────────────────────────────────────────────────────────

    def _collect_design(self):
        boutons = []
        for b in self._boutons:
            t = b["texte"].text().strip()
            u = b["url"].text().strip()
            if t and u:
                boutons.append({"texte": t, "url": u, "couleur": b["couleur"]})
        return {
            "org_nom":        self._dv["org_nom"].text().strip(),
            "org_slogan":     self._dv["org_slogan"].text().strip(),
            "header_couleur": self._header_color_inp.text().strip(),
            "message":        self._msg_edit.toPlainText(),
            "html_mode":      self._html_check.isChecked(),
            "boutons":        boutons,
            "footer":         self._dv["footer"].text().strip(),
        }

    def _toggle_html_mode(self, checked):
        c = _DARK if self._dark_mode else _LIGHT
        if checked:
            self._msg_edit.setStyleSheet(f"""
                QTextEdit {{
                    background: {c['html_bg']};
                    font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
                    font-size: 12px; color: {c['html_color']}; border: 1px solid #2563eb;
                }}
            """)
            self._lbl_hint.setText(
                "Mode HTML actif — écrivez du HTML brut. Utilisez {colonne} comme en mode texte.")
        else:
            self._msg_edit.setStyleSheet("")
            self._lbl_hint.setText(
                "Corps du mail. Utilisez {colonne} pour insérer une valeur du CSV.")

    def _pick_header_color(self):
        c = QColorDialog.getColor(QColor(self._header_color_inp.text()), self, "Couleur du header")
        if c.isValid():
            self._header_color_inp.setText(c.name())

    def _update_color_swatch(self, val):
        if QColor(val).isValid():
            c = _DARK if self._dark_mode else _LIGHT
            self._header_swatch.setStyleSheet(
                f"background: {val}; border-radius: 4px; border: 1px solid {c['swatch_border']};")

    def _preview_html(self):
        import webbrowser
        design = self._collect_design()
        html   = build_html(design)
        path   = self._csv_input.text()
        if path and os.path.exists(path):
            try:
                rows = load_csv(path)
                if rows:
                    for k, v in rows[0].items():
                        html = html.replace(
                            f"{{{k}}}",
                            f"<span style='background:#fff3cd;padding:0 3px'>{v}</span>")
            except Exception:
                pass
        preview = Path.home() / "apercu_email_preview.html"
        with open(preview, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open(preview.as_uri())

    # ── Bouton rows ───────────────────────────────────────────────────────────

    def _add_bouton_row(self, texte="", url="", couleur="#1e3a5f"):
        if len(self._boutons) >= 4:
            QMessageBox.information(self, "Limite", "Maximum 4 boutons.")
            return

        idx = len(self._boutons)
        row_w = QWidget()
        row_w.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row_w)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)

        lbl = QLabel(f"Bouton {idx+1} :")
        lbl.setFixedWidth(72)
        c = _DARK if self._dark_mode else _LIGHT
        lbl.setStyleSheet(f"color: {c['muted']};")
        texte_inp = QLineEdit(texte)
        texte_inp.setPlaceholderText("Texte")
        texte_inp.setFixedWidth(148)
        url_inp = QLineEdit(url)
        url_inp.setPlaceholderText("https://...")

        swatch = QPushButton()
        swatch.setFixedSize(32, 32)
        swatch.setCursor(Qt.PointingHandCursor)
        swatch.setStyleSheet(
            f"background: {couleur}; border-radius: 4px; border: 1px solid {c['swatch_border']};")

        entry = {
            "row": row_w, "texte": texte_inp,
            "url": url_inp, "couleur": couleur,
            "swatch": swatch, "lbl": lbl,
        }

        def pick(e=entry):
            col = QColorDialog.getColor(QColor(e["couleur"]), self, "Couleur du bouton")
            if col.isValid():
                e["couleur"] = col.name()
                tc = _DARK if self._dark_mode else _LIGHT
                e["swatch"].setStyleSheet(
                    f"background: {col.name()}; border-radius: 4px; "
                    f"border: 1px solid {tc['swatch_border']};")

        swatch.clicked.connect(pick)

        rm = QPushButton("✕")
        rm.setFixedSize(32, 32)
        rm.setCursor(Qt.PointingHandCursor)
        rm.setStyleSheet(
            f"QPushButton {{ {c['rm_normal']} border-radius: 4px; font-weight: 700; }}"
            f"QPushButton:hover {{ {c['rm_hover']} }}"
        )
        entry["rm"] = rm

        def remove(e=entry):
            e["row"].deleteLater()
            self._boutons.remove(e)
            self._renumber_bouton_rows()

        rm.clicked.connect(remove)

        rl.addWidget(lbl)
        rl.addWidget(texte_inp)
        rl.addWidget(url_inp)
        rl.addWidget(swatch)
        rl.addWidget(rm)

        self._bouton_rows_layout.addWidget(row_w)
        self._boutons.append(entry)

    def _renumber_bouton_rows(self):
        for i, b in enumerate(self._boutons):
            b["lbl"].setText(f"Bouton {i+1} :")

    # ── CSV ───────────────────────────────────────────────────────────────────

    def _browse_csv(self):
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir le fichier CSV", data_dir,
            "Fichiers CSV (*.csv);;Tous les fichiers (*.*)")
        if path:
            self._csv_input.setText(path)
            self.cfg["csv_path"] = path
            self._update_count()

    def _update_count(self):
        path = self._csv_input.text()
        if not path:
            return
        try:
            rows = load_csv(path)
            self._lbl_count.setText(f"✅  {len(rows)} destinataire(s) chargé(s)")
            self._lbl_count.setStyleSheet("color: #a6e3a1; font-size: 12px;")
            if rows:
                cols = list(rows[0].keys())
                self._email_col_combo.clear()
                self._email_col_combo.addItems(cols)
                cur = self.cfg.get("email_col", "")
                if cur in cols:
                    self._email_col_combo.setCurrentText(cur)
                else:
                    for col in cols:
                        if col.strip().lower() in ("email", "mail", "e-mail", "courriel"):
                            self._email_col_combo.setCurrentText(col)
                            break
                self._update_col_hint(cols)
        except Exception as e:
            self._lbl_count.setText(f"❌  Erreur lecture CSV : {e}")
            self._lbl_count.setStyleSheet("color: #f38ba8; font-size: 12px;")

    def _update_col_hint(self, cols):
        placeholders = "   ".join(f"{{{c}}}" for c in cols)
        self._lbl_cols.setText(f"Variables disponibles : {placeholders}")
        c = _DARK if self._dark_mode else _LIGHT
        self._lbl_cols.setStyleSheet(f"color: {c['accent']}; font-size: 11px;")

    # ── PDF ───────────────────────────────────────────────────────────────────

    def _browse_pdf_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Choisir le dossier contenant les PDF")
        if path:
            self._pdf_dir_input.setText(path)
            self.cfg["pdf_dir"] = path
            self._update_pdf_count()

    def _update_pdf_count(self):
        d = self._pdf_dir_input.text()
        if d and os.path.isdir(d):
            pdfs = [f for f in os.listdir(d) if f.lower().endswith(".pdf")]
            self._lbl_pdf.setText(f"✅  {len(pdfs)} fichier(s) PDF trouvé(s)")
            self._lbl_pdf.setStyleSheet("color: #a6e3a1; font-size: 12px;")
        else:
            self._lbl_pdf.setText("Dossier introuvable.")
            self._lbl_pdf.setStyleSheet("color: #f38ba8; font-size: 12px;")

    def _find_pdf(self, pdf_dir, dest, email):
        if not pdf_dir or not os.path.isdir(pdf_dir):
            return None
        prenom, nom = "", ""
        for k, v in dest.items():
            kl = k.strip().lower()
            if kl in ("prenom", "prénom", "firstname", "first_name"):
                prenom = v.strip()
            elif kl in ("nom", "name", "lastname", "last_name", "surname"):
                nom = v.strip()
        candidates = []
        if prenom and nom:
            candidates += [
                f"{prenom}_{nom}.pdf", f"{nom}_{prenom}.pdf",
                f"{prenom} {nom}.pdf", f"{nom} {prenom}.pdf",
            ]
        if email:
            candidates.append(f"{email}.pdf")
        try:
            files_lower = {f.lower(): f for f in os.listdir(pdf_dir)}
        except Exception:
            return None
        for name in candidates:
            match = files_lower.get(name.lower())
            if match:
                return os.path.join(pdf_dir, match)
        return None

    # ── SMTP test ─────────────────────────────────────────────────────────────

    def _test_smtp(self):
        self._collect_config()
        host, port = self.cfg["smtp_host"], int(self.cfg["smtp_port"] or 587)
        user, password = self.cfg["smtp_user"], self.cfg["smtp_password"]
        use_tls = self.cfg["smtp_tls"]
        self._do_log(f"Test connexion → {host}:{port} ...", "INFO")
        sig = self._sig

        def _do():
            try:
                ctx = ssl.create_default_context()
                with smtplib.SMTP(host, port, timeout=10) as s:
                    if use_tls:
                        s.starttls(context=ctx)
                    s.login(user, password)
                sig.smtp_test_ok.emit()
            except Exception as e:
                sig.smtp_test_err.emit(str(e))

        threading.Thread(target=_do, daemon=True).start()

    # ── Send ──────────────────────────────────────────────────────────────────

    def _start_send(self):
        if self._sending:
            return
        self._collect_config()
        csv_path = self.cfg["csv_path"]
        if not csv_path or not os.path.exists(csv_path):
            QMessageBox.critical(self, "Erreur", "Veuillez sélectionner un fichier CSV valide.")
            return
        if not self.cfg["smtp_host"] or not self.cfg["smtp_user"]:
            QMessageBox.critical(self, "Erreur", "Veuillez configurer le serveur SMTP.")
            return
        if not self.cfg.get("email_col"):
            QMessageBox.critical(self, "Erreur", "Veuillez sélectionner la colonne email.")
            return
        try:
            destinataires = load_csv(csv_path)
        except Exception as e:
            QMessageBox.critical(self, "Erreur CSV", str(e))
            return
        if not destinataires:
            QMessageBox.warning(self, "Fichier vide", "Aucun destinataire trouvé dans le CSV.")
            return

        delai          = self._delai_spin.value()
        pause_tous_les = self._pause_tous_les_spin.value()
        pause_duree    = self._pause_duree_spin.value()
        total          = len(destinataires)
        nb_pauses      = (total // pause_tous_les) if pause_tous_les > 0 else 0
        duree_estimee  = total * delai + nb_pauses * pause_duree
        detail_pause   = (f"\nPause de {pause_duree} s tous les {pause_tous_les} envois "
                          f"({nb_pauses} pause(s) prévue(s))") if pause_tous_les > 0 else ""
        ret = QMessageBox.question(
            self, "Confirmer",
            f"Envoyer à {total} destinataire(s) avec un délai de {delai} s ?{detail_pause}\n\n"
            f"Durée estimée : ~{duree_estimee} secondes",
        )
        if ret != QMessageBox.Yes:
            return

        self._stop_flag = False
        self._sending   = True
        self._btn_send.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._progress.setMaximum(total)
        self._progress.setValue(0)
        self._tabs.setCurrentWidget(self._tab_log)

        threading.Thread(target=self._send_all, args=(destinataires,), daemon=True).start()

    def _stop_send(self):
        self._stop_flag = True
        self._do_log("Arrêt demandé — en attente de fin d'envoi en cours...", "WARN")

    @staticmethod
    def _build_from_addr(user: str, host: str) -> str:
        """Construit une adresse From complète si smtp_user n'a pas de domaine.
        Ex : 'zahire.benkhelifa' + 'smtp.monlycee.net' → 'zahire.benkhelifa@monlycee.net'"""
        if "@" in user:
            return user
        parts = host.split(".")
        domain = ".".join(parts[1:]) if parts[0].lower() in ("smtp", "mail", "mx", "imap") else host
        return f"{user}@{domain}" if domain else user

    def _send_all(self, destinataires):
        host      = self.cfg["smtp_host"]
        port      = int(self.cfg["smtp_port"] or 587)
        user      = self.cfg["smtp_user"]
        password  = self.cfg["smtp_password"]
        use_tls   = self.cfg["smtp_tls"]
        delai          = int(self.cfg["delai"])
        pause_tous_les = int(self.cfg.get("pause_tous_les", 0))
        pause_duree    = int(self.cfg.get("pause_duree", 30))
        objet     = self.cfg["objet"]
        design    = self.cfg["design"]
        pdf_dir   = self.cfg.get("pdf_dir", "")
        email_col = self.cfg.get("email_col", "email")
        from_addr = self._build_from_addr(user, host)
        template  = build_html(design)
        total     = len(destinataires)
        ok_count  = 0
        err_list: list = []
        err_rows: list = []
        sig = self._sig

        sig.log_append.emit(f"Début de l'envoi — {total} destinataires", "START")

        def _connect():
            ctx = ssl.create_default_context()
            s = smtplib.SMTP(host, port, timeout=15)
            if use_tls:
                s.starttls(context=ctx)
            s.login(user, password)
            return s

        try:
            server = _connect()
            sig.log_append.emit(f"Connecté au serveur SMTP ({from_addr}).", "OK")

            try:
                for i, dest in enumerate(destinataires):
                    if self._stop_flag:
                        sig.log_append.emit("Envoi interrompu par l'utilisateur.", "WARN")
                        break

                    email = ""
                    for k, v in dest.items():
                        if k.strip().lower() == email_col.strip().lower():
                            email = v.strip()
                            break
                    if not email:
                        sig.log_append.emit(
                            f"Ligne {i+1} : colonne '{email_col}' vide — ignorée", "WARN")
                        sig.progress_update.emit(i + 1, total)
                        continue

                    corps_html  = template
                    corps_texte = design.get("message", "")
                    for key, val in dest.items():
                        corps_html  = corps_html.replace(f"{{{key}}}", val)
                        corps_texte = corps_texte.replace(f"{{{key}}}", val)

                    pdf_path = self._find_pdf(pdf_dir, dest, email)
                    if pdf_path:
                        msg = MIMEMultipart("mixed")
                        alt = MIMEMultipart("alternative")
                        alt.attach(MIMEText(corps_texte, "plain", "utf-8"))
                        alt.attach(MIMEText(corps_html,  "html",  "utf-8"))
                        msg.attach(alt)
                        with open(pdf_path, "rb") as fp:
                            att = MIMEApplication(fp.read(), _subtype="pdf")
                        att.add_header("Content-Disposition", "attachment",
                                       filename=os.path.basename(pdf_path))
                        msg.attach(att)
                    else:
                        msg = MIMEMultipart("alternative")
                        msg.attach(MIMEText(corps_texte, "plain", "utf-8"))
                        msg.attach(MIMEText(corps_html,  "html",  "utf-8"))

                    msg["Subject"] = objet
                    msg["From"]    = from_addr
                    msg["To"]      = email

                    try:
                        server.sendmail(from_addr, email, msg.as_string())
                        ok_count += 1
                        pj = f" 📎 {os.path.basename(pdf_path)}" if pdf_path else ""
                        sig.log_append.emit(f"[{i+1}/{total}] ✔ Envoyé à {email}{pj}", "OK")
                    except smtplib.SMTPServerDisconnected:
                        # Reconnexion automatique après coupure serveur
                        sig.log_append.emit("Connexion perdue — reconnexion...", "WARN")
                        try:
                            server = _connect()
                            server.sendmail(from_addr, email, msg.as_string())
                            ok_count += 1
                            pj = f" 📎 {os.path.basename(pdf_path)}" if pdf_path else ""
                            sig.log_append.emit(f"[{i+1}/{total}] ✔ Envoyé à {email}{pj} (après reconnexion)", "OK")
                        except Exception as e2:
                            err_list.append(email)
                            err_rows.append(dest)
                            sig.log_append.emit(f"[{i+1}/{total}] ❌ Échec après reconnexion <{email}> : {e2}", "ERR")
                    except Exception as e:
                        err_list.append(email)
                        err_rows.append(dest)
                        _p = next((v.strip() for k, v in dest.items()
                                   if k.strip().lower() in ("prenom", "prénom")), "")
                        _n = next((v.strip() for k, v in dest.items()
                                   if k.strip().lower() == "nom"), "")
                        sig.log_append.emit(f"Erreur {_p} {_n} <{email}> : {e}", "ERR")

                    sig.progress_update.emit(i + 1, total)
                    if i < total - 1 and not self._stop_flag:
                        envois_faits = i + 1
                        if pause_tous_les > 0 and envois_faits % pause_tous_les == 0:
                            sig.log_append.emit(
                                f"⏸ Pause de {pause_duree} s après {envois_faits} envois...", "WARN")
                            time.sleep(pause_duree)
                        else:
                            time.sleep(delai)
            finally:
                try:
                    server.quit()
                except Exception:
                    pass

        except Exception as e:
            sig.log_append.emit(f"Erreur SMTP : {e}", "ERR")

        sig.send_finished.emit(ok_count, total, err_list, err_rows)

    def _do_send_finished(self, ok_count, total, err_list, err_rows):
        self._sending = False
        self._btn_send.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._do_log("─" * 50, "INFO")
        self._do_log(f"Envoi terminé : {ok_count} succès, {len(err_list)} erreur(s)", "OK")
        if err_rows:
            self._do_log(f"Emails en erreur : {', '.join(err_list)}", "WARN")
            # Écrire à côté du CSV source (chemin toujours accessible, même en app compilée)
            csv_source = self.cfg.get("csv_path", "")
            err_dir = os.path.dirname(csv_source) if csv_source else str(Path.home())
            ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
            err_path = os.path.join(err_dir, f"erreurs_{ts}.csv")
            try:
                with open(err_path, "w", newline="", encoding="utf-8-sig") as fe:
                    writer = csv.DictWriter(fe, fieldnames=list(err_rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(err_rows)
                self._do_log(f"CSV erreurs exporté → {err_path}", "WARN")
            except Exception as ex:
                self._do_log(f"Impossible d'écrire le CSV erreurs : {ex}", "ERR")
        self._lbl_progress.setText(f"Terminé — {ok_count}/{total} envoyés")

    def _do_progress(self, val, total):
        self._progress.setValue(val)
        self._lbl_progress.setText(f"Envoi en cours : {val}/{total}")

    # ── Log ───────────────────────────────────────────────────────────────────

    _LOG_COLORS = _DARK["log_colors"]

    def _do_log(self, msg, level="INFO"):
        color = self._LOG_COLORS.get(level, "#a6adc8")
        icon  = self._LOG_ICONS.get(level, "•")
        ts    = datetime.now().strftime("%H:%M:%S")
        html  = (f'<span style="color:{color}; font-family: monospace;">'
                 f'[{ts}] {icon}&nbsp; {msg}</span><br>')
        self._log_edit.moveCursor(QTextCursor.End)
        self._log_edit.insertHtml(html)
        self._log_edit.ensureCursorVisible()
        if level == "ERR":
            self._tabs.setCurrentWidget(self._tab_log)

    def _clear_log(self):
        self._log_edit.clear()

    def _export_log(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le log",
            f"log_envoi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Fichier texte (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._log_edit.toPlainText())
            QMessageBox.information(self, "Exporté", f"Log exporté vers :\n{path}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("MailCent Pro")
    app.setStyle("Fusion")
    window = App()
    window.show()
    sys.exit(app.exec())

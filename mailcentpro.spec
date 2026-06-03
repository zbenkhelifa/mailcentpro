# -*- mode: python ; coding: utf-8 -*-
"""
Spec PyInstaller — MailCent Pro  (Windows / Mac / Linux)
Filtrage des libs Qt non utilisées : -100 Mo sur le bundle final.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files

_IS_MAC = sys.platform == "darwin"

# ── Libs Qt à supprimer après analyse binaire ─────────────────────────────────
_REMOVE_PREFIXES = (
    "libavcodec", "libavformat", "libavutil",
    "libavdevice", "libavfilter", "libswresample", "libswscale",
    "libQt6Qml", "libQt6QmlCore", "libQt6QmlMeta",
    "libQt6QmlModels", "libQt6QmlWorkerScript", "libQt6QmlCompiler",
    "libQt6Quick", "libQt6QuickControls", "libQt6QuickShapes",
    "libQt6QuickLayouts", "libQt6QuickTemplates2", "libQt6QuickWidgets",
    "libQt6QuickControls2", "libQt6QuickControls2Impl",
    "libQt6QuickVectorImage",
    "libQt63DAnim", "libQt63DCore", "libQt63DExtras",
    "libQt63DInput", "libQt63DLogic", "libQt63DRender",
    "libQt6Quick3D",
    "libQt6Designer", "libQt6DesignerComponents",
    "libQt6ShaderTools",
    "libQt6Multimedia", "libQt6SpatialAudio",
    "libQt6Lottie", "libQt6CanvasPainter",
    "libQt6Charts", "libQt6DataVisualization", "libQt6Graphs",
    "libQt6Bluetooth", "libQt6Nfc", "libQt6SerialBus", "libQt6SerialPort",
    "libQt6Positioning", "libQt6Location",
    "libQt6RemoteObjects", "libQt6Scxml", "libQt6StateMachine",
    "libQt6TextToSpeech", "libQt6Pdf", "libQt6Sql",
    "libQt6WebChannel", "libQt6WebSockets", "libQt6WebView",
    "libQt6HttpServer", "libQt6VirtualKeyboard", "libQt6NetworkAuth",
    "libQt6Sensors", "libQt6UiTools", "libQt6Help",
    "libQt6WaylandCompositor", "libQt6WlShellIntegration",
    "libQt6EglFsKmsSupport", "libQt6LabsStyleKit",
)

def _keep(name: str) -> bool:
    low = name.lower()
    return not any(low.startswith(p.lower()) or ("/" + p.lower()) in low
                   for p in _REMOVE_PREFIXES)

# ── Analyse ───────────────────────────────────────────────────────────────────
a = Analysis(
    ["mailcentpro.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
        "email.mime.text", "email.mime.multipart", "email.mime.application",
    ],
    hookspath=[],
    hooksconfig={
        "PySide6": {
            "excluded_qml_modules": [
                "QtQuick", "QtQml", "Qt3D", "QtWebEngine", "QtMultimedia",
            ],
        }
    },
    runtime_hooks=[],
    excludes=[
        "tkinter", "_tkinter",
        "matplotlib", "numpy", "scipy", "pandas",
        "PySide6.Qt3DAnimation",   "PySide6.Qt3DCore",    "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",       "PySide6.Qt3DLogic",   "PySide6.Qt3DRender",
        "PySide6.QtBluetooth",     "PySide6.QtCanvasPainter",
        "PySide6.QtCharts",        "PySide6.QtDataVisualization",
        "PySide6.QtDesigner",      "PySide6.QtGraphs",    "PySide6.QtGraphsWidgets",
        "PySide6.QtHelp",          "PySide6.QtHttpServer",
        "PySide6.QtLocation",      "PySide6.QtMultimedia","PySide6.QtMultimediaWidgets",
        "PySide6.QtNfc",           "PySide6.QtNetworkAuth",
        "PySide6.QtOpenGLWidgets",
        "PySide6.QtPdf",           "PySide6.QtPdfWidgets",
        "PySide6.QtPositioning",   "PySide6.QtPrintSupport",
        "PySide6.QtQml",           "PySide6.QtQuick",
        "PySide6.QtQuickControls2","PySide6.QtQuickWidgets",
        "PySide6.QtRemoteObjects", "PySide6.QtScxml",
        "PySide6.QtSensors",       "PySide6.QtSerialBus", "PySide6.QtSerialPort",
        "PySide6.QtShaderTools",   "PySide6.QtSpatialAudio",
        "PySide6.QtSql",           "PySide6.QtStateMachine",
        "PySide6.QtSvg",           "PySide6.QtSvgWidgets",
        "PySide6.QtTest",          "PySide6.QtTextToSpeech",
        "PySide6.QtUiTools",       "PySide6.QtWebChannel",
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets","PySide6.QtWebSockets",
        "PySide6.QtXml",
        "unittest", "doctest", "pdb", "difflib",
    ],
    noarchive=False,
)

# ── Filtrage post-analyse des .so / .dll non nécessaires ─────────────────────
a.binaries = [(n, p, t) for n, p, t in a.binaries if _keep(n)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MailCentPro",
    debug=False,
    strip=not _IS_MAC,   # strip peut casser la signature Mac
    upx=not _IS_MAC,     # upx incompatible avec Gatekeeper
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=not _IS_MAC,
    upx=not _IS_MAC,
    upx_exclude=[],
    name="MailCentPro",
)

# ── Sur macOS : créer un vrai .app bundle ─────────────────────────────────────
if _IS_MAC:
    app = BUNDLE(
        coll,
        name="MailCentPro.app",
        bundle_identifier="fr.mailcentpro.app",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "2.0",
            "LSMinimumSystemVersion": "12.0",
            "CFBundleName": "MailCentPro",
        },
    )

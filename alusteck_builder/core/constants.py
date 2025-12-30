"""
Project-wide Constants für Alusteck Builder.
Zentrale Platzierung aller Konfigurationswerte.
"""

# ============================================================================
# SYSTEM KONFIGURATION
# ============================================================================

SYSTEM_SIZES_MM = [20.0, 25.0, 30.0]
DEFAULT_SYSTEM = "25"  # Standard-System

# ============================================================================
# ALUMINIUM PROFIL KONFIGURATION
# ============================================================================

DEFAULT_WALL_MM = 1.5  # Standard Wandstärke
DEFAULT_SOCKET_TOLERANCE_MM = 0.5  # Zapfen-Toleranz
PROFILE_TYPES = ["standard", "steg_single", "steg_double"]

# ============================================================================
# SNAP ENGINE KONFIGURATION
# ============================================================================

SNAP_DISTANCE_THRESHOLD_MM = 50.0  # Snap-Distanz
SNAP_ALIGNMENT_TOLERANCE_MM = 10.0  # Alignment-Toleranz
SNAP_PREVIEW_ENABLED = True
SNAP_AUTO_VALIDATE = True

# ============================================================================
# VERBINDER KONFIGURATION
# ============================================================================

CONNECTOR_TYPES = {
    "gerade": {"ways": 2, "angle": 180},
    "winkel": {"ways": 2, "angle": 90},
    "t-stueck": {"ways": 3, "angle": 90},
    "eckverbinder": {"ways": 3, "angle": 90},
    "kreuz": {"ways": 4, "angle": 90},
    "wuerfel": {"ways": 6, "angle": 90},
}

# ============================================================================
# DATENBANK KONFIGURATION
# ============================================================================

DATA_FILENAME = "alusteck_database.json"
SNAP_RULES_FILENAME = "snap_rules.json"

# Datenbank-Updates
AUTO_UPDATE_DATABASE = False  # Automatisches Update
UPDATE_CHECK_INTERVAL_DAYS = 7

# ============================================================================
# UI/UX KONFIGURATION
# ============================================================================

UI_ICON_PROFILE = "MOD_BUILD"
UI_ICON_CONNECTOR = "OUTLINER_OB_LATTICE"
UI_ICON_ACCESSORY = "COMMUNITY"
UI_ICON_SNAP = "MAGNET"
UI_ICON_VALIDATE = "CHECKMARK"
UI_ICON_EXPORT = "EXPORT"

# ============================================================================
# MATERIAL KONFIGURATION
# ============================================================================

DEFAULT_PROFILE_COLOR = (0.7, 0.7, 0.75, 1.0)  # Aluminium grau
DEFAULT_CONNECTOR_COLOR = (0.2, 0.2, 0.2, 1.0)  # Kunststoff schwarz
HIGHLIGHT_COLOR = (0.0, 1.0, 0.0, 1.0)  # Snap-Vorschau grün

# ============================================================================
# EXPORT KONFIGURATION
# ============================================================================

EXPORT_BOM_FORMATS = ["csv", "json"]
DEFAULT_EXPORT_FORMAT = "csv"
EXPORT_CURRENCY = "EUR"
EXPORT_MARGIN_DEFAULT = 1.25  # 25% Gewinnzuschlag

# ============================================================================
# AI INTEGRATION KONFIGURATION
# ============================================================================

AI_MODEL = "claude-3-5-sonnet-20241022"
AI_MAX_TOKENS = 2048
AI_TEMPERATURE = 0.7
AI_USE_BEST_PRACTICES = True

# ============================================================================
# LOGGING
# ============================================================================

DEBUG_MODE = False
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = False

"""
Core Module - Zentrale Funktionalität für Alusteck Builder.
Exportiert Datenbank, Registry und Konstanten.
"""

from . import constants
from . import database
from . import registry

# ============================================================================
# PUBLIC API
# ============================================================================

# Constants
from .constants import (
    SYSTEM_SIZES_MM,
    DEFAULT_SYSTEM,
    DEFAULT_WALL_MM,
    DEFAULT_SOCKET_TOLERANCE_MM,
    SNAP_DISTANCE_THRESHOLD_MM,
    CONNECTOR_TYPES,
    DATA_FILENAME,
    SNAP_RULES_FILENAME,
)

# Database Functions
from .database import (
    load_json,
    load_components,
    load_snap_rules,
    get_system_info,
    get_profile_variants,
    get_connectors,
    get_accessories,
    get_snap_rule,
    list_all_systems,
    validate_database,
)

# Registry
from .registry import (
    ComponentRegistry,
    get_registry,
)

__all__ = [
    # Constants
    "constants",
    "SYSTEM_SIZES_MM",
    "DEFAULT_SYSTEM",
    "DEFAULT_WALL_MM",
    "DEFAULT_SOCKET_TOLERANCE_MM",
    "SNAP_DISTANCE_THRESHOLD_MM",
    "CONNECTOR_TYPES",
    
    # Database
    "database",
    "load_json",
    "load_components",
    "load_snap_rules",
    "get_system_info",
    "get_profile_variants",
    "get_connectors",
    "get_accessories",
    "get_snap_rule",
    "list_all_systems",
    "validate_database",
    
    # Registry
    "registry",
    "ComponentRegistry",
    "get_registry",
]


def initialize():
    """
    Initialisiert den Core-Modul.
    Sollte beim Addon-Laden aufgerufen werden.
    """
    # Validiere Datenbank
    is_valid = validate_database()
    
    if not is_valid:
        print("⚠ Datenbank-Validierung fehlgeschlagen!")
        print("  Versuche zu initialisieren...")
    
    # Lade Registry
    reg = get_registry()
    systems = reg.list_systems()
    print(f"✓ Core initialized ({len(systems)} systems available)")
    
    return is_valid

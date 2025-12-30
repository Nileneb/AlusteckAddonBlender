"""
Database Module - Lädt Komponenten und Snap-Regeln aus JSON.
"""

from pathlib import Path
import json
from typing import Dict, Optional, Any
from . import constants


def _get_data_dir() -> Path:
    """Gibt Pfad zum data-Verzeichnis zurück."""
    return Path(__file__).resolve().parent.parent / "data"


def load_json(filename: str) -> Dict[str, Any]:
    """
    Lädt eine JSON-Datei aus dem data-Verzeichnis.
    
    Args:
        filename: Name der Datei (z.B. "alusteck_database.json")
    
    Returns:
        Dict mit Datei-Inhalt oder {} falls nicht gefunden
    """
    data_path = _get_data_dir() / filename
    
    if not data_path.exists():
        print(f"⚠ Datenbank nicht gefunden: {data_path}")
        return {}
    
    try:
        with data_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        print(f"❌ Fehler beim Parsen: {data_path}")
        return {}
    except Exception as e:
        print(f"❌ Fehler beim Laden: {e}")
        return {}


def load_components() -> Dict[str, Any]:
    """Lädt Komponenten-Datenbank."""
    return load_json(constants.DATA_FILENAME)


def load_snap_rules() -> Dict[str, Any]:
    """Lädt Snap-Regeln."""
    return load_json(constants.SNAP_RULES_FILENAME)


def get_system_info(system: str) -> Optional[Dict[str, Any]]:
    """Holt Informationen zu einem System (20/25/30mm)."""
    db = load_components()
    return db.get("systems", {}).get(system)


def get_profile_variants(system: str) -> list:
    """Holt alle Profil-Varianten eines Systems."""
    system_info = get_system_info(system)
    if not system_info:
        return []
    return system_info.get("profile", {}).get("variants", [])


def get_connectors(system: str) -> list:
    """Holt alle Verbinder eines Systems."""
    system_info = get_system_info(system)
    if not system_info:
        return []
    return system_info.get("connectors", [])


def get_accessories(system: str) -> list:
    """Holt all Zubehör eines Systems."""
    system_info = get_system_info(system)
    if not system_info:
        return []
    return system_info.get("accessories", [])


def get_snap_rule(system: str, key: str) -> Optional[Dict[str, Any]]:
    """Holt eine Snap-Regel."""
    rules = load_snap_rules()
    return rules.get(system, {}).get(key)


def list_all_systems() -> list:
    """Gibt Liste aller Systeme zurück."""
    db = load_components()
    return list(db.get("systems", {}).keys())


def validate_database() -> bool:
    """Überprüft ob Datenbank intakt ist."""
    db = load_components()
    
    if not db:
        print("❌ Datenbank ist leer!")
        return False
    
    # Überprüfe notwendige Keys
    required = ["meta", "systems"]
    for key in required:
        if key not in db:
            print(f"❌ Fehlender Key in Datenbank: {key}")
            return False
    
    # Überprüfe Systeme
    systems = db.get("systems", {})
    if not systems:
        print("❌ Keine Systeme in Datenbank!")
        return False
    
    print(f"✅ Datenbank OK ({len(systems)} Systeme)")
    return True

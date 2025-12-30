"""Database loader for component metadata and snap rules."""

from pathlib import Path
import json
from . import constants


def load_json(filename: str) -> dict:
    """Load a JSON file from the addon data directory."""
    data_path = Path(__file__).resolve().parent.parent / "data" / filename
    if not data_path.exists():
        return {}
    with data_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_components() -> dict:
    return load_json(constants.DATA_FILENAME)


def load_snap_rules() -> dict:
    return load_json(constants.SNAP_RULES_FILENAME)

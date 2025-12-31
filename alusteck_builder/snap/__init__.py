"""
SNAP MODULE - Intelligentes Snap-System für Komponenten-Verbindungen
=====================================================================

Sub-Module:
- engine.py       - Haupt-Snap-Engine mit Modal Operator
- collision.py    - BVH-basierte Kollisionserkennung
- validation.py   - Konstruktions-Validierung
- rules.py        - Snap-Regeln und Kompatibilität
"""

from .engine import (
    AlusteckSnapEngine,
    get_snap_engine,
    ALUSTECK_OT_snap_move,
    PortDirection,
    Port,
    StegConfig,
    SnapCandidate,
)

from .collision import CollisionDetector

from .validation import (
    StructuralValidator,
    get_validator,
    ValidationIssue,
    IssueLevel,
    LoadAnalysis,
)

__all__ = [
    # Engine
    "AlusteckSnapEngine",
    "get_snap_engine",
    "ALUSTECK_OT_snap_move",
    "PortDirection",
    "Port",
    "StegConfig",
    "SnapCandidate",
    
    # Collision
    "CollisionDetector",
    
    # Validation
    "StructuralValidator",
    "get_validator",
    "ValidationIssue",
    "IssueLevel",
    "LoadAnalysis",
]


def register():
    """Registriert Snap-Module in Blender"""
    import bpy
    bpy.utils.register_class(ALUSTECK_OT_snap_move)


def unregister():
    """Unregistriert Snap-Module"""
    import bpy
    bpy.utils.unregister_class(ALUSTECK_OT_snap_move)

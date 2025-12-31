"""
UI MODULE - Blender User Interface Elements
============================================

Sub-Module:
- panels.py      - Sidebar Panels (Snap-Tools, Stückliste, Export, Validierung)
- operators.py   - UI Operators (Add Profile/Connector, Snap, Export, Validierung)
- menus.py       - Add-Menüs
- preferences.py - Addon Preferences
"""

from . import panels
from . import operators
from . import menus

# Panels
from .panels import (
    ALUSTECK_PT_snap_tools,
    ALUSTECK_PT_stuckliste,
    ALUSTECK_PT_export,
    ALUSTECK_PT_validation,
    register as register_panels,
    unregister as unregister_panels,
)

# Operators
from .operators import (
    ALUSTECK_OT_add_profile,
    ALUSTECK_OT_add_connector,
    ALUSTECK_OT_snap_connector,
    ALUSTECK_OT_export_bom,
    ALUSTECK_OT_export_bom_json,
    ALUSTECK_OT_export_costs,
    ALUSTECK_OT_export_shop_link,
    ALUSTECK_OT_validate_structure,
    register_operators,
    unregister_operators,
)

# Menus
from .menus import (
    ALUSTECK_MT_add_menu,
    register as register_menus,
    unregister as unregister_menus,
)

__all__ = [
    # Panels
    "ALUSTECK_PT_snap_tools",
    "ALUSTECK_PT_stuckliste",
    "ALUSTECK_PT_export",
    "ALUSTECK_PT_validation",
    
    # Operators
    "ALUSTECK_OT_add_profile",
    "ALUSTECK_OT_add_connector",
    "ALUSTECK_OT_snap_connector",
    "ALUSTECK_OT_export_bom",
    "ALUSTECK_OT_export_bom_json",
    "ALUSTECK_OT_export_costs",
    "ALUSTECK_OT_export_shop_link",
    "ALUSTECK_OT_validate_structure",
    
    # Menus
    "ALUSTECK_MT_add_menu",
    
    # Functions
    "register",
    "unregister",
]


def register():
    """Registriert alle UI-Elemente"""
    register_panels()
    register_operators()
    register_menus()


def unregister():
    """Unregistriert alle UI-Elemente"""
    unregister_menus()
    unregister_operators()
    unregister_panels()


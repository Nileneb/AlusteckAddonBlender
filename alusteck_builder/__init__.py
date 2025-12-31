# ============================================
# ALUSTECK BUILDER - Blender Addon
# Version: 1.0.0
# ============================================

bl_info = {
    "name": "Alusteck Builder",
    "author": "Alusteck",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Add > Mesh > Alusteck",
    "description": "Alusteck 25x25mm Stecksystem mit Komponenten",
    "warning": "",
    "doc_url": "https://www.alusteck.de/25-mm-alu-stecksystem/",
    "category": "Add Mesh",
}

import bpy
from .core import load_components, get_registry
from .snap.engine import ALUSTECK_OT_snap_move
from .ui import register as register_ui, unregister as unregister_ui


# ============================================
# DATENBANK LADEN (beim Import)
# ============================================

def _load_database():
    """Lädt Alusteck-Datenbank beim Addon-Start"""
    try:
        from .core import load_components
        data = load_components()
        
        if data and data.get("kategorien"):
            # Zähle Komponenten
            total = 0
            for system in data.get("kategorien", {}).values():
                total += len(system.get("profile", []))
                total += len(system.get("verbinder", []))
            return data, total
        
        print("⚠️  Datenbank ist leer oder ungültig")
        return None, 0
    except Exception as e:
        print(f"❌ Fehler beim Laden der Datenbank: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

ALUSTECK_DATABASE, _COMPONENT_COUNT = _load_database()


# ============================================
# REGISTRIERUNG
# ============================================

def register():
    """Registriert Addon und alle Module"""
    # Snap-Engine Operator
    bpy.utils.register_class(ALUSTECK_OT_snap_move)
    
    # Alle UI-Module (Panels, Operators, Menus)
    register_ui()
    
    # Info
    if ALUSTECK_DATABASE:
        print(f"✅ Alusteck Builder geladen! ({_COMPONENT_COUNT} Komponenten)")
    else:
        print("⚠️  Alusteck Builder geladen (Datenbank NICHT verfügbar)")


def unregister():
    """Unregistriert Addon und alle Module"""
    # UI-Module
    unregister_ui()
    
    # Snap-Engine Operator
    bpy.utils.unregister_class(ALUSTECK_OT_snap_move)
    
    print("✅ Alusteck Builder entladen.")


if __name__ == "__main__":
    register()

"""
UI PANELS - Blender Sidebar Panels für Alusteck Builder
========================================================

Module organisiert nach Funktion:
- ALUSTECK_PT_snap_tools   - Snap-Engine Controls
- ALUSTECK_PT_stuckliste   - Bill of Materials & Kosten
- ALUSTECK_PT_export       - Export Funktionen (BOM, Kosten, Shop)
- ALUSTECK_PT_validation   - Konstruktions-Validierung (TODO)
"""

import bpy
from bpy.types import Panel


# ============================================================================
# SNAP-TOOLS PANEL
# ============================================================================

class ALUSTECK_PT_snap_tools(Panel):
    """Panel mit Snap-Engine Controls"""
    bl_label = "🧲 Snap-Tools"
    bl_idname = "ALUSTECK_PT_snap_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Alusteck"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Verbinder-Modus:", icon='SNAP_ON')
        row = layout.row()
        row.operator("alusteck.snap_connector", text="Snap starten", icon='MAGNET')
        
        layout.separator()
        layout.label(text="So funktioniert's:", icon='INFO')
        layout.label(text="1. Wähle einen Verbinder")
        layout.label(text="2. Klick auf 'Snap starten'")
        layout.label(text="3. Bewege die Maus über Profile")
        layout.label(text="4. Klick zum Verbinden", icon='MOUSE_LMB')
        layout.label(text="5. ESC zum Abbrechen", icon='MOUSE_RMB')


# ============================================================================
# STÜCKLISTE PANEL
# ============================================================================

class ALUSTECK_PT_stuckliste(Panel):
    """Panel mit Stückliste und Kostenübersicht"""
    bl_label = "📋 Stückliste"
    bl_idname = "ALUSTECK_PT_stuckliste"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Alusteck"
    
    def draw(self, context):
        layout = self.layout
        
        # Lade Datenbank
        from .. import ALUSTECK_DATABASE
        
        if not ALUSTECK_DATABASE:
            layout.label(text="⚠️ Datenbank nicht geladen!", icon='ERROR')
            return
        
        # Sammle alle Komponenten nach Artikel-Nummer
        components = {}
        total_profile_length = 0.0
        
        for obj in context.scene.objects:
            if "alusteck_artikel_nr" not in obj:
                continue
            
            artikel_nr = obj["alusteck_artikel_nr"]
            name = obj.get("alusteck_name", artikel_nr)
            price = obj.get("alusteck_price", 0.0)
            obj_type = obj.get("alusteck_type", "unknown")
            
            if artikel_nr not in components:
                components[artikel_nr] = {
                    "name": name,
                    "type": obj_type,
                    "count": 0,
                    "length": 0.0,
                    "price": price,
                }
            
            components[artikel_nr]["count"] += 1
            
            if obj_type == "profile" and "alusteck_length" in obj:
                length = obj["alusteck_length"]
                components[artikel_nr]["length"] += length
                total_profile_length += length
        
        # Komponenten-Liste
        box = layout.box()
        box.label(text="🔩 Komponenten:", icon='LINENUMBERS_ON')
        
        if not components:
            box.label(text="(Keine Komponenten in der Szene)")
        else:
            total_cost = 0.0
            
            for artikel_nr in sorted(components.keys()):
                comp = components[artikel_nr]
                
                if comp["type"] == "profile":
                    text = f"{comp['name']}: {comp['count']}x {comp['length']:.2f}m"
                    cost = comp["length"] * comp["price"]
                else:
                    text = f"{comp['name']}: {comp['count']}x"
                    cost = comp["count"] * comp["price"]
                
                row = box.row()
                row.label(text=text)
                row.label(text=f"{cost:.2f}€", icon='FUND')
                total_cost += cost
            
            # Gesamtkosten
            layout.separator()
            box2 = layout.box()
            box2.label(text="💰 Geschätzte Kosten:", icon='FUND')
            row = box2.row()
            row.label(text="GESAMT:", icon='FUND')
            row.label(text=f"{total_cost:.2f}€")
            
            # Info
            layout.separator()
            info_box = layout.box()
            info_box.label(text=f"Gesamtprofilänge: {total_profile_length:.2f}m")
            info_box.label(text=f"Komponenten insgesamt: {len(components)}")


# ============================================================================
# EXPORT PANEL
# ============================================================================

class ALUSTECK_PT_export(Panel):
    """Panel mit Export-Funktionen"""
    bl_label = "📤 Export"
    bl_idname = "ALUSTECK_PT_export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Alusteck"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Konstruktion exportieren:", icon='EXPORT')
        
        # BOM Export
        row = layout.row()
        row.operator("alusteck.export_bom", text="📊 BOM (CSV)", icon='FILE_TEXT')
        row.operator("alusteck.export_bom_json", text="JSON", icon='FILE')
        
        # Kosten Export
        layout.operator("alusteck.export_costs", text="💰 Kostenreport", icon='FUND')
        
        # Shop-Link
        layout.operator("alusteck.export_shop_link", text="🛒 Shop-Link", icon='INTERNET')
        
        layout.separator()
        layout.label(text="Dateien werden gespeichert in:", icon='INFO')
        layout.label(text="~/Alusteck_BOM.csv")
        layout.label(text="~/Alusteck_Costs.txt")


# ============================================================================
# VALIDATION PANEL (STUB - TODO später implementieren)
# ============================================================================

class ALUSTECK_PT_validation(Panel):
    """Panel mit Struktur-Validierung"""
    bl_label = "✓ Validierung"
    bl_idname = "ALUSTECK_PT_validation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Alusteck"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Strukturvalidierung:", icon='CHECKMARK')
        
        # Hauptbutton
        row = layout.row()
        row.scale_y = 1.5
        row.operator("alusteck.validate_structure", text="🔍 Struktur prüfen", icon='FILE_TICK')
        
        layout.separator()
        layout.label(text="Überprüft:", icon='INFO')
        
        # Check-Items
        box = layout.box()
        box.label(text="Komponenten-Verbindungen", icon='CONSTRAINT_DISTANCE')
        box.label(text="Profil-Längen (zu lang?)", icon='STRAIGHTCURVE')
        box.label(text="Port-Belegung", icon='PIVOT_CURSOR')
        box.label(text="Geometrische Symmetrie", icon='ALIGN_CENTER')
        box.label(text="Basis-Stabilität", icon='OUTLINER_OB_ARMATURE')
        
        layout.separator()
        layout.label(text="Reports werden in Console angezeigt", icon='CONSOLE')
        layout.label(text="(Window > Toggle System Console)", icon='INFO')


# ============================================================================
# REGISTRATION
# ============================================================================

def register():
    """Registriert alle Panel-Klassen"""
    bpy.utils.register_class(ALUSTECK_PT_snap_tools)
    bpy.utils.register_class(ALUSTECK_PT_stuckliste)
    bpy.utils.register_class(ALUSTECK_PT_export)
    bpy.utils.register_class(ALUSTECK_PT_validation)


def unregister():
    """Unregistriert alle Panel-Klassen"""
    bpy.utils.unregister_class(ALUSTECK_PT_validation)
    bpy.utils.unregister_class(ALUSTECK_PT_export)
    bpy.utils.unregister_class(ALUSTECK_PT_stuckliste)
    bpy.utils.unregister_class(ALUSTECK_PT_snap_tools)


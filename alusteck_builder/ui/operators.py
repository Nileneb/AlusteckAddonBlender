"""
UI OPERATORS - All Blender Operators
====================================

Module organisiert nach Funktion:
- ALUSTECK_OT_add_profile       - Profil aus Datenbank hinzufügen
- ALUSTECK_OT_add_connector     - Verbinder aus Datenbank hinzufügen
- ALUSTECK_OT_snap_connector    - Snap-Mode für interaktives Verbinden
- ALUSTECK_OT_export_bom        - Bill of Materials CSV Export
- ALUSTECK_OT_export_bom_json   - Bill of Materials JSON Export
- ALUSTECK_OT_export_costs      - Kostenreport Export
- ALUSTECK_OT_export_shop_link  - Alusteck Shop Link Generator
- ALUSTECK_OT_validate_structure - Struktur-Validierung
"""

import bpy
import os
import json
import csv
from bpy.types import Operator
from bpy.props import FloatProperty, StringProperty, EnumProperty


# ============================================================================
# ADD OPERATORS - KOMPONENTEN AUS DATENBANK
# ============================================================================

class ALUSTECK_OT_add_profile(Operator):
    """Fügt ein Alusteck Vierkantrohr aus der Datenbank hinzu"""
    bl_idname = "alusteck.add_profile"
    bl_label = "Vierkantrohr"
    bl_options = {'REGISTER', 'UNDO'}
    
    length: float = FloatProperty(
        name="Länge",
        description="Profillänge in Metern",
        default=1.0,
        min=0.01,
        max=6.0,
        unit='LENGTH',
    )
    
    artikel_nr: str = ""
    kategorie: str = "25mm"
    
    def execute(self, context):
        from .. import ALUSTECK_DATABASE
        from ..components.materials import get_aluminum_material
        from ..components.profile import create_profile_mesh as create_profile_bmesh
        
        if not ALUSTECK_DATABASE:
            self.report({'ERROR'}, "Alusteck Datenbank nicht verfügbar!")
            return {'CANCELLED'}
        
        # Finde Profil in Datenbank
        profile_data = None
        for profil in ALUSTECK_DATABASE.get("kategorien", {}).get(self.kategorie, {}).get("profile", []):
            if profil.get("artikel_nr") == self.artikel_nr:
                profile_data = profil
                break
        
        if not profile_data:
            self.report({'ERROR'}, f"Profil {self.artikel_nr} nicht gefunden!")
            return {'CANCELLED'}
        
        # Konvertiere von mm zu m
        outer = profile_data["aussen_mm"] / 1000
        wall = profile_data["wandstaerke_mm"] / 1000
        
        bm = create_profile_bmesh(outer, wall, self.length)
        
        mesh = bpy.data.meshes.new(f"Alusteck_{profile_data['artikel_nr']}")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.data.materials.append(get_aluminum_material())
        
        # Custom Properties für Stückliste
        obj["alusteck_type"] = "profile"
        obj["alusteck_artikel_nr"] = profile_data["artikel_nr"]
        obj["alusteck_kategorie"] = self.kategorie
        obj["alusteck_length"] = self.length
        obj["alusteck_name"] = profile_data["name"]
        obj["alusteck_price"] = profile_data.get("preis_pro_meter", 5.90)
        
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        return {'FINISHED'}


class ALUSTECK_OT_add_connector(Operator):
    """Fügt einen Steckverbinder aus der Datenbank hinzu"""
    bl_idname = "alusteck.add_connector"
    bl_label = "Steckverbinder"
    bl_options = {'REGISTER', 'UNDO'}
    
    artikel_nr: str = ""
    kategorie: str = "25mm"
    
    def execute(self, context):
        from .. import ALUSTECK_DATABASE
        from ..components.materials import get_connector_material
        from ..components.connector import create_connector_cube
        
        if not ALUSTECK_DATABASE:
            self.report({'ERROR'}, "Alusteck Datenbank nicht verfügbar!")
            return {'CANCELLED'}
        
        # Finde Verbinder in Datenbank
        connector_data = None
        for verb in ALUSTECK_DATABASE.get("kategorien", {}).get(self.kategorie, {}).get("verbinder", []):
            if verb.get("artikel_nr") == self.artikel_nr:
                connector_data = verb
                break
        
        if not connector_data:
            self.report({'ERROR'}, f"Verbinder {self.artikel_nr} nicht gefunden!")
            return {'CANCELLED'}
        
        directions = connector_data.get("anzahl_wege", 6)
        size = connector_data.get("zapfen_laenge_mm", 25.0) / 1000  # mm zu m
        
        bm = create_connector_cube(size, directions)
        
        mesh = bpy.data.meshes.new(f"Alusteck_{connector_data['artikel_nr']}")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.data.materials.append(get_connector_material())
        
        obj["alusteck_type"] = "connector"
        obj["alusteck_artikel_nr"] = connector_data["artikel_nr"]
        obj["alusteck_kategorie"] = self.kategorie
        obj["alusteck_ways"] = directions
        obj["alusteck_name"] = connector_data["name"]
        obj["alusteck_price"] = connector_data.get("preis", 2.50)
        
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        return {'FINISHED'}


class ALUSTECK_OT_snap_connector(Operator):
    """WRAPPER: Ruft snap_move aus snap/engine.py auf"""
    bl_idname = "alusteck.snap_connector"
    bl_label = "Snap Verbinder zu Profilen"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """Delegiert zu snap/engine.py ALUSTECK_OT_snap_move"""
        return bpy.ops.alusteck.snap_move('INVOKE_DEFAULT')


# ============================================================================
# EXPORT - BOM (CSV)

class ALUSTECK_OT_export_bom(Operator):
    """Exportiert Stückliste als CSV"""
    bl_idname = "alusteck.export_bom"
    bl_label = "Export BOM (CSV)"
    
    def execute(self, context):
        from .. import ALUSTECK_DATABASE
        
        if not ALUSTECK_DATABASE:
            self.report({'ERROR'}, "Datenbank nicht geladen!")
            return {'CANCELLED'}
        
        # Sammle Komponenten
        components = {}
        
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
                    "price_per_unit": price,
                }
            
            components[artikel_nr]["count"] += 1
            
            if obj_type == "profile" and "alusteck_length" in obj:
                components[artikel_nr]["length"] += obj["alusteck_length"]
        
        # Schreibe CSV
        home = os.path.expanduser("~")
        csv_path = os.path.join(home, "Alusteck_BOM.csv")
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Header
                writer.writerow(["Artikel-Nr", "Name", "Typ", "Menge", "Länge (m)", "Preis/Einheit", "Gesamt"])
                
                # Zeilen
                total_cost = 0.0
                for artikel_nr in sorted(components.keys()):
                    comp = components[artikel_nr]
                    
                    if comp["type"] == "profile":
                        quantity = f"{comp['count']}x {comp['length']:.2f}m"
                        cost = comp["length"] * comp["price_per_unit"]
                    else:
                        quantity = comp["count"]
                        cost = comp["count"] * comp["price_per_unit"]
                    
                    writer.writerow([
                        artikel_nr,
                        comp["name"],
                        comp["type"],
                        quantity,
                        comp.get("length", ""),
                        f"{comp['price_per_unit']:.2f}",
                        f"{cost:.2f}"
                    ])
                    total_cost += cost
                
                # Gesamt
                writer.writerow([])
                writer.writerow(["GESAMT", "", "", "", "", "", f"{total_cost:.2f}€"])
            
            self.report({'INFO'}, f"✅ BOM exportiert: {csv_path}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Fehler beim Export: {e}")
            return {'CANCELLED'}


# ============================================================================
# EXPORT - BOM (JSON)
# ============================================================================

class ALUSTECK_OT_export_bom_json(Operator):
    """Exportiert Stückliste als JSON"""
    bl_idname = "alusteck.export_bom_json"
    bl_label = "Export BOM (JSON)"
    
    def execute(self, context):
        from .. import ALUSTECK_DATABASE
        
        if not ALUSTECK_DATABASE:
            self.report({'ERROR'}, "Datenbank nicht geladen!")
            return {'CANCELLED'}
        
        # Sammle Komponenten
        components = {}
        total_cost = 0.0
        
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
                    "length_m": 0.0,
                    "price_per_unit": price,
                }
            
            components[artikel_nr]["count"] += 1
            
            if obj_type == "profile" and "alusteck_length" in obj:
                components[artikel_nr]["length_m"] += obj["alusteck_length"]
                cost = obj["alusteck_length"] * price
            else:
                cost = price
            
            total_cost += cost
        
        # Schreibe JSON
        home = os.path.expanduser("~")
        json_path = os.path.join(home, "Alusteck_BOM.json")
        
        try:
            bom_data = {
                "meta": {
                    "created_from": context.blend_data.filepath,
                    "scene": context.scene.name,
                    "total_cost_eur": round(total_cost, 2),
                    "component_count": len(components),
                },
                "components": components
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(bom_data, f, indent=2, ensure_ascii=False)
            
            self.report({'INFO'}, f"✅ BOM exportiert: {json_path}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Fehler beim Export: {e}")
            return {'CANCELLED'}


# ============================================================================
# EXPORT - KOSTENREPORT
# ============================================================================

class ALUSTECK_OT_export_costs(Operator):
    """Exportiert detaillierten Kostenreport"""
    bl_idname = "alusteck.export_costs"
    bl_label = "Export Kostenreport"
    
    def execute(self, context):
        # Sammle Komponenten
        components = {}
        cost_by_type = {}
        total_cost = 0.0
        
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
                    "length_m": 0.0,
                    "total_cost": 0.0,
                    "price_per_unit": price,
                }
            
            components[artikel_nr]["count"] += 1
            
            if obj_type == "profile" and "alusteck_length" in obj:
                length = obj["alusteck_length"]
                components[artikel_nr]["length_m"] += length
                cost = length * price
            else:
                cost = price
            
            components[artikel_nr]["total_cost"] += cost
            
            if obj_type not in cost_by_type:
                cost_by_type[obj_type] = 0.0
            cost_by_type[obj_type] += cost
            
            total_cost += cost
        
        # Schreibe Report
        home = os.path.expanduser("~")
        report_path = os.path.join(home, "Alusteck_Costs.txt")
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("ALUSTECK BUILDER - KOSTENREPORT\n")
                f.write("=" * 60 + "\n\n")
                
                f.write("KOSTENAUFSCHLÜSSELUNG NACH TYP:\n")
                f.write("-" * 60 + "\n")
                for obj_type in sorted(cost_by_type.keys()):
                    cost = cost_by_type[obj_type]
                    percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                    f.write(f"{obj_type.upper():20s} {cost:10.2f}€  ({percentage:5.1f}%)\n")
                
                f.write("-" * 60 + "\n")
                f.write(f"GESAMT:              {total_cost:10.2f}€\n\n")
                
                f.write("DETAILLIERTE KOMPONENTEN:\n")
                f.write("-" * 60 + "\n")
                for artikel_nr in sorted(components.keys()):
                    comp = components[artikel_nr]
                    f.write(f"\n{comp['name']} ({artikel_nr})\n")
                    f.write(f"  Typ:     {comp['type']}\n")
                    f.write(f"  Menge:   {comp['count']}x\n")
                    if comp['length_m'] > 0:
                        f.write(f"  Länge:   {comp['length_m']:.2f}m\n")
                    f.write(f"  Kosten:  {comp['total_cost']:.2f}€\n")
                
                f.write("\n" + "=" * 60 + "\n")
            
            self.report({'INFO'}, f"✅ Kostenreport exportiert: {report_path}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Fehler beim Export: {e}")
            return {'CANCELLED'}


# ============================================================================
# EXPORT - SHOP LINK
# ============================================================================

class ALUSTECK_OT_export_shop_link(Operator):
    """Generiert Shop-Link für Warenkorb-Import"""
    bl_idname = "alusteck.export_shop_link"
    bl_label = "Export Shop Link"
    
    def execute(self, context):
        # Sammle Komponenten mit Artikel-Nummern
        cart_items = {}
        
        for obj in context.scene.objects:
            if "alusteck_artikel_nr" not in obj:
                continue
            
            artikel_nr = obj["alusteck_artikel_nr"]
            obj_type = obj.get("alusteck_type", "unknown")
            
            if artikel_nr not in cart_items:
                cart_items[artikel_nr] = 0
            
            if obj_type == "profile" and "alusteck_length" in obj:
                # Profile: Länge in Meter runden
                length = round(obj["alusteck_length"], 1)
                cart_items[artikel_nr] += length
            else:
                # Verbinder/Zubehör: Stück
                cart_items[artikel_nr] += 1
        
        # Baue Shop-Link
        base_url = "https://www.alusteck.de/"
        
        if cart_items:
            # QueryString für Warenkorb (Beispiel - anpassen bei echtem Shop)
            params = "&".join([f"{nr}={int(qty)}" for nr, qty in sorted(cart_items.items())])
            shop_link = f"{base_url}?add_to_cart={params}"
        else:
            shop_link = base_url
        
        # Speichere Link in Clipboard und Datei
        home = os.path.expanduser("~")
        link_path = os.path.join(home, "Alusteck_ShopLink.txt")
        
        try:
            with open(link_path, 'w', encoding='utf-8') as f:
                f.write("ALUSTECK SHOP LINK\n")
                f.write("=" * 80 + "\n\n")
                f.write("Link (zum Browser kopieren):\n")
                f.write(shop_link + "\n\n")
                f.write("Komponenten im Warenkorb:\n")
                for nr, qty in sorted(cart_items.items()):
                    f.write(f"  {nr}: {qty}\n")
            
            # Versuche in Clipboard zu kopieren
            try:
                import subprocess
                if os.name == 'nt':  # Windows
                    subprocess.run(['clip'], input=shop_link.encode(), check=True)
                    clipboard_msg = "(in Clipboard kopiert)"
                else:  # macOS/Linux
                    subprocess.run(['xclip', '-selection', 'clipboard'], 
                                 input=shop_link.encode(), check=True)
                    clipboard_msg = "(in Clipboard kopiert)"
            except:
                clipboard_msg = "(nicht in Clipboard kopierbar)"
            
            print(f"🛒 Shop-Link: {shop_link} {clipboard_msg}")
            self.report({'INFO'}, f"✅ Shop-Link generiert und gespeichert:\n{link_path}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Fehler beim Export: {e}")
            return {'CANCELLED'}


# ============================================================================
# VALIDATION (STUB - TODO später)
# ============================================================================

class ALUSTECK_OT_validate_structure(Operator):
    """Validiert Konstruktionsstruktur"""
    bl_idname = "alusteck.validate_structure"
    bl_label = "Validate Structure"
    
    def execute(self, context):
        """Führt Struktur-Validierung durch"""
        from ..snap.validation import get_validator, IssueLevel
        
        # Sammle alle Komponenten in der Szene
        components = list(context.scene.objects)
        
        # Validiere
        validator = get_validator()
        issues = validator.validate_structure(components)
        
        # Gebe Report aus
        validator.print_report()
        
        # Zähle Fehler
        errors = [i for i in issues if i.level == IssueLevel.ERROR]
        warnings = [i for i in issues if i.level == IssueLevel.WARNING]
        
        if errors:
            self.report({'ERROR'}, f"🔴 {len(errors)} Fehler gefunden!")
            return {'FINISHED'}
        elif warnings:
            self.report({'WARNING'}, f"🟡 {len(warnings)} Warnungen gefunden")
            return {'FINISHED'}
        else:
            self.report({'INFO'}, "✅ Struktur ist validiert!")
            return {'FINISHED'}


# ============================================================================
# REGISTRATION
# ============================================================================

def register_operators():
    """Registriert alle Operatoren"""
    bpy.utils.register_class(ALUSTECK_OT_add_profile)
    bpy.utils.register_class(ALUSTECK_OT_add_connector)
    bpy.utils.register_class(ALUSTECK_OT_snap_connector)
    bpy.utils.register_class(ALUSTECK_OT_export_bom)
    bpy.utils.register_class(ALUSTECK_OT_export_bom_json)
    bpy.utils.register_class(ALUSTECK_OT_export_costs)
    bpy.utils.register_class(ALUSTECK_OT_export_shop_link)
    bpy.utils.register_class(ALUSTECK_OT_validate_structure)


def unregister_operators():
    """Unregistriert alle Operatoren"""
    bpy.utils.unregister_class(ALUSTECK_OT_validate_structure)
    bpy.utils.unregister_class(ALUSTECK_OT_export_shop_link)
    bpy.utils.unregister_class(ALUSTECK_OT_export_costs)
    bpy.utils.unregister_class(ALUSTECK_OT_export_bom_json)
    bpy.utils.unregister_class(ALUSTECK_OT_export_bom)
    bpy.utils.unregister_class(ALUSTECK_OT_snap_connector)
    bpy.utils.unregister_class(ALUSTECK_OT_add_connector)
    bpy.utils.unregister_class(ALUSTECK_OT_add_profile)

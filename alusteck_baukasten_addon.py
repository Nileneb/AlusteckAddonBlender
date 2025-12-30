# ============================================
# ALUSTECK BAUKASTEN - Blender Addon
# Version: 1.0.0
# Blender: 4.0+ / 5.0+
# ============================================
# Installation: Edit > Preferences > Add-ons > Install
# Usage: Add > Mesh > Alusteck 25mm > [Component]
# ============================================

bl_info = {
    "name": "Alusteck Baukasten",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Add > Mesh > Alusteck 25mm",
    "description": "Alusteck 25x25mm Stecksystem Komponenten",
    "warning": "",
    "doc_url": "https://www.alusteck.de/25-mm-alu-stecksystem/",
    "category": "Add Mesh",
}

import bpy
import bmesh
import math
from bpy.types import Operator, Menu, Panel
from bpy.props import FloatProperty, EnumProperty, BoolProperty


# ============================================
# ALUSTECK KOMPONENTEN-DATENBANK
# Alle Maße in Metern (SI-Einheit)
# ============================================

ALUSTECK_PARTS = {
    # === PROFILE ===
    "profile_25x25": {
        "name": "Vierkantrohr 25x25x1.5mm",
        "type": "profile",
        "outer_size": 0.025,      # 25mm
        "wall_thickness": 0.0015,  # 1.5mm
        "inner_size": 0.022,       # 22mm (25 - 2*1.5)
        "default_length": 1.0,     # 1m default
        "material": "aluminum",
        "article_prefix": "VK25",
        "price_per_meter": 5.90,
    },
    "profile_20x20": {
        "name": "Vierkantrohr 20x20x1.5mm",
        "type": "profile",
        "outer_size": 0.020,
        "wall_thickness": 0.0015,
        "inner_size": 0.017,
        "default_length": 1.0,
        "material": "aluminum",
        "article_prefix": "VK20",
        "price_per_meter": 4.90,
    },
    "profile_30x30": {
        "name": "Vierkantrohr 30x30x2mm",
        "type": "profile",
        "outer_size": 0.030,
        "wall_thickness": 0.002,
        "inner_size": 0.026,
        "default_length": 1.0,
        "material": "aluminum",
        "article_prefix": "VK30",
        "price_per_meter": 7.90,
    },
    
    # === STECKVERBINDER 25mm ===
    "connector_2way_straight": {
        "name": "Verbinder gerade 2-Wege",
        "type": "connector",
        "profile_size": 0.025,
        "insert_depth": 0.025,     # 25mm Einstecktiefe
        "directions": 2,
        "angle": 180,
        "material": "polyamid",
        "article_nr": "2D25",
        "price": 1.50,
    },
    "connector_2way_90": {
        "name": "Winkelverbinder 90° 2-Wege",
        "type": "connector",
        "profile_size": 0.025,
        "insert_depth": 0.025,
        "directions": 2,
        "angle": 90,
        "material": "polyamid",
        "article_nr": "2W25",
        "price": 1.80,
    },
    "connector_3way_t": {
        "name": "T-Verbinder 3-Wege",
        "type": "connector",
        "profile_size": 0.025,
        "insert_depth": 0.025,
        "directions": 3,
        "angle": 90,
        "material": "polyamid",
        "article_nr": "3T25",
        "price": 2.20,
    },
    "connector_3way_corner": {
        "name": "Eckverbinder 3-Wege (Würfel)",
        "type": "connector",
        "profile_size": 0.025,
        "insert_depth": 0.025,
        "cube_size": 0.025,        # Würfelgröße
        "directions": 3,
        "material": "polyamid",
        "article_nr": "3E25",
        "price": 2.50,
    },
    "connector_4way_cross": {
        "name": "Kreuzverbinder 4-Wege",
        "type": "connector",
        "profile_size": 0.025,
        "insert_depth": 0.025,
        "directions": 4,
        "material": "polyamid",
        "article_nr": "4K25",
        "price": 2.80,
    },
    "connector_4way_corner": {
        "name": "Eckverbinder 4-Wege",
        "type": "connector",
        "profile_size": 0.025,
        "insert_depth": 0.025,
        "directions": 4,
        "material": "polyamid",
        "article_nr": "4E25",
        "price": 3.20,
    },
    "connector_5way": {
        "name": "Verbinder 5-Wege",
        "type": "connector",
        "profile_size": 0.025,
        "insert_depth": 0.025,
        "directions": 5,
        "material": "polyamid",
        "article_nr": "5V25",
        "price": 3.80,
    },
    "connector_6way": {
        "name": "Würfelverbinder 6-Wege",
        "type": "connector",
        "profile_size": 0.025,
        "insert_depth": 0.025,
        "cube_size": 0.025,
        "directions": 6,
        "material": "polyamid",
        "article_nr": "6W25",
        "price": 4.50,
    },
    
    # === ZUBEHÖR ===
    "endcap_25": {
        "name": "Endkappe 25x25mm",
        "type": "accessory",
        "profile_size": 0.025,
        "insert_depth": 0.010,
        "material": "polyamid",
        "article_nr": "EK25",
        "price": 0.40,
    },
    "foot_adjustable": {
        "name": "Stellfuß verstellbar",
        "type": "accessory",
        "profile_size": 0.025,
        "height_min": 0.015,
        "height_max": 0.030,
        "foot_diameter": 0.030,
        "material": "polyamid+steel",
        "article_nr": "SF25",
        "price": 2.90,
    },
}


# ============================================
# MATERIAL ERSTELLEN
# ============================================

def get_or_create_material(name, color, metallic=0.0, roughness=0.5):
    """Holt oder erstellt ein Material"""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def get_aluminum_material():
    return get_or_create_material(
        "Alusteck_Aluminum",
        (0.85, 0.85, 0.88, 1.0),
        metallic=0.9,
        roughness=0.3
    )


def get_connector_material(color="black"):
    colors = {
        "black": (0.1, 0.1, 0.1, 1.0),
        "gray": (0.5, 0.5, 0.5, 1.0),
        "white": (0.9, 0.9, 0.9, 1.0),
    }
    return get_or_create_material(
        f"Alusteck_Connector_{color}",
        colors.get(color, colors["black"]),
        metallic=0.0,
        roughness=0.4
    )


# ============================================
# MESH GENERATOREN
# ============================================

def create_profile_mesh(outer_size, wall_thickness, length):
    """Erstellt ein Hohlprofil (Vierkantrohr)"""
    bm = bmesh.new()
    
    inner_size = outer_size - 2 * wall_thickness
    half_outer = outer_size / 2
    half_inner = inner_size / 2
    half_length = length / 2
    
    # Äußeres Rechteck (Querschnitt)
    outer_verts = [
        (-half_outer, -half_outer),
        (half_outer, -half_outer),
        (half_outer, half_outer),
        (-half_outer, half_outer),
    ]
    
    # Inneres Rechteck (Hohlraum)
    inner_verts = [
        (-half_inner, -half_inner),
        (half_inner, -half_inner),
        (half_inner, half_inner),
        (-half_inner, half_inner),
    ]
    
    # Vorne (Z = -half_length)
    front_outer = [bm.verts.new((x, y, -half_length)) for x, y in outer_verts]
    front_inner = [bm.verts.new((x, y, -half_length)) for x, y in inner_verts]
    
    # Hinten (Z = +half_length)
    back_outer = [bm.verts.new((x, y, half_length)) for x, y in outer_verts]
    back_inner = [bm.verts.new((x, y, half_length)) for x, y in inner_verts]
    
    bm.verts.ensure_lookup_table()
    
    # Außenflächen
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([front_outer[i], front_outer[next_i], 
                      back_outer[next_i], back_outer[i]])
    
    # Innenflächen
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([front_inner[next_i], front_inner[i], 
                      back_inner[i], back_inner[next_i]])
    
    # Stirnflächen (vorne)
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([front_outer[next_i], front_outer[i], 
                      front_inner[i], front_inner[next_i]])
    
    # Stirnflächen (hinten)
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([back_outer[i], back_outer[next_i], 
                      back_inner[next_i], back_inner[i]])
    
    return bm


def create_connector_cube(size, directions):
    """Erstellt einen Würfelverbinder mit Zapfen"""
    bm = bmesh.new()
    
    half = size / 2
    zapfen_length = size  # Einsteckzapfen
    zapfen_size = size * 0.9  # Etwas kleiner als Profil-Innenmaß
    half_zapfen = zapfen_size / 2
    
    # Hauptwürfel
    bmesh.ops.create_cube(bm, size=size)
    
    # Zapfen in aktive Richtungen hinzufügen
    direction_vectors = {
        '+X': (1, 0, 0),
        '-X': (-1, 0, 0),
        '+Y': (0, 1, 0),
        '-Y': (0, -1, 0),
        '+Z': (0, 0, 1),
        '-Z': (0, 0, -1),
    }
    
    # Für 3-Wege Eckverbinder: +X, +Y, +Z
    if directions == 3:
        active_dirs = ['+X', '+Y', '+Z']
    elif directions == 6:
        active_dirs = list(direction_vectors.keys())
    elif directions == 4:
        active_dirs = ['+X', '-X', '+Y', '-Y']
    elif directions == 2:
        active_dirs = ['+Z', '-Z']
    else:
        active_dirs = ['+X', '+Y', '+Z', '-X', '-Y'][:directions]
    
    for dir_name in active_dirs:
        dx, dy, dz = direction_vectors[dir_name]
        
        # Zapfen-Startposition
        start_x = half * dx
        start_y = half * dy
        start_z = half * dz
        
        # Zapfen-Endposition
        end_x = (half + zapfen_length) * dx
        end_y = (half + zapfen_length) * dy
        end_z = (half + zapfen_length) * dz
        
        # Zapfen als extrudierter Quader
        # Vereinfacht: Box an Position
        center = (
            (start_x + end_x) / 2,
            (start_y + end_y) / 2,
            (start_z + end_z) / 2
        )
        
        # Zapfen-Größe je nach Richtung
        if dx != 0:
            zapfen_dims = (zapfen_length, zapfen_size, zapfen_size)
        elif dy != 0:
            zapfen_dims = (zapfen_size, zapfen_length, zapfen_size)
        else:
            zapfen_dims = (zapfen_size, zapfen_size, zapfen_length)
        
        # Zapfen-Vertices
        hx, hy, hz = zapfen_dims[0]/2, zapfen_dims[1]/2, zapfen_dims[2]/2
        cx, cy, cz = center
        
        verts = [
            bm.verts.new((cx-hx, cy-hy, cz-hz)),
            bm.verts.new((cx+hx, cy-hy, cz-hz)),
            bm.verts.new((cx+hx, cy+hy, cz-hz)),
            bm.verts.new((cx-hx, cy+hy, cz-hz)),
            bm.verts.new((cx-hx, cy-hy, cz+hz)),
            bm.verts.new((cx+hx, cy-hy, cz+hz)),
            bm.verts.new((cx+hx, cy+hy, cz+hz)),
            bm.verts.new((cx-hx, cy+hy, cz+hz)),
        ]
        
        # Faces für Zapfen
        bm.faces.new([verts[0], verts[1], verts[2], verts[3]])  # unten
        bm.faces.new([verts[4], verts[7], verts[6], verts[5]])  # oben
        bm.faces.new([verts[0], verts[4], verts[5], verts[1]])  # vorne
        bm.faces.new([verts[2], verts[6], verts[7], verts[3]])  # hinten
        bm.faces.new([verts[0], verts[3], verts[7], verts[4]])  # links
        bm.faces.new([verts[1], verts[5], verts[6], verts[2]])  # rechts
    
    return bm


# ============================================
# OPERATORS
# ============================================

class ALUSTECK_OT_add_profile(Operator):
    """Fügt ein Alusteck Vierkantrohr hinzu"""
    bl_idname = "mesh.alusteck_add_profile"
    bl_label = "Vierkantrohr 25x25mm"
    bl_options = {'REGISTER', 'UNDO'}
    
    length: FloatProperty(
        name="Länge",
        description="Profillänge in Metern",
        default=1.0,
        min=0.01,
        max=6.0,
        unit='LENGTH',
    )
    
    profile_size: EnumProperty(
        name="Profilgröße",
        items=[
            ('25', "25x25mm", "Standard 25x25x1.5mm"),
            ('20', "20x20mm", "Kompakt 20x20x1.5mm"),
            ('30', "30x30mm", "Schwerlast 30x30x2mm"),
        ],
        default='25',
    )
    
    def execute(self, context):
        sizes = {
            '25': (0.025, 0.0015),
            '20': (0.020, 0.0015),
            '30': (0.030, 0.002),
        }
        
        outer, wall = sizes[self.profile_size]
        
        bm = create_profile_mesh(outer, wall, self.length)
        
        mesh = bpy.data.meshes.new(f"Alusteck_Profil_{self.profile_size}")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.data.materials.append(get_aluminum_material())
        
        # Custom Properties für Stückliste
        obj["alusteck_type"] = "profile"
        obj["alusteck_size"] = self.profile_size
        obj["alusteck_length"] = self.length
        
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        return {'FINISHED'}


class ALUSTECK_OT_add_connector_3way(Operator):
    """Fügt einen 3-Wege Eckverbinder hinzu"""
    bl_idname = "mesh.alusteck_add_connector_3way"
    bl_label = "Eckverbinder 3-Wege"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bm = create_connector_cube(0.025, 3)
        
        mesh = bpy.data.meshes.new("Alusteck_Eckverbinder_3W")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.data.materials.append(get_connector_material("black"))
        
        obj["alusteck_type"] = "connector"
        obj["alusteck_ways"] = 3
        
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        return {'FINISHED'}


class ALUSTECK_OT_add_connector_6way(Operator):
    """Fügt einen 6-Wege Würfelverbinder hinzu"""
    bl_idname = "mesh.alusteck_add_connector_6way"
    bl_label = "Würfelverbinder 6-Wege"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bm = create_connector_cube(0.025, 6)
        
        mesh = bpy.data.meshes.new("Alusteck_Wuerfel_6W")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.data.materials.append(get_connector_material("black"))
        
        obj["alusteck_type"] = "connector"
        obj["alusteck_ways"] = 6
        
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        return {'FINISHED'}


class ALUSTECK_OT_add_connector_4way(Operator):
    """Fügt einen 4-Wege Kreuzverbinder hinzu"""
    bl_idname = "mesh.alusteck_add_connector_4way"
    bl_label = "Kreuzverbinder 4-Wege"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bm = create_connector_cube(0.025, 4)
        
        mesh = bpy.data.meshes.new("Alusteck_Kreuz_4W")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.data.materials.append(get_connector_material("black"))
        
        obj["alusteck_type"] = "connector"
        obj["alusteck_ways"] = 4
        
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        return {'FINISHED'}


class ALUSTECK_OT_add_connector_2way(Operator):
    """Fügt einen 2-Wege Verbinder hinzu"""
    bl_idname = "mesh.alusteck_add_connector_2way"
    bl_label = "Verbinder gerade 2-Wege"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bm = create_connector_cube(0.025, 2)
        
        mesh = bpy.data.meshes.new("Alusteck_Gerade_2W")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.data.materials.append(get_connector_material("black"))
        
        obj["alusteck_type"] = "connector"
        obj["alusteck_ways"] = 2
        
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        return {'FINISHED'}


# ============================================
# MENÜ
# ============================================

class ALUSTECK_MT_add_menu(Menu):
    bl_idname = "ALUSTECK_MT_add_menu"
    bl_label = "Alusteck 25mm"
    
    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Profile:", icon='MOD_ARRAY')
        layout.operator("mesh.alusteck_add_profile", text="Vierkantrohr 25x25mm", icon='MESH_CUBE')
        
        layout.separator()
        layout.label(text="Steckverbinder:", icon='PIVOT_INDIVIDUAL')
        layout.operator("mesh.alusteck_add_connector_2way", text="Verbinder 2-Wege", icon='ARROW_LEFTRIGHT')
        layout.operator("mesh.alusteck_add_connector_3way", text="Eckverbinder 3-Wege", icon='ORIENTATION_LOCAL')
        layout.operator("mesh.alusteck_add_connector_4way", text="Kreuzverbinder 4-Wege", icon='ADD')
        layout.operator("mesh.alusteck_add_connector_6way", text="Würfelverbinder 6-Wege", icon='MESH_CUBE')


def menu_func(self, context):
    self.layout.menu("ALUSTECK_MT_add_menu", icon='MOD_BUILD')


# ============================================
# STÜCKLISTEN-PANEL
# ============================================

class ALUSTECK_PT_panel(Panel):
    bl_label = "Alusteck Stückliste"
    bl_idname = "ALUSTECK_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Alusteck"
    
    def draw(self, context):
        layout = self.layout
        
        # Zähle Komponenten
        profiles = []
        connectors = {"2": 0, "3": 0, "4": 0, "6": 0}
        total_length = 0.0
        
        for obj in context.scene.objects:
            if "alusteck_type" in obj:
                if obj["alusteck_type"] == "profile":
                    length = obj.get("alusteck_length", 1.0)
                    profiles.append(length)
                    total_length += length
                elif obj["alusteck_type"] == "connector":
                    ways = str(obj.get("alusteck_ways", 0))
                    if ways in connectors:
                        connectors[ways] += 1
        
        # Anzeige
        box = layout.box()
        box.label(text="Komponenten:", icon='LINENUMBERS_ON')
        
        if profiles:
            box.label(text=f"Profile: {len(profiles)} Stück")
            box.label(text=f"Gesamtlänge: {total_length:.2f}m")
        
        for ways, count in connectors.items():
            if count > 0:
                box.label(text=f"Verbinder {ways}-Wege: {count}x")
        
        # Kostenberechnung
        layout.separator()
        box2 = layout.box()
        box2.label(text="Geschätzte Kosten:", icon='FUND')
        
        profile_cost = total_length * 5.90
        connector_cost = sum([
            connectors["2"] * 1.50,
            connectors["3"] * 2.50,
            connectors["4"] * 2.80,
            connectors["6"] * 4.50,
        ])
        total_cost = profile_cost + connector_cost
        
        box2.label(text=f"Profile: {profile_cost:.2f}€")
        box2.label(text=f"Verbinder: {connector_cost:.2f}€")
        box2.label(text=f"GESAMT: {total_cost:.2f}€")


# ============================================
# REGISTRIERUNG
# ============================================

classes = [
    ALUSTECK_OT_add_profile,
    ALUSTECK_OT_add_connector_2way,
    ALUSTECK_OT_add_connector_3way,
    ALUSTECK_OT_add_connector_4way,
    ALUSTECK_OT_add_connector_6way,
    ALUSTECK_MT_add_menu,
    ALUSTECK_PT_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    print("Alusteck Baukasten Addon geladen!")


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Alusteck Baukasten Addon entladen.")


if __name__ == "__main__":
    register()

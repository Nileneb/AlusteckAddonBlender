"""
UI Menus - Component selection menus
"""

import bpy
from bpy.types import Menu


class ALUSTECK_MT_add_menu(Menu):
    """Dynamisches Menü für Komponenten aus Datenbank"""
    bl_idname = "ALUSTECK_MT_add_menu"
    bl_label = "Alusteck Stecksystem"
    
    def draw(self, context):
        from .. import ALUSTECK_DATABASE
        
        layout = self.layout
        
        if not ALUSTECK_DATABASE:
            layout.label(text="⚠️ Datenbank nicht verfügbar!", icon='ERROR')
            return
        
        kategorien = ALUSTECK_DATABASE.get("kategorien", {})
        
        for kategorie_name in sorted(kategorien.keys()):
            layout.separator()
            layout.label(text=f"{kategorie_name} System", icon='MOD_BUILD')
            
            kat_data = kategorien[kategorie_name]
            
            # Profile
            profile_list = kat_data.get("profile", [])
            if profile_list:
                layout.label(text="  ▸ Profile", icon='MOD_ARRAY')
                for profil in profile_list:
                    op = layout.operator(
                        "alusteck.add_profile",
                        text=f"    {profil['name']}"
                    )
                    op.artikel_nr = profil["artikel_nr"]
                    op.kategorie = kategorie_name
            
            # Verbinder
            verbinder_list = kat_data.get("verbinder", [])
            if verbinder_list:
                layout.label(text="  ▸ Steckverbinder", icon='PIVOT_INDIVIDUAL')
                for verb in verbinder_list:
                    op = layout.operator(
                        "alusteck.add_connector",
                        text=f"    {verb['name']}"
                    )
                    op.artikel_nr = verb["artikel_nr"]
                    op.kategorie = kategorie_name


def menu_func(self, context):
    """Hook für Add > Mesh > Alusteck"""
    self.layout.menu("ALUSTECK_MT_add_menu", icon='MOD_BUILD')


def register():
    """Registriert alle Menus"""
    bpy.utils.register_class(ALUSTECK_MT_add_menu)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    """Unregistriert alle Menus"""
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(ALUSTECK_MT_add_menu)


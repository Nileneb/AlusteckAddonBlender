"""Blender sidebar panels for Alusteck Builder."""

try:
    import bpy
    HAS_BLENDER = True
except ImportError:
    bpy = None
    HAS_BLENDER = False


if HAS_BLENDER:
    class ALUSTECK_PT_main_panel(bpy.types.Panel):
        """Main Alusteck Builder sidebar panel."""
        bl_label = "Alusteck Builder"
        bl_idname = "ALUSTECK_PT_main_panel"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Alusteck"

        def draw(self, context):  # noqa: D401
            layout = self.layout
            layout.label(text="Komponente hinzufügen", icon='ADD')
            
            col = layout.column(align=True)
            # Use the menu instead of direct operator calls (proper Blender 5.0 approach)
            col.menu("ALUSTECK_MT_add_menu", text="Komponenten", icon='PLUGIN')
            
            layout.separator()
            layout.label(text="Snap Engine", icon='SNAP_ON')
            col = layout.column(align=True)
            col.operator("alusteck.snap_move", text="Snap verschieben", icon='ARROW_LEFTRIGHT')
            col.operator("alusteck.validate_structure", text="Struktur validieren", icon='CHECKMARK')
            
            layout.separator()
            layout.label(text="Export", icon='EXPORT')
            col = layout.column(align=True)
            col.operator("alusteck.export_bom", text="Stückliste (CSV)", icon='FILE_TEXT')
            col.operator("alusteck.export_costs", text="Kostenberechnung", icon='MONEY')
            col.operator("alusteck.export_shop_link", text="Shop-Link", icon='WORLD')

if HAS_BLENDER:
    class ALUSTECK_PT_database_panel(bpy.types.Panel):
        """Database information panel."""
        bl_label = "Komponenten"
        bl_idname = "ALUSTECK_PT_database_panel"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Alusteck"
        bl_parent_id = "ALUSTECK_PT_main_panel"
        bl_options = {"DEFAULT_CLOSED"}

        def draw(self, context):  # noqa: D401
            layout = self.layout
            layout.label(text="Verfügbare Komponenten:")
            
            # Load database info (placeholder)
            try:
                from alusteck_builder.core import database
                db = database.load_json("alusteck_database.json")
                
                if db and "systems" in db:
                    for system_name in ["20mm", "25mm", "30mm"]:
                        if system_name in db["systems"]:
                            box = layout.box()
                            system = db["systems"][system_name]
                            box.label(text=system_name, icon='CUBE')
            except Exception as e:
                layout.label(text=f"Fehler beim Laden: {e}")


if HAS_BLENDER:
    classes = (
        ALUSTECK_PT_main_panel,
        ALUSTECK_PT_database_panel,
    )
else:
    classes = tuple()


def register_panels():
    if not HAS_BLENDER:
        return
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_panels():
    if not HAS_BLENDER:
        return
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

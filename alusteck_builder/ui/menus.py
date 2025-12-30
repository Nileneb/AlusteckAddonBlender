"""Blender menus for Alusteck Builder - Add menu integration."""

try:
    import bpy
    HAS_BLENDER = True
except ImportError:
    bpy = None
    HAS_BLENDER = False


if HAS_BLENDER:
    class ALUSTECK_MT_add_menu(bpy.types.Menu):
        """Add menu for Alusteck components."""
        bl_idname = "ALUSTECK_MT_add_menu"
        bl_label = "Alusteck Builder"

        def draw(self, context):  # noqa: D401
            layout = self.layout
            
            # Systems
            layout.label(text="Systeme:")
            row = layout.row(align=True)
            row.label(text="20mm")
            row.label(text="25mm")
            row.label(text="30mm")
            
            # Components
            layout.separator()
            layout.label(text="Komponenten:")
            col = layout.column(align=True)
            
            # Use properties dict to pass operator arguments (Blender 5.0 compatible)
            op = col.operator("alusteck.add_component", text="Profil")
            if op:
                op.component_type = "PROFILE"
                op.system = "25"
            
            op = col.operator("alusteck.add_component", text="Verbinder")
            if op:
                op.component_type = "CONNECTOR"
                op.system = "25"
            
            op = col.operator("alusteck.add_component", text="Zubehör")
            if op:
                op.component_type = "ACCESSORY"
            op.system = "25"


def _menu_func(self, context):
    """Add Alusteck menu to Add > Mesh menu."""
    self.layout.menu("ALUSTECK_MT_add_menu", icon='PLUGIN')


if HAS_BLENDER:
    classes = (ALUSTECK_MT_add_menu,)
else:
    classes = tuple()


def register_menus():
    if not HAS_BLENDER:
        return
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(_menu_func)


def unregister_menus():
    if not HAS_BLENDER:
        return
    bpy.types.VIEW3D_MT_mesh_add.remove(_menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

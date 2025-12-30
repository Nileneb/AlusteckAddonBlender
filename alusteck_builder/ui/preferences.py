"""Addon preferences for API keys and settings."""

try:
    import bpy
    from bpy.props import StringProperty, IntProperty, BoolProperty
except ImportError:
    bpy = None
    StringProperty = IntProperty = BoolProperty = None


class ALUSTECK_AddonPreferences(bpy.types.AddonPreferences if bpy else object):
    """Alusteck Builder addon preferences."""
    bl_idname = "alusteck_builder"

    claude_api_key: StringProperty(
        name="Claude API Key",
        description="Your Anthropic Claude API key (for AI features)",
        subtype='PASSWORD',
        default="",
    ) if bpy else None

    snap_distance_mm: IntProperty(
        name="Snap Distance (mm)",
        description="Distance threshold for snapping (mm)",
        default=50,
        min=5,
        max=500,
    ) if bpy else None

    auto_validate: BoolProperty(
        name="Auto-validate Structure",
        description="Automatically validate structure after placement",
        default=True,
    ) if bpy else None

    def draw(self, context):  # noqa: D401
        layout = self.layout
        
        box = layout.box()
        box.label(text="AI Features", icon='PLAY')
        box.prop(self, "claude_api_key")
        
        box = layout.box()
        box.label(text="Snap Engine", icon='MAGNET')
        box.prop(self, "snap_distance_mm")
        box.prop(self, "auto_validate")


classes = (ALUSTECK_AddonPreferences,) if bpy else tuple()


def register_preferences():
    if not bpy:
        return
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_preferences():
    if not bpy:
        return
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

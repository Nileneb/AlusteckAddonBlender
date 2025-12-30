"""UI scaffolding for Blender panels and operators."""

from alusteck_builder.ui import operators, panels, menus, preferences


def register():
    """Register all UI submodules."""
    operators.register_operators()
    panels.register_panels()
    menus.register_menus()
    preferences.register_preferences()


def unregister():
    """Unregister all UI submodules."""
    preferences.unregister_preferences()
    menus.unregister_menus()
    panels.unregister_panels()
    operators.unregister_operators()

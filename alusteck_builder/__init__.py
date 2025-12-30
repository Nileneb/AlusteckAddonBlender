"""Alusteck Builder Blender Addon entry point."""

bl_info = {
    "name": "Alusteck Builder",
    "author": "Alusteck",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Alusteck",
    "description": "Parametric Alusteck builder with snapping and AI helpers.",
    "category": "Mesh",
}

# Lazy imports to keep registration light during scaffolding
def register():
    """Blender registration hook."""
    try:
        from alusteck_builder import ui
    except ImportError:
        return None
    ui.register()
    return None


def unregister():
    """Blender unregistration hook."""
    try:
        from alusteck_builder import ui
    except ImportError:
        return None
    ui.unregister()
    return None


if __name__ == "__main__":
    register()

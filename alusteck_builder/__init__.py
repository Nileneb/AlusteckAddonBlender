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


def register():
    """Blender registration hook - register all submodules."""
    try:
        # Register UI (operators, panels, menus, preferences)
        from alusteck_builder import ui
        ui.register()
    except Exception as e:
        print(f"Error registering UI module: {e}")
    
    try:
        # Register Snap engine and handlers
        from alusteck_builder.snap import engine as snap_engine
        snap_engine.register()
    except Exception as e:
        print(f"Error registering Snap engine: {e}")
    
    print("✅ Alusteck Builder Addon registered successfully!")


def unregister():
    """Blender unregistration hook - unregister all submodules."""
    try:
        # Unregister Snap engine
        from alusteck_builder.snap import engine as snap_engine
        snap_engine.unregister()
    except Exception as e:
        print(f"Error unregistering Snap engine: {e}")
    
    try:
        # Unregister UI
        from alusteck_builder import ui
        ui.unregister()
    except Exception as e:
        print(f"Error unregistering UI module: {e}")
    
    print("✅ Alusteck Builder Addon unregistered.")


if __name__ == "__main__":
    register()

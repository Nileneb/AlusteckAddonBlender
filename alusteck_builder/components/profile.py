"""Profile mesh generator for hollow square tubes (Vierkantrohr)."""

try:
    import bmesh
except ImportError:
    bmesh = None


def create_profile_mesh(profile_spec: dict):
    """
    Generate a hollow square tube profile mesh.
    
    Args:
        profile_spec: Dict with keys:
            - system: "20", "25", or "30" (size in mm)
            - length_mm: Profile length
            - steg: Optional steg configuration dict
            
    Returns:
        bpy.types.Object or None if outside Blender
    """
    if not bmesh:
        raise RuntimeError("BMesh not available outside Blender")
    
    # Get system constants (mm)
    system = profile_spec.get("system", "25")
    system_map = {
        "20": {"outer": 0.020, "wall": 0.0015},
        "25": {"outer": 0.025, "wall": 0.0015},
        "30": {"outer": 0.030, "wall": 0.002},
    }
    specs = system_map.get(system, system_map["25"])
    
    outer = specs["outer"]
    wall = specs["wall"]
    length = profile_spec.get("length_mm", 1000.0) / 1000.0  # Convert mm to m
    
    # Create BMesh
    bm = _create_hollow_profile(outer, wall, length)
    
    # Create mesh and object (requires Blender context)
    try:
        import bpy
        mesh = bpy.data.meshes.new("Profile")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new("Profile", mesh)
        bpy.context.collection.objects.link(obj)
        return obj
    except (ImportError, RuntimeError):
        bm.free()
        return None


def _create_hollow_profile(outer_size: float, wall_thickness: float, length: float) -> object:
    """
    Create the actual hollow profile geometry.
    
    Args:
        outer_size: Outer dimension (m)
        wall_thickness: Wall thickness (m)
        length: Profile length (m)
    """
    bm = bmesh.new()
    
    inner_size = outer_size - 2 * wall_thickness
    half_outer = outer_size / 2
    half_inner = inner_size / 2
    half_length = length / 2
    
    # Outer corners (cross-section)
    outer_verts = [
        (-half_outer, -half_outer),
        (half_outer, -half_outer),
        (half_outer, half_outer),
        (-half_outer, half_outer),
    ]
    
    # Inner corners (hollow)
    inner_verts = [
        (-half_inner, -half_inner),
        (half_inner, -half_inner),
        (half_inner, half_inner),
        (-half_inner, half_inner),
    ]
    
    # Front face (Z = -half_length)
    front_outer = [bm.verts.new((x, y, -half_length)) for x, y in outer_verts]
    front_inner = [bm.verts.new((x, y, -half_length)) for x, y in inner_verts]
    
    # Back face (Z = +half_length)
    back_outer = [bm.verts.new((x, y, half_length)) for x, y in outer_verts]
    back_inner = [bm.verts.new((x, y, half_length)) for x, y in inner_verts]
    
    bm.verts.ensure_lookup_table()
    
    # Outer walls
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([front_outer[i], front_outer[next_i],
                      back_outer[next_i], back_outer[i]])
    
    # Inner walls
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([front_inner[next_i], front_inner[i],
                      back_inner[i], back_inner[next_i]])
    
    # Front end cap
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([front_outer[i], front_inner[i],
                      front_inner[next_i], front_outer[next_i]])
    
    # Back end cap
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([back_inner[i], back_outer[i],
                      back_outer[next_i], back_inner[next_i]])
    
    return bm

"""Connector mesh generator for multi-way connectors (2-6 ways)."""

try:
    import bmesh
except ImportError:
    bmesh = None


def create_connector_mesh(connector_spec: dict):
    """
    Generate a connector cube with insertion points.
    
    Args:
        connector_spec: Dict with keys:
            - system: "20", "25", or "30" (size in mm)
            - id: Article number (e.g. "3E25K")
            
    Returns:
        bpy.types.Object or None if outside Blender
    """
    if not bmesh:
        raise RuntimeError("BMesh not available outside Blender")
    
    # Get system constants (mm)
    system = connector_spec.get("system", "25")
    system_map = {
        "20": 0.020,
        "25": 0.025,
        "30": 0.030,
    }
    connector_size = system_map.get(system, 0.025)
    
    # Infer connector type from ID or default to 6-way
    connector_id = connector_spec.get("id", "6W")
    if "2D" in connector_id or "gerade" in str(connector_spec):
        directions = 2
    elif "3E" in connector_id or "3-Wege" in str(connector_spec):
        directions = 3
    elif "4K" in connector_id or "4-Wege" in str(connector_spec):
        directions = 4
    elif "6W" in connector_id:
        directions = 6
    else:
        directions = 6
    
    # Create BMesh
    bm = _create_connector_cube(connector_size, directions)
    
    # Create mesh and object (requires Blender context)
    try:
        import bpy
        mesh = bpy.data.meshes.new("Connector")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new("Connector", mesh)
        bpy.context.collection.objects.link(obj)
        return obj
    except (ImportError, RuntimeError):
        bm.free()
        return None


def _create_connector_cube(size: float, directions: int) -> object:
    """
    Create a connector cube with insertion zapfen.
    
    Args:
        size: Cube size (m)
        directions: Number of connection directions (2, 3, 4, or 6)
    """
    bm = bmesh.new()
    
    # Create base cube
    bmesh.ops.create_cube(bm, size=size)
    
    # Zapfen specifications
    zapfen_length = size
    zapfen_size = size * 0.88  # Slightly smaller than profile inner
    half_zapfen = zapfen_size / 2
    half_cube = size / 2
    
    # Direction vectors: (name, vector)
    directions_map = {
        '+X': (1, 0, 0),
        '-X': (-1, 0, 0),
        '+Y': (0, 1, 0),
        '-Y': (0, -1, 0),
        '+Z': (0, 0, 1),
        '-Z': (0, 0, -1),
    }
    
    # Determine active directions
    if directions == 2:
        active_dirs = ['+Z', '-Z']
    elif directions == 3:
        active_dirs = ['+X', '+Y', '+Z']
    elif directions == 4:
        active_dirs = ['+X', '-X', '+Y', '-Y']
    elif directions == 6:
        active_dirs = ['+X', '-X', '+Y', '-Y', '+Z', '-Z']
    else:
        active_dirs = []
    
    # Add zapfen for each active direction
    for dir_name in active_dirs:
        dx, dy, dz = directions_map[dir_name]
        
        # Position: cube surface + zapfen length/2
        pos_offset = half_cube + zapfen_length / 2
        center_x = dx * pos_offset
        center_y = dy * pos_offset
        center_z = dz * pos_offset
        
        # Create zapfen as a small cube
        zapfen_verts = [
            (center_x - half_zapfen, center_y - half_zapfen, center_z - half_zapfen),
            (center_x + half_zapfen, center_y - half_zapfen, center_z - half_zapfen),
            (center_x + half_zapfen, center_y + half_zapfen, center_z - half_zapfen),
            (center_x - half_zapfen, center_y + half_zapfen, center_z - half_zapfen),
            (center_x - half_zapfen, center_y - half_zapfen, center_z + half_zapfen),
            (center_x + half_zapfen, center_y - half_zapfen, center_z + half_zapfen),
            (center_x + half_zapfen, center_y + half_zapfen, center_z + half_zapfen),
            (center_x - half_zapfen, center_y + half_zapfen, center_z + half_zapfen),
        ]
        
        # Add vertices
        zapfen_vs = [bm.verts.new(v) for v in zapfen_verts]
        bm.verts.ensure_lookup_table()
        
        # Add faces (cube)
        faces_indices = [
            [0, 1, 2, 3],  # Bottom
            [4, 7, 6, 5],  # Top
            [0, 4, 5, 1],  # Front
            [2, 6, 7, 3],  # Back
            [0, 3, 7, 4],  # Left
            [1, 5, 6, 2],  # Right
        ]
        for face_idx in faces_indices:
            bm.faces.new([zapfen_vs[i] for i in face_idx])
    
    return bm

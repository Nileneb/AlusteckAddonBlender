"""
Material definitions and management.
"""

import bpy


def get_or_create_material(name, color, metallic=0.0, roughness=0.5):
    """Holt oder erstellt ein Material."""
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
    """Aluminium-Material für Profile."""
    return get_or_create_material(
        "Alusteck_Aluminum",
        (0.85, 0.85, 0.88, 1.0),
        metallic=0.9,
        roughness=0.3
    )


def get_connector_material():
    """Schwarz-Material für Verbinder."""
    return get_or_create_material(
        "Alusteck_Connector_Black",
        (0.1, 0.1, 0.1, 1.0),
        metallic=0.0,
        roughness=0.4
    )

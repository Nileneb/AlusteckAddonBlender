"""
COMPONENTS MODULE - Mesh-Generator für Alusteck-Komponenten
==========================================================

Sub-Module:
- profile.py     - Profil-Mesh (hohle Vierkantrohr mit optional Stegen)
- connector.py   - Verbinder-Mesh (2-6 Wege mit Zapfen)
- accessory.py   - Zubehör-Mesh (Kappen, Gleiter, Füße)
- materials.py   - Material-Definitionen (Alu, Kunststoff)
"""

from .profile import create_profile_mesh
from .connector import create_connector_mesh
from .materials import (
    get_or_create_material,
    get_aluminum_material,
    get_connector_material,
)

__all__ = [
    # Mesh Generators
    "create_profile_mesh",
    "create_connector_mesh",
    
    # Materials
    "get_or_create_material",
    "get_aluminum_material",
    "get_connector_material",
]

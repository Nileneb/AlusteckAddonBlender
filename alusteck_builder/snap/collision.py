"""
🔍 COLLISION DETECTION
=======================
Präzise Kollisionserkennung für Alusteck-Komponenten
"""

import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from typing import List, Tuple, Optional


class CollisionDetector:
    """
    Erweiterte Kollisionserkennung mit BVH-Trees
    """
    
    def __init__(self):
        self.bvh_cache = {}  # object_name -> BVHTree
        self.cache_valid = {}  # object_name -> is_valid
    
    def check_collision(self, obj_a: bpy.types.Object, 
                       obj_b: bpy.types.Object,
                       margin: float = 0.001) -> bool:
        """
        Prüft ob zwei Objekte kollidieren
        
        Args:
            obj_a, obj_b: Zu prüfende Objekte
            margin: Sicherheitsabstand in Metern (1mm)
            
        Returns:
            True wenn Kollision
        """
        # Schneller AABB-Test zuerst
        if not self._aabb_intersect(obj_a, obj_b):
            return False
        
        # Detaillierter BVH-Test
        return self._bvh_intersect(obj_a, obj_b, margin)
    
    def check_collision_with_scene(self, obj: bpy.types.Object,
                                  exclude: List[bpy.types.Object] = None,
                                  margin: float = 0.001) -> Optional[bpy.types.Object]:
        """
        Prüft ob Objekt mit irgendetwas in der Szene kollidiert
        
        Returns:
            Erstes kollidierende Objekt oder None
        """
        exclude = exclude or []
        exclude_names = {e.name for e in exclude}
        
        for other in bpy.context.scene.objects:
            if other == obj:
                continue
            if other.name in exclude_names:
                continue
            if other.type != 'MESH':
                continue
            if not other.visible_get():
                continue
            
            if self.check_collision(obj, other, margin):
                return other
        
        return None
    
    def get_clearance(self, obj_a: bpy.types.Object,
                     obj_b: bpy.types.Object) -> float:
        """
        Berechnet minimalen Abstand zwischen zwei Objekten
        
        Returns:
            Abstand in Metern (negativ = Überlappung)
        """
        bvh_a = self._get_bvh(obj_a)
        bvh_b = self._get_bvh(obj_b)
        
        if not bvh_a or not bvh_b:
            return float('inf')
        
        # Finde nächste Punkte
        min_dist = float('inf')
        
        # Sample Punkte auf obj_a und finde nächsten Punkt auf obj_b
        mesh_a = obj_a.data
        for vert in mesh_a.vertices:
            world_co = obj_a.matrix_world @ vert.co
            location, normal, index, distance = bvh_b.find_nearest(world_co)
            
            if distance is not None and distance < min_dist:
                min_dist = distance
        
        return min_dist
    
    # ------------------------------------------------------------------------
    # AABB (Axis-Aligned Bounding Box)
    # ------------------------------------------------------------------------
    
    def _aabb_intersect(self, obj_a: bpy.types.Object,
                       obj_b: bpy.types.Object) -> bool:
        """Schneller Bounding-Box Test"""
        bbox_a = self._get_world_bbox(obj_a)
        bbox_b = self._get_world_bbox(obj_b)
        
        min_a = Vector((min(v.x for v in bbox_a),
                       min(v.y for v in bbox_a),
                       min(v.z for v in bbox_a)))
        max_a = Vector((max(v.x for v in bbox_a),
                       max(v.y for v in bbox_a),
                       max(v.z for v in bbox_a)))
        
        min_b = Vector((min(v.x for v in bbox_b),
                       min(v.y for v in bbox_b),
                       min(v.z for v in bbox_b)))
        max_b = Vector((max(v.x for v in bbox_b),
                       max(v.y for v in bbox_b),
                       max(v.z for v in bbox_b)))
        
        return (min_a.x <= max_b.x and max_a.x >= min_b.x and
                min_a.y <= max_b.y and max_a.y >= min_b.y and
                min_a.z <= max_b.z and max_a.z >= min_b.z)
    
    def _get_world_bbox(self, obj: bpy.types.Object) -> List[Vector]:
        """Gibt Welt-Bounding-Box zurück"""
        return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    # ------------------------------------------------------------------------
    # BVH (Bounding Volume Hierarchy)
    # ------------------------------------------------------------------------
    
    def _bvh_intersect(self, obj_a: bpy.types.Object,
                      obj_b: bpy.types.Object,
                      margin: float) -> bool:
        """Präziser BVH-Tree Overlap Test"""
        bvh_a = self._get_bvh(obj_a)
        bvh_b = self._get_bvh(obj_b)
        
        if not bvh_a or not bvh_b:
            return False
        
        # BVH Overlap Test
        overlap = bvh_a.overlap(bvh_b)
        
        if not overlap:
            return False
        
        # Bei Überlappung: Prüfe ob innerhalb Margin
        for pair in overlap[:10]:  # Max 10 Paare checken
            # Hole Face-Zentren
            face_a_idx, face_b_idx = pair
            
            mesh_a = obj_a.data
            mesh_b = obj_b.data
            
            if face_a_idx >= len(mesh_a.polygons) or face_b_idx >= len(mesh_b.polygons):
                continue
            
            face_a_center = obj_a.matrix_world @ mesh_a.polygons[face_a_idx].center
            face_b_center = obj_b.matrix_world @ mesh_b.polygons[face_b_idx].center
            
            dist = (face_a_center - face_b_center).length
            
            if dist < margin:
                return True
        
        return False
    
    def _get_bvh(self, obj: bpy.types.Object) -> Optional[BVHTree]:
        """
        Gibt BVH-Tree für Objekt zurück (gecacht)
        """
        # Cache prüfen
        if obj.name in self.bvh_cache:
            if self._is_cache_valid(obj):
                return self.bvh_cache[obj.name]
        
        # BVH neu erstellen
        bvh = self._create_bvh(obj)
        
        if bvh:
            self.bvh_cache[obj.name] = bvh
            self._mark_cache_valid(obj)
        
        return bvh
    
    def _create_bvh(self, obj: bpy.types.Object) -> Optional[BVHTree]:
        """Erstellt BVH-Tree aus Mesh"""
        if obj.type != 'MESH':
            return None
        
        # BMesh erstellen
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
        
        # BVH erstellen
        bvh = BVHTree.FromBMesh(bm)
        
        bm.free()
        return bvh
    
    def _is_cache_valid(self, obj: bpy.types.Object) -> bool:
        """Prüft ob Cache noch gültig ist"""
        # TODO: Prüfe ob Mesh oder Transform geändert wurde
        return self.cache_valid.get(obj.name, False)
    
    def _mark_cache_valid(self, obj: bpy.types.Object):
        """Markiert Cache als gültig"""
        self.cache_valid[obj.name] = True
    
    def invalidate_cache(self, obj_name: str = None):
        """Invalidiert Cache"""
        if obj_name:
            if obj_name in self.bvh_cache:
                del self.bvh_cache[obj_name]
            if obj_name in self.cache_valid:
                del self.cache_valid[obj_name]
        else:
            self.bvh_cache.clear()
            self.cache_valid.clear()


# ============================================================================
# RAY-CASTING HELPERS
# ============================================================================

def raycast_to_connector(origin: Vector, direction: Vector,
                        max_distance: float = 10.0) -> Optional[Tuple[bpy.types.Object, Vector]]:
    """
    Sendet Ray und findet nächsten Alusteck-Verbinder
    
    Returns:
        (connector_obj, hit_location) oder None
    """
    # Ray-Cast in Szene
    result = bpy.context.scene.ray_cast(
        bpy.context.view_layer.depsgraph,
        origin,
        direction,
        distance=max_distance
    )
    
    success, location, normal, index, obj, matrix = result
    
    if not success:
        return None
    
    # Prüfe ob Alusteck-Verbinder
    if obj and obj.get("alusteck_component") == "connector":
        return obj, location
    
    return None


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_collision_detector = None

def get_collision_detector() -> CollisionDetector:
    """Singleton-Zugriff"""
    global _collision_detector
    if _collision_detector is None:
        _collision_detector = CollisionDetector()
    return _collision_detector

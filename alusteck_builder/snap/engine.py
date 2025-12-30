"""
🧲 ALUSTECK SNAP ENGINE v2.0
================================
Intelligentes Snap-System für automatische Verbindungen mit:
- Port-basierte Architektur
- Echtzeit-Kollisionserkennung
- Steg-Kompatibilitätsprüfung
- Visuelles Feedback (Highlighting)
- Performance-Optimierung
"""

import bpy
import bmesh
from mathutils import Vector, Matrix
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class PortDirection(Enum):
    """Standardisierte Port-Richtungen"""
    POS_X = (1, 0, 0)
    NEG_X = (-1, 0, 0)
    POS_Y = (0, 1, 0)
    NEG_Y = (0, -1, 0)
    POS_Z = (0, 0, 1)
    NEG_Z = (0, 0, -1)
    
    @property
    def vector(self):
        return Vector(self.value)


@dataclass
class Port:
    """Ein einzelner Anschlusspunkt an einem Verbinder"""
    owner: bpy.types.Object  # Der Verbinder
    direction: Vector        # Richtungsvektor (normalisiert)
    position: Vector         # Weltkoordinaten
    occupied: bool = False
    connected_to: Optional[bpy.types.Object] = None
    
    def __hash__(self):
        return hash((self.owner.name, tuple(self.position)))
    
    @property
    def is_free(self) -> bool:
        """Prüft ob Port frei ist"""
        if self.occupied:
            return False
        # Zusätzlich checken ob das verbundene Objekt noch existiert
        if self.connected_to and self.connected_to.name not in bpy.data.objects:
            self.connected_to = None
            self.occupied = False
        return not self.occupied


@dataclass
class StegConfig:
    """Steg-Konfiguration eines Profils"""
    count: int                          # 1 oder 2 Stege
    type: str                           # 'single', 'double'
    position: str                       # 'inner_corner', 'opposite', 'outer_corner'
    height_mm: float
    blocked_directions: List[Vector]    # Richtungen, die blockiert sind
    
    def is_compatible_with_port(self, port: Port) -> bool:
        """Prüft ob Steg in Port-Richtung passt"""
        port_dir = port.direction.normalized()
        
        for blocked_dir in self.blocked_directions:
            # Wenn Port-Richtung parallel zu blockierter Richtung
            if abs(port_dir.dot(blocked_dir)) > 0.99:
                return False
        return True


@dataclass
class SnapCandidate:
    """Ein möglicher Snap-Punkt"""
    port: Port
    snap_position: Vector      # Wo das Profil hin-snappt
    snap_rotation: Matrix      # Wie es rotiert werden muss
    distance: float            # Distanz zum Cursor/Profil
    score: float              # Snap-Qualität (0-1)
    
    def __lt__(self, other):
        return self.score > other.score  # Höherer Score = besser


# ============================================================================
# SNAP ENGINE CORE
# ============================================================================

class AlusteckSnapEngine:
    """
    Hauptklasse für das Snap-System
    """
    
    # Globale Einstellungen
    SNAP_THRESHOLD = 0.5        # Meter (50cm)
    SOCKET_DEPTH = 0.025        # 25mm Einstecktiefe
    ALIGNMENT_TOLERANCE = 0.01  # 1cm für Alignment
    
    def __init__(self):
        self.ports: Dict[str, List[Port]] = {}  # connector_name -> ports
        self.steg_configs: Dict[str, StegConfig] = {}  # profile_name -> steg
        self.kd_tree = None
        self.port_lookup = []  # Für KD-Tree Mapping
        
    # ------------------------------------------------------------------------
    # PORT MANAGEMENT
    # ------------------------------------------------------------------------
    
    def register_connector(self, obj: bpy.types.Object):
        """
        Registriert einen Verbinder und erstellt seine Ports
        """
        if not self._is_alusteck_connector(obj):
            return
        
        # Port-Konfiguration aus Custom Properties lesen
        connector_type = obj.get("alusteck_type", "unknown")
        system = obj.get("alusteck_system", 25)
        
        ports = self._create_ports_for_connector(obj, connector_type, system)
        self.ports[obj.name] = ports
        
        # KD-Tree neu aufbauen
        self._rebuild_kdtree()
        
    def unregister_connector(self, obj_name: str):
        """Entfernt einen Verbinder"""
        if obj_name in self.ports:
            del self.ports[obj_name]
            self._rebuild_kdtree()
    
    def _create_ports_for_connector(self, obj: bpy.types.Object, 
                                   conn_type: str, system: int) -> List[Port]:
        """
        Erstellt Ports basierend auf Verbinder-Typ
        """
        mat = obj.matrix_world
        center = mat.translation
        cube_half = system / 2000.0  # mm -> m und halbiert
        socket_depth = self.SOCKET_DEPTH
        
        ports = []
        
        # Port-Templates basierend auf Typ
        port_templates = {
            "gerade": [
                (PortDirection.POS_Z, Vector((0, 0, cube_half))),
                (PortDirection.NEG_Z, Vector((0, 0, -cube_half)))
            ],
            "winkel": [
                (PortDirection.POS_X, Vector((cube_half, 0, 0))),
                (PortDirection.POS_Y, Vector((0, cube_half, 0)))
            ],
            "t-stueck": [
                (PortDirection.POS_X, Vector((cube_half, 0, 0))),
                (PortDirection.NEG_X, Vector((-cube_half, 0, 0))),
                (PortDirection.POS_Y, Vector((0, cube_half, 0)))
            ],
            "wuerfel_3": [
                (PortDirection.POS_X, Vector((cube_half, 0, 0))),
                (PortDirection.POS_Y, Vector((0, cube_half, 0))),
                (PortDirection.POS_Z, Vector((0, 0, cube_half)))
            ],
            "kreuz": [
                (PortDirection.POS_X, Vector((cube_half, 0, 0))),
                (PortDirection.NEG_X, Vector((-cube_half, 0, 0))),
                (PortDirection.POS_Y, Vector((0, cube_half, 0))),
                (PortDirection.NEG_Y, Vector((0, -cube_half, 0)))
            ],
            "wuerfel_6": [
                (PortDirection.POS_X, Vector((cube_half, 0, 0))),
                (PortDirection.NEG_X, Vector((-cube_half, 0, 0))),
                (PortDirection.POS_Y, Vector((0, cube_half, 0))),
                (PortDirection.NEG_Y, Vector((0, -cube_half, 0))),
                (PortDirection.POS_Z, Vector((0, 0, cube_half))),
                (PortDirection.NEG_Z, Vector((0, 0, -cube_half)))
            ]
        }
        
        templates = port_templates.get(conn_type, [])
        
        for direction_enum, local_offset in templates:
            # Transformiere in Weltkoordinaten
            world_dir = (mat @ direction_enum.vector) - mat.translation
            world_dir.normalize()
            world_pos = mat @ local_offset
            
            port = Port(
                owner=obj,
                direction=world_dir,
                position=world_pos,
                occupied=False
            )
            ports.append(port)
        
        return ports
    
    # ------------------------------------------------------------------------
    # STEG MANAGEMENT
    # ------------------------------------------------------------------------
    
    def register_profile_steg(self, obj: bpy.types.Object):
        """Registriert Steg-Konfiguration eines Profils"""
        if not self._is_alusteck_profile(obj):
            return
        
        steg_type = obj.get("alusteck_steg", None)
        if not steg_type:
            return
        
        # Parse Steg-Config
        steg_config = self._parse_steg_config(steg_type, obj.matrix_world)
        self.steg_configs[obj.name] = steg_config
    
    def _parse_steg_config(self, steg_type: str, mat: Matrix) -> StegConfig:
        """
        Parst Steg-Typ zu Konfiguration
        
        Beispiele:
        - "2SI" = 2 Stege Innenwinkel
        - "1SA" = 1 Steg Außen
        - "2SG" = 2 Stege Gegenüber
        """
        count = int(steg_type[0])
        position_code = steg_type[2] if len(steg_type) > 2 else 'I'
        
        position_map = {
            'I': 'innenwinkel',
            'A': 'aussenwinkel',
            'G': 'gegenueber'
        }
        
        position = position_map.get(position_code, 'innenwinkel')
        
        # Blockierte Richtungen berechnen
        blocked = []
        if position == 'innenwinkel':
            # Blockiert: +X und +Y (in lokalen Koordinaten)
            blocked = [
                (mat @ Vector((1, 0, 0))) - mat.translation,
                (mat @ Vector((0, 1, 0))) - mat.translation
            ]
        elif position == 'gegenueber':
            # Blockiert: +X und -X
            blocked = [
                (mat @ Vector((1, 0, 0))) - mat.translation,
                (mat @ Vector((-1, 0, 0))) - mat.translation
            ]
        
        return StegConfig(
            count=count,
            type='single' if count == 1 else 'double',
            position=position,
            height_mm=15.0,
            blocked_directions=[v.normalized() for v in blocked]
        )
    
    # ------------------------------------------------------------------------
    # SNAP DETECTION
    # ------------------------------------------------------------------------
    
    def find_snap_candidates(self, profile: bpy.types.Object, 
                            cursor_loc: Vector,
                            max_candidates: int = 5) -> List[SnapCandidate]:
        """
        Findet die besten Snap-Kandidaten für ein Profil
        
        Args:
            profile: Das zu snappende Profil-Objekt
            cursor_loc: Aktuelle Cursor/Profil-Position
            max_candidates: Maximale Anzahl zurückgegebener Kandidaten
            
        Returns:
            Sortierte Liste von SnapCandidates (beste zuerst)
        """
        if not self.kd_tree:
            return []
        
        candidates = []
        
        # Finde nahegelegene Ports via KD-Tree
        nearby_indices = self._find_nearby_ports(cursor_loc, self.SNAP_THRESHOLD)
        
        for idx in nearby_indices:
            port = self.port_lookup[idx]
            
            # Skip belegte Ports
            if not port.is_free:
                continue
            
            # Prüfe Steg-Kompatibilität
            if not self._check_steg_compatibility(profile, port):
                continue
            
            # Berechne Snap-Transform
            snap_pos, snap_rot = self._calculate_snap_transform(profile, port)
            
            # Prüfe Kollisionen
            if self._would_collide(profile, snap_pos, snap_rot, port):
                continue
            
            # Berechne Score
            distance = (cursor_loc - snap_pos).length
            alignment_score = self._calculate_alignment_score(profile, port)
            score = self._calculate_snap_score(distance, alignment_score)
            
            candidate = SnapCandidate(
                port=port,
                snap_position=snap_pos,
                snap_rotation=snap_rot,
                distance=distance,
                score=score
            )
            candidates.append(candidate)
        
        # Sortiere nach Score und limitiere
        candidates.sort()
        return candidates[:max_candidates]
    
    def _calculate_snap_transform(self, profile: bpy.types.Object, 
                                 port: Port) -> Tuple[Vector, Matrix]:
        """
        Berechnet Position und Rotation für perfekten Snap
        """
        # Profil-Länge auslesen
        profile_length = profile.get("alusteck_length", 1.0)
        
        # Position: Port-Position + (Richtung * halbe Profil-Länge)
        snap_position = port.position + (port.direction * (profile_length / 2 + self.SOCKET_DEPTH))
        
        # Rotation: Profil-Z-Achse soll entgegengesetzt zur Port-Richtung zeigen
        target_dir = -port.direction
        
        # Berechne Rotationsmatrix
        up = Vector((0, 0, 1))
        if abs(target_dir.dot(up)) > 0.99:
            up = Vector((1, 0, 0))
        
        right = target_dir.cross(up).normalized()
        up = right.cross(target_dir).normalized()
        
        rot_matrix = Matrix((
            right,
            up,
            target_dir
        )).transposed().to_4x4()
        
        return snap_position, rot_matrix
    
    def _calculate_snap_score(self, distance: float, alignment: float) -> float:
        """
        Berechnet Snap-Qualität (0-1, höher = besser)
        
        Faktoren:
        - Distanz (näher = besser)
        - Alignment (besser ausgerichtet = besser)
        """
        # Normalisiere Distanz (0 = max_threshold, 1 = 0)
        dist_score = 1.0 - (distance / self.SNAP_THRESHOLD)
        dist_score = max(0, min(1, dist_score))
        
        # Gewichtung: 60% Distanz, 40% Alignment
        return (0.6 * dist_score) + (0.4 * alignment)
    
    def _calculate_alignment_score(self, profile: bpy.types.Object, 
                                  port: Port) -> float:
        """
        Bewertet wie gut Profil und Port bereits ausgerichtet sind
        """
        # Profil-Z-Achse
        profile_dir = (profile.matrix_world @ Vector((0, 0, 1))) - profile.matrix_world.translation
        profile_dir.normalize()
        
        # Optimal: Profil zeigt genau entgegengesetzt zum Port
        alignment = abs(profile_dir.dot(-port.direction))
        return alignment
    
    # ------------------------------------------------------------------------
    # COLLISION DETECTION
    # ------------------------------------------------------------------------
    
    def _would_collide(self, profile: bpy.types.Object, 
                      snap_pos: Vector, snap_rot: Matrix,
                      exclude_port: Port) -> bool:
        """
        Prüft ob Profil an snap_pos kollidieren würde
        """
        # Temporäre Bounding Box des Profils an neuer Position
        profile_bbox = self._get_transformed_bbox(profile, snap_pos, snap_rot)
        
        # Prüfe gegen alle Verbinder (außer dem Ziel-Verbinder)
        for conn_name, ports in self.ports.items():
            if conn_name == exclude_port.owner.name:
                continue
            
            connector = bpy.data.objects.get(conn_name)
            if not connector:
                continue
            
            conn_bbox = self._get_bbox(connector)
            
            if self._bboxes_intersect(profile_bbox, conn_bbox):
                return True
        
        # Prüfe gegen andere Profile
        for obj in bpy.context.scene.objects:
            if obj == profile:
                continue
            if not self._is_alusteck_profile(obj):
                continue
            
            other_bbox = self._get_bbox(obj)
            if self._bboxes_intersect(profile_bbox, other_bbox):
                return True
        
        return False
    
    def _get_transformed_bbox(self, obj: bpy.types.Object, 
                             pos: Vector, rot: Matrix) -> List[Vector]:
        """Gibt Bounding Box an neuer Transform zurück"""
        # Lokale Bbox-Ecken
        bbox_corners = [Vector(corner) for corner in obj.bound_box]
        
        # Kombinierte Transform-Matrix
        trans_matrix = Matrix.Translation(pos) @ rot
        
        # Transformiere alle Ecken
        return [trans_matrix @ corner for corner in bbox_corners]
    
    def _get_bbox(self, obj: bpy.types.Object) -> List[Vector]:
        """Gibt Welt-Bounding-Box zurück"""
        return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    def _bboxes_intersect(self, bbox1: List[Vector], bbox2: List[Vector]) -> bool:
        """AABB Intersection Test"""
        # Min/Max für beide Boxen
        min1 = Vector((min(v.x for v in bbox1), 
                      min(v.y for v in bbox1), 
                      min(v.z for v in bbox1)))
        max1 = Vector((max(v.x for v in bbox1), 
                      max(v.y for v in bbox1), 
                      max(v.z for v in bbox1)))
        
        min2 = Vector((min(v.x for v in bbox2), 
                      min(v.y for v in bbox2), 
                      min(v.z for v in bbox2)))
        max2 = Vector((max(v.x for v in bbox2), 
                      max(v.y for v in bbox2), 
                      max(v.z for v in bbox2)))
        
        # Überlappung in allen 3 Achsen?
        return (min1.x <= max2.x and max1.x >= min2.x and
                min1.y <= max2.y and max1.y >= min2.y and
                min1.z <= max2.z and max1.z >= min2.z)
    
    # ------------------------------------------------------------------------
    # STEG COMPATIBILITY
    # ------------------------------------------------------------------------
    
    def _check_steg_compatibility(self, profile: bpy.types.Object, 
                                  port: Port) -> bool:
        """Prüft ob Profil mit Steg in Port passt"""
        steg = self.steg_configs.get(profile.name)
        
        if not steg:
            return True  # Kein Steg = immer kompatibel
        
        return steg.is_compatible_with_port(port)
    
    # ------------------------------------------------------------------------
    # KD-TREE OPTIMIZATION
    # ------------------------------------------------------------------------
    
    def _rebuild_kdtree(self):
        """Baut KD-Tree für schnelle räumliche Suche neu auf"""
        if not self.ports:
            self.kd_tree = None
            self.port_lookup = []
            return
        
        # Alle Ports flach sammeln
        all_ports = []
        for ports_list in self.ports.values():
            all_ports.extend(ports_list)
        
        # KD-Tree aufbauen
        kd = kdtree.KDTree(len(all_ports))
        
        for idx, port in enumerate(all_ports):
            kd.insert(port.position, idx)
        
        kd.balance()
        
        self.kd_tree = kd
        self.port_lookup = all_ports
    
    def _find_nearby_ports(self, location: Vector, radius: float) -> List[int]:
        """Findet Port-Indizes in Radius um location"""
        if not self.kd_tree:
            return []
        
        results = self.kd_tree.find_range(location, radius)
        return [idx for (co, idx, dist) in results]
    
    # ------------------------------------------------------------------------
    # SNAP EXECUTION
    # ------------------------------------------------------------------------
    
    def execute_snap(self, profile: bpy.types.Object, 
                    candidate: SnapCandidate) -> bool:
        """
        Führt den Snap aus und markiert Port als belegt
        """
        # Setze Transform
        profile.location = candidate.snap_position
        profile.rotation_mode = 'QUATERNION'
        profile.rotation_quaternion = candidate.snap_rotation.to_quaternion()
        
        # Markiere Port als belegt
        candidate.port.occupied = True
        candidate.port.connected_to = profile
        
        # Speichere Verbindung in Profile
        profile["alusteck_connected_to"] = candidate.port.owner.name
        profile["alusteck_port_index"] = self.port_lookup.index(candidate.port)
        
        return True
    
    def release_snap(self, profile: bpy.types.Object):
        """Löst Snap-Verbindung eines Profils"""
        port_idx = profile.get("alusteck_port_index")
        
        if port_idx is not None and port_idx < len(self.port_lookup):
            port = self.port_lookup[port_idx]
            port.occupied = False
            port.connected_to = None
        
        # Lösche Metadaten
        if "alusteck_connected_to" in profile:
            del profile["alusteck_connected_to"]
        if "alusteck_port_index" in profile:
            del profile["alusteck_port_index"]
    
    # ------------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------------
    
    def _is_alusteck_connector(self, obj: bpy.types.Object) -> bool:
        """Prüft ob Objekt ein Alusteck-Verbinder ist"""
        return (obj and obj.type == 'MESH' and 
                "alusteck_component" in obj and 
                obj["alusteck_component"] == "connector")
    
    def _is_alusteck_profile(self, obj: bpy.types.Object) -> bool:
        """Prüft ob Objekt ein Alusteck-Profil ist"""
        return (obj and obj.type == 'MESH' and 
                "alusteck_component" in obj and 
                obj["alusteck_component"] == "profile")
    
    def update_port_transforms(self):
        """Aktualisiert Port-Positionen nach Connector-Bewegung"""
        for conn_name, ports in self.ports.items():
            connector = bpy.data.objects.get(conn_name)
            if not connector:
                continue
            
            # Neu generieren
            connector_type = connector.get("alusteck_type", "unknown")
            system = connector.get("alusteck_system", 25)
            new_ports = self._create_ports_for_connector(connector, connector_type, system)
            
            # Occupation-Status übertragen
            for old_port, new_port in zip(ports, new_ports):
                new_port.occupied = old_port.occupied
                new_port.connected_to = old_port.connected_to
            
            self.ports[conn_name] = new_ports
        
        self._rebuild_kdtree()


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_snap_engine_instance = None

def get_snap_engine() -> AlusteckSnapEngine:
    """Singleton-Zugriff auf Snap-Engine"""
    global _snap_engine_instance
    if _snap_engine_instance is None:
        _snap_engine_instance = AlusteckSnapEngine()
    return _snap_engine_instance


# ============================================================================
# BLENDER OPERATORS
# ============================================================================

class ALUSTECK_OT_snap_move(bpy.types.Operator):
    """Move with automatic snapping to connectors (own modal loop - no conflicts)"""
    bl_idname = "alusteck.snap_move"
    bl_label = "Snap Move"
    bl_options = {'REGISTER', 'UNDO', 'GRAB_CURSOR', 'BLOCKING'}
    
    # Modal tracking
    _timer = None
    _handle = None
    _initial_mouse = None
    _initial_pos = None
    _current_candidate = None
    _is_moving = False
    
    def modal(self, context, event):
        """Own modal loop - no nested bpy.ops.transform calls."""
        engine = get_snap_engine()
        
        if event.type == 'TIMER':
            # Echtzeit-Update bei Mausbewegung
            if self._is_moving and context.active_object:
                profile = context.active_object
                
                # Aktuelle Mausposition
                mouse_delta = Vector((
                    event.mouse_region_x - self._initial_mouse.x,
                    event.mouse_region_y - self._initial_mouse.y
                ))
                
                # Mausposition in 3D-Raum konvertieren
                region = context.region
                region_3d = context.space_data.region_3d
                
                # Einfache Projektion: delta in viewport-pixels
                move_offset = mouse_delta * 0.01
                profile.location = self._initial_pos + Vector((
                    move_offset.x,
                    move_offset.y,
                    0.0
                ))
                
                # Finde Snap-Kandidaten
                candidates = engine.find_snap_candidates(
                    profile, 
                    profile.location,
                    max_candidates=1
                )
                
                if candidates:
                    self._current_candidate = candidates[0]
                    # Visual Feedback
                    if context.area:
                        context.area.tag_redraw()
                else:
                    self._current_candidate = None
                    if context.area:
                        context.area.tag_redraw()
        
        elif event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                # Start dragging
                self._is_moving = True
                self._initial_pos = context.active_object.location.copy()
                self._initial_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
            
            elif event.value == 'RELEASE':
                # Drop - execute snap if candidate
                if self._current_candidate and context.active_object:
                    engine.execute_snap(context.active_object, self._current_candidate)
                    self.report({'INFO'}, "Snapped successfully")
                
                self._cleanup(context)
                return {'FINISHED'}
        
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            # Cancel - restore original position
            if context.active_object:
                context.active_object.location = self._initial_pos
            
            self._cleanup(context)
            return {'CANCELLED'}
        
        elif event.type == 'TIMER':
            # Periodisches Redraw
            if context.area:
                context.area.tag_redraw()
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        if not self._is_valid_profile(context.active_object):
            self.report({'WARNING'}, "Select an Alusteck profile")
            return {'CANCELLED'}
        
        # Setup initial state
        obj = context.active_object
        self._initial_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
        self._initial_pos = obj.location.copy()
        self._current_candidate = None
        self._is_moving = False
        
        # Add timer für regelmäßige Updates
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.016, window=context.window)  # ~60 FPS
        wm.modal_handler_add(self)
        
        # Add draw handler für visual feedback (kein nested modal!)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_snap_highlights, 
            (context,), 
            'WINDOW', 
            'POST_VIEW'
        )
        
        self.report({'INFO'}, "LMB drag to move, Snap preview shows green")
        return {'RUNNING_MODAL'}
    
    def _draw_snap_highlights(self, context):
        """Zeichnet Snap-Vorschau (Grüner Kreis um nächsten Port)."""
        try:
            import gpu
            from gpu_extras.batch import batch_for_shader
        except ImportError:
            return  # GPU module nicht verfügbar
        
        if not self._current_candidate:
            return
        
        try:
            # Shader
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            
            # Port-Position
            port_pos = self._current_candidate.port.position
            
            # Kreis um Port
            segments = 32
            radius = 0.05
            vertices = []
            
            for i in range(segments):
                angle = (i / segments) * 2 * math.pi
                x = port_pos.x + radius * math.cos(angle)
                y = port_pos.y + radius * math.sin(angle)
                z = port_pos.z
                vertices.append((x, y, z))
            
            batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": vertices})
            
            shader.bind()
            shader.uniform_float("color", (0.0, 1.0, 0.0, 0.8))  # Grün
            batch.draw(shader)
        except Exception:
            pass  # GPU drawing fehler - nicht kritisch
    
    def _cleanup(self, context):
        """Räumt Modal Handler und Timer auf."""
        wm = context.window_manager
        
        if self._timer:
            wm.event_timer_remove(self._timer)
            self._timer = None
        
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            self._handle = None
        
        if context.area:
            context.area.tag_redraw()
    
    def _is_valid_profile(self, obj):
        """Check if object is an Alusteck profile."""
        return (obj and obj.type == 'MESH' and 
                obj.get("alusteck_component") == "profile")


# ============================================================================
# REGISTRATION
# ============================================================================

def register():
    bpy.utils.register_class(ALUSTECK_OT_snap_move)

def unregister():
    bpy.utils.unregister_class(ALUSTECK_OT_snap_move)

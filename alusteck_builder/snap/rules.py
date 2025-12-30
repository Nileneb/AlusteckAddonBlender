"""
📋 SNAP RULES & VALIDATION
===========================
Best-Practice Regeln für stabile Konstruktionen
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Set
import bpy
from mathutils import Vector


@dataclass
class ValidationIssue:
    """Ein gefundenes Problem"""
    severity: str  # 'warning', 'error', 'info'
    message: str
    affected_objects: List[bpy.types.Object]
    suggestion: Optional[str] = None


class AlusteckValidator:
    """
    Validiert Konstruktionen nach Best Practices
    """
    
    # Regeln
    MAX_UNSUPPORTED_LENGTH = 1.0  # 1m ohne Stütze
    MIN_SUPPORT_DISTANCE = 0.6    # 60cm zwischen Stützen
    MAX_CONNECTIONS_PER_PORT = 1   # 1 Profil pro Port
    
    def __init__(self, snap_engine):
        self.engine = snap_engine
        self.issues = []
    
    def validate_scene(self) -> List[ValidationIssue]:
        """Validiert gesamte Szene"""
        self.issues = []
        
        # Alle Alusteck-Objekte sammeln
        connectors = [obj for obj in bpy.context.scene.objects 
                     if obj.get("alusteck_component") == "connector"]
        profiles = [obj for obj in bpy.context.scene.objects 
                   if obj.get("alusteck_component") == "profile"]
        
        # Verschiedene Checks
        self._check_unsupported_lengths(profiles)
        self._check_overloaded_ports(connectors)
        self._check_floating_components(connectors + profiles)
        self._check_structural_integrity(connectors, profiles)
        
        return self.issues
    
    def _check_unsupported_lengths(self, profiles: List[bpy.types.Object]):
        """Warnt vor zu langen Profilen ohne Mittelstütze"""
        for profile in profiles:
            length = profile.get("alusteck_length", 1.0)
            
            if length > self.MAX_UNSUPPORTED_LENGTH:
                # Prüfe ob Mittelstütze vorhanden
                has_center_support = self._has_support_at_center(profile)
                
                if not has_center_support:
                    self.issues.append(ValidationIssue(
                        severity='warning',
                        message=f"Profil '{profile.name}' ist {length}m lang ohne Mittelstütze",
                        affected_objects=[profile],
                        suggestion=f"Füge eine Stütze bei {length/2}m hinzu"
                    ))
    
    def _check_overloaded_ports(self, connectors: List[bpy.types.Object]):
        """Prüft ob zu viele Profile an einem Port"""
        for conn in connectors:
            ports = self.engine.ports.get(conn.name, [])
            
            for port in ports:
                if not port.occupied:
                    continue
                
                # Count connections
                connections = self._count_connections_at_port(port)
                
                if connections > self.MAX_CONNECTIONS_PER_PORT:
                    self.issues.append(ValidationIssue(
                        severity='error',
                        message=f"Port überlastet: {connections} Verbindungen",
                        affected_objects=[conn, port.connected_to],
                        suggestion="Verwende einen größeren Verbinder"
                    ))
    
    def _check_floating_components(self, all_objects: List[bpy.types.Object]):
        """Findet unverbundene Komponenten"""
        for obj in all_objects:
            is_connected = obj.get("alusteck_connected_to") is not None
            
            if not is_connected and obj.get("alusteck_component") == "profile":
                self.issues.append(ValidationIssue(
                    severity='info',
                    message=f"'{obj.name}' ist nicht verbunden",
                    affected_objects=[obj],
                    suggestion="Verbinde mit Verbinder oder lösche"
                ))
    
    def _check_structural_integrity(self, connectors, profiles):
        """Prüft Gesamt-Stabilität"""
        # Graph-basierte Analyse
        graph = self._build_connection_graph(connectors, profiles)
        
        # Finde isolierte Subgraphen
        islands = self._find_islands(graph)
        
        if len(islands) > 1:
            self.issues.append(ValidationIssue(
                severity='warning',
                message=f"Konstruktion besteht aus {len(islands)} getrennten Teilen",
                affected_objects=[],
                suggestion="Verbinde alle Teile zu einer Struktur"
            ))
    
    def _has_support_at_center(self, profile: bpy.types.Object) -> bool:
        """Prüft ob Profil Mittelstütze hat"""
        # Finde Mittelpunkt des Profils
        center = profile.location
        length = profile.get("alusteck_length", 1.0)
        
        # Suche nahegelegene Verbinder
        tolerance = 0.1  # 10cm Toleranz
        
        for obj in bpy.context.scene.objects:
            if obj.get("alusteck_component") != "connector":
                continue
            
            dist = (obj.location - center).length
            if dist < length / 2 + tolerance:
                return True
        
        return False
    
    def _count_connections_at_port(self, port) -> int:
        """Zählt Verbindungen an Port"""
        return 1 if port.occupied else 0
    
    def _build_connection_graph(self, connectors, profiles) -> Dict[str, Set[str]]:
        """Baut Verbindungsgraph"""
        graph = {}
        
        # Alle Objekte als Knoten
        for obj in connectors + profiles:
            graph[obj.name] = set()
        
        # Verbindungen hinzufügen
        for profile in profiles:
            conn_name = profile.get("alusteck_connected_to")
            if conn_name and conn_name in graph:
                graph[profile.name].add(conn_name)
                graph[conn_name].add(profile.name)
        
        return graph
    
    def _find_islands(self, graph: Dict[str, Set[str]]) -> List[Set[str]]:
        """Findet isolierte Subgraphen (Depth-First Search)"""
        visited = set()
        islands = []
        
        def dfs(node, island):
            visited.add(node)
            island.add(node)
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, island)
        
        for node in graph:
            if node not in visited:
                island = set()
                dfs(node, island)
                islands.append(island)
        
        return islands


class SnapRuleChecker:
    """
    Prüft Snap-Regeln während der Konstruktion
    """
    
    def __init__(self):
        self.snap_rules = self._load_snap_rules()
    
    def _load_snap_rules(self) -> dict:
        """Lädt Snap-Regeln aus JSON"""
        from ..core import database
        return database.load_snap_rules()
    
    def can_connect(self, profile: bpy.types.Object, 
                   connector: bpy.types.Object,
                   port_direction: Vector) -> tuple[bool, Optional[str]]:
        """
        Prüft ob Verbindung erlaubt ist
        
        Returns:
            (erlaubt: bool, grund: str oder None)
        """
        # System-Kompatibilität
        profile_system = profile.get("alusteck_system", 25)
        connector_system = connector.get("alusteck_system", 25)
        
        if profile_system != connector_system:
            return False, f"Inkompatible Systeme: {profile_system}mm vs {connector_system}mm"
        
        # Steg-Kompatibilität
        steg_type = profile.get("alusteck_steg")
        if steg_type:
            rules = self.snap_rules.get(f"{profile_system}mm", {})
            steg_rules = rules.get("steg_regeln", {})
            
            # Parse Steg-Position
            position_map = {'I': 'innenwinkel', 'A': 'aussenwinkel', 'G': 'gegenueber'}
            steg_pos = position_map.get(steg_type[2] if len(steg_type) > 2 else 'I')
            
            if steg_pos in steg_rules:
                blocked = steg_rules[steg_pos].get("blockierte_richtungen", [])
                
                # Prüfe ob Port-Richtung blockiert ist
                for blocked_dir in blocked:
                    if self._vectors_parallel(port_direction, Vector(blocked_dir)):
                        return False, f"Steg blockiert Richtung {blocked_dir}"
        
        # Verbinder-Kapazität
        connector_type = connector.get("alusteck_type", "unknown")
        rules = self.snap_rules.get(f"{connector_system}mm", {})
        verb_types = rules.get("verbinder_typen", {})
        
        if connector_type in verb_types:
            max_conn = verb_types[connector_type].get("max_anschluesse", 2)
            
            # Zähle aktuelle Verbindungen
            current_conns = sum(1 for p in bpy.context.scene.objects 
                              if p.get("alusteck_connected_to") == connector.name)
            
            if current_conns >= max_conn:
                return False, f"Verbinder voll ({current_conns}/{max_conn})"
        
        return True, None
    
    def _vectors_parallel(self, v1: Vector, v2: Vector, tolerance=0.01) -> bool:
        """Prüft ob zwei Vektoren parallel sind"""
        v1_norm = v1.normalized()
        v2_norm = v2.normalized()
        dot = abs(v1_norm.dot(v2_norm))
        return dot > (1.0 - tolerance)


# ============================================================================
# BLENDER OPERATOR
# ============================================================================

class ALUSTECK_OT_validate_structure(bpy.types.Operator):
    """Validate Alusteck construction for stability"""
    bl_idname = "alusteck.validate_structure"
    bl_label = "Validate Structure"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        from .engine import get_snap_engine
        
        engine = get_snap_engine()
        validator = AlusteckValidator(engine)
        
        issues = validator.validate_scene()
        
        if not issues:
            self.report({'INFO'}, "✅ Konstruktion ist valide")
            return {'FINISHED'}
        
        # Gruppiere nach Severity
        errors = [i for i in issues if i.severity == 'error']
        warnings = [i for i in issues if i.severity == 'warning']
        infos = [i for i in issues if i.severity == 'info']
        
        # Report
        if errors:
            self.report({'ERROR'}, f"❌ {len(errors)} Fehler gefunden")
        if warnings:
            self.report({'WARNING'}, f"⚠️ {len(warnings)} Warnungen")
        if infos:
            self.report({'INFO'}, f"ℹ️ {len(infos)} Hinweise")
        
        # Details ausgeben
        for issue in errors[:3]:  # Max 3 anzeigen
            self.report({'ERROR'}, issue.message)
        
        return {'FINISHED'}


# ============================================================================
# REGISTRATION
# ============================================================================

def register():
    bpy.utils.register_class(ALUSTECK_OT_validate_structure)

def unregister():
    bpy.utils.unregister_class(ALUSTECK_OT_validate_structure)

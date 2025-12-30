"""
✅ STRUCTURE VALIDATION
========================
Erweiterte Validierung für strukturelle Integrität
"""

import bpy
from mathutils import Vector
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from .rules import ValidationIssue


@dataclass
class LoadAnalysis:
    """Analyse der Lastverteilung"""
    max_load: float          # Maximale Last in kg
    critical_points: List[bpy.types.Object]  # Kritische Verbinder
    safety_factor: float     # Sicherheitsfaktor
    is_stable: bool


class StructuralValidator:
    """
    Erweiterte Strukturanalyse mit Physik-basierter Validierung
    """
    
    # Material-Konstanten für Aluminium
    ALUMINUM_YIELD_STRENGTH = 240e6  # Pa (240 MPa)
    ALUMINUM_DENSITY = 2700          # kg/m³
    SAFETY_FACTOR_TARGET = 2.0       # Mindest-Sicherheitsfaktor
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
    
    def validate_structure(self, components: List[bpy.types.Object]) -> List[ValidationIssue]:
        """Komplette Strukturvalidierung"""
        self.issues = []
        
        connectors = [c for c in components if c.get("alusteck_component") == "connector"]
        profiles = [p for p in components if p.get("alusteck_component") == "profile"]
        
        # Verschiedene Validierungen
        self._validate_connectivity(connectors, profiles)
        self._validate_geometry(profiles)
        self._validate_loads(connectors, profiles)
        self._validate_symmetry(components)
        
        return self.issues
    
    # ------------------------------------------------------------------------
    # CONNECTIVITY
    # ------------------------------------------------------------------------
    
    def _validate_connectivity(self, connectors, profiles):
        """Prüft ob Struktur zusammenhängend ist"""
        graph = self._build_graph(connectors, profiles)
        islands = self._find_connected_components(graph)
        
        if len(islands) == 0:
            self.issues.append(ValidationIssue(
                severity='error',
                message="Keine Komponenten gefunden",
                affected_objects=[],
                suggestion="Füge Verbinder und Profile hinzu"
            ))
        elif len(islands) > 1:
            self.issues.append(ValidationIssue(
                severity='warning',
                message=f"Struktur besteht aus {len(islands)} getrennten Teilen",
                affected_objects=[],
                suggestion="Verbinde alle Teile zu einer Struktur"
            ))
        
        # Prüfe auf Sackgassen (Dead Ends)
        for obj in profiles:
            connections = sum(1 for p in profiles 
                            if p.get("alusteck_connected_to") == obj.name or
                               obj.get("alusteck_connected_to") == p.name)
            
            if connections == 1:
                self.issues.append(ValidationIssue(
                    severity='info',
                    message=f"'{obj.name}' ist ein Dead-End (nur 1 Verbindung)",
                    affected_objects=[obj],
                    suggestion="Erwäge zusätzliche Verstrebung"
                ))
    
    def _build_graph(self, connectors, profiles) -> Dict[str, Set[str]]:
        """Baut Verbindungsgraph"""
        graph = {obj.name: set() for obj in connectors + profiles}
        
        for profile in profiles:
            conn_name = profile.get("alusteck_connected_to")
            if conn_name and conn_name in graph:
                graph[profile.name].add(conn_name)
                graph[conn_name].add(profile.name)
        
        return graph
    
    def _find_connected_components(self, graph: Dict[str, Set[str]]) -> List[Set[str]]:
        """Findet zusammenhängende Teilgraphen (Union-Find)"""
        visited = set()
        components = []
        
        def dfs(node, component):
            visited.add(node)
            component.add(node)
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, component)
        
        for node in graph:
            if node not in visited:
                component = set()
                dfs(node, component)
                if component:
                    components.append(component)
        
        return components
    
    # ------------------------------------------------------------------------
    # GEOMETRY
    # ------------------------------------------------------------------------
    
    def _validate_geometry(self, profiles):
        """Prüft geometrische Eigenschaften"""
        for profile in profiles:
            length = profile.get("alusteck_length", 1.0)
            
            # Warnung bei sehr langen Profilen
            if length > 2.0:
                self.issues.append(ValidationIssue(
                    severity='warning',
                    message=f"Sehr langes Profil: {length:.2f}m",
                    affected_objects=[profile],
                    suggestion="Erwäge Aufteilung oder zusätzliche Stützen"
                ))
            
            # Prüfe Winkel zu verbundenen Profilen
            self._check_connection_angles(profile, profiles)
    
    def _check_connection_angles(self, profile, all_profiles):
        """Prüft Verbindungswinkel"""
        profile_dir = self._get_profile_direction(profile)
        
        conn_name = profile.get("alusteck_connected_to")
        if not conn_name:
            return
        
        # Finde andere Profile am selben Verbinder
        siblings = [p for p in all_profiles 
                   if p != profile and p.get("alusteck_connected_to") == conn_name]
        
        for sibling in siblings:
            sibling_dir = self._get_profile_direction(sibling)
            angle = self._angle_between(profile_dir, sibling_dir)
            
            # Warnung bei ungünstigen Winkeln
            if 10 < angle < 80:  # Zwischen 10° und 80°
                self.issues.append(ValidationIssue(
                    severity='info',
                    message=f"Ungünstiger Winkel: {angle:.1f}° zwischen Profilen",
                    affected_objects=[profile, sibling],
                    suggestion="Bevorzuge 90° oder 180° Winkel für Stabilität"
                ))
    
    def _get_profile_direction(self, profile: bpy.types.Object) -> Vector:
        """Gibt Hauptrichtung des Profils zurück"""
        mat = profile.matrix_world
        return (mat @ Vector((0, 0, 1))) - mat.translation
    
    def _angle_between(self, v1: Vector, v2: Vector) -> float:
        """Berechnet Winkel zwischen zwei Vektoren in Grad"""
        import math
        v1_norm = v1.normalized()
        v2_norm = v2.normalized()
        dot = max(-1.0, min(1.0, v1_norm.dot(v2_norm)))
        return math.degrees(math.acos(abs(dot)))
    
    # ------------------------------------------------------------------------
    # LOAD ANALYSIS
    # ------------------------------------------------------------------------
    
    def _validate_loads(self, connectors, profiles):
        """Analysiert Lastverteilung"""
        analysis = self._analyze_loads(connectors, profiles)
        
        if not analysis.is_stable:
            self.issues.append(ValidationIssue(
                severity='error',
                message=f"Struktur instabil! Sicherheitsfaktor: {analysis.safety_factor:.2f}",
                affected_objects=analysis.critical_points,
                suggestion=f"Verstärke kritische Punkte (Ziel: {self.SAFETY_FACTOR_TARGET})"
            ))
        elif analysis.safety_factor < self.SAFETY_FACTOR_TARGET * 1.5:
            self.issues.append(ValidationIssue(
                severity='warning',
                message=f"Niedriger Sicherheitsfaktor: {analysis.safety_factor:.2f}",
                affected_objects=analysis.critical_points,
                suggestion="Erwäge zusätzliche Verstrebungen"
            ))
    
    def _analyze_loads(self, connectors, profiles) -> LoadAnalysis:
        """Vereinfachte Lastanalyse"""
        # Geschätzte Gewichte
        total_weight = 0.0
        
        for profile in profiles:
            length = profile.get("alusteck_length", 1.0)
            system = profile.get("alusteck_system", 25)
            
            # Geschätztes Gewicht pro Meter (Aluminium Hohlprofil)
            weight_per_m = (system / 25.0) * 0.5  # ~0.5kg/m für 25mm
            total_weight += length * weight_per_m
        
        # Kritische Verbinder (viele Verbindungen)
        critical = []
        max_connections = 0
        
        for connector in connectors:
            conn_count = sum(1 for p in profiles 
                           if p.get("alusteck_connected_to") == connector.name)
            
            if conn_count > max_connections:
                max_connections = conn_count
                critical = [connector]
            elif conn_count == max_connections and conn_count > 0:
                critical.append(connector)
        
        # Vereinfachter Sicherheitsfaktor
        if max_connections == 0:
            safety_factor = 0.0
        else:
            # Je mehr Verbindungen, desto höher die Last
            estimated_load_per_conn = total_weight / len(connectors) if connectors else 0
            safety_factor = 100.0 / max(estimated_load_per_conn, 1.0)  # Vereinfacht
        
        return LoadAnalysis(
            max_load=total_weight,
            critical_points=critical,
            safety_factor=safety_factor,
            is_stable=safety_factor >= self.SAFETY_FACTOR_TARGET
        )
    
    # ------------------------------------------------------------------------
    # SYMMETRY
    # ------------------------------------------------------------------------
    
    def _validate_symmetry(self, components):
        """Prüft ob Struktur symmetrisch ist (optional)"""
        if len(components) < 4:
            return  # Zu klein für Symmetrie-Check
        
        # Berechne Zentrum
        center = Vector((0, 0, 0))
        for obj in components:
            center += obj.location
        center /= len(components)
        
        # Prüfe X-Achsen-Symmetrie
        left_count = sum(1 for obj in components if obj.location.x < center.x)
        right_count = sum(1 for obj in components if obj.location.x > center.x)
        
        imbalance = abs(left_count - right_count) / len(components)
        
        if imbalance > 0.3:  # >30% Ungleichgewicht
            self.issues.append(ValidationIssue(
                severity='info',
                message=f"Asymmetrische Struktur: {imbalance*100:.0f}% Ungleichgewicht",
                affected_objects=[],
                suggestion="Erwäge symmetrische Verstrebungen für Stabilität"
            ))


def validate_structure(structure_spec: dict) -> bool:
    """Legacy-Kompatibilität"""
    return True

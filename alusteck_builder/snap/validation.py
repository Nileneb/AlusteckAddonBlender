"""
✅ STRUCTURE VALIDATION
========================
Validierung für strukturelle Integrität von Alusteck-Konstruktionen
"""

import bpy
from mathutils import Vector
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math


class IssueLevel(Enum):
    """Schweregrad eines Problems"""
    ERROR = "ERROR"      # 🔴 Kritisch
    WARNING = "WARNING"  # 🟡 Warnung
    INFO = "INFO"        # 🔵 Hinweis


@dataclass
class ValidationIssue:
    """Ein Validierungsproblem"""
    message: str
    level: IssueLevel
    objects: List[bpy.types.Object]


@dataclass
class LoadAnalysis:
    """Analyseergebnis für Lastverteilung"""
    max_load: float
    critical_points: List[bpy.types.Object]
    safety_factor: float
    is_stable: bool


# ============================================================================
# HAUPTKLASSE: STRUCTURAL VALIDATOR
# ============================================================================

class StructuralValidator:
    """
    Strukturanalyse für Alusteck-Konstruktionen
    """
    
    # Material-Konstanten für Aluminium
    ALUMINUM_YIELD_STRENGTH = 240e6  # Pa (240 MPa)
    ALUMINUM_DENSITY = 2700          # kg/m³
    SAFETY_FACTOR_TARGET = 2.0       # Mindest-Sicherheitsfaktor
    
    # Konstruktions-Regeln
    MAX_UNSUPPORTED_PROFILE_LENGTH = 1.0  # 1 Meter ohne Mittelstütze
    MAX_PORTS_PER_CONNECTOR = 6
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
    
    # ========================================================================
    # HAUPTVALIDIERUNG
    # ========================================================================
    
    def validate_structure(self, components: List[bpy.types.Object]) -> List[ValidationIssue]:
        """Komplette Strukturvalidierung"""
        self.issues = []
        
        if not components:
            self.issues.append(ValidationIssue(
                message="Keine Komponenten in der Szene",
                level=IssueLevel.WARNING,
                objects=[]
            ))
            return self.issues
        
        connectors = [c for c in components if c.get("alusteck_type") == "connector"]
        profiles = [p for p in components if p.get("alusteck_type") == "profile"]
        
        if not connectors and not profiles:
            return self.issues
        
        # Validierungssuite
        self._validate_connectivity(connectors, profiles)
        self._validate_profile_length(profiles)
        self._validate_port_usage(connectors)
        self._validate_symmetry(profiles)
        self._validate_stability(profiles, connectors)
        
        return self.issues
    
    # ========================================================================
    # CONNECTIVITY CHECK
    # ========================================================================
    
    def _validate_connectivity(self, connectors: List[bpy.types.Object], 
                              profiles: List[bpy.types.Object]):
        """Prüft ob alle Komponenten verbunden sind"""
        if not profiles:
            return
        
        # Baut Verbindungsgraph
        graph = self._build_connectivity_graph(connectors, profiles)
        
        # Findet zusammenhängende Komponenten
        islands = self._find_connected_components(graph)
        
        if len(islands) == 0:
            self.issues.append(ValidationIssue(
                message="Keine Komponenten gefunden",
                level=IssueLevel.WARNING,
                objects=[]
            ))
        elif len(islands) > 1:
            self.issues.append(ValidationIssue(
                message=f"Struktur besteht aus {len(islands)} getrennten Teilen",
                level=IssueLevel.WARNING,
                objects=[]
            ))
        
        # Prüfe auf Sackgassen (Dead Ends)
        for obj in profiles:
            connections = sum(1 for c in connectors 
                            if self._are_connected(obj, c))
            
            if connections == 1:
                self.issues.append(ValidationIssue(
                    message=f"'{obj.name}' ist nur einfach verbunden (Dead-End)",
                    level=IssueLevel.INFO,
                    objects=[obj]
                ))
    
    def _build_connectivity_graph(self, connectors, profiles) -> Dict[str, Set[str]]:
        """Baut Verbindungsgraph basierend auf alusteck_connected_to"""
        graph = {obj.name: set() for obj in connectors + profiles}
        
        for profile in profiles:
            conn_name = profile.get("alusteck_connected_to")
            if conn_name and conn_name in graph:
                graph[profile.name].add(conn_name)
                graph[conn_name].add(profile.name)
        
        return graph
    
    def _find_connected_components(self, graph: Dict[str, Set[str]]) -> List[Set[str]]:
        """Findet zusammenhängende Teilgraphen mittels DFS"""
        visited = set()
        components = []
        
        def dfs(node, component):
            if node in visited:
                return
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
    
    def _are_connected(self, obj1: bpy.types.Object, obj2: bpy.types.Object) -> bool:
        """Prüft ob zwei Objekte direkt verbunden sind"""
        return (obj1.get("alusteck_connected_to") == obj2.name or
                obj2.get("alusteck_connected_to") == obj1.name)
    
    # ========================================================================
    # PROFILE LENGTH CHECK
    # ========================================================================
    
    def _validate_profile_length(self, profiles: List[bpy.types.Object]):
        """Prüft ob Profile zu lang ohne Mittelstütze sind"""
        unsupported = []
        
        for profile in profiles:
            length = profile.get("alusteck_length", 0.0)
            
            # Zu lang ohne Mittelstütze?
            if length > self.MAX_UNSUPPORTED_PROFILE_LENGTH:
                unsupported.append(profile)
        
        if unsupported:
            self.issues.append(ValidationIssue(
                message=f"{len(unsupported)} Profile sind über {self.MAX_UNSUPPORTED_PROFILE_LENGTH:.1f}m lang",
                level=IssueLevel.WARNING,
                objects=unsupported
            ))
    
    # ========================================================================
    # PORT USAGE CHECK
    # ========================================================================
    
    def _validate_port_usage(self, connectors: List[bpy.types.Object]):
        """Prüft Portvergabe"""
        invalid = []
        
        for connector in connectors:
            # Zähle verbundene Profile
            connected_count = 0
            for obj in bpy.context.scene.objects:
                if obj.get("alusteck_connected_to") == connector.name:
                    connected_count += 1
            
            if connected_count > self.MAX_PORTS_PER_CONNECTOR:
                invalid.append(connector)
        
        if invalid:
            self.issues.append(ValidationIssue(
                message=f"{len(invalid)} Verbinder haben zu viele angeschlossene Profile",
                level=IssueLevel.ERROR,
                objects=invalid
            ))
    
    # ========================================================================
    # SYMMETRY CHECK
    # ========================================================================
    
    def _validate_symmetry(self, profiles: List[bpy.types.Object]):
        """Prüft geometrische Symmetrie (optionale Warnung)"""
        if not profiles:
            return
        
        # Sammle Profilhöhen
        profile_lengths = [p.get("alusteck_length", 0.0) for p in profiles]
        
        if len(set(profile_lengths)) > 1:
            self.issues.append(ValidationIssue(
                message="Asymmetrische Längenverhältnisse erkannt",
                level=IssueLevel.INFO,
                objects=profiles
            ))
    
    # ========================================================================
    # STABILITY CHECK
    # ========================================================================
    
    def _validate_stability(self, profiles: List[bpy.types.Object], 
                           connectors: List[bpy.types.Object]):
        """Prüft strukturelle Stabilität"""
        if not profiles or not connectors:
            return
        
        # Berechne Zentrum
        center = Vector((0, 0, 0))
        for obj in profiles + connectors:
            center += obj.location
        center /= (len(profiles) + len(connectors))
        
        # Prüfe auf asymmetrische Last
        distances = [obj.location - center for obj in profiles]
        if distances:
            avg_distance = sum(d.length for d in distances) / len(distances)
            
            # Warnung bei sehr exzentrischer Last
            if avg_distance > 2.0:
                self.issues.append(ValidationIssue(
                    message="Struktur hat unausgewogene Lastverteilung",
                    level=IssueLevel.WARNING,
                    objects=profiles + connectors
                ))


# ============================================================================
# SINGLETON
# ============================================================================

_validator_instance: Optional[StructuralValidator] = None


def get_validator() -> StructuralValidator:
    """Singleton-Zugriff auf Validator"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = StructuralValidator()
    return _validator_instance

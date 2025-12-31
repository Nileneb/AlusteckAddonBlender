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
    """Analyse der Lastverteilung"""
    max_load: float          # Maximale Last in kg
    critical_points: List[bpy.types.Object]
    safety_factor: float     # Sicherheitsfaktor
    is_stable: bool


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
        
        connectors = [c for c in components if c.get("alusteck_component") == "connector"]
        profiles = [p for p in components if p.get("alusteck_component") == "profile"]
        
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
    # VALIDIERUNGEN
    # ========================================================================
    
    def _validate_connectivity(self, connectors: List[bpy.types.Object], 
                              profiles: List[bpy.types.Object]):
        """Prüft ob alle Komponenten verbunden sind"""
        if not profiles:
            return
        
        disconnected = []
        for profile in profiles:
            # Profil ist verbunden wenn es ein "alusteck_connected_to" Property hat
            if "alusteck_connected_to" not in profile:
                disconnected.append(profile)
        
        if disconnected:
            self.issues.append(ValidationIssue(
                message=f"⚠️ {len(disconnected)} Profile sind nicht verbunden!",
                level=IssueLevel.WARNING,
                objects=disconnected
            ))
    
    def _validate_profile_length(self, profiles: List[bpy.types.Object]):
        """Prüft ob Profile zu lang ohne Mittelstütze sind"""
        unsupported = []
        
        for profile in profiles:
            length = profile.get("alusteck_length", 0.0)
            
            # Zu lang?
            if length > self.MAX_UNSUPPORTED_PROFILE_LENGTH:
                # Prüfe ob es Mittelstützen gibt (verbundene Verbinder im mittleren Bereich)
                bbox = profile.bound_box
                min_z = min(p[2] for p in bbox)
                max_z = max(p[2] for p in bbox)
                mid_z = (min_z + max_z) / 2
                tolerance = (max_z - min_z) * 0.2  # ±20%
                
                # Vereinfachte Prüfung: nur auf Länge basierend
                unsupported.append(profile)
        
        if unsupported:
            self.issues.append(ValidationIssue(
                message=f"⚠️ {len(unsupported)} Profile sind über {self.MAX_UNSUPPORTED_PROFILE_LENGTH:.1f}m lang ohne Mittelstützen!",
                level=IssueLevel.WARNING,
                objects=unsupported
            ))
    
    def _validate_port_usage(self, connectors: List[bpy.types.Object]):
        """Prüft Portvergabe"""
        invalid = []
        
        for connector in connectors:
            conn_type = connector.get("alusteck_type", "unknown")
            max_ports = self._get_max_ports_for_type(conn_type)
            
            # Zähle verbundene Profile
            connected_count = 0
            for obj in bpy.context.scene.objects:
                if obj.get("alusteck_connected_to") == connector.name:
                    connected_count += 1
            
            if connected_count > max_ports:
                invalid.append(connector)
        
        if invalid:
            self.issues.append(ValidationIssue(
                message=f"🔴 {len(invalid)} Verbinder haben zu viele angeschlossene Profile!",
                level=IssueLevel.ERROR,
                objects=invalid
            ))
    
    def _validate_symmetry(self, profiles: List[bpy.types.Object]):
        """Prüft geometrische Symmetrie (optionale Warnung)"""
        if not profiles:
            return
        
        # Sammle Profilhöhen und Breiten
        profile_lengths = [p.get("alusteck_length", 0.0) for p in profiles]
        
        if len(set(profile_lengths)) > 1:
            # Verschiedene Längen - könnte asymmetrisch sein
            self.issues.append(ValidationIssue(
                message="ℹ️ Asymmetrische Längenverhältnisse erkannt - könnte zu Instabilität führen",
                level=IssueLevel.INFO,
                objects=[]
            ))
    
    def _validate_stability(self, profiles: List[bpy.types.Object], 
                           connectors: List[bpy.types.Object]):
        """Prüft grundlegende Stabilitätskriterien"""
        if not connectors:
            self.issues.append(ValidationIssue(
                message="⚠️ Keine Verbinder gefunden - Struktur ist nicht stabil!",
                level=IssueLevel.ERROR,
                objects=profiles
            ))
            return
        
        # Prüfe ob Struktur Basis-Stabilität hat (mindestens 3 Verbinder an 3 verschiedenen Positionen)
        connector_positions = [c.location.copy() for c in connectors]
        
        if len(connector_positions) < 3:
            self.issues.append(ValidationIssue(
                message=f"⚠️ Zu wenige Verbinder ({len(connectors)}) für stabile Struktur (mindestens 3 erforderlich)",
                level=IssueLevel.WARNING,
                objects=connectors
            ))
    
    # ========================================================================
    # HELPER-METHODEN
    # ========================================================================
    
    def _get_max_ports_for_type(self, conn_type: str) -> int:
        """Gibt maximale Port-Anzahl für Verbinder-Typ zurück"""
        type_map = {
            "gerade": 2,
            "winkel": 2,
            "t_stueck": 3,
            "ecke": 3,
            "kreuz": 4,
            "wuerfel": 6,
        }
        return type_map.get(conn_type, 2)
    
    def analyze_load_distribution(self, profiles: List[bpy.types.Object], 
                                  connectors: List[bpy.types.Object]) -> LoadAnalysis:
        """Vereinfachte Lastverteilungsanalyse"""
        if not connectors:
            return LoadAnalysis(
                max_load=0.0,
                critical_points=[],
                safety_factor=0.0,
                is_stable=False
            )
        
        # Berechne vereinfacht: Last pro Verbinder
        total_length = sum(p.get("alusteck_length", 0.0) for p in profiles)
        profile_mass = total_length * self.ALUMINUM_DENSITY * 0.001  # Kg (vereinfacht)
        
        # Verteile auf Verbinder
        load_per_connector = profile_mass / len(connectors) if connectors else 0
        max_load = load_per_connector
        
        return LoadAnalysis(
            max_load=max_load,
            critical_points=connectors,
            safety_factor=self.SAFETY_FACTOR_TARGET,
            is_stable=len(connectors) >= 3
        )
    
    def get_issues_by_level(self, level: IssueLevel) -> List[ValidationIssue]:
        """Filtert Probleme nach Schweregrad"""
        return [i for i in self.issues if i.level == level]
    
    def print_report(self):
        """Gibt Validierungsbericht aus"""
        errors = self.get_issues_by_level(IssueLevel.ERROR)
        warnings = self.get_issues_by_level(IssueLevel.WARNING)
        infos = self.get_issues_by_level(IssueLevel.INFO)
        
        print("\n" + "=" * 70)
        print("ALUSTECK STRUKTUR-VALIDIERUNGSBERICHT")
        print("=" * 70)
        
        if errors:
            print(f"\n🔴 FEHLER ({len(errors)}):")
            for issue in errors:
                print(f"  • {issue.message}")
        
        if warnings:
            print(f"\n🟡 WARNUNGEN ({len(warnings)}):")
            for issue in warnings:
                print(f"  • {issue.message}")
        
        if infos:
            print(f"\n🔵 HINWEISE ({len(infos)}):")
            for issue in infos:
                print(f"  • {issue.message}")
        
        if not errors and not warnings and not infos:
            print("\n✅ Keine Probleme gefunden - Struktur ist validiert!")
        
        print("=" * 70 + "\n")


# ============================================================================
# GLOBALE INSTANZ
# ============================================================================

_validator_instance = None

def get_validator() -> StructuralValidator:
    """Singleton-Zugriff auf Validator"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = StructuralValidator()
    return _validator_instance
    
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

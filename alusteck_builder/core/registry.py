"""
COMPONENT REGISTRY
==================
Index und Zugriff auf alle Alusteck-Komponenten
Lädt Daten aus JSON-Datenbank und indexiert für schnellen Zugriff
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ComponentMetadata:
    """Metadata für eine Komponente"""
    artikel_nr: str
    name: str
    component_type: str  # "profile" | "connector" | "accessory"
    system: str         # "20mm" | "25mm" | "30mm"
    price: float
    specs: Dict[str, Any]


class ComponentRegistry:
    """
    Zentrale Registry für alle Alusteck-Komponenten
    - Lädt Datenbank einmalig
    - Indexiert nach Artikel-Nr, Typ, System
    - Bietet schnelle Lookups
    """
    
    def __init__(self):
        """Initialisiert Registry und lädt Datenbank"""
        self._profiles: Dict[str, ComponentMetadata] = {}      # artikel_nr -> metadata
        self._connectors: Dict[str, ComponentMetadata] = {}
        self._accessories: Dict[str, ComponentMetadata] = {}
        self._by_system: Dict[str, List[str]] = {}              # system -> [artikel_nrs]
        self._loaded = False
        self.load()
    
    def load(self):
        """Lädt alle Komponenten aus Datenbank"""
        if self._loaded:
            return
        
        try:
            # Finde Datenbank
            addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(addon_dir, "data", "alusteck_database.json")
            
            if not os.path.exists(db_path):
                print(f"⚠️  Datenbank nicht gefunden: {db_path}")
                return
            
            with open(db_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
            
            # Indexiere nach System
            for system_name, system_data in db.get("kategorien", {}).items():
                self._by_system[system_name] = []
                
                # Profile
                for profile in system_data.get("profile", []):
                    artikel_nr = profile.get("artikel_nr")
                    if artikel_nr:
                        self._profiles[artikel_nr] = ComponentMetadata(
                            artikel_nr=artikel_nr,
                            name=profile.get("name", ""),
                            component_type="profile",
                            system=system_name,
                            price=profile.get("preis_pro_meter", 0.0),
                            specs={
                                "aussen_mm": profile.get("aussen_mm"),
                                "wandstaerke_mm": profile.get("wandstaerke_mm"),
                                "innendurchmesser_mm": profile.get("innendurchmesser_mm"),
                            }
                        )
                        self._by_system[system_name].append(artikel_nr)
                
                # Verbinder
                for connector in system_data.get("verbinder", []):
                    artikel_nr = connector.get("artikel_nr")
                    if artikel_nr:
                        self._connectors[artikel_nr] = ComponentMetadata(
                            artikel_nr=artikel_nr,
                            name=connector.get("name", ""),
                            component_type="connector",
                            system=system_name,
                            price=connector.get("preis", 0.0),
                            specs={
                                "anzahl_wege": connector.get("anzahl_wege"),
                                "zapfen_laenge_mm": connector.get("zapfen_laenge_mm"),
                                "anschluss_punkte": connector.get("anschluss_punkte"),
                            }
                        )
                        self._by_system[system_name].append(artikel_nr)
            
            self._loaded = True
            total = len(self._profiles) + len(self._connectors) + len(self._accessories)
            print(f"✅ Registry geladen: {total} Komponenten aus Datenbank")
        
        except Exception as e:
            print(f"❌ Fehler beim Laden der Registry: {e}")
    
    # ========================================================================
    # LOOKUPS
    # ========================================================================
    
    def get_profile(self, artikel_nr: str) -> Optional[ComponentMetadata]:
        """Gibt Profil-Metadata zurück"""
        return self._profiles.get(artikel_nr)
    
    def get_connector(self, artikel_nr: str) -> Optional[ComponentMetadata]:
        """Gibt Verbinder-Metadata zurück"""
        return self._connectors.get(artikel_nr)
    
    def get_component(self, artikel_nr: str) -> Optional[ComponentMetadata]:
        """Gibt beliebige Komponente zurück (Profile oder Verbinder)"""
        return (self._profiles.get(artikel_nr) or 
                self._connectors.get(artikel_nr) or 
                self._accessories.get(artikel_nr))
    
    def get_profiles_by_system(self, system: str) -> List[ComponentMetadata]:
        """Gibt alle Profile eines Systems zurück"""
        artikel_nrs = self._by_system.get(system, [])
        return [self._profiles[nr] for nr in artikel_nrs if nr in self._profiles]
    
    def get_connectors_by_system(self, system: str) -> List[ComponentMetadata]:
        """Gibt alle Verbinder eines Systems zurück"""
        artikel_nrs = self._by_system.get(system, [])
        return [self._connectors[nr] for nr in artikel_nrs if nr in self._connectors]
    
    def list_all_profiles(self) -> List[ComponentMetadata]:
        """Alle Profile"""
        return list(self._profiles.values())
    
    def list_all_connectors(self) -> List[ComponentMetadata]:
        """Alle Verbinder"""
        return list(self._connectors.values())
    
    def search(self, query: str) -> List[ComponentMetadata]:
        """Sucht Komponenten nach Name oder Artikel-Nr"""
        query_lower = query.lower()
        results = []
        
        for comp in list(self._profiles.values()) + list(self._connectors.values()):
            if (query_lower in comp.artikel_nr.lower() or 
                query_lower in comp.name.lower()):
                results.append(comp)
        
        return results
    
    def get_price(self, artikel_nr: str) -> float:
        """Gibt Preis einer Komponente zurück"""
        comp = self.get_component(artikel_nr)
        return comp.price if comp else 0.0
    
    def get_price_for_length(self, artikel_nr: str, length_m: float) -> float:
        """Berechnet Preis für Profil-Länge"""
        comp = self.get_profile(artikel_nr)
        if not comp:
            return 0.0
        return comp.price * length_m
    
    # ========================================================================
    # SYSTEM-MANAGEMENT
    # ========================================================================
    
    def list_systems(self) -> List[str]:
        """Listet alle verfügbaren Systeme"""
        return list(self._by_system.keys())
    
    def get_system_components(self, system: str) -> Dict[str, List[ComponentMetadata]]:
        """Gibt alle Komponenten eines Systems nach Typ gruppiert"""
        return {
            "profile": self.get_profiles_by_system(system),
            "connector": self.get_connectors_by_system(system),
        }
    
    # ========================================================================
    # VALIDIERUNG
    # ========================================================================
    
    def is_valid_component(self, artikel_nr: str) -> bool:
        """Prüft ob Komponente in Registry existiert"""
        return self.get_component(artikel_nr) is not None
    
    def is_valid_profile(self, artikel_nr: str) -> bool:
        """Prüft ob Profil existiert"""
        return artikel_nr in self._profiles
    
    def is_valid_connector(self, artikel_nr: str) -> bool:
        """Prüft ob Verbinder existiert"""
        return artikel_nr in self._connectors
    
    def validate_system_compatibility(self, artikel_nr1: str, artikel_nr2: str) -> bool:
        """Prüft ob zwei Komponenten im gleichen System sind"""
        comp1 = self.get_component(artikel_nr1)
        comp2 = self.get_component(artikel_nr2)
        
        if not comp1 or not comp2:
            return False
        
        return comp1.system == comp2.system
    
    # ========================================================================
    # STATISTIKEN
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Registry-Statistiken zurück"""
        return {
            "total_profiles": len(self._profiles),
            "total_connectors": len(self._connectors),
            "total_accessories": len(self._accessories),
            "systems": list(self._by_system.keys()),
            "components_per_system": {
                sys: len(self._by_system.get(sys, []))
                for sys in self._by_system.keys()
            },
            "loaded": self._loaded,
        }


# ============================================================================
# GLOBALE INSTANZ
# ============================================================================

_registry_instance = None

def get_registry() -> ComponentRegistry:
    """Singleton-Zugriff auf Component Registry"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ComponentRegistry()
    return _registry_instance

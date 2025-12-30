"""
Component Registry - Index und Zugriff auf alle Alusteck-Komponenten.
Lädt Daten aus der Datenbank und indexiert sie für schnellen Zugriff.
"""

from typing import Dict, List, Optional, Any
from . import database


class ComponentRegistry:
    """Registry für Profile, Verbinder und Zubehör."""
    
    def __init__(self):
        """Initialisiert Registry und lädt Datenbank."""
        self._components: Dict[str, Dict] = {}  # system -> type -> id -> data
        self._connectors: Dict[str, Dict] = {}
        self._accessories: Dict[str, Dict] = {}
        self._loaded = False
        self._load_from_database()
    
    def _load_from_database(self):
        """Lädt alle Komponenten aus der JSON-Datenbank."""
        if self._loaded:
            return
        
        db = database.load_components()
        
        if not db or "systems" not in db:
            print("⚠ Keine Komponenten-Datenbank gefunden!")
            return
        
        # Indexiere für jedes System
        for system_name, system_data in db.get("systems", {}).items():
            # Profile
            profiles = system_data.get("profile", {}).get("variants", [])
            if system_name not in self._components:
                self._components[system_name] = {}
            
            for profile in profiles:
                pid = profile.get("id")
                if pid:
                    self._components[system_name][pid] = profile
            
            # Verbinder
            connectors = system_data.get("connectors", [])
            if system_name not in self._connectors:
                self._connectors[system_name] = {}
            
            for connector in connectors:
                cid = connector.get("id")
                if cid:
                    self._connectors[system_name][cid] = connector
            
            # Zubehör
            accessories = system_data.get("accessories", [])
            if system_name not in self._accessories:
                self._accessories[system_name] = {}
            
            for accessory in accessories:
                aid = accessory.get("id")
                if aid:
                    self._accessories[system_name][aid] = accessory
        
        self._loaded = True
    
    # =================================================================
    # PROFILE
    # =================================================================
    
    def get_profile(self, system: str, profile_id: str) -> Optional[Dict]:
        """Holt ein Profil nach System und ID."""
        return self._components.get(system, {}).get(profile_id)
    
    def get_all_profiles(self, system: str) -> List[Dict]:
        """Holt alle Profile eines Systems."""
        return list(self._components.get(system, {}).values())
    
    def get_profiles_by_steg(self, system: str, steg_type: Optional[str]) -> List[Dict]:
        """Filtert Profile nach Steg-Typ."""
        profiles = self.get_all_profiles(system)
        
        if steg_type is None:
            return [p for p in profiles if not p.get("steg")]
        
        return [p for p in profiles 
                if p.get("steg") and p.get("steg").get("type") == steg_type]
    
    # =================================================================
    # VERBINDER
    # =================================================================
    
    def get_connector(self, system: str, connector_id: str) -> Optional[Dict]:
        """Holt einen Verbinder nach System und ID."""
        return self._connectors.get(system, {}).get(connector_id)
    
    def get_all_connectors(self, system: str) -> List[Dict]:
        """Holt alle Verbinder eines Systems."""
        return list(self._connectors.get(system, {}).values())
    
    def get_connectors_by_type(self, system: str, conn_type: str) -> List[Dict]:
        """Filtert Verbinder nach Typ."""
        connectors = self.get_all_connectors(system)
        return [c for c in connectors if c.get("type") == conn_type]
    
    def get_connectors_by_ways(self, system: str, ways: int) -> List[Dict]:
        """Filtert Verbinder nach Anzahl Wege."""
        connectors = self.get_all_connectors(system)
        return [c for c in connectors if c.get("ways") == ways]
    
    # =================================================================
    # ZUBEHÖR
    # =================================================================
    
    def get_accessory(self, system: str, accessory_id: str) -> Optional[Dict]:
        """Holt ein Zubehör-Teil."""
        return self._accessories.get(system, {}).get(accessory_id)
    
    def get_all_accessories(self, system: str) -> List[Dict]:
        """Holt all Zubehör eines Systems."""
        return list(self._accessories.get(system, {}).values())
    
    def get_accessories_by_type(self, system: str, acc_type: str) -> List[Dict]:
        """Filtert Zubehör nach Typ."""
        accessories = self.get_all_accessories(system)
        return [a for a in accessories if a.get("type") == acc_type]
    
    # =================================================================
    # ALLGEMEIN
    # =================================================================
    
    def get_systems(self) -> List[str]:
        """Gibt alle verfügbaren Systeme zurück."""
        return list(set(
            list(self._components.keys()) +
            list(self._connectors.keys()) +
            list(self._accessories.keys())
        ))
    
    def search(self, query: str, system: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Sucht Komponenten nach Name."""
        query_lower = query.lower()
        results = {
            "profiles": [],
            "connectors": [],
            "accessories": []
        }
        
        systems = [system] if system else self.get_systems()
        
        for sys in systems:
            # Profile
            for profile in self.get_all_profiles(sys):
                if query_lower in profile.get("name", "").lower():
                    results["profiles"].append(profile)
            
            # Verbinder
            for connector in self.get_all_connectors(sys):
                if query_lower in connector.get("name", "").lower():
                    results["connectors"].append(connector)
            
            # Zubehör
            for accessory in self.get_all_accessories(sys):
                if query_lower in accessory.get("name", "").lower():
                    results["accessories"].append(accessory)
        
        return results
    
    def clear(self):
        """Löscht alle Daten und leert Registry."""
        self._components.clear()
        self._connectors.clear()
        self._accessories.clear()
        self._loaded = False


# Globale Registry-Instanz
_global_registry: Optional[ComponentRegistry] = None


def get_registry() -> ComponentRegistry:
    """Singleton-Zugriff auf die Registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ComponentRegistry()
    return _global_registry


def reload_registry() -> ComponentRegistry:
    """Lädt Registry neu."""
    global _global_registry
    _global_registry = ComponentRegistry()
    return _global_registry

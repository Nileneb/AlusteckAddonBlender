"""Registry placeholder for components and connectors."""

from typing import Dict, Any


class ComponentRegistry:
    def __init__(self):
        self.components: Dict[str, Any] = {}
        self.connectors: Dict[str, Any] = {}
        self.accessories: Dict[str, Any] = {}

    def register_component(self, key: str, value: Any):
        self.components[key] = value

    def register_connector(self, key: str, value: Any):
        self.connectors[key] = value

    def register_accessory(self, key: str, value: Any):
        self.accessories[key] = value

    def clear(self):
        self.components.clear()
        self.connectors.clear()
        self.accessories.clear()

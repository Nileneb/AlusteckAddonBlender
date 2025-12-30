"""Generate direct shopping cart links for alusteck.de."""

from typing import List, Dict, Optional
from urllib.parse import urlencode, quote


class ShopLinkGenerator:
    """Create direct Alusteck shop links with pre-filled carts."""

    BASE_URL = "https://www.alusteck.de"
    SHOP_URL = f"{BASE_URL}/shop"

    def __init__(self):
        self.cart_items: List[Dict[str, any]] = []

    def add_item(self, article_nr: str, quantity: int, quantity_unit: str = "meter"):
        """Add item to shop cart."""
        self.cart_items.append({
            "article_nr": article_nr,
            "quantity": quantity,
            "unit": quantity_unit
        })

    def from_bom(self, bom):
        """Build shop cart from BOM object."""
        if not bom or not hasattr(bom, 'items'):
            return
        
        for item in bom.items:
            # Map article numbers
            quantity = item.quantity
            
            # Für Profile: Länge in Metern
            if 'profil' in item.name.lower():
                quantity_unit = "meter"
            else:
                quantity_unit = "stück"  # Pieces
            
            self.add_item(item.article_nr, quantity, quantity_unit)

    def generate_simple_link(self) -> str:
        """Generate simple product list URL."""
        if not self.cart_items:
            return self.BASE_URL
        
        # Format: /shop?s=VK25;2D25K;3E25K
        article_str = ";".join([item["article_nr"] for item in self.cart_items])
        return f"{self.SHOP_URL}?s={quote(article_str)}"

    def generate_bom_report(self) -> str:
        """Generate text report suitable for email or inquiry."""
        report = []
        report.append("╔════════════════════════════════════════╗")
        report.append("║    ALUSTECK BESTELLLISTE - ANFRAGE     ║")
        report.append("╚════════════════════════════════════════╝")
        report.append("")
        report.append("Folgende Komponenten werden benötigt:")
        report.append("")
        
        for i, item in enumerate(self.cart_items, 1):
            report.append(f"{i:2d}. {item['article_nr']:10s}  x  {item['quantity']:5.2f} {item['unit']}")
        
        report.append("")
        report.append("Bitte um Angebot für diese Komponenten.")
        report.append("")
        report.append(f"Shop-Link: {self.generate_simple_link()}")
        
        return "\n".join(report)


def create_shopping_link(bom) -> str:
    """Convenience function: BOM -> Shopping link."""
    generator = ShopLinkGenerator()
    generator.from_bom(bom)
    return generator.generate_simple_link()

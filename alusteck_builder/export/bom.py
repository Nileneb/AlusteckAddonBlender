"""Bill of Materials (Stückliste) export for CSV and JSON formats."""

import json
import csv
from io import StringIO
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class BOMItem:
    """Single line item in BOM."""
    article_nr: str
    name: str
    quantity: int
    system_mm: int
    unit_price: float
    total_price: float


class BillOfMaterials:
    """Generate Bills of Materials from Blender scene."""

    def __init__(self):
        self.items: List[BOMItem] = []
        self.total_cost = 0.0

    def add_item(self, article_nr: str, name: str, quantity: int,
                 system_mm: int, unit_price: float):
        """Add an item to BOM."""
        total = unit_price * quantity
        self.items.append(BOMItem(
            article_nr=article_nr,
            name=name,
            quantity=quantity,
            system_mm=system_mm,
            unit_price=unit_price,
            total_price=total
        ))
        self.total_cost += total

    def to_csv(self) -> str:
        """Export BOM as CSV string."""
        output = StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # Header
        writer.writerow([
            'Artikel-Nr.',
            'Bezeichnung',
            'Menge',
            'System (mm)',
            'Einzelpreis €',
            'Gesamtpreis €'
        ])
        
        # Items
        for item in self.items:
            writer.writerow([
                item.article_nr,
                item.name,
                item.quantity,
                item.system_mm,
                f"{item.unit_price:.2f}",
                f"{item.total_price:.2f}"
            ])
        
        # Total
        writer.writerow([])
        writer.writerow(['GESAMTSUMME:', '', '', '', '', f"{self.total_cost:.2f}"])
        
        return output.getvalue()

    def to_json(self) -> str:
        """Export BOM as JSON string."""
        data = {
            "metadata": {
                "format": "alusteck_bom_v1",
                "total_cost": round(self.total_cost, 2)
            },
            "items": [
                {
                    "article_nr": item.article_nr,
                    "name": item.name,
                    "quantity": item.quantity,
                    "system_mm": item.system_mm,
                    "unit_price": round(item.unit_price, 2),
                    "total_price": round(item.total_price, 2)
                }
                for item in self.items
            ]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

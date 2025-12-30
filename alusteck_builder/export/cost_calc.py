"""Cost calculation and budget analysis."""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class CostBreakdown:
    """Detailed cost breakdown by component type."""
    profiles_cost: float = 0.0
    connectors_cost: float = 0.0
    accessories_cost: float = 0.0
    total_cost: float = 0.0
    count_profiles: int = 0
    count_connectors: int = 0
    count_accessories: int = 0


class CostCalculator:
    """Calculate material costs from BOM."""

    def __init__(self):
        self.breakdown = CostBreakdown()

    def from_bom(self, bom) -> CostBreakdown:
        """Calculate costs from BOM object."""
        breakdown = CostBreakdown()
        
        if not bom or not hasattr(bom, 'items'):
            return breakdown
        
        for item in bom.items:
            # Gruppierung nach Typ (heuristische Erkennung)
            if 'profil' in item.name.lower() or 'rohr' in item.name.lower():
                breakdown.profiles_cost += item.total_price
                breakdown.count_profiles += item.quantity
            elif 'verbinder' in item.name.lower():
                breakdown.connectors_cost += item.total_price
                breakdown.count_connectors += item.quantity
            else:
                breakdown.accessories_cost += item.total_price
                breakdown.count_accessories += item.quantity
        
        breakdown.total_cost = (
            breakdown.profiles_cost +
            breakdown.connectors_cost +
            breakdown.accessories_cost
        )
        
        self.breakdown = breakdown
        return breakdown

    def add_margin(self, cost: float, margin_percent: float) -> float:
        """Apply profit margin to cost."""
        return cost * (1.0 + margin_percent / 100.0)

    def format_cost_report(self) -> str:
        """Format cost analysis as readable report."""
        bd = self.breakdown
        
        report = []
        report.append("╔════════════════════════════════════════╗")
        report.append("║      ALUSTECK KOSTENBERECHNUNG         ║")
        report.append("╚════════════════════════════════════════╝")
        report.append("")
        report.append("KOMPONENTEN-ÜBERSICHT:")
        report.append(f"  Profile:    {bd.count_profiles:3d} Stück   {bd.profiles_cost:8.2f} €")
        report.append(f"  Verbinder:  {bd.count_connectors:3d} Stück   {bd.connectors_cost:8.2f} €")
        report.append(f"  Zubehör:    {bd.count_accessories:3d} Stück   {bd.accessories_cost:8.2f} €")
        report.append("-" * 40)
        report.append(f"  GESAMT:                {bd.total_cost:8.2f} €")
        report.append("")
        
        # Margin examples
        report.append("GEWINNMARGEN (Beispiele):")
        for margin in [10, 20, 30]:
            price = self.add_margin(bd.total_cost, margin)
            report.append(f"  +{margin}%: {price:8.2f} €")
        report.append("")
        
        return "\n".join(report)

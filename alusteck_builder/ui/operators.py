"""Blender operators for adding Alusteck components with a system switch."""

from typing import Optional

try:  # Blender context
    import bpy
    from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
    HAS_BLENDER = True
except ImportError:  # pragma: no cover - makes the module importable outside Blender
    bpy = None
    BoolProperty = EnumProperty = FloatProperty = StringProperty = None
    HAS_BLENDER = False

from alusteck_builder.components import accessory, connector, profile


def _system_items(_self, _context):
    return [
        ("20", "20mm", "Alusteck 20mm System"),
        ("25", "25mm", "Alusteck 25mm System"),
        ("30", "30mm", "Alusteck 30mm System"),
    ]


def _component_items(_self, _context):
    return [
        ("PROFILE", "Profil", "Vierkantrohr-Profile"),
        ("CONNECTOR", "Verbinder", "Verbinder 2-6 Wege"),
        ("ACCESSORY", "Zubehör", "Abdeckkappen, Zubehör"),
    ]


if HAS_BLENDER:
    class ALUSTECK_OT_add_component(bpy.types.Operator):
        bl_idname = "alusteck.add_component"
        bl_label = "Alusteck Komponente hinzufügen"
        bl_options = {"REGISTER", "UNDO"}

        system = EnumProperty(name="System", items=_system_items, default="25")
        component_type = EnumProperty(name="Typ", items=_component_items, default="PROFILE")
        component_id = StringProperty(name="Komponenten-ID", description="Datenbank-ID oder Preset")
        length_mm = FloatProperty(name="Länge (mm)", default=1000.0, min=1.0)
        snap_to_cursor = BoolProperty(name="Am 3D-Cursor ausrichten", default=True)

        def execute(self, context):  # noqa: D401 - Blender signature
            if not bpy:
                self.report({"ERROR"}, "Blender API nicht verfügbar")
                return {"CANCELLED"}

            try:
                self._create_component(context)
            except NotImplementedError as exc:
                self.report({"ERROR"}, f"Generator fehlt: {exc}")
                return {"CANCELLED"}
            except Exception as exc:  # pragma: no cover - runtime safety
                self.report({"ERROR"}, f"Fehler: {exc}")
                return {"CANCELLED"}

            self.report({"INFO"}, f"Alusteck {self.component_type} ({self.system}mm) hinzugefügt")
            return {"FINISHED"}

        def _create_component(self, context):
            if self.component_type == "PROFILE":
                spec = self._profile_spec()
                obj = profile.create_profile_mesh(spec)
            elif self.component_type == "CONNECTOR":
                spec = self._connector_spec()
                obj = connector.create_connector_mesh(spec)
            elif self.component_type == "ACCESSORY":
                spec = self._accessory_spec()
                obj = accessory.create_accessory(spec)
            else:
                raise ValueError(f"Unbekannter Typ {self.component_type}")

            if obj and self.snap_to_cursor:
                self._place_at_cursor(context, obj)

        def _profile_spec(self) -> dict:
            return {
                "system": self.system,
                "id": self.component_id or f"PROFILE-{self.system}",
                "length_mm": self.length_mm,
            }

        def _connector_spec(self) -> dict:
            return {
                "system": self.system,
                "id": self.component_id or f"CONNECTOR-{self.system}",
            }

        def _accessory_spec(self) -> dict:
            return {
                "system": self.system,
                "id": self.component_id or f"ACCESSORY-{self.system}",
            }

        def _place_at_cursor(self, context, obj):
            cursor_loc = context.scene.cursor.location
            obj.location = cursor_loc

if HAS_BLENDER:
    class ALUSTECK_OT_export_bom(bpy.types.Operator):
        """Export Bill of Materials as CSV or JSON."""
        bl_idname = "alusteck.export_bom"
        bl_label = "Stückliste exportieren"
        bl_options = {"REGISTER"}

        filename_ext = StringProperty(default=".csv")
        filter_glob = StringProperty(default="*.csv;*.json")

        def execute(self, context):  # noqa: D401
            if not bpy:
                self.report({"ERROR"}, "Blender API not available")
                return {"CANCELLED"}

            try:
                from alusteck_builder.export import BillOfMaterials
            except ImportError:
                self.report({"ERROR"}, "Export module not found")
                return {"CANCELLED"}

            # Generate BOM from scene
            bom = BillOfMaterials()
            
            # Dummy: Add some test items
            bom.add_item("VK25-STD", "Profil 25x25mm Standard", 4, 25, 5.90)
            bom.add_item("3E25K", "Eckverbinder 3-Wege", 8, 25, 2.50)
            bom.add_item("2D25K", "Verbinder gerade 2-Wege", 4, 25, 1.50)
            
            # Export as CSV
            csv_content = bom.to_csv()
            
            # Write file
            import os
            filepath = os.path.expanduser("~/Alusteck_BOM.csv")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(csv_content)
            
            self.report({'INFO'}, f"BOM exported to {filepath}")
            return {"FINISHED"}


if HAS_BLENDER:
    class ALUSTECK_OT_export_costs(bpy.types.Operator):
        """Export cost analysis and margin calculations."""
        bl_idname = "alusteck.export_costs"
        bl_label = "Kostenberechnung anzeigen"
        bl_options = {"REGISTER"}

        def execute(self, context):  # noqa: D401
            if not bpy:
                self.report({"ERROR"}, "Blender API not available")
                return {"CANCELLED"}

            try:
                from alusteck_builder.export import BillOfMaterials, CostCalculator
            except ImportError:
                self.report({"ERROR"}, "Export module not found")
                return {"CANCELLED"}

            # Generate BOM
            bom = BillOfMaterials()
            bom.add_item("VK25-STD", "Profil 25x25mm Standard", 4, 25, 5.90)
            bom.add_item("3E25K", "Eckverbinder 3-Wege", 8, 25, 2.50)
            
            # Calculate costs
            calc = CostCalculator()
            calc.from_bom(bom)
            
            # Print to console
            report = calc.format_cost_report()
            print(report)
            
            self.report({'INFO'}, "Kostenberechnung angezeigt (siehe Console)")
            return {"FINISHED"}


if HAS_BLENDER:
    class ALUSTECK_OT_export_shop_link(bpy.types.Operator):
        """Generate shop.alusteck.de link with pre-filled items."""
        bl_idname = "alusteck.export_shop_link"
        bl_label = "Shop-Link generieren"
        bl_options = {"REGISTER"}

        def execute(self, context):  # noqa: D401
            if not bpy:
                self.report({"ERROR"}, "Blender API not available")
                return {"CANCELLED"}

            try:
                from alusteck_builder.export import BillOfMaterials, ShopLinkGenerator
            except ImportError:
                self.report({"ERROR"}, "Export module not found")
                return {"CANCELLED"}

            # Generate BOM
            bom = BillOfMaterials()
            bom.add_item("VK25-STD", "Profil 25x25mm Standard", 4, 25, 5.90)
            bom.add_item("3E25K", "Eckverbinder 3-Wege", 8, 25, 2.50)
            
            # Generate shop link
            gen = ShopLinkGenerator()
            gen.from_bom(bom)
            link = gen.generate_simple_link()
            
            # Copy to clipboard (if wm_clipboard available)
            try:
                context.window_manager.clipboard = link
                self.report({'INFO'}, f"Link kopiert: {link}")
            except Exception:
                self.report({'INFO'}, f"Link: {link}")
            
            return {"FINISHED"}


if HAS_BLENDER:
    classes = (
        ALUSTECK_OT_add_component,
        ALUSTECK_OT_export_bom,
        ALUSTECK_OT_export_costs,
        ALUSTECK_OT_export_shop_link,
    )
else:
    classes = tuple()


def register_operators():
    if not HAS_BLENDER:
        return
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_operators():
    if not HAS_BLENDER:
        return
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

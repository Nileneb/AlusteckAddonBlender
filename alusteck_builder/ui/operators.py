"""Blender operators for adding Alusteck components with a system switch."""

from typing import Optional

try:  # Blender context
    import bpy
    from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
except ImportError:  # pragma: no cover - makes the module importable outside Blender
    bpy = None
    BoolProperty = EnumProperty = FloatProperty = StringProperty = None

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


class ALUSTECK_OT_add_component(bpy.types.Operator if bpy else object):
    bl_idname = "alusteck.add_component"
    bl_label = "Alusteck Komponente hinzufügen"
    bl_options = {"REGISTER", "UNDO"}

    system: EnumProperty(name="System", items=_system_items, default="25") if bpy else None
    component_type: EnumProperty(name="Typ", items=_component_items, default="PROFILE") if bpy else None
    component_id: StringProperty(name="Komponenten-ID", description="Datenbank-ID oder Preset") if bpy else None
    length_mm: FloatProperty(name="Länge (mm)", default=1000.0, min=1.0) if bpy else None
    snap_to_cursor: BoolProperty(name="Am 3D-Cursor ausrichten", default=True) if bpy else None

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


classes = (ALUSTECK_OT_add_component,) if bpy else tuple()


def register_operators():
    if not bpy:
        return
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_operators():
    if not bpy:
        return
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

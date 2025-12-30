"""UI scaffolding for Blender panels and operators."""

from alusteck_builder.ui import operators


def register():
	operators.register_operators()


def unregister():
	operators.unregister_operators()

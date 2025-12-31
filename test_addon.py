#!/usr/bin/env python3
"""
COMPREHENSIVE ADDON VALIDATION TESTS - IMPROVED
================================================
Tests structure, syntax, AND logic errors.
"""

import sys
import os
import json
import ast
from pathlib import Path

addon_path = Path(__file__).parent / "alusteck_builder"
sys.path.insert(0, str(addon_path.parent))

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test(self, name, condition, error_msg=""):
        if condition:
            print(f"✅ {name}")
            self.passed += 1
        else:
            print(f"❌ {name}")
            self.failed += 1
            if error_msg:
                self.errors.append(f"{name}: {error_msg}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"RESULTS: {self.passed}/{total} tests passed")
        print(f"{'='*60}")
        if self.errors:
            print("\nFAILURES:")
            for error in self.errors:
                print(f"  - {error}")
        return self.failed == 0

results = TestResults()

print("ALUSTECK BUILDER ADDON - COMPREHENSIVE TEST SUITE")
print("=" * 60)

# ============================================================================
# TEST 1: DUPLICATE FUNCTION DEFINITIONS (CRITICAL!)
# ============================================================================
print("\n[1] DUPLICATE FUNCTION DEFINITIONS")
print("-" * 60)

py_files = list(addon_path.glob("**/*.py"))
for py_file in sorted(py_files):
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        function_defs = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name not in function_defs:
                    function_defs[node.name] = 0
                function_defs[node.name] += 1
        
        duplicates = {name: count for name, count in function_defs.items() if count > 1}
        if duplicates:
            results.test(f"No duplicate functions in {py_file.name}", False,
                       f"CRITICAL: Functions defined multiple times: {duplicates}")
        else:
            results.test(f"No duplicate functions in {py_file.name}", True)
    
    except Exception as e:
        results.test(f"Parse {py_file.name}", False, str(e))

# ============================================================================
# TEST 1B: DUPLICATE CLASS DEFINITIONS (CRITICAL!)
# ============================================================================
print("\n[1B] DUPLICATE CLASS DEFINITIONS")
print("-" * 60)

for py_file in sorted(py_files):
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        class_defs = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name not in class_defs:
                    class_defs[node.name] = 0
                class_defs[node.name] += 1
        
        duplicates = {name: count for name, count in class_defs.items() if count > 1}
        if duplicates:
            results.test(f"No duplicate classes in {py_file.name}", False,
                       f"CRITICAL: Classes defined multiple times: {duplicates}")
        else:
            results.test(f"No duplicate classes in {py_file.name}", True)
    
    except Exception as e:
        results.test(f"Parse {py_file.name}", False, str(e))

# ============================================================================
# TEST 2: FILE STRUCTURE
# ============================================================================
print("\n[2] FILE STRUCTURE")
print("-" * 60)

expected_files = [
    "alusteck_builder/__init__.py",
    "alusteck_builder/core/__init__.py",
    "alusteck_builder/core/database.py",
    "alusteck_builder/core/registry.py",
    "alusteck_builder/core/constants.py",
    "alusteck_builder/snap/__init__.py",
    "alusteck_builder/snap/engine.py",
    "alusteck_builder/snap/collision.py",
    "alusteck_builder/snap/validation.py",
    "alusteck_builder/ui/__init__.py",
    "alusteck_builder/ui/panels.py",
    "alusteck_builder/ui/operators.py",
    "alusteck_builder/ui/menus.py",
    "alusteck_builder/components/__init__.py",
    "alusteck_builder/components/materials.py",
    "alusteck_builder/components/profile.py",
    "alusteck_builder/components/connector.py",
    "alusteck_builder/export/__init__.py",
    "alusteck_builder/data/alusteck_database.json",
]

base_path = Path(__file__).parent
for file in expected_files:
    file_path = base_path / file
    results.test(f"File exists: {file}", file_path.exists(), 
                 f"Not found at {file_path}")

# ============================================================================
# TEST 3: PYTHON SYNTAX
# ============================================================================
print("\n[3] PYTHON SYNTAX VALIDATION")
print("-" * 60)

import py_compile

py_files = list(addon_path.glob("**/*.py"))
for py_file in sorted(py_files):
    try:
        py_compile.compile(str(py_file), doraise=True)
        results.test(f"Syntax OK: {py_file.relative_to(base_path)}", True)
    except py_compile.PyCompileError as e:
        results.test(f"Syntax OK: {py_file.relative_to(base_path)}", False, str(e))

# ============================================================================
# TEST 4: DATABASE INTEGRITY
# ============================================================================
print("\n[4] DATABASE INTEGRITY")
print("-" * 60)

db_path = base_path / "alusteck_builder" / "data" / "alusteck_database.json"
try:
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)
    results.test("Database JSON valid", True)
    
    # Check structure
    results.test("Has 'kategorien' key", "kategorien" in db)
    
    if "kategorien" in db:
        kategorien = db["kategorien"]
        total_profiles = 0
        total_connectors = 0
        
        for system_name, system_data in kategorien.items():
            profiles = system_data.get("profile", [])
            connectors = system_data.get("verbinder", [])
            total_profiles += len(profiles)
            total_connectors += len(connectors)
            
            for profile in profiles:
                if "artikel_nr" not in profile:
                    results.test(f"Profile has artikel_nr", False, 
                                f"Profile in {system_name} missing artikel_nr")
            
            for connector in connectors:
                if "artikel_nr" not in connector:
                    results.test(f"Connector has artikel_nr", False,
                                f"Connector in {system_name} missing artikel_nr")
        
        results.test(f"Database has profiles", total_profiles > 0, 
                    f"Found {total_profiles} profiles")
        results.test(f"Database has connectors", total_connectors > 0,
                    f"Found {total_connectors} connectors")

except Exception as e:
    results.test("Database JSON valid", False, str(e))

# ============================================================================
# TEST 5: CORE MODULES (WITHOUT BLENDER)
# ============================================================================
print("\n[5] CORE MODULES (NON-BLENDER TESTS)")
print("-" * 60)

try:
    from alusteck_builder.core import constants
    results.test("core.constants imports", True)
    results.test("SYSTEM_SIZES_MM defined", hasattr(constants, 'SYSTEM_SIZES_MM'))
    
except Exception as e:
    results.test("core.constants imports", False, str(e))

try:
    from alusteck_builder.core import database
    results.test("core.database imports", True)
    results.test("load_json function exists", hasattr(database, 'load_json'))
    results.test("load_components function exists", hasattr(database, 'load_components'))
    
except Exception as e:
    results.test("core.database imports", False, str(e))

# ============================================================================
# TEST 6: REGISTRY (NON-BLENDER)
# ============================================================================
print("\n[6] REGISTRY MODULE")
print("-" * 60)

try:
    from alusteck_builder.core.registry import ComponentRegistry, get_registry
    results.test("registry imports", True)
    
    # Create registry instance
    registry = ComponentRegistry()
    results.test("ComponentRegistry instantiates", True)
    results.test("Registry has profiles", len(registry._profiles) > 0,
                f"Found {len(registry._profiles)} profiles")
    results.test("Registry has connectors", len(registry._connectors) > 0,
                f"Found {len(registry._connectors)} connectors")
    
    # Test methods
    results.test("get_profile method exists", hasattr(registry, 'get_profile'))
    results.test("get_connector method exists", hasattr(registry, 'get_connector'))
    results.test("search method exists", hasattr(registry, 'search'))
    results.test("list_systems method exists", hasattr(registry, 'list_systems'))
    
    systems = registry.list_systems()
    results.test("list_systems returns systems", len(systems) > 0,
                f"Found {len(systems)} systems")
    
except Exception as e:
    results.test("registry imports", False, str(e))

# ============================================================================
# TEST 7: MODULE __init__.py FILES
# ============================================================================
print("\n[7] MODULE EXPORTS (__init__.py)")
print("-" * 60)

modules_to_check = {
    "alusteck_builder.core": ["constants", "database", "get_registry"],
    "alusteck_builder.snap": ["AlusteckSnapEngine", "CollisionDetector"],
    "alusteck_builder.ui": ["register", "unregister"],
    "alusteck_builder.components": [],
    "alusteck_builder.export": [],
}

for module_name, required_exports in modules_to_check.items():
    try:
        module = __import__(module_name, fromlist=[''])
        results.test(f"{module_name} imports", True)
        
        for export in required_exports:
            has_export = hasattr(module, export)
            results.test(f"{module_name}.{export} exists", has_export,
                        f"Missing {export}")
    except ImportError as e:
        results.test(f"{module_name} imports", False, str(e))

# ============================================================================
# TEST 8: JSON ICONS (UI VALIDATION)
# ============================================================================
print("\n[8] UI ICONS VALIDATION")
print("-" * 60)

# List of valid Blender 5.0 icons
valid_icons = {
    'SNAP_ON', 'INFO', 'MOUSE_LMB', 'MOUSE_RMB', 'DOT', 'CHECKMARK',
    'FILE_TICK', 'CONSTRAINT', 'MESH_CUBE', 'PIVOT_CURSOR', 'PHYSICS',
    'CONSOLE', 'EXPORT', 'FILE_TEXT', 'FILE', 'FUND', 'INTERNET',
    'MOD_BUILD', 'MOD_ARRAY', 'PIVOT_INDIVIDUAL', 'ERROR', 'ADD',
    'NONE', 'X',
}

used_icons = set()

# Extract icons from panels.py
panels_py = base_path / "alusteck_builder" / "ui" / "panels.py"
with open(panels_py, 'r', encoding='utf-8') as f:
    content = f.read()
    import re
    icon_pattern = r"icon='([^']+)'"
    found_icons = re.findall(icon_pattern, content)
    used_icons.update(found_icons)

all_valid = True
for icon in sorted(used_icons):
    is_valid = icon in valid_icons
    if not is_valid:
        all_valid = False
    results.test(f"Icon '{icon}' valid", is_valid)

results.test("All panels.py icons valid", all_valid)

# ============================================================================
# TEST 9: MAIN __init__.py STRUCTURE
# ============================================================================
print("\n[9] MAIN ADDON __init__.py")
print("-" * 60)

main_init = base_path / "alusteck_builder" / "__init__.py"
with open(main_init, 'r', encoding='utf-8') as f:
    init_content = f.read()

results.test("__init__.py has bl_info", "bl_info" in init_content)
results.test("__init__.py has register()", "def register():" in init_content)
results.test("__init__.py has unregister()", "def unregister():" in init_content)
results.test("__init__.py has ALUSTECK_DATABASE", "ALUSTECK_DATABASE" in init_content)

# ============================================================================
# SUMMARY
# ============================================================================
success = results.summary()
sys.exit(0 if success else 1)

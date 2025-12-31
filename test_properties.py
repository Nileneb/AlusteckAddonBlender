"""Test Property Annotations in Operators"""
import sys
import ast

def test_property_annotations():
    """Test dass Properties mit : Annotation definiert sind"""
    
    # Lese operators.py
    with open("alusteck_builder/ui/operators.py", "r", encoding="utf-8") as f:
        source = f.read()
    
    # Parse AST
    tree = ast.parse(source)
    
    results = []
    
    # Finde Klassen
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name in ["ALUSTECK_OT_add_profile", "ALUSTECK_OT_add_connector"]:
                print(f"\n✓ Klasse gefunden: {node.name}")
                
                # Prüfe Annotations
                found_props = []
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        if isinstance(item.target, ast.Name):
                            prop_name = item.target.id
                            
                            # Prüfe ob es ein Property ist
                            if isinstance(item.value, ast.Call):
                                if isinstance(item.value.func, ast.Name):
                                    func_name = item.value.func.id
                                    if "Property" in func_name:
                                        found_props.append(prop_name)
                                        print(f"  ✓ Property mit Annotation: {prop_name}: {func_name}(...)")
                
                if node.name == "ALUSTECK_OT_add_profile":
                    expected = ["artikel_nr", "kategorie", "length"]
                else:
                    expected = ["artikel_nr", "kategorie"]
                
                missing = set(expected) - set(found_props)
                if missing:
                    print(f"  ✗ FEHLER: Fehlende Properties: {missing}")
                    results.append(False)
                else:
                    print(f"  ✓ Alle Properties vorhanden: {found_props}")
                    results.append(True)
    
    return all(results)

if __name__ == "__main__":
    print("=" * 60)
    print("TEST: Property Annotations")
    print("=" * 60)
    
    success = test_property_annotations()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALLE TESTS BESTANDEN")
        sys.exit(0)
    else:
        print("❌ TESTS FEHLGESCHLAGEN")
        sys.exit(1)

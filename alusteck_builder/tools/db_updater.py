"""
Database Updater - Integriert Scraper mit Datenbank-Export.
Lädt Demo-Daten oder live-gescrapte Daten in die Addon-Datenbank.
"""

import json
import os
from pathlib import Path


def get_database_path():
    """Findet den Pfad zur alusteck_database.json"""
    # Arbeitet relativ zum aktuellen Skript
    script_dir = Path(__file__).parent.parent  # alusteck_builder/
    db_path = script_dir / "data" / "alusteck_database.json"
    return db_path


def get_snap_rules_path():
    """Findet den Pfad zur snap_rules.json"""
    script_dir = Path(__file__).parent.parent
    rules_path = script_dir / "data" / "snap_rules.json"
    return rules_path


def update_database(use_live_scraper=False):
    """
    Aktualisiert die Addon-Datenbank.
    
    Args:
        use_live_scraper: Wenn True, nutzt Live-Web-Scraping.
                         Wenn False, generiert Demo-Daten (offline).
    """
    from scraper import AlusteckScraper
    
    print("\n" + "="*60)
    print("DATABASE UPDATER")
    print("="*60)
    
    scraper = AlusteckScraper()
    
    if use_live_scraper:
        print("\n🌐 Starte Live-Web-Scraping...")
        print("   (Benötigt Internetverbindung)")
        scraper.scrape_all()
    else:
        print("\n📋 Generiere Demo-Datenbank...")
        print("   (Offline - keine Internetverbindung nötig)")
        scraper.generate_demo_data()
    
    # Snap-Regeln generieren
    print("\n🧲 Generiere Snap-Regeln...")
    scraper.generate_snap_rules()
    
    # Speichern
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Speichere Datenbank...")
    scraper.save_database(str(db_path))
    
    # Snap-Regeln separat speichern
    snap_rules_path = get_snap_rules_path()
    with open(snap_rules_path, 'w', encoding='utf-8') as f:
        json.dump(scraper.data.get("snap_rules", {}), f, indent=2, ensure_ascii=False)
    print(f"✅ Snap-Regeln gespeichert: {snap_rules_path}")
    
    return True


def validate_database():
    """Überprüft ob Datenbank intakt ist"""
    db_path = get_database_path()
    
    if not db_path.exists():
        print(f"❌ Datenbank nicht gefunden: {db_path}")
        return False
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basis-Struktur prüfen
        required_keys = ['meta', 'kategorien', 'snap_rules']
        for key in required_keys:
            if key not in data:
                print(f"❌ Fehlender Key in Datenbank: {key}")
                return False
        
        # Kategorien-Struktur prüfen
        for size in ["20mm", "25mm", "30mm"]:
            if size not in data['kategorien']:
                print(f"❌ Fehlende Kategorie: {size}")
                return False
        
        print(f"✅ Datenbank intakt!")
        print(f"   Pfad: {db_path}")
        print(f"   Größe: {db_path.stat().st_size / 1024:.1f} KB")
        
        return True
    
    except json.JSONDecodeError:
        print(f"❌ Fehler beim Parsen von JSON: {db_path}")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def repair_database():
    """Repariert die Datenbank durch Neugeneration"""
    print("\n🔧 Repariere Datenbank...")
    return update_database(use_live_scraper=False)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "live":
        # Live scraping
        update_database(use_live_scraper=True)
    else:
        # Demo-Daten (default)
        update_database(use_live_scraper=False)
    
    # Validierung
    validate_database()

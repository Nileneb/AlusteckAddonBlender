#!/usr/bin/env python
# ============================================
# ALUSTECK WEB SCRAPER
# Fetcht alle Produktdaten von alusteck.de
# ============================================
# 
# USAGE:
#   python alusteck_scraper.py
#
# OUTPUT:
#   alusteck_database.json
#
# REQUIREMENTS:
#   pip install requests beautifulsoup4 lxml
# ============================================

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import os

# ============================================
# KONFIGURATION
# ============================================

BASE_URL = "https://www.alusteck.de"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Kategorien zum Scrapen
CATEGORIES = {
    "20mm": {
        "profile": "/aluprofile/alu-vierkantrohre/alu-vierkantrohre-20x20/",
        "verbinder": "/steckverbinder-20-x-20-mm/",
        "zubehoer": "/vierkantrohr-zubehoer-stecksystem-20x20mm/",
    },
    "25mm": {
        "profile": "/aluprofile/alu-vierkantrohre/alu-vierkantrohre-25x25/",
        "verbinder": "/25-mm-alu-stecksystem/steckverbinder-verbinder-vierkantrohre-vierkant-eckverbinder-kunststoff/",
        "zubehoer": "/vierkantrohr-zubehoer-stecksystem-25x25mm/",
    },
    "30mm": {
        "profile": "/aluprofile/alu-vierkantrohre/alu-vierkantrohre-30x30/",
        "verbinder": "/steckverbinder-30-x-30-mm/",
        "zubehoer": "/vierkantrohr-zubehoer-stecksystem-30x30mm/",
    },
}

# ============================================
# DATENSTRUKTUREN
# ============================================

@dataclass
class Schnittbild:
    """Schnittbild-Optionen für Profile"""
    typ: str              # "A", "B", "C"
    beschreibung: str     # "Gerade", "45° Gehrung", etc.
    aufpreis: float       # Zusatzkosten in EUR

@dataclass 
class Steg:
    """Steg-Konfiguration für Profile"""
    anzahl: int           # 0, 1, 2
    typ: str              # "einfach", "doppel"
    position: str         # "innenwinkel", "aussenwinkel", "gegenueber"
    hoehe_mm: float       # Steghöhe in mm

@dataclass
class Profil:
    """Aluminium-Profil Datenstruktur"""
    artikel_nr: str
    name: str
    kategorie: str        # "20mm", "25mm", "30mm"
    aussen_mm: float      # Außenmaß
    wandstaerke_mm: float # Wandstärke
    innen_mm: float       # Innenmaß (berechnet)
    steg: Optional[Steg]  # Steg-Konfiguration
    schnittbilder: List[Schnittbild]
    laengen_mm: List[int] # Verfügbare Längen
    preis_pro_meter: float
    url: str
    bild_url: str

@dataclass
class Verbinder:
    """Steckverbinder Datenstruktur"""
    artikel_nr: str
    name: str
    kategorie: str        # "20mm", "25mm", "30mm"
    typ: str              # "gerade", "winkel", "t-stueck", "kreuz", "wuerfel"
    anzahl_wege: int      # 2, 3, 4, 5, 6
    winkel_grad: List[int]  # [180] für gerade, [90, 90, 90] für 3-Wege-Ecke
    zapfen_laenge_mm: float
    zapfen_toleranz_mm: float  # Für Passgenauigkeit
    material: str         # "PA6", "PA6-GF30", etc.
    farbe: str
    preis: float
    url: str
    bild_url: str
    # Geometrie für Snap-System
    anschluss_punkte: List[Dict]  # [{richtung: [1,0,0], position: [0.025,0,0]}]

@dataclass
class Zubehoer:
    """Zubehör Datenstruktur"""
    artikel_nr: str
    name: str
    kategorie: str
    typ: str              # "endkappe", "fuss", "scharnier", "rolle"
    preis: float
    url: str
    bild_url: str

# ============================================
# SCRAPER FUNKTIONEN
# ============================================

class AlusteckScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.data = {
            "meta": {
                "version": "1.0",
                "source": "alusteck.de",
                "scraped_at": None,
            },
            "kategorien": {
                "20mm": {"profile": [], "verbinder": [], "zubehoer": []},
                "25mm": {"profile": [], "verbinder": [], "zubehoer": []},
                "30mm": {"profile": [], "verbinder": [], "zubehoer": []},
            },
            "snap_rules": {},
        }
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Holt eine Seite und parst sie"""
        try:
            full_url = urljoin(BASE_URL, url)
            print(f"  Fetching: {full_url}")
            response = self.session.get(full_url, timeout=10)
            response.raise_for_status()
            time.sleep(0.5)  # Rate limiting
            return BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            print(f"  ERROR: {e}")
            return None
    
    def extract_price(self, text: str) -> float:
        """Extrahiert Preis aus Text"""
        match = re.search(r'(\d+[.,]\d+)\s*€', text.replace(',', '.'))
        if match:
            return float(match.group(1).replace(',', '.'))
        return 0.0
    
    def extract_dimensions(self, name: str) -> Dict:
        """Extrahiert Maße aus Produktname"""
        dims = {"aussen": 0, "wand": 0, "steg": None}
        
        # Pattern: 25 x 25 x 1,5 mm
        match = re.search(r'(\d+)\s*x\s*(\d+)\s*x\s*(\d+[.,]?\d*)\s*mm', name)
        if match:
            dims["aussen"] = float(match.group(1))
            dims["wand"] = float(match.group(3).replace(',', '.'))
        
        # Steg erkennen
        if "2 Stege" in name or "2 Doppelstege" in name:
            dims["steg"] = {"anzahl": 2, "typ": "doppel" if "Doppel" in name else "einfach"}
        elif "1 Steg" in name:
            dims["steg"] = {"anzahl": 1, "typ": "einfach"}
        
        # Position erkennen
        if "Innenwinkel" in name:
            if dims["steg"]:
                dims["steg"]["position"] = "innenwinkel"
        elif "Außenwinkel" in name:
            if dims["steg"]:
                dims["steg"]["position"] = "aussenwinkel"
        elif "gegenüber" in name:
            if dims["steg"]:
                dims["steg"]["position"] = "gegenueber"
        
        return dims
    
    def extract_verbinder_type(self, name: str) -> Dict:
        """Extrahiert Verbinder-Typ aus Name"""
        info = {"typ": "unbekannt", "wege": 0, "winkel": []}
        
        # Anzahl Wege
        wege_match = re.search(r'(\d)\s*-?\s*Wege', name, re.IGNORECASE)
        if wege_match:
            info["wege"] = int(wege_match.group(1))
        
        # Abgänge zählen
        abgang_match = re.search(r'(\d)\s*Abg', name)
        if abgang_match:
            info["wege"] = int(abgang_match.group(1)) + 1  # +1 für Hauptrichtung
        
        # Typ erkennen
        name_lower = name.lower()
        if "gerade" in name_lower or "verbinder gerade" in name_lower:
            info["typ"] = "gerade"
            info["wege"] = 2
            info["winkel"] = [180]
        elif "winkel" in name_lower or "rechter winkel" in name_lower:
            info["typ"] = "winkel"
            info["wege"] = max(info["wege"], 2)
            info["winkel"] = [90] * (info["wege"] - 1)
        elif "würfel" in name_lower or "wuerfel" in name_lower or "eckverbinder" in name_lower:
            info["typ"] = "wuerfel"
            info["wege"] = max(info["wege"], 3)
        elif "t-stück" in name_lower or "t-verbinder" in name_lower:
            info["typ"] = "t-stueck"
            info["wege"] = 3
            info["winkel"] = [90, 90]
        elif "kreuz" in name_lower:
            info["typ"] = "kreuz"
            info["wege"] = 4
            info["winkel"] = [90, 90, 90, 90]
        
        return info
    
    def parse_product_listing(self, soup: BeautifulSoup, kategorie: str, typ: str) -> List[Dict]:
        """Parst eine Produktlisting-Seite"""
        products = []
        
        # Produktkarten finden (verschiedene mögliche Selektoren)
        cards = soup.select('.product-box, .product-item, .cms-listing-col')
        
        for card in cards:
            try:
                # Name
                name_elem = card.select_one('.product-name, .product-title, a[title]')
                name = name_elem.get_text(strip=True) if name_elem else ""
                
                # URL
                link = card.select_one('a[href*="/"]')
                url = link.get('href', '') if link else ""
                
                # Preis
                price_elem = card.select_one('.product-price, .price')
                price_text = price_elem.get_text() if price_elem else "0"
                price = self.extract_price(price_text)
                
                # Bild
                img = card.select_one('img[src]')
                img_url = img.get('src', '') if img else ""
                
                # Artikel-Nr aus URL extrahieren
                artikel_nr = url.split('/')[-1] if url else ""
                
                if name and url:
                    product = {
                        "artikel_nr": artikel_nr,
                        "name": name,
                        "kategorie": kategorie,
                        "preis": price,
                        "url": url,
                        "bild_url": img_url,
                    }
                    
                    if typ == "profile":
                        dims = self.extract_dimensions(name)
                        product.update({
                            "aussen_mm": dims["aussen"],
                            "wandstaerke_mm": dims["wand"],
                            "innen_mm": dims["aussen"] - 2 * dims["wand"] if dims["wand"] else 0,
                            "steg": dims["steg"],
                            "schnittbilder": ["A", "B", "C"],  # Standard
                        })
                    elif typ == "verbinder":
                        vinfo = self.extract_verbinder_type(name)
                        product.update({
                            "typ": vinfo["typ"],
                            "anzahl_wege": vinfo["wege"],
                            "winkel_grad": vinfo["winkel"],
                            "zapfen_laenge_mm": float(kategorie.replace("mm", "")),  # Schätzung
                        })
                    
                    products.append(product)
                    
            except Exception as e:
                print(f"    Error parsing card: {e}")
                continue
        
        return products
    
    def scrape_all(self):
        """Scrapt alle Kategorien"""
        from datetime import datetime
        self.data["meta"]["scraped_at"] = datetime.now().isoformat()
        
        for kat_name, kat_urls in CATEGORIES.items():
            print(f"\n{'='*50}")
            print(f"KATEGORIE: {kat_name}")
            print('='*50)
            
            for typ, url in kat_urls.items():
                print(f"\n  Typ: {typ}")
                soup = self.fetch_page(url)
                
                if soup:
                    products = self.parse_product_listing(soup, kat_name, typ)
                    self.data["kategorien"][kat_name][typ] = products
                    print(f"    Gefunden: {len(products)} Produkte")
    
    def generate_snap_rules(self):
        """Generiert Snap-Regeln basierend auf den Verbindern"""
        print("\n" + "="*50)
        print("GENERIERE SNAP-REGELN")
        print("="*50)
        
        for kat_name in ["20mm", "25mm", "30mm"]:
            size = float(kat_name.replace("mm", ""))
            zapfen = size  # Zapfenlänge = Profilgröße
            
            self.data["snap_rules"][kat_name] = {
                "profil_aussen_mm": size,
                "profil_innen_mm": size - 3,  # Ca. 1.5mm Wandstärke
                "zapfen_laenge_mm": zapfen,
                "zapfen_toleranz_mm": 0.5,
                "snap_distanz_mm": zapfen,  # Einstecktiefe
                "verbinder_typen": {
                    "gerade": {
                        "max_anschluesse": 2,
                        "richtungen": [[1,0,0], [-1,0,0]],
                        "kollisions_check": False,
                    },
                    "winkel": {
                        "max_anschluesse": 2,
                        "richtungen": [[1,0,0], [0,1,0]],
                        "winkel": 90,
                        "kollisions_check": True,
                    },
                    "t-stueck": {
                        "max_anschluesse": 3,
                        "richtungen": [[1,0,0], [-1,0,0], [0,1,0]],
                        "kollisions_check": True,
                    },
                    "wuerfel_3": {
                        "max_anschluesse": 3,
                        "richtungen": [[1,0,0], [0,1,0], [0,0,1]],
                        "kollisions_check": True,
                    },
                    "kreuz": {
                        "max_anschluesse": 4,
                        "richtungen": [[1,0,0], [-1,0,0], [0,1,0], [0,-1,0]],
                        "kollisions_check": True,
                    },
                    "wuerfel_4": {
                        "max_anschluesse": 4,
                        "richtungen": [[1,0,0], [0,1,0], [0,0,1], [-1,0,0]],
                        "kollisions_check": True,
                    },
                    "wuerfel_5": {
                        "max_anschluesse": 5,
                        "richtungen": [[1,0,0], [-1,0,0], [0,1,0], [0,-1,0], [0,0,1]],
                        "kollisions_check": True,
                    },
                    "wuerfel_6": {
                        "max_anschluesse": 6,
                        "richtungen": [[1,0,0], [-1,0,0], [0,1,0], [0,-1,0], [0,0,1], [0,0,-1]],
                        "kollisions_check": True,
                    },
                },
                "steg_regeln": {
                    "innenwinkel": {
                        "blockierte_richtungen": [[1,0,0], [0,1,0]],  # Innenecke blockiert
                        "erlaubte_verbinder": ["winkel", "t-stueck"],
                    },
                    "aussenwinkel": {
                        "blockierte_richtungen": [[-1,0,0], [0,-1,0]],
                        "erlaubte_verbinder": ["winkel", "t-stueck"],
                    },
                    "gegenueber": {
                        "blockierte_richtungen": [[1,0,0], [-1,0,0]],
                        "erlaubte_verbinder": ["gerade", "kreuz"],
                    },
                },
            }
        
        print("  Snap-Regeln generiert für: 20mm, 25mm, 30mm")
    
    def save_database(self, filename: str = "alusteck_database.json"):
        """Speichert die Datenbank als JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Datenbank gespeichert: {filename}")
        print(f"   Größe: {os.path.getsize(filename) / 1024:.1f} KB")


# ============================================
# HAUPTPROGRAMM
# ============================================

def main():
    print("="*60)
    print("ALUSTECK WEB SCRAPER")
    print("="*60)
    print("\nDieser Scraper sammelt alle Produktdaten von alusteck.de")
    print("und erstellt eine strukturierte JSON-Datenbank.\n")
    
    scraper = AlusteckScraper()
    
    # Option 1: Live scrapen (benötigt Internetverbindung)
    # scraper.scrape_all()
    
    # Option 2: Demo-Daten generieren (offline)
    print("Generiere Demo-Datenbank...")
    scraper.generate_demo_data()
    
    # Snap-Regeln generieren
    scraper.generate_snap_rules()
    
    # Speichern
    scraper.save_database()
    
    # Statistik
    print("\n" + "="*60)
    print("STATISTIK")
    print("="*60)
    for kat in ["20mm", "25mm", "30mm"]:
        p = len(scraper.data["kategorien"][kat]["profile"])
        v = len(scraper.data["kategorien"][kat]["verbinder"])
        z = len(scraper.data["kategorien"][kat]["zubehoer"])
        print(f"  {kat}: {p} Profile, {v} Verbinder, {z} Zubehör")


# ============================================
# DEMO-DATEN (für Offline-Test)
# ============================================

def generate_demo_data(self):
    """Generiert Demo-Daten basierend auf bekannten Produkten"""
    
    # 25mm Profile
    profile_25 = [
        {
            "artikel_nr": "VK25-STD",
            "name": "Aluprofil 25 x 25 x 1,5 mm Vierkantrohr",
            "kategorie": "25mm",
            "aussen_mm": 25.0,
            "wandstaerke_mm": 1.5,
            "innen_mm": 22.0,
            "steg": None,
            "schnittbilder": ["A", "B", "C"],
            "preis_pro_meter": 5.90,
            "url": "/aluprofil-25-x-25-x-1-5-mm-alu-vierkantrohr-quadratrohr",
            "bild_url": "",
        },
        {
            "artikel_nr": "VK25-2SI",
            "name": "Aluprofil 2 Stege 15 mm Innenwinkel 25 x 25 mm",
            "kategorie": "25mm",
            "aussen_mm": 25.0,
            "wandstaerke_mm": 1.5,
            "innen_mm": 22.0,
            "steg": {"anzahl": 2, "typ": "einfach", "position": "innenwinkel", "hoehe_mm": 15.0},
            "schnittbilder": ["A", "B", "C"],
            "preis_pro_meter": 13.77,
            "url": "/aluprofil-2-stege-15-mm-innenwinkel-25-x-25-mm",
            "bild_url": "",
        },
        {
            "artikel_nr": "VK25-2SA",
            "name": "Aluprofil 2 Stege 15 mm Außenwinkel 25 x 25 mm",
            "kategorie": "25mm",
            "aussen_mm": 25.0,
            "wandstaerke_mm": 1.5,
            "innen_mm": 22.0,
            "steg": {"anzahl": 2, "typ": "einfach", "position": "aussenwinkel", "hoehe_mm": 15.0},
            "schnittbilder": ["A", "B", "C"],
            "preis_pro_meter": 13.77,
            "url": "/aluprofil-2-stege-15-mm-aussenwinkel-25-x-25-mm",
            "bild_url": "",
        },
        {
            "artikel_nr": "VK25-2SG",
            "name": "Aluprofil 2 Stege 15 mm gegenüber 25 x 25 mm",
            "kategorie": "25mm",
            "aussen_mm": 25.0,
            "wandstaerke_mm": 1.5,
            "innen_mm": 22.0,
            "steg": {"anzahl": 2, "typ": "einfach", "position": "gegenueber", "hoehe_mm": 15.0},
            "schnittbilder": ["A", "B", "C"],
            "preis_pro_meter": 13.77,
            "url": "/aluprofil-2-stege-15-mm-gegenueber-25-x-25-mm",
            "bild_url": "",
        },
        {
            "artikel_nr": "VK25-2DSI",
            "name": "Aluprofil 2 Doppelstege 15 mm Innenwinkel 25 x 25 mm",
            "kategorie": "25mm",
            "aussen_mm": 25.0,
            "wandstaerke_mm": 1.5,
            "innen_mm": 22.0,
            "steg": {"anzahl": 2, "typ": "doppel", "position": "innenwinkel", "hoehe_mm": 15.0},
            "schnittbilder": ["A", "B", "C"],
            "preis_pro_meter": 13.35,
            "url": "/aluprofil-2-doppelstege-15-mm-innenwinkel-25-x-25-mm",
            "bild_url": "",
        },
    ]
    
    # 25mm Verbinder
    verbinder_25 = [
        {
            "artikel_nr": "2D25K",
            "name": "Verbinder gerade 2-Wege 25x25mm",
            "kategorie": "25mm",
            "typ": "gerade",
            "anzahl_wege": 2,
            "winkel_grad": [180],
            "zapfen_laenge_mm": 25.0,
            "zapfen_toleranz_mm": 0.5,
            "material": "PA6",
            "farbe": "schwarz",
            "preis": 1.50,
            "url": "/verbinder-gerade-2-wege-25x25mm",
            "bild_url": "",
            "anschluss_punkte": [
                {"richtung": [0, 0, 1], "position": [0, 0, 0.0125]},
                {"richtung": [0, 0, -1], "position": [0, 0, -0.0125]},
            ],
        },
        {
            "artikel_nr": "2W25K",
            "name": "Winkelverbinder 90° 2-Wege 25x25mm",
            "kategorie": "25mm",
            "typ": "winkel",
            "anzahl_wege": 2,
            "winkel_grad": [90],
            "zapfen_laenge_mm": 25.0,
            "zapfen_toleranz_mm": 0.5,
            "material": "PA6",
            "farbe": "schwarz",
            "preis": 1.80,
            "url": "/rechter-winkel-25-x-25-mm-steckverbinder-vierkantrohr",
            "bild_url": "",
            "anschluss_punkte": [
                {"richtung": [1, 0, 0], "position": [0.0125, 0, 0]},
                {"richtung": [0, 1, 0], "position": [0, 0.0125, 0]},
            ],
        },
        {
            "artikel_nr": "3E25K",
            "name": "Eckverbinder 3-Wege Würfel 25x25mm",
            "kategorie": "25mm",
            "typ": "wuerfel_3",
            "anzahl_wege": 3,
            "winkel_grad": [90, 90, 90],
            "zapfen_laenge_mm": 25.0,
            "zapfen_toleranz_mm": 0.5,
            "material": "PA6",
            "farbe": "schwarz",
            "preis": 2.50,
            "url": "/eckverbinder-wuerfel-25-x-25-mm-steckverbinder-vierkantrohr",
            "bild_url": "",
            "anschluss_punkte": [
                {"richtung": [1, 0, 0], "position": [0.0125, 0, 0]},
                {"richtung": [0, 1, 0], "position": [0, 0.0125, 0]},
                {"richtung": [0, 0, 1], "position": [0, 0, 0.0125]},
            ],
        },
        {
            "artikel_nr": "3T25K",
            "name": "T-Verbinder 3-Wege 25x25mm",
            "kategorie": "25mm",
            "typ": "t-stueck",
            "anzahl_wege": 3,
            "winkel_grad": [90, 90],
            "zapfen_laenge_mm": 25.0,
            "zapfen_toleranz_mm": 0.5,
            "material": "PA6",
            "farbe": "schwarz",
            "preis": 2.20,
            "url": "/t-verbinder-3-wege-25x25mm",
            "bild_url": "",
            "anschluss_punkte": [
                {"richtung": [1, 0, 0], "position": [0.0125, 0, 0]},
                {"richtung": [-1, 0, 0], "position": [-0.0125, 0, 0]},
                {"richtung": [0, 1, 0], "position": [0, 0.0125, 0]},
            ],
        },
        {
            "artikel_nr": "4K25K",
            "name": "Kreuzverbinder 4-Wege 25x25mm",
            "kategorie": "25mm",
            "typ": "kreuz",
            "anzahl_wege": 4,
            "winkel_grad": [90, 90, 90, 90],
            "zapfen_laenge_mm": 25.0,
            "zapfen_toleranz_mm": 0.5,
            "material": "PA6",
            "farbe": "schwarz",
            "preis": 2.80,
            "url": "/kreuzverbinder-4-wege-25x25mm",
            "bild_url": "",
            "anschluss_punkte": [
                {"richtung": [1, 0, 0], "position": [0.0125, 0, 0]},
                {"richtung": [-1, 0, 0], "position": [-0.0125, 0, 0]},
                {"richtung": [0, 1, 0], "position": [0, 0.0125, 0]},
                {"richtung": [0, -1, 0], "position": [0, -0.0125, 0]},
            ],
        },
        {
            "artikel_nr": "6W25K",
            "name": "Würfelverbinder 6-Wege 25x25mm",
            "kategorie": "25mm",
            "typ": "wuerfel_6",
            "anzahl_wege": 6,
            "winkel_grad": [90, 90, 90, 90, 90, 90],
            "zapfen_laenge_mm": 25.0,
            "zapfen_toleranz_mm": 0.5,
            "material": "PA6",
            "farbe": "schwarz",
            "preis": 4.50,
            "url": "/wuerfelverbinder-6-wege-25x25mm",
            "bild_url": "",
            "anschluss_punkte": [
                {"richtung": [1, 0, 0], "position": [0.0125, 0, 0]},
                {"richtung": [-1, 0, 0], "position": [-0.0125, 0, 0]},
                {"richtung": [0, 1, 0], "position": [0, 0.0125, 0]},
                {"richtung": [0, -1, 0], "position": [0, -0.0125, 0]},
                {"richtung": [0, 0, 1], "position": [0, 0, 0.0125]},
                {"richtung": [0, 0, -1], "position": [0, 0, -0.0125]},
            ],
        },
    ]
    
    # 25mm Zubehör
    zubehoer_25 = [
        {
            "artikel_nr": "EK25K",
            "name": "Endkappe 25x25mm schwarz",
            "kategorie": "25mm",
            "typ": "endkappe",
            "preis": 0.40,
            "url": "/endkappe-25x25mm",
            "bild_url": "",
        },
        {
            "artikel_nr": "SF25",
            "name": "Stellfuß verstellbar 25mm",
            "kategorie": "25mm",
            "typ": "stellfuss",
            "preis": 2.90,
            "url": "/stellfuss-25mm",
            "bild_url": "",
        },
    ]
    
    # Daten zuweisen
    self.data["kategorien"]["25mm"]["profile"] = profile_25
    self.data["kategorien"]["25mm"]["verbinder"] = verbinder_25
    self.data["kategorien"]["25mm"]["zubehoer"] = zubehoer_25
    
    # 20mm und 30mm analog (skaliert)
    for size in ["20mm", "30mm"]:
        scale = float(size.replace("mm", "")) / 25.0
        
        # Profile skalieren
        self.data["kategorien"][size]["profile"] = [
            {**p, 
             "kategorie": size,
             "aussen_mm": p["aussen_mm"] * scale,
             "innen_mm": p["innen_mm"] * scale,
             "artikel_nr": p["artikel_nr"].replace("25", size.replace("mm", "")),
            } for p in profile_25[:2]  # Nur Basis-Profile
        ]
        
        # Verbinder skalieren
        self.data["kategorien"][size]["verbinder"] = [
            {**v,
             "kategorie": size,
             "zapfen_laenge_mm": v["zapfen_laenge_mm"] * scale,
             "artikel_nr": v["artikel_nr"].replace("25", size.replace("mm", "")),
            } for v in verbinder_25
        ]
    
    print("  Demo-Daten generiert!")

# Methode zur Klasse hinzufügen
AlusteckScraper.generate_demo_data = generate_demo_data


if __name__ == "__main__":
    main()

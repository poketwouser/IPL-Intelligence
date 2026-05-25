"""
Player Image Pipeline — Automated player photo management.
Downloads, caches, and serves player images for the IPL Intelligence Platform.
Uses ESPNcricinfo player photo URLs as primary source.
"""

import os
import hashlib
import json
import logging
import re
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "assets" / "images" / "players"
CACHE_FILE = IMAGES_DIR / "_cache.json"

# Ensure directory exists
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


# ── ESPNcricinfo Player ID Mapping ────────────────────────────────────────────
# Maps player names (as they appear in Cricsheet data) to ESPNcricinfo player IDs
# This enables reliable image URLs: https://p.imgci.com/db/PICTURES/CMS/{id}.jpg

PLAYER_ID_MAP = {
    # Top All-Time Batters
    "V Kohli":          "253802",
    "S Dhawan":         "28235",
    "RG Sharma":        "34102",
    "DA Warner":        "219889",
    "SK Raina":         "33141",
    "AB de Villiers":   "44936",
    "CH Gayle":         "51880",
    "MS Dhoni":         "28081",
    "KL Rahul":         "422108",
    "RV Uthappa":       "35582",
    "G Gambhir":        "28794",
    "AT Rayudu":        "33141",
    "SA Yadav":         "446507",
    "SV Samson":        "425943",
    "F du Plessis":     "44828",
    "S Watson":         "8180",
    "JC Buttler":       "308967",
    "HH Pandya":        "625371",
    "KD Karthik":       "30045",
    "M Vijay":          "237095",
    "AJ Finch":         "5334",
    "R Pant":           "931581",
    "PP Shaw":          "1070168",
    "YK Pathan":        "32498",
    "Shubman Gill":     "1119026",
    "RR Pant":          "931581",
    "RD Gaikwad":       "1060377",
    "D Padikkal":       "1119022",

    # Top All-Time Bowlers
    "YS Chahal":        "430246",
    "DJ Bravo":         "51439",
    "SL Malinga":       "49758",
    "A Mishra":         "31107",
    "SP Narine":        "230559",
    "PP Chawla":        "32966",
    "B Kumar":          "326016",
    "R Ashwin":         "26421",
    "Harbhajan Singh":  "29264",
    "JJ Bumrah":        "625383",
    "RA Jadeja":        "234675",
    "Rashid Khan":      "793463",
    "Harshal Patel":    "390484",
    "AR Patel":         "554691",
    "T Natarajan":      "802498",
    "Mohammed Shami":   "481896",
    "K Rabada":         "550215",
    "TA Boult":         "277912",
    "DL Chahar":        "447261",
    "Mohammed Siraj":   "940973",
    "Arshdeep Singh":   "1078233",
    "M Pathirana":      "1283987",
    "Kuldeep Yadav":    "559235",
    "T Shamsi":         "455498",

    # Other Notable Players
    "KS Williamson":    "277906",
    "BA Stokes":        "311158",
    "JE Root":          "303669",
    "SPD Smith":        "267192",
    "PD Salt":          "601618",
    "DP Conway":        "539475",
    "Q de Kock":        "379143",
    "N Pooran":         "733735",
    "M Jansen":         "925883",
    "PJ Cummins":       "489889",
    "MA Starc":         "311592",
    "TG Southee":       "232364",
    "JR Hazlewood":     "298694",
    "Washington Sundar": "719715",
    "Ishan Kishan":     "720471",
    "Tilak Varma":      "1228458",
    "YBK Jaiswal":      "1151288",
    "T Head":           "530592",
    "GJ Maxwell":       "325026",
    "M Labuschagne":    "438710",
    "MK Pandey":        "290630",
    "Manish Pandey":    "290630",
    "SN Thakur":        "481375",
    "Shardul Thakur":   "481375",
    "Avesh Khan":       "778979",
    "Umran Malik":      "1259873",
    "JM Sharma":        "1259873",
    "N Rana":           "604302",
    "Nitish Rana":      "604302",
    "V Iyer":           "1079562",
    "Venkatesh Iyer":   "1079562",
    "R Parag":          "1175441",
    "Riyan Parag":      "1175441",
    "Abhishek Sharma":  "1175435",
    "T Stubbs":         "940953",
}


def _normalize_name(name: str) -> str:
    """Normalize player name for matching."""
    if not isinstance(name, str):
        return ""
    return re.sub(r'\s+', ' ', name.strip())


def _get_image_filename(player_name: str) -> str:
    """Generate consistent filename from player name."""
    safe = re.sub(r'[^a-zA-Z0-9]', '_', player_name.lower()).strip('_')
    return f"{safe}.jpg"


def _load_cache() -> dict:
    """Load image cache from disk."""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}


def _save_cache(cache: dict):
    """Save image cache to disk."""
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding='utf-8')
    except Exception as e:
        logger.warning(f"Failed to save image cache: {e}")


def get_wikimedia_image(player_name: str) -> bytes | None:
    """Primary Source: Wikimedia API (Highly reliable, no bot blocks)"""
    import urllib.parse
    import requests
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    
    # 1. Search for Wikipedia page
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(player_name + ' cricketer')}&utf8=&format=json"
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        data = resp.json()
        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            return None
            
        title = search_results[0]["title"]
        
        # 2. Get original image for that page
        img_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={urllib.parse.quote(title)}"
        resp2 = requests.get(img_url, headers=headers, timeout=10)
        data2 = resp2.json()
        
        pages = data2.get("query", {}).get("pages", {})
        for page_id, page_info in pages.items():
            if "original" in page_info:
                img_src = page_info["original"]["source"]
                img_resp = requests.get(img_src, headers=headers, timeout=10)
                if img_resp.status_code == 200:
                    return img_resp.content
    except Exception as e:
        logger.debug(f"Wikimedia source failed for {player_name}: {e}")
    return None

def get_bing_fallback_image(player_name: str) -> bytes | None:
    """Secondary Source: Bing Images HTML extraction"""
    import urllib.parse
    import requests
    from bs4 import BeautifulSoup
    import json
    
    query = urllib.parse.quote(player_name + " cricketer headshot profile")
    url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for a in soup.find_all('a', class_='iusc'):
            m = a.get('m')
            if m:
                m_data = json.loads(m)
                img_url = m_data.get('murl')
                if img_url and img_url.startswith('http'):
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200:
                        return img_resp.content
    except Exception as e:
        logger.debug(f"Bing source failed for {player_name}: {e}")
    return None

def download_player_image(player_name: str, force: bool = False) -> str | None:
    """
    Robust Multi-Source Image Acquisition Pipeline.
    1. Wikimedia API
    2. Bing Images Fallback
    """
    name = _normalize_name(player_name)
    if not name:
        return None

    filename = _get_image_filename(name)
    filepath = IMAGES_DIR / filename

    # Check cache
    if filepath.exists() and not force:
        return f"/assets/images/players/{filename}"

    # Source 1: Wikimedia
    logger.info(f"Attempting Wikimedia source for {name}...")
    img_bytes = get_wikimedia_image(name)
    
    # Source 2: Bing Images (Fallback)
    if not img_bytes:
        logger.info(f"Wikimedia failed. Attempting Bing fallback for {name}...")
        img_bytes = get_bing_fallback_image(name)
        
    if img_bytes and len(img_bytes) > 1000:
        try:
            filepath.write_bytes(img_bytes)
            logger.info(f"Successfully saved image for {name}")
            return f"/assets/images/players/{filename}"
        except Exception as e:
            logger.error(f"Failed to write image for {name}: {e}")
            
    logger.warning(f"All sources failed for {name}. Falling back to UI Avatar.")
    return None


def get_player_image_url(player_name: str) -> str | None:
    """
    Get the player image URL (local path for Dash).
    Returns cached path if available, attempts download otherwise.
    Falls back to None (caller should show initials).
    """
    name = _normalize_name(player_name)
    if not name:
        return None

    filename = _get_image_filename(name)
    filepath = IMAGES_DIR / filename

    # Already downloaded
    if filepath.exists():
        return f"/assets/images/players/{filename}"

    # Try download
    return download_player_image(name)


@lru_cache(maxsize=1)
def bulk_download_top_players(limit: int = 50) -> dict:
    """
    Download images for all mapped players.
    Returns dict of {player_name: image_url_or_none}.
    Called once at startup for top players.
    """
    results = {}
    for name in list(PLAYER_ID_MAP.keys())[:limit]:
        url = get_player_image_url(name)
        results[name] = url
    return results


def get_team_logo_url(team_name: str) -> str | None:
    """Get team logo URL. Returns None if not available."""
    # Team logos are embedded via CSS gradients and abbreviations
    # No external images needed for the current design
    return None


# ── Pre-built avatar gradient for fallback ─────────────────────────────────────

def get_avatar_gradient(team_color: str) -> str:
    """Generate CSS gradient for avatar fallback."""
    return f"radial-gradient(circle at 30% 30%, {team_color}44, {team_color}11)"

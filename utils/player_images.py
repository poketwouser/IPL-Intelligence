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
    """Normalize player name for cache key and filename generation."""
    if not isinstance(name, str):
        return ""
    return re.sub(r'\s+', ' ', name.strip())

def _expand_name(name: str) -> str:
    """Expand abbreviated player name to full name for accurate web search."""
    if not isinstance(name, str):
        return ""
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Abbreviation mapping for major players
    full_name_map = {
        "YS Chahal": "Yuzvendra Chahal",
        "AD Russell": "Andre Russell",
        "DA Warner": "David Warner",
        "MS Dhoni": "MS Dhoni",
        "RG Sharma": "Rohit Sharma",
        "SK Raina": "Suresh Raina",
        "AB de Villiers": "AB de Villiers",
        "CH Gayle": "Chris Gayle",
        "KL Rahul": "KL Rahul",
        "RV Uthappa": "Robin Uthappa",
        "G Gambhir": "Gautam Gambhir",
        "AT Rayudu": "Ambati Rayudu",
        "SA Yadav": "Suryakumar Yadav",
        "SV Samson": "Sanju Samson",
        "F du Plessis": "Faf du Plessis",
        "S Watson": "Shane Watson",
        "JC Buttler": "Jos Buttler",
        "HH Pandya": "Hardik Pandya",
        "KD Karthik": "Dinesh Karthik",
        "M Vijay": "Murali Vijay",
        "AJ Finch": "Aaron Finch",
        "R Pant": "Rishabh Pant",
        "PP Shaw": "Prithvi Shaw",
        "YK Pathan": "Yusuf Pathan",
        "RR Pant": "Rishabh Pant",
        "RD Gaikwad": "Ruturaj Gaikwad",
        "D Padikkal": "Devdutt Padikkal",
        "DJ Bravo": "Dwayne Bravo",
        "SL Malinga": "Lasith Malinga",
        "A Mishra": "Amit Mishra",
        "SP Narine": "Sunil Narine",
        "PP Chawla": "Piyush Chawla",
        "B Kumar": "Bhuvneshwar Kumar",
        "R Ashwin": "Ravichandran Ashwin",
        "JJ Bumrah": "Jasprit Bumrah",
        "RA Jadeja": "Ravindra Jadeja",
        "AR Patel": "Axar Patel",
        "T Natarajan": "T Natarajan",
        "K Rabada": "Kagiso Rabada",
        "TA Boult": "Trent Boult",
        "DL Chahar": "Deepak Chahar",
        "M Pathirana": "Matheesha Pathirana",
        "T Shamsi": "Tabraiz Shamsi",
        "KS Williamson": "Kane Williamson",
        "BA Stokes": "Ben Stokes",
        "JE Root": "Joe Root",
        "SPD Smith": "Steve Smith",
        "PD Salt": "Phil Salt",
        "DP Conway": "Devon Conway",
        "Q de Kock": "Quinton de Kock",
        "N Pooran": "Nicholas Pooran",
        "M Jansen": "Marco Jansen",
        "PJ Cummins": "Pat Cummins",
        "MA Starc": "Mitchell Starc",
        "TG Southee": "Tim Southee",
        "JR Hazlewood": "Josh Hazlewood",
        "T Head": "Travis Head",
        "GJ Maxwell": "Glenn Maxwell",
        "M Labuschagne": "Marnus Labuschagne",
        "MK Pandey": "Manish Pandey",
        "SN Thakur": "Shardul Thakur",
        "JM Sharma": "Jitesh Sharma",
        "N Rana": "Nitish Rana",
        "V Iyer": "Venkatesh Iyer",
        "R Parag": "Riyan Parag",
        "T Stubbs": "Tristan Stubbs",
    }
    return full_name_map.get(name, name)


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
    # Use a highly descriptive User-Agent to prevent 429 Too Many Requests from Wikimedia API
    api_headers = {"User-Agent": "IPLAnalyticsPlatform/1.0 (contact@example.com)"}
    # Use standard browser User-Agent for the actual CDN image download to prevent 403
    img_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 1. Search for Wikipedia page
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(player_name + ' cricketer')}&utf8=&format=json"
    try:
        resp = requests.get(search_url, headers=api_headers, timeout=10)
        data = resp.json()
        search_results = data.get("query", {}).get("search", [])
        if not search_results:
            return None
            
        title = search_results[0]["title"]
        
        # 2. Get original image for that page
        img_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={urllib.parse.quote(title)}"
        resp2 = requests.get(img_url, headers=api_headers, timeout=10)
        data2 = resp2.json()
        
        pages = data2.get("query", {}).get("pages", {})
        for page_id, page_info in pages.items():
            if "original" in page_info:
                img_src = page_info["original"]["source"]
                img_resp = requests.get(img_src, headers=img_headers, timeout=10)
                if img_resp.status_code == 200:
                    return img_resp.content
    except Exception as e:
        logger.debug(f"Wikimedia source failed for {player_name}: {e}")
    return None

def _validate_image_face(img_bytes: bytes) -> bool:
    """Validate that the image contains a prominent face."""
    try:
        import cv2
        import numpy as np
        
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            return False
            
        max_face_area = 0
        img_area = img.shape[0] * img.shape[1]
        for (x, y, w, h) in faces:
            area = w * h
            if area > max_face_area:
                max_face_area = area
                
        # Face must be at least 1.5% of the image area
        ratio = max_face_area / img_area
        if ratio < 0.015:
            return False
            
        # Reject images with too many people (e.g. team photos)
        if len(faces) > 3:
            return False
            
        return True
    except Exception as e:
        logger.warning(f"Face validation failed to execute: {e}")
        # If opencv fails for some reason, don't block the pipeline entirely
        return True


def get_bing_fallback_image(player_name: str) -> bytes | None:
    """Secondary Source: Bing Images HTML extraction with intelligent scoring."""
    import urllib.parse
    import requests
    from bs4 import BeautifulSoup
    import json
    
    query = urllib.parse.quote(
        f'"{player_name}" cricket IPL player portrait '
        '-actor -movie -film -hollywood '
        '-food -recipe -baby -shopping -wallpaper -celebrity'
    )
    url = f"https://www.bing.com/images/search?q={query}&form=HDRSC2"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
    
    candidates = []
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Parse all image candidates
        for a in soup.find_all('a', class_='iusc'):
            m = a.get('m')
            if m:
                m_data = json.loads(m)
                img_url = m_data.get('murl')
                page_url = m_data.get('purl', '').lower()
                title = m_data.get('t', '').lower()
                
                if not img_url or not img_url.startswith('http'):
                    continue
                    
                score = 0
                
                # 1. Domain Scoring
                preferred_domains = ['cricket', 'espn', 'cricbuzz', 'icc', 'sports', 'ipl', 'wikipedia', 'wikimedia']
                rejected_domains = ['food', 'baby', 'recipe', 'actor', 'movie', 'film', 'wallpaper', 'celebrity', 'festival', 'shopping', 'imdb', 'pinterest', 'alamy']
                
                if any(domain in page_url for domain in preferred_domains):
                    score += 50
                if any(domain in page_url for domain in rejected_domains):
                    score -= 100
                    
                # 2. Semantic Keyword Scoring
                semantic_keywords = ['cricket', 'ipl', 'batting', 'bowling', 'team', 'player', 'profile']
                if any(kw in title for kw in semantic_keywords) or any(kw in page_url for kw in semantic_keywords):
                    score += 30
                    
                # 3. Exact Name Matching
                name_parts = player_name.lower().split()
                if all(part in title for part in name_parts):
                    score += 40
                    
                # 4. Negative Keywords in title
                negative_words = ['actor', 'movie', 'film', 'hollywood', 'wallpaper', 'wife', 'girlfriend', 'family', 'food', 'recipe', 'baby']
                if any(word in title for word in negative_words):
                    score -= 100
                    
                candidates.append({
                    'url': img_url,
                    'score': score
                })
                
        # Sort candidates by score descending
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Test the top candidates
        for idx, candidate in enumerate(candidates[:10]):
            # Confidence Threshold
            if candidate['score'] < 20:
                logger.warning(f"Candidate score too low ({candidate['score']}) for {player_name}. Rejecting.")
                continue
                
            try:
                img_resp = requests.get(candidate['url'], headers=headers, timeout=8)
                if img_resp.status_code == 200:
                    img_bytes = img_resp.content
                    # Validate that it actually contains a face
                    if _validate_image_face(img_bytes):
                        logger.info(f"Selected candidate {idx+1} for {player_name} (Score: {candidate['score']})")
                        return img_bytes
            except Exception:
                continue
                
    except Exception as e:
        logger.debug(f"Bing source failed for {player_name}: {e}")
    return None

def download_player_image(player_name: str, force: bool = False) -> str | None:
    """
    Robust Multi-Source Image Acquisition Pipeline.
    1. Wikimedia API
    2. Bing Images Fallback
    """
    canonical_name = _normalize_name(player_name)
    if not canonical_name:
        return None

    filename = _get_image_filename(canonical_name)
    filepath = IMAGES_DIR / filename

    # Check cache
    if filepath.exists() and not force:
        return f"/assets/images/players/{filename}"

    search_name = _expand_name(canonical_name)

    # Source 1: Wikimedia
    logger.info(f"Attempting Wikimedia source for {search_name}...")
    img_bytes = get_wikimedia_image(search_name)
    
    # Source 2: Bing Images (Fallback)
    if not img_bytes:
        logger.info(f"Wikimedia failed. Attempting Bing fallback for {search_name}...")
        img_bytes = get_bing_fallback_image(search_name)
        
    if img_bytes and len(img_bytes) > 1000:
        try:
            filepath.write_bytes(img_bytes)
            logger.info(f"Successfully saved image for {canonical_name} as {filename}")
            return f"/assets/images/players/{filename}"
        except Exception as e:
            logger.error(f"Failed to write image for {canonical_name}: {e}")
            
    logger.warning(f"All sources failed for {canonical_name}. Falling back to UI Avatar.")
    return None


def get_player_image_url(player_name: str) -> str | None:
    """
    Get the player image URL (local path for Dash).
    Returns cached path if available, attempts download otherwise.
    Falls back to None (caller should show initials).
    """
    canonical_name = _normalize_name(player_name)
    if not canonical_name:
        return None

    filename = _get_image_filename(canonical_name)
    filepath = IMAGES_DIR / filename

    # Already downloaded
    if filepath.exists():
        return f"/assets/images/players/{filename}"

    # Try download
    return download_player_image(canonical_name)


@lru_cache(maxsize=1)
def bulk_download_top_players(limit: int = 50) -> dict:
    """
    Download images for all mapped players.
    Returns dict of {player_name: image_url_or_none}.
    Called once at startup for top players.
    """
    import time
    results = {}
    for name in list(PLAYER_ID_MAP.keys())[:limit]:
        url = get_player_image_url(name)
        results[name] = url
        time.sleep(0.5) # Prevent blasting Wikipedia/Bing APIs
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

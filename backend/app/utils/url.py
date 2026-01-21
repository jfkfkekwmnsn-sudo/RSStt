import hashlib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional, Dict, List


def normalize_url(url: str, rules: Optional[Dict] = None) -> str:
    """Normalize URL by removing tracking parameters"""
    if not url:
        return url
    
    rules = rules or {}
    
    # Parse URL
    parsed = urlparse(url)
    
    # Get query parameters
    params = parse_qs(parsed.query, keep_blank_values=True)
    
    # Parameters to remove by default
    params_to_remove = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "ref", "referer", "referrer",
        "fbclid", "gclid", "msclkid",
        "mc_cid", "mc_eid",
        "_ga", "_gl",
    }
    
    # Add custom params from rules
    if rules.get("remove_utm", True):
        params_to_remove.update({"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"})
    
    if rules.get("remove_ref", True):
        params_to_remove.update({"ref", "referer", "referrer"})
    
    custom_params = rules.get("custom_params_to_remove", [])
    params_to_remove.update(custom_params)
    
    # Filter parameters
    filtered_params = {
        k: v for k, v in params.items() 
        if k.lower() not in params_to_remove
    }
    
    # Rebuild query string
    new_query = urlencode(filtered_params, doseq=True) if filtered_params else ""
    
    # Rebuild URL
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/") if parsed.path != "/" else "/",
        parsed.params,
        new_query,
        ""  # Remove fragment
    ))
    
    return normalized


def hash_url(url: str) -> str:
    """Create hash of URL for deduplication"""
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode()).hexdigest()


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ""

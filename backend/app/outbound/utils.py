"""
Utility functions for the outbound pipeline.
"""

import hashlib
import hmac
import re
from datetime import datetime, timedelta
from typing import Optional

import pytz
from fastapi import HTTPException


# Legal suffixes to remove during company normalization
LEGAL_SUFFIXES = [
    # French
    'sarl', 'sas', 'sasl', 'sci', 'scp', 'sas', 'sarl', 'eurl', 'snc',
    # German
    'gmbh', 'ag', 'kg', 'ohg', 'gbr', 'mbh', 'gmbh & co kg',
    # Italian
    'srl', 'spa', 'sas', 'snc', 'ss', 'sas', 'srl',
    # Spanish
    'sl', 'sa', 'sau', 'sll', 'sad', 'sas', 'srl',
    # Dutch
    'bv', 'nv', 'vof', 'cv', 'maatschap', 'eenmanszaak',
    # Nordic
    'oy', 'ab', 'as', 'aps', 'kft', 'sp z oo', 'sp. z o.o.',
    # UK/Irish
    'ltd', 'limited', 'plc', 'llc', 'inc', 'corp', 'corporation',
    # Generic
    'company', 'co', 'group', 'holding', 'holdings'
]


def normalize_company(name: str) -> str:
    """
    Normalize company name by removing legal suffixes and standardizing format.
    
    Args:
        name: Raw company name
        
    Returns:
        Normalized company name (lowercase, no legal suffixes)
    """
    if not name:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()
    
    # Remove common punctuation
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    # Remove legal suffixes
    for suffix in LEGAL_SUFFIXES:
        # Match suffix at end of string (with optional punctuation)
        pattern = rf'\b{suffix}\b\s*$'
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
    
    # Clean up again after suffix removal
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def now_paris() -> datetime:
    """
    Get current datetime in Europe/Paris timezone.
    
    Returns:
        Timezone-aware datetime in Europe/Paris
    """
    paris_tz = pytz.timezone('Europe/Paris')
    return datetime.now(paris_tz)


def sign_unsub(email: str, secret: str) -> str:
    """
    Generate HMAC signature for unsubscribe token.
    
    Args:
        email: Email address to sign
        secret: Secret key for signing
        
    Returns:
        Base64-encoded HMAC signature
    """
    import base64
    
    message = email.encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        message,
        hashlib.sha256
    ).digest()
    
    return base64.urlsafe_b64encode(signature).decode('utf-8')


def verify_unsub_token(email: str, token: str, secret: str) -> bool:
    """
    Verify HMAC signature for unsubscribe token.
    
    Args:
        email: Email address
        token: Token to verify
        secret: Secret key for verification
        
    Returns:
        True if token is valid, False otherwise
    """
    expected_token = sign_unsub(email, secret)
    return hmac.compare_digest(token, expected_token)


def is_cache_valid(expires_at: datetime) -> bool:
    """
    Check if cached data is still valid.
    
    Args:
        expires_at: Expiration timestamp
        
    Returns:
        True if cache is valid, False if expired
    """
    return datetime.utcnow() < expires_at


def calculate_fit_score(
    cpv_match: bool,
    value_in_sme_range: bool,
    country_focus: bool,
    recency_days: int
) -> float:
    """
    Calculate fit score for prospect based on various factors.
    
    Args:
        cpv_match: Whether CPV code matches prospect's focus
        value_in_sme_range: Whether tender value is suitable for SME
        country_focus: Whether prospect focuses on this country
        recency_days: Days since tender was published
        
    Returns:
        Fit score between 0.0 and 1.0
    """
    score = 0.0
    
    # CPV match (40% weight)
    if cpv_match:
        score += 0.4
    
    # Value in SME range (20% weight)
    if value_in_sme_range:
        score += 0.2
    
    # Country focus (20% weight)
    if country_focus:
        score += 0.2
    
    # Recency (20% weight) - more recent is better
    if recency_days <= 7:
        score += 0.2
    elif recency_days <= 30:
        score += 0.15
    elif recency_days <= 90:
        score += 0.1
    else:
        score += 0.05
    
    return min(score, 1.0)


def is_role_email(email: str) -> bool:
    """
    Check if email is a role-based email that should be avoided.
    
    Args:
        email: Email address to check
        
    Returns:
        True if it's a role email, False otherwise
    """
    if not email:
        return True
    
    email_lower = email.lower()
    
    # Common role-based email patterns
    role_patterns = [
        r'^no-reply@',
        r'^noreply@',
        r'^privacy@',
        r'^legal@',
        r'^admin@',
        r'^postmaster@',
        r'^abuse@',
        r'^security@',
        r'^billing@',
        r'^accounts@',
        r'^finance@',
        r'^hr@',
        r'^recruitment@',
        r'^jobs@',
        r'^careers@',
        r'^press@',
        r'^media@',
        r'^marketing@',
        r'^sales@',
        r'^support@',
        r'^help@',
        r'^info@',
        r'^contact@',
        r'^webmaster@',
        r'^root@',
        r'^test@',
        r'^demo@',
        r'^example@'
    ]
    
    for pattern in role_patterns:
        if re.match(pattern, email_lower):
            return True
    
    return False


def extract_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    
    Args:
        email: Email address
        
    Returns:
        Domain name or None if invalid
    """
    if not email or '@' not in email:
        return None
    
    try:
        return email.split('@')[1].lower().strip()
    except (IndexError, AttributeError):
        return None


def is_domain_blacklisted(domain: str, blacklist: list) -> bool:
    """
    Check if domain is in blacklist.
    
    Args:
        domain: Domain to check
        blacklist: List of blacklisted domains
        
    Returns:
        True if domain is blacklisted, False otherwise
    """
    if not domain or not blacklist:
        return False
    
    domain_lower = domain.lower()
    
    for blacklisted in blacklist:
        if blacklisted.lower() in domain_lower or domain_lower in blacklisted.lower():
            return True
    
    return False


def format_currency(amount: float, currency: str = "EUR") -> str:
    """
    Format currency amount for display.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if currency.upper() == "EUR":
        return f"€{amount:,.0f}"
    elif currency.upper() == "USD":
        return f"${amount:,.0f}"
    elif currency.upper() == "GBP":
        return f"£{amount:,.0f}"
    else:
        return f"{amount:,.0f} {currency}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def validate_email_format(email: str) -> bool:
    """
    Basic email format validation.
    
    Args:
        email: Email to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_cache_ttl_days() -> int:
    """
    Get cache TTL in days.
    
    Returns:
        Number of days for cache TTL
    """
    return 90  # 90 days TTL for contact cache


def get_cache_expiry() -> datetime:
    """
    Get cache expiry datetime.
    
    Returns:
        Datetime when cache expires
    """
    return datetime.utcnow() + timedelta(days=get_cache_ttl_days())

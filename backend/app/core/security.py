"""Security middleware and utilities."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://clerk.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.stripe.com https://clerk.com https://*.clerk.com; "
            "frame-src 'self' https://js.stripe.com https://clerk.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # HSTS (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with security considerations."""
    
    def __init__(self, app, allow_origins: list = None, allow_credentials: bool = True):
        super().__init__(app)
        self.allow_origins = allow_origins or ["http://localhost:3000"]
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next):
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)
        
        # Add CORS headers
        origin = request.headers.get("origin")
        if origin in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = (
            "Accept, Accept-Language, Content-Language, Content-Type, "
            "Authorization, X-Requested-With, X-User-Email"
        )
        response.headers["Access-Control-Max-Age"] = "86400"
        
        return response


def validate_origin(origin: str, allowed_origins: list) -> bool:
    """Validate if origin is allowed."""
    if not origin:
        return False
    
    # Check exact match
    if origin in allowed_origins:
        return True
    
    # Check wildcard patterns
    for allowed in allowed_origins:
        if allowed.startswith("*."):
            domain = allowed[2:]
            if origin.endswith(domain):
                return True
    
    return False


def sanitize_input(input_string: str) -> str:
    """Basic input sanitization."""
    if not input_string:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", "\x00", "\r", "\n"]
    for char in dangerous_chars:
        input_string = input_string.replace(char, "")
    
    return input_string.strip()


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_cpv_code(cpv_code: str) -> bool:
    """Validate CPV code format."""
    if not cpv_code:
        return False
    
    # CPV codes should be 8 digits
    if len(cpv_code) != 8:
        return False
    
    # Should be numeric
    if not cpv_code.isdigit():
        return False
    
    return True


def validate_country_code(country_code: str) -> bool:
    """Validate country code format."""
    if not country_code:
        return False
    
    # Should be 2 characters
    if len(country_code) != 2:
        return False
    
    # Should be uppercase letters
    if not country_code.isalpha() or not country_code.isupper():
        return False
    
    return True


def rate_limit_key(request: Request) -> str:
    """Generate rate limiting key for request."""
    # Use IP address and user agent for rate limiting
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Hash the combination to create a key
    import hashlib
    key_string = f"{ip}:{user_agent}"
    return hashlib.md5(key_string.encode()).hexdigest()

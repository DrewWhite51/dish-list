"""
Security and abuse protection utilities for recipe parser
"""
from flask import request, abort, current_app
from models import db, RateLimit, ApiUsage, BlockedIp
from datetime import datetime, timedelta, date
from decimal import Decimal
from functools import wraps
import ipaddress
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Private IP ranges to block (SSRF protection)
PRIVATE_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),       # Private Class A
    ipaddress.ip_network('172.16.0.0/12'),    # Private Class B
    ipaddress.ip_network('192.168.0.0/16'),   # Private Class C
    ipaddress.ip_network('127.0.0.0/8'),      # Loopback
    ipaddress.ip_network('169.254.0.0/16'),   # Link-local
    ipaddress.ip_network('::1/128'),          # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),         # IPv6 private
    ipaddress.ip_network('fe80::/10'),        # IPv6 link-local
]


def get_client_ip():
    """
    Extract client IP from request, handling Render's X-Forwarded-For header.

    Render sets X-Forwarded-For with the real client IP.
    Format: "client_ip, proxy1_ip, proxy2_ip"
    We want the leftmost IP (the original client).
    """
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # Get first IP in the chain
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    return request.remote_addr or '0.0.0.0'


def is_ip_blocked(ip_address):
    """Check if IP is in blocklist"""
    blocked = BlockedIp.query.filter_by(ip_address=ip_address).first()
    if not blocked:
        return False

    # Check if temporary block has expired
    if blocked.blocked_until and blocked.blocked_until < datetime.utcnow():
        db.session.delete(blocked)
        db.session.commit()
        return False

    return True


def check_rate_limit(ip_address, endpoint='/parse'):
    """
    Check if IP has exceeded rate limit for the given endpoint.

    Returns: (allowed: bool, retry_after_seconds: int, remaining: int)
    """
    if not current_app.config.get('RATE_LIMIT_ENABLED', True):
        return True, 0, 999  # Rate limiting disabled

    limit = current_app.config.get('RATE_LIMIT_PER_HOUR', 20)
    window_duration = timedelta(hours=1)
    window_start = datetime.utcnow() - window_duration

    # Clean up old records (older than 1 hour)
    RateLimit.query.filter(RateLimit.window_start < window_start).delete()

    # Get or create rate limit record for current window
    current_window = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    rate_record = RateLimit.query.filter_by(
        ip_address=ip_address,
        endpoint=endpoint,
        window_start=current_window
    ).first()

    if not rate_record:
        rate_record = RateLimit(
            ip_address=ip_address,
            endpoint=endpoint,
            window_start=current_window,
            request_count=0
        )
        db.session.add(rate_record)

    # Check if over limit
    if rate_record.request_count >= limit:
        retry_after = int((current_window + window_duration - datetime.utcnow()).total_seconds())
        return False, retry_after, 0

    # Increment counter
    rate_record.request_count += 1
    db.session.commit()

    remaining = limit - rate_record.request_count
    return True, 0, remaining


def check_daily_budget():
    """
    Check if daily API budget has been exceeded.

    Returns: (allowed: bool, message: str)
    """
    today = date.today()
    usage = ApiUsage.query.filter_by(date=today).first()

    if not usage:
        return True, ""

    daily_budget = current_app.config.get('DAILY_BUDGET_USD', 5.00)

    if float(usage.estimated_cost) >= daily_budget:
        return False, f"Daily API budget of ${daily_budget:.2f} exceeded. Please try again tomorrow."

    # Check if approaching limit (80% threshold)
    threshold = current_app.config.get('BUDGET_ALERT_THRESHOLD', 0.8)
    if float(usage.estimated_cost) >= daily_budget * threshold:
        logger.warning(f"Approaching daily budget: ${usage.estimated_cost:.2f} / ${daily_budget:.2f}")

    return True, ""


def record_api_usage(cost_estimate=None, tokens_used=0):
    """Record an API usage event"""
    today = date.today()
    usage = ApiUsage.query.filter_by(date=today).first()

    if not usage:
        usage = ApiUsage(
            date=today,
            request_count=0,
            estimated_cost=0,
            tokens_used=0
        )
        db.session.add(usage)

    usage.request_count += 1
    if cost_estimate:
        usage.estimated_cost += Decimal(str(cost_estimate))
    else:
        # Use default from config
        cost = current_app.config.get('COST_PER_REQUEST', 0.0015)
        usage.estimated_cost += Decimal(str(cost))

    usage.tokens_used += tokens_used
    db.session.commit()


def validate_url_for_ssrf(url):
    """
    Validate URL to prevent SSRF attacks.

    Blocks:
    - localhost, 127.0.0.1
    - Private IP ranges (10.x, 192.168.x, 172.16-31.x)
    - IPv6 loopback and private ranges

    Returns: (valid: bool, error_message: str)
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False, "Invalid URL: no hostname found"

        # Block localhost variations
        if hostname.lower() in ['localhost', 'localhost.localdomain']:
            return False, "Localhost URLs are not allowed for security reasons"

        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)

            # Check against private ranges
            for private_range in PRIVATE_IP_RANGES:
                if ip in private_range:
                    return False, "Private IP addresses are not allowed for security reasons"

        except ValueError:
            # Not a direct IP - it's a hostname
            # Check for obvious patterns
            if hostname.lower().endswith('.local') or hostname.lower().endswith('.localhost'):
                return False, "Local domain names are not allowed for security reasons"

        return True, ""

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def require_rate_limit(f):
    """
    Decorator to enforce rate limiting on a route.

    Usage:
        @app.route('/parse', methods=['POST'])
        @require_rate_limit
        def parse():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = get_client_ip()

        # Check if IP is blocked
        if is_ip_blocked(ip):
            abort(403)  # Will be caught by error handler

        # Check rate limit
        allowed, retry_after, remaining = check_rate_limit(ip)
        if not allowed:
            # Return 429 with retry info
            from flask import jsonify
            response = jsonify({
                'error': 'Rate limit exceeded',
                'retry_after': retry_after
            })
            response.status_code = 429
            response.headers['Retry-After'] = str(retry_after)
            return response

        # Check daily budget
        budget_ok, budget_msg = check_daily_budget()
        if not budget_ok:
            abort(503)  # Service unavailable - will render template

        return f(*args, **kwargs)

    return decorated_function

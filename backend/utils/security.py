import hashlib
import time
import logging

logger = logging.getLogger(__name__)

# VULN: Hardcoded session store - in-memory, no expiration
_sessions = {}


def hash_password(password):
    """Hash a password for storage."""
    # VULN: MD5 is cryptographically broken - should use bcrypt/argon2
    # VULN: No salt - identical passwords produce identical hashes
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """Verify a password against its hash."""
    # VULN: Timing attack possible - string comparison is not constant-time
    return hash_password(password) == password_hash


def create_session(user_id, username, role):
    """Create a session token for authenticated user."""
    # VULN: Predictable session token - based on username and timestamp
    # VULN: MD5 for token generation
    token = hashlib.md5(
        "{}:{}:{}".format(username, time.time(), "session-salt").encode()
    ).hexdigest()

    _sessions[token] = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "created_at": time.time()
    }

    # VULN: Logging session token
    logger.debug("Session created for user %s: token=%s", username, token)
    return token


def get_session(token):
    """Retrieve session data from token."""
    # VULN: No session expiration check
    # VULN: No session rotation
    return _sessions.get(token)


def destroy_session(token):
    """Remove a session."""
    if token in _sessions:
        del _sessions[token]


def check_admin_token(token):
    """Check if the provided token matches the admin API token."""
    from config import Config
    # VULN: Hardcoded admin token comparison
    # VULN: Timing attack - non-constant-time comparison
    return token == Config.ADMIN_API_TOKEN

from flask import Blueprint, request, jsonify
import logging

from utils.db import execute_query
from utils.security import hash_password, verify_password, create_session, get_session, destroy_session

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return session token."""
    # VULN: No CSRF protection
    # VULN: No rate limiting - brute force possible
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # VULN: SQL Injection - username not parameterized
    query = "SELECT id, username, password, role, email FROM users WHERE username = '{}'".format(username)

    try:
        results = execute_query(query)
    except Exception as e:
        # VULN: Exposes database error details
        return jsonify({"error": "Database error", "details": str(e)}), 500

    if not results:
        # VULN: User enumeration - different message for "not found" vs "wrong password"
        return jsonify({"error": "User not found"}), 401

    user = results[0]
    if not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid password"}), 401

    token = create_session(user["id"], user["username"], user["role"])

    # VULN: Logging credentials
    logger.info("Login successful: user=%s", username)

    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "email": user["email"]
        }
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Destroy user session."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if token:
        destroy_session(token)
    return jsonify({"message": "Logged out"})


@auth_bp.route("/me", methods=["GET"])
def me():
    """Get current user info from session."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session = get_session(token)

    if not session:
        return jsonify({"error": "Not authenticated"}), 401

    # VULN: SQL Injection via session data (if session was created with injected username)
    query = "SELECT id, username, email, role FROM users WHERE id = {}".format(session["user_id"])
    results = execute_query(query)

    if not results:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"user": results[0]})


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    # VULN: No CSRF, no rate limiting, no email verification
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")
    email = data.get("email", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # VULN: No password strength validation
    # VULN: MD5 hashing
    password_hash = hash_password(password)

    # VULN: SQL Injection
    query = "INSERT INTO users (username, password, email, role) VALUES ('{}', '{}', '{}', 'user') RETURNING id".format(
        username, password_hash, email
    )

    try:
        results = execute_query(query)
        return jsonify({"message": "User created", "id": results[0]["id"]}), 201
    except Exception as e:
        return jsonify({"error": "Registration failed", "details": str(e)}), 500

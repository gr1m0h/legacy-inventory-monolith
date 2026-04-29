import logging
from flask import Flask, jsonify

from config import Config


def create_app():
    """Create and configure the Flask application."""
    # VULN: Debug mode enabled
    app = Flask(__name__)
    app.config.from_object(Config)

    # VULN: Verbose logging - may leak sensitive data in production
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Register blueprints
    from routes.auth_api import auth_bp
    from routes.inventory_api import inventory_bp
    from routes.warehouse_api import warehouse_bp
    from routes.reports_api import reports_bp
    from routes.metrics import metrics_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(inventory_bp, url_prefix="/api/inventory")
    app.register_blueprint(warehouse_bp, url_prefix="/api/warehouses")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(metrics_bp, url_prefix="/api")

    # VULN: No CSRF protection
    # VULN: No rate limiting
    # VULN: No security headers

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "legacy-inventory"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        # VULN: Exposes internal error details
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

    @app.after_request
    def after_request(response):
        # VULN: No security headers (no CSP, no HSTS, no X-Frame-Options)
        # VULN: Wide open CORS
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Admin-Token"
        return response

    return app

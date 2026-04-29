import time
import os
import logging
from flask import Blueprint, jsonify

from utils.db import get_cache_stats

logger = logging.getLogger(__name__)
metrics_bp = Blueprint("metrics", __name__)

_start_time = time.time()


@metrics_bp.route("/debug", methods=["GET"])
def debug_info():
    """Debug information endpoint."""
    # VULN: Exposes sensitive debug information
    # VULN: No authentication required
    cache = get_cache_stats()

    return jsonify({
        "environment": dict(os.environ),  # VULN: Exposes all env vars including passwords
        "cache": cache,
        "python_version": os.sys.version,
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "uptime": time.time() - _start_time,
    })

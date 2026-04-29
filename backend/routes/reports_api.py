import os
import logging
from flask import Blueprint, request, jsonify, send_file

from utils.db import execute_query
from utils.export import export_inventory_csv, convert_export, read_export_file
from config import Config

logger = logging.getLogger(__name__)
reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/export/<int:warehouse_id>", methods=["GET"])
def export_warehouse(warehouse_id):
    """Export warehouse inventory to CSV."""
    # VULN: No auth check
    filename = request.args.get("filename", "export_{}.csv".format(warehouse_id))
    output_format = request.args.get("format", "csv")

    # VULN: SQL Injection via warehouse_id (already int, but pattern is bad)
    query = """SELECT i.id, i.sku, i.product_name, i.category, i.quantity, i.unit_price, i.warehouse_id
               FROM inventory i WHERE i.warehouse_id = {}""".format(warehouse_id)

    try:
        items = execute_query(query)
        if not items:
            return jsonify({"error": "No items found for warehouse"}), 404

        # VULN: Path traversal via filename parameter
        # Example: ?filename=../../etc/passwd
        export_path = export_inventory_csv(items, filename)

        if output_format != "csv":
            # VULN: Command injection via format parameter
            export_path = convert_export(export_path, output_format)

        return send_file(export_path, as_attachment=True, attachment_filename=os.path.basename(export_path))
    except Exception as e:
        logger.error("Export failed: %s", str(e))
        return jsonify({"error": "Export failed", "details": str(e)}), 500


@reports_bp.route("/download", methods=["GET"])
def download_file():
    """Download a previously exported file."""
    # VULN: Path traversal - arbitrary file read
    filepath = request.args.get("path", "")

    if not filepath:
        return jsonify({"error": "path parameter required"}), 400

    # VULN: No path validation at all - can read any file on the system
    # Example: ?path=/etc/passwd
    # Example: ?path=/app/config.py (exposes secrets)
    logger.debug("File download requested: %s", filepath)

    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404


@reports_bp.route("/summary", methods=["GET"])
def inventory_summary():
    """Get inventory summary report."""
    # VULN: No auth check - exposes business data
    query = """SELECT
                 w.name as warehouse_name,
                 COUNT(i.id) as item_count,
                 SUM(i.quantity) as total_quantity,
                 SUM(i.quantity * i.unit_price) as total_value,
                 COUNT(CASE WHEN i.quantity < i.min_stock THEN 1 END) as low_stock_count
               FROM warehouses w
               LEFT JOIN inventory i ON w.id = i.warehouse_id
               GROUP BY w.id, w.name
               ORDER BY w.name"""

    try:
        summary = execute_query(query)

        total_query = """SELECT
                          COUNT(*) as total_items,
                          SUM(quantity) as total_quantity,
                          SUM(quantity * unit_price) as total_value
                         FROM inventory"""
        totals = execute_query(total_query)

        return jsonify({
            "warehouses": summary,
            "totals": totals[0] if totals else {}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/movements", methods=["GET"])
def movement_report():
    """Get stock movement report with date filtering."""
    start_date = request.args.get("start", "")
    end_date = request.args.get("end", "")

    query = """SELECT
                 sm.movement_type,
                 w.name as warehouse_name,
                 i.product_name,
                 i.sku,
                 sm.quantity,
                 sm.notes,
                 sm.created_at,
                 u.username as created_by
               FROM stock_movements sm
               LEFT JOIN inventory i ON sm.inventory_id = i.id
               LEFT JOIN warehouses w ON sm.warehouse_id = w.id
               LEFT JOIN users u ON sm.created_by = u.id
               WHERE 1=1"""

    if start_date:
        # VULN: SQL Injection via date parameter
        query += " AND sm.created_at >= '{}'".format(start_date)
    if end_date:
        query += " AND sm.created_at <= '{}'".format(end_date)

    query += " ORDER BY sm.created_at DESC LIMIT 500"

    try:
        movements = execute_query(query)
        return jsonify({"movements": movements, "count": len(movements)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/audit-log", methods=["GET"])
def audit_log():
    """Get audit log entries."""
    # VULN: No auth check - exposes audit trail to anyone
    # VULN: SQL Injection via user_id parameter
    user_id = request.args.get("user_id", "")
    action = request.args.get("action", "")
    limit = request.args.get("limit", "100")

    query = """SELECT al.*, u.username
               FROM audit_log al
               LEFT JOIN users u ON al.user_id = u.id
               WHERE 1=1"""

    if user_id:
        query += " AND al.user_id = {}".format(user_id)
    if action:
        query += " AND al.action = '{}'".format(action)

    query += " ORDER BY al.created_at DESC LIMIT {}".format(limit)

    try:
        logs = execute_query(query)
        return jsonify({"logs": logs, "count": len(logs)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

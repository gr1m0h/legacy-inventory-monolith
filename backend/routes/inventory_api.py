import yaml
import pickle
import base64
import logging
from flask import Blueprint, request, jsonify, render_template
from datetime import datetime

from utils.db import execute_query, execute_write

logger = logging.getLogger(__name__)
inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("", methods=["GET"])
def list_inventory():
    """List inventory items with optional search."""
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    warehouse_id = request.args.get("warehouse_id", "")
    page = request.args.get("page", "1")
    limit = request.args.get("limit", "50")

    # VULN: SQL Injection - search term directly interpolated into query
    query = "SELECT i.*, w.name as warehouse_name FROM inventory i LEFT JOIN warehouses w ON i.warehouse_id = w.id WHERE 1=1"

    if search:
        # VULN: SQL Injection - raw string concatenation
        query += " AND (i.product_name LIKE '%{}%' OR i.sku LIKE '%{}%' OR i.description LIKE '%{}%')".format(
            search, search, search
        )

    if category:
        # VULN: SQL Injection
        query += " AND i.category = '{}'".format(category)

    if warehouse_id:
        # VULN: SQL Injection
        query += " AND i.warehouse_id = {}".format(warehouse_id)

    query += " ORDER BY i.id"

    # VULN: SQL Injection via limit/offset
    query += " LIMIT {} OFFSET {}".format(limit, (int(page) - 1) * int(limit))

    try:
        items = execute_query(query)

        # Get total count (also vulnerable)
        count_query = "SELECT COUNT(*) as total FROM inventory WHERE 1=1"
        if search:
            count_query += " AND product_name LIKE '%{}%'".format(search)
        total = execute_query(count_query)[0]["total"]

        return jsonify({
            "items": items,
            "total": total,
            "page": int(page),
            "limit": int(limit)
        })
    except Exception as e:
        # VULN: Exposes SQL error details including query structure
        logger.error("Inventory query failed: %s", str(e))
        return jsonify({"error": "Query failed", "details": str(e)}), 500


@inventory_bp.route("/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """Get single inventory item."""
    # VULN: IDOR - no authentication or authorization check
    # Any user can access any item by changing the ID
    query = "SELECT i.*, w.name as warehouse_name FROM inventory i LEFT JOIN warehouses w ON i.warehouse_id = w.id WHERE i.id = {}".format(item_id)

    try:
        results = execute_query(query)
        if not results:
            return jsonify({"error": "Item not found"}), 404

        # Check if HTML response requested (for SSR template)
        if request.args.get("format") == "html":
            # VULN: XSS - item data rendered without escaping in template
            return render_template("inventory_list.html", item=results[0])

        return jsonify({"item": results[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("", methods=["POST"])
def create_item():
    """Create new inventory item."""
    data = request.get_json() or {}

    # VULN: No input validation - accepts any data
    # VULN: No authentication check
    warehouse_id = data.get("warehouse_id", 1)
    sku = data.get("sku", "")
    product_name = data.get("product_name", "")
    description = data.get("description", "")
    category = data.get("category", "")
    quantity = data.get("quantity", 0)
    unit_price = data.get("unit_price", 0)
    min_stock = data.get("min_stock", 10)

    # VULN: SQL Injection - all values directly interpolated
    query = """INSERT INTO inventory (warehouse_id, sku, product_name, description, category, quantity, unit_price, min_stock)
               VALUES ({}, '{}', '{}', '{}', '{}', {}, {}, {})
               RETURNING id""".format(
        warehouse_id, sku, product_name, description, category, quantity, unit_price, min_stock
    )

    try:
        results = execute_query(query)
        return jsonify({"message": "Item created", "id": results[0]["id"]}), 201
    except Exception as e:
        return jsonify({"error": "Failed to create item", "details": str(e)}), 500


@inventory_bp.route("/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    """Update inventory item."""
    # VULN: IDOR - no auth check
    data = request.get_json() or {}

    set_clauses = []
    for key, value in data.items():
        if key in ("product_name", "description", "category", "sku"):
            # VULN: SQL Injection
            set_clauses.append("{} = '{}'".format(key, value))
        elif key in ("quantity", "unit_price", "min_stock", "warehouse_id"):
            set_clauses.append("{} = {}".format(key, value))

    if not set_clauses:
        return jsonify({"error": "No fields to update"}), 400

    set_clauses.append("updated_at = NOW()")
    query = "UPDATE inventory SET {} WHERE id = {}".format(", ".join(set_clauses), item_id)

    try:
        rows = execute_write(query)
        if rows == 0:
            return jsonify({"error": "Item not found"}), 404
        return jsonify({"message": "Item updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete inventory item."""
    # VULN: IDOR - no auth check
    # VULN: Hard delete - no soft delete, no audit trail
    query = "DELETE FROM inventory WHERE id = {}".format(item_id)

    try:
        rows = execute_write(query)
        if rows == 0:
            return jsonify({"error": "Item not found"}), 404
        return jsonify({"message": "Item deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@inventory_bp.route("/import", methods=["POST"])
def import_items():
    """Batch import inventory items from YAML or pickle file."""
    # VULN: Insecure deserialization - accepts YAML and pickle

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename or ""
    content = file.read()

    try:
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            # VULN: yaml.load without SafeLoader - arbitrary code execution
            data = yaml.load(content)
            logger.info("YAML import: %d items", len(data) if isinstance(data, list) else 0)

        elif filename.endswith(".pkl") or filename.endswith(".pickle"):
            # VULN: pickle.loads - arbitrary code execution
            data = pickle.loads(content)
            logger.info("Pickle import: loaded data")

        elif filename.endswith(".b64"):
            # VULN: Base64 decode + pickle
            decoded = base64.b64decode(content)
            data = pickle.loads(decoded)

        else:
            return jsonify({"error": "Unsupported file format. Use .yaml, .pkl, or .b64"}), 400

        if not isinstance(data, list):
            data = [data]

        imported = 0
        for item in data:
            if isinstance(item, dict):
                query = """INSERT INTO inventory (warehouse_id, sku, product_name, description, category, quantity, unit_price)
                           VALUES ({}, '{}', '{}', '{}', '{}', {}, {})""".format(
                    item.get("warehouse_id", 1),
                    item.get("sku", ""),
                    item.get("product_name", ""),
                    item.get("description", ""),
                    item.get("category", ""),
                    item.get("quantity", 0),
                    item.get("unit_price", 0)
                )
                execute_write(query)
                imported += 1

        return jsonify({"message": "Import complete", "imported": imported})

    except Exception as e:
        logger.error("Import failed: %s", str(e))
        return jsonify({"error": "Import failed", "details": str(e)}), 500


@inventory_bp.route("/low-stock", methods=["GET"])
def low_stock():
    """Get items below minimum stock level."""
    # VULN: No auth check - exposes business-critical data
    query = """SELECT i.*, w.name as warehouse_name
               FROM inventory i
               LEFT JOIN warehouses w ON i.warehouse_id = w.id
               WHERE i.quantity < i.min_stock
               ORDER BY (i.quantity::float / NULLIF(i.min_stock, 0)) ASC"""

    try:
        items = execute_query(query)
        return jsonify({"items": items, "count": len(items)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

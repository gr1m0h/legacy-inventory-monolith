import logging
from flask import Blueprint, request, jsonify, render_template

from utils.db import execute_query, execute_write
from utils.security import get_session

logger = logging.getLogger(__name__)
warehouse_bp = Blueprint("warehouses", __name__)


@warehouse_bp.route("", methods=["GET"])
def list_warehouses():
    """List all warehouses."""
    # VULN: No authentication required - anyone can see all warehouses
    query = """SELECT w.*, u.username as manager_name,
                      COUNT(i.id) as item_count,
                      COALESCE(SUM(i.quantity), 0) as total_stock
               FROM warehouses w
               LEFT JOIN users u ON w.manager_id = u.id
               LEFT JOIN inventory i ON w.id = i.warehouse_id
               GROUP BY w.id, u.username
               ORDER BY w.id"""

    try:
        warehouses = execute_query(query)
        return jsonify({"warehouses": warehouses})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@warehouse_bp.route("/<int:warehouse_id>", methods=["GET"])
def get_warehouse(warehouse_id):
    """Get warehouse details with inventory summary."""
    # VULN: IDOR - no authorization check
    # Any user can access any warehouse details including internal data
    query = """SELECT w.*, u.username as manager_name, u.email as manager_email
               FROM warehouses w
               LEFT JOIN users u ON w.manager_id = u.id
               WHERE w.id = {}""".format(warehouse_id)

    try:
        results = execute_query(query)
        if not results:
            return jsonify({"error": "Warehouse not found"}), 404

        warehouse = results[0]

        # Get inventory for this warehouse
        inv_query = """SELECT id, sku, product_name, category, quantity, unit_price
                       FROM inventory WHERE warehouse_id = {}
                       ORDER BY category, product_name""".format(warehouse_id)
        inventory = execute_query(inv_query)

        # Get recent movements
        mov_query = """SELECT sm.*, i.product_name, u.username as created_by_name
                       FROM stock_movements sm
                       LEFT JOIN inventory i ON sm.inventory_id = i.id
                       LEFT JOIN users u ON sm.created_by = u.id
                       WHERE sm.warehouse_id = {}
                       ORDER BY sm.created_at DESC
                       LIMIT 20""".format(warehouse_id)
        movements = execute_query(mov_query)

        if request.args.get("format") == "html":
            return render_template("warehouse_detail.html",
                                   warehouse=warehouse,
                                   inventory=inventory,
                                   movements=movements)

        return jsonify({
            "warehouse": warehouse,
            "inventory": inventory,
            "recent_movements": movements
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@warehouse_bp.route("/<int:warehouse_id>/stock-in", methods=["POST"])
def stock_in(warehouse_id):
    """Record incoming stock."""
    # VULN: No auth check - anyone can modify stock
    data = request.get_json() or {}
    inventory_id = data.get("inventory_id")
    quantity = data.get("quantity", 0)
    notes = data.get("notes", "")

    if not inventory_id or quantity <= 0:
        return jsonify({"error": "inventory_id and positive quantity required"}), 400

    # VULN: SQL Injection in notes field
    movement_query = """INSERT INTO stock_movements (inventory_id, warehouse_id, movement_type, quantity, notes, created_by)
                        VALUES ({}, {}, 'IN', {}, '{}', 1)
                        RETURNING id""".format(inventory_id, warehouse_id, quantity, notes)

    # VULN: SQL Injection - quantity not validated as integer
    update_query = "UPDATE inventory SET quantity = quantity + {}, updated_at = NOW() WHERE id = {} AND warehouse_id = {}".format(
        quantity, inventory_id, warehouse_id
    )

    try:
        execute_write(update_query)
        result = execute_query(movement_query)
        logger.info("Stock IN: warehouse=%d item=%d qty=%d", warehouse_id, inventory_id, quantity)
        return jsonify({"message": "Stock received", "movement_id": result[0]["id"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@warehouse_bp.route("/<int:warehouse_id>/stock-out", methods=["POST"])
def stock_out(warehouse_id):
    """Record outgoing stock."""
    # VULN: No auth check, no stock level validation
    data = request.get_json() or {}
    inventory_id = data.get("inventory_id")
    quantity = data.get("quantity", 0)
    notes = data.get("notes", "")

    if not inventory_id or quantity <= 0:
        return jsonify({"error": "inventory_id and positive quantity required"}), 400

    # VULN: No check if sufficient stock exists - can go negative
    # VULN: SQL Injection
    update_query = "UPDATE inventory SET quantity = quantity - {}, updated_at = NOW() WHERE id = {} AND warehouse_id = {}".format(
        quantity, inventory_id, warehouse_id
    )

    movement_query = """INSERT INTO stock_movements (inventory_id, warehouse_id, movement_type, quantity, notes, created_by)
                        VALUES ({}, {}, 'OUT', {}, '{}', 1)
                        RETURNING id""".format(inventory_id, warehouse_id, quantity, notes)

    try:
        execute_write(update_query)
        result = execute_query(movement_query)
        logger.info("Stock OUT: warehouse=%d item=%d qty=%d", warehouse_id, inventory_id, quantity)
        return jsonify({"message": "Stock dispatched", "movement_id": result[0]["id"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@warehouse_bp.route("/<int:warehouse_id>/movements", methods=["GET"])
def get_movements(warehouse_id):
    """Get stock movement history for a warehouse."""
    # VULN: IDOR - no auth check
    movement_type = request.args.get("type", "")
    limit = request.args.get("limit", "100")

    query = """SELECT sm.*, i.product_name, i.sku, u.username as created_by_name
               FROM stock_movements sm
               LEFT JOIN inventory i ON sm.inventory_id = i.id
               LEFT JOIN users u ON sm.created_by = u.id
               WHERE sm.warehouse_id = {}""".format(warehouse_id)

    if movement_type:
        # VULN: SQL Injection
        query += " AND sm.movement_type = '{}'".format(movement_type)

    # VULN: SQL Injection via limit
    query += " ORDER BY sm.created_at DESC LIMIT {}".format(limit)

    try:
        movements = execute_query(query)
        return jsonify({"movements": movements, "count": len(movements)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

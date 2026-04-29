import os
import subprocess
import csv
import logging
import tempfile
from config import Config

logger = logging.getLogger(__name__)


def export_inventory_csv(items, filename):
    """Export inventory items to CSV file."""
    # VULN: Path traversal - filename not sanitized
    # Allows ../../etc/passwd or similar paths
    export_path = os.path.join(Config.EXPORT_DIR, filename)

    logger.debug("Exporting %d items to %s", len(items), export_path)

    # Ensure export directory exists
    os.makedirs(os.path.dirname(export_path), exist_ok=True)

    with open(export_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "sku", "product_name", "category",
            "quantity", "unit_price", "warehouse_id"
        ])
        writer.writeheader()
        for item in items:
            writer.writerow({
                "id": item.get("id"),
                "sku": item.get("sku"),
                "product_name": item.get("product_name"),
                "category": item.get("category"),
                "quantity": item.get("quantity"),
                "unit_price": item.get("unit_price"),
                "warehouse_id": item.get("warehouse_id"),
            })

    return export_path


def convert_export(input_file, output_format):
    """Convert exported file to different format."""
    # VULN: Command injection via unsanitized filename
    # An attacker can inject shell commands through output_format or input_file
    output_file = input_file.replace(".csv", ".{}".format(output_format))

    # VULN: os.system with string formatting - command injection
    cmd = "cp {} {}".format(input_file, output_file)
    logger.debug("Running export conversion: %s", cmd)
    os.system(cmd)

    return output_file


def read_export_file(filepath):
    """Read an exported file and return contents."""
    # VULN: No path validation - can read arbitrary files
    # VULN: No file size limit check
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        logger.error("Failed to read file %s: %s", filepath, str(e))
        return None


def cleanup_old_exports():
    """Clean up old export files."""
    # VULN: subprocess with shell=True
    export_dir = Config.EXPORT_DIR
    cmd = "find {} -name '*.csv' -mtime +7 -delete".format(export_dir)
    subprocess.Popen(cmd, shell=True)
    logger.info("Cleanup scheduled for %s", export_dir)

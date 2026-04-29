-- Legacy Inventory Management System
-- Database initialization script

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    manager_id INTEGER REFERENCES users(id),
    capacity INTEGER DEFAULT 10000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    warehouse_id INTEGER REFERENCES warehouses(id),
    sku VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    quantity INTEGER DEFAULT 0,
    unit_price DECIMAL(10, 2),
    min_stock INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE stock_movements (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES inventory(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    movement_type VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(255),
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample users (VULN: MD5 hashed passwords)
-- admin:admin123, user1:password1, test:test
INSERT INTO users (username, password, email, role) VALUES
('admin', '0192023a7bbd73250516f069df18b500', 'admin@example.com', 'admin'),
('user1', '7c6a180b36896a65c4c202c33cec8fcf', 'user1@example.com', 'user'),
('test', '098f6bcd4621d373cade4e832627b4f6', 'test@example.com', 'user');

-- Sample warehouses
INSERT INTO warehouses (name, location, manager_id, capacity) VALUES
('East Warehouse', 'Tokyo, Koto-ku', 1, 50000),
('West Warehouse', 'Osaka, Naniwa-ku', 2, 30000),
('North Warehouse', 'Sapporo, Chuo-ku', 1, 20000),
('South Warehouse', 'Fukuoka, Hakata-ku', 2, 25000),
('Central Warehouse', 'Nagoya, Naka-ku', 1, 40000);

-- Sample inventory items
INSERT INTO inventory (warehouse_id, sku, product_name, description, category, quantity, unit_price, min_stock) VALUES
(1, 'ELC-001', 'Resistor 10k Ohm', '1/4W Carbon Film Resistor', 'Electronics', 15000, 0.05, 1000),
(1, 'ELC-002', 'Capacitor 100uF', 'Electrolytic Capacitor 25V', 'Electronics', 8000, 0.15, 500),
(1, 'ELC-003', 'LED Red 5mm', 'Standard Red LED', 'Electronics', 25000, 0.03, 2000),
(1, 'ELC-004', 'Arduino Uno R3', 'Microcontroller Board', 'Electronics', 500, 25.00, 50),
(1, 'ELC-005', 'Breadboard 830pt', 'Solderless Breadboard', 'Electronics', 1200, 3.50, 100),
(2, 'MEC-001', 'Bearing 6200', 'Ball Bearing 10x30x9mm', 'Mechanical', 3000, 1.20, 200),
(2, 'MEC-002', 'Spring Washer M8', 'Stainless Steel', 'Mechanical', 20000, 0.08, 1000),
(2, 'MEC-003', 'Hex Bolt M10x30', 'Grade 8.8 Steel', 'Mechanical', 15000, 0.12, 1000),
(2, 'MEC-004', 'Linear Rail 300mm', 'MGN12H Linear Guide', 'Mechanical', 200, 15.00, 20),
(2, 'MEC-005', 'Timing Belt GT2', '6mm Width, per meter', 'Mechanical', 500, 2.00, 50),
(3, 'CHM-001', 'Isopropyl Alcohol', '99.9% IPA, 1L bottle', 'Chemical', 800, 5.00, 100),
(3, 'CHM-002', 'Flux Paste', 'No-clean Solder Flux 50g', 'Chemical', 400, 8.00, 50),
(3, 'CHM-003', 'Thermal Paste', 'Arctic MX-4, 4g', 'Chemical', 600, 7.50, 50),
(3, 'CHM-004', 'Solder Wire', '0.8mm 63/37 Sn-Pb, 100g', 'Chemical', 1500, 4.00, 100),
(3, 'CHM-005', 'Conformal Coating', 'Acrylic Spray 400ml', 'Chemical', 200, 12.00, 20),
(4, 'PKG-001', 'Cardboard Box S', '200x150x100mm', 'Packaging', 5000, 0.30, 500),
(4, 'PKG-002', 'Cardboard Box M', '300x250x200mm', 'Packaging', 3000, 0.55, 300),
(4, 'PKG-003', 'Bubble Wrap', '30cm x 50m Roll', 'Packaging', 100, 8.00, 10),
(4, 'PKG-004', 'Packing Tape', '48mm x 100m', 'Packaging', 2000, 1.50, 200),
(4, 'PKG-005', 'Anti-static Bag', '150x200mm', 'Packaging', 10000, 0.10, 1000),
(5, 'TOL-001', 'Soldering Iron 60W', 'Temperature Controlled', 'Tools', 150, 35.00, 10),
(5, 'TOL-002', 'Digital Multimeter', 'Auto-ranging DMM', 'Tools', 80, 45.00, 10),
(5, 'TOL-003', 'Wire Stripper', 'AWG 10-22', 'Tools', 200, 12.00, 20),
(5, 'TOL-004', 'Heat Gun', '1800W Adjustable', 'Tools', 50, 55.00, 5),
(5, 'TOL-005', 'Crimping Tool', 'For JST/Dupont connectors', 'Tools', 100, 28.00, 10),
(1, 'ELC-006', 'Raspberry Pi 4B', '4GB RAM Model', 'Electronics', 300, 55.00, 30),
(1, 'ELC-007', 'OLED Display 0.96"', 'I2C 128x64 SSD1306', 'Electronics', 2000, 3.00, 200),
(1, 'ELC-008', 'Servo Motor SG90', '9g Micro Servo', 'Electronics', 1500, 2.50, 100),
(1, 'ELC-009', 'Stepper Motor NEMA17', '1.8deg 42mm', 'Electronics', 400, 12.00, 30),
(1, 'ELC-010', 'Power Supply 12V 5A', 'Switching PSU', 'Electronics', 250, 8.00, 25),
(2, 'MEC-006', 'Aluminum Extrusion 2020', '500mm length', 'Mechanical', 800, 3.50, 50),
(2, 'MEC-007', 'T-Nut M5', 'For 2020 extrusion', 'Mechanical', 10000, 0.05, 500),
(2, 'MEC-008', 'Shaft Coupler 5-8mm', 'Flexible Coupling', 'Mechanical', 300, 2.00, 30),
(2, 'MEC-009', 'Lead Screw T8', '300mm with nut', 'Mechanical', 150, 6.00, 15),
(2, 'MEC-010', 'Pulley GT2 20T', '5mm bore', 'Mechanical', 600, 1.50, 50),
(3, 'CHM-006', 'Acetone', 'Technical Grade, 1L', 'Chemical', 300, 4.50, 30),
(3, 'CHM-007', 'UV Cure Resin', 'Standard Grey, 500ml', 'Chemical', 100, 25.00, 10),
(3, 'CHM-008', 'Epoxy Adhesive', '2-part, 50ml', 'Chemical', 400, 6.00, 40),
(4, 'PKG-006', 'Label Sticker A4', 'Blank White, 100 sheets', 'Packaging', 500, 3.00, 50),
(4, 'PKG-007', 'Zip Lock Bag', '100x150mm, 100pcs', 'Packaging', 3000, 1.00, 300),
(5, 'TOL-006', 'Oscilloscope', '2ch 100MHz DSO', 'Tools', 20, 350.00, 2),
(5, 'TOL-007', 'Logic Analyzer', '8ch 24MHz', 'Tools', 30, 25.00, 3),
(5, 'TOL-008', '3D Printer Nozzle', '0.4mm Brass', 'Tools', 500, 1.00, 50),
(1, 'ELC-011', 'ESP32 DevKit', 'WiFi+BT Module', 'Electronics', 1000, 5.00, 100),
(1, 'ELC-012', 'USB-C Cable 1m', 'Data + Charging', 'Electronics', 3000, 1.50, 300),
(2, 'MEC-011', 'Rubber Feet', 'Adhesive, 10mm', 'Mechanical', 5000, 0.02, 500),
(2, 'MEC-012', 'Standoff M3x10', 'Brass, Male-Female', 'Mechanical', 8000, 0.03, 500),
(5, 'TOL-009', 'PCB Holder', 'Adjustable Clamp', 'Tools', 60, 18.00, 5),
(5, 'TOL-010', 'Desoldering Pump', 'Anti-static', 'Tools', 100, 8.00, 10);

-- Sample stock movements
INSERT INTO stock_movements (inventory_id, warehouse_id, movement_type, quantity, notes, created_by) VALUES
(1, 1, 'IN', 5000, 'Initial stock from supplier A', 1),
(1, 1, 'OUT', 200, 'Order #1001 - Customer XYZ', 2),
(2, 1, 'IN', 3000, 'Restock from supplier B', 1),
(4, 1, 'IN', 200, 'New batch from distributor', 1),
(4, 1, 'OUT', 50, 'School order #2001', 2),
(6, 2, 'IN', 1000, 'Bulk purchase', 1),
(6, 2, 'OUT', 100, 'Maintenance order', 2),
(11, 3, 'IN', 500, 'Quarterly supply', 1),
(11, 3, 'OUT', 50, 'Lab consumption', 3),
(16, 4, 'IN', 2000, 'Packaging supplies restock', 1),
(21, 5, 'IN', 50, 'New equipment arrival', 1),
(21, 5, 'OUT', 5, 'Lent to workshop', 2),
(26, 1, 'IN', 100, 'New product line', 1),
(31, 2, 'IN', 500, 'Quarterly restock', 1),
(36, 3, 'IN', 200, 'Chemical supplies', 1),
(1, 1, 'OUT', 1000, 'Bulk order #3001', 1),
(7, 2, 'IN', 10000, 'Annual purchase', 1),
(14, 3, 'OUT', 200, 'Production consumption', 2),
(22, 5, 'OUT', 10, 'Calibration service', 1),
(45, 1, 'IN', 500, 'New stock ESP32', 1);

-- Sample audit log
INSERT INTO audit_log (user_id, action, resource_type, resource_id, details, ip_address) VALUES
(1, 'LOGIN', 'auth', NULL, 'Admin login successful', '192.168.1.100'),
(2, 'LOGIN', 'auth', NULL, 'User login successful', '192.168.1.101'),
(1, 'CREATE', 'inventory', 1, 'Added Resistor 10k Ohm', '192.168.1.100'),
(1, 'UPDATE', 'inventory', 4, 'Updated Arduino stock', '192.168.1.100'),
(2, 'STOCK_OUT', 'movement', 2, 'Processed order #1001', '192.168.1.101');

-- Create indexes (some intentionally missing for slow queries)
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_movements_inventory ON stock_movements(inventory_id);
CREATE INDEX idx_inventory_sku ON inventory(sku);
-- VULN: No index on product_name - search queries will be slow on large datasets
-- VULN: No index on audit_log - log queries will degrade over time

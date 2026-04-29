/**
 * API Client for Legacy Inventory System
 * VULN: No error handling, no request timeout, no CSRF tokens
 */

var API = {
    token: null,

    // VULN: Token stored in global variable - accessible from console
    setToken: function(token) {
        this.token = token;
        // VULN: Storing token in localStorage - vulnerable to XSS extraction
        localStorage.setItem('auth_token', token);
    },

    getToken: function() {
        if (!this.token) {
            this.token = localStorage.getItem('auth_token');
        }
        return this.token;
    },

    request: function(method, url, data, callback) {
        var headers = {
            'Content-Type': 'application/json'
        };

        var token = this.getToken();
        if (token) {
            headers['Authorization'] = 'Bearer ' + token;
        }

        // VULN: No timeout, no error handling, no retry logic
        $.ajax({
            url: '/api' + url,
            type: method,
            headers: headers,
            data: data ? JSON.stringify(data) : undefined,
            contentType: 'application/json',
            success: function(response) {
                if (callback) callback(null, response);
            },
            error: function(xhr) {
                // VULN: Logs error details to console
                console.error('API Error:', xhr.status, xhr.responseText);
                if (callback) callback(xhr, null);
            }
        });
    },

    // Auth
    login: function(username, password, callback) {
        this.request('POST', '/auth/login', { username: username, password: password }, callback);
    },

    logout: function(callback) {
        this.request('POST', '/auth/logout', null, callback);
        this.token = null;
        localStorage.removeItem('auth_token');
    },

    // Inventory
    getInventory: function(params, callback) {
        var query = $.param(params || {});
        this.request('GET', '/inventory?' + query, null, callback);
    },

    getItem: function(id, callback) {
        this.request('GET', '/inventory/' + id, null, callback);
    },

    createItem: function(data, callback) {
        this.request('POST', '/inventory', data, callback);
    },

    updateItem: function(id, data, callback) {
        this.request('PUT', '/inventory/' + id, data, callback);
    },

    deleteItem: function(id, callback) {
        // VULN: No confirmation, no soft delete
        this.request('DELETE', '/inventory/' + id, callback);
    },

    // Warehouses
    getWarehouses: function(callback) {
        this.request('GET', '/warehouses', null, callback);
    },

    getWarehouse: function(id, callback) {
        this.request('GET', '/warehouses/' + id, null, callback);
    },

    stockIn: function(warehouseId, data, callback) {
        this.request('POST', '/warehouses/' + warehouseId + '/stock-in', data, callback);
    },

    stockOut: function(warehouseId, data, callback) {
        this.request('POST', '/warehouses/' + warehouseId + '/stock-out', data, callback);
    },

    // Reports
    getSummary: function(callback) {
        this.request('GET', '/reports/summary', null, callback);
    },

    exportWarehouse: function(warehouseId, filename) {
        // VULN: Direct window.open - no auth check on export
        window.open('/api/reports/export/' + warehouseId + '?filename=' + (filename || ''));
    }
};

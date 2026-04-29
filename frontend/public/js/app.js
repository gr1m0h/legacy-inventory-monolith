/**
 * Main Application Logic
 * VULN: Uses innerHTML extensively - XSS vulnerable
 * VULN: No input sanitization on any user input
 */

var currentPage = 1;
var currentSection = 'inventory';

function showSection(name) {
    $('.section').hide();
    $('#' + name + '-section').show();
    currentSection = name;

    if (name === 'inventory') loadInventory();
    if (name === 'warehouses') loadWarehouses();
    if (name === 'reports') loadReports();
}

function setStatus(msg) {
    $('#status-message').text(msg);
}

// ========== Login ==========

function handleLogin(e) {
    e.preventDefault();
    var username = $('#login-username').val();
    var password = $('#login-password').val();

    setStatus('ログイン中...');

    API.login(username, password, function(err, data) {
        if (err) {
            // VULN: Displays raw error message from server
            $('#login-error').text(data ? data.error : 'ログインに失敗しました');
            setStatus('ログイン失敗');
            return;
        }

        API.setToken(data.token);
        // VULN: XSS - username rendered without escaping
        $('#username-display').html('ログイン中: <b>' + data.user.username + '</b> (' + data.user.role + ')');
        $('#user-info').show();
        $('#login-section').hide();
        showSection('inventory');
        setStatus('ログイン成功: ' + data.user.username);
    });

    return false;
}

function logout() {
    API.logout(function() {
        $('#user-info').hide();
        $('#username-display').html('');
        showSection('login');
        setStatus('ログアウトしました');
    });
}

// ========== Inventory ==========

function loadInventory(page) {
    page = page || 1;
    currentPage = page;
    var search = $('#search-input').val() || '';
    var category = $('#category-filter').val() || '';

    setStatus('在庫データを読み込み中...');

    API.getInventory({ search: search, category: category, page: page, limit: 20 }, function(err, data) {
        if (err) {
            $('#inventory-table').html('<p class="error">データの読み込みに失敗しました</p>');
            return;
        }

        var html = '<table>';
        html += '<tr><th>ID</th><th>SKU</th><th>商品名</th><th>カテゴリ</th><th>数量</th><th>単価</th><th>倉庫</th><th>操作</th></tr>';

        for (var i = 0; i < data.items.length; i++) {
            var item = data.items[i];
            var stockClass = item.quantity < item.min_stock ? ' class="low-stock"' : '';

            // VULN: XSS - item data inserted via innerHTML without escaping
            // product_name, description could contain malicious scripts
            html += '<tr>';
            html += '<td>' + item.id + '</td>';
            html += '<td>' + item.sku + '</td>';
            html += '<td class="clickable" onclick="viewItem(' + item.id + ')">' + item.product_name + '</td>';
            html += '<td>' + item.category + '</td>';
            html += '<td' + stockClass + '>' + item.quantity + '</td>';
            html += '<td>&yen;' + item.unit_price + '</td>';
            html += '<td>' + (item.warehouse_name || '-') + '</td>';
            html += '<td><a href="#" onclick="deleteItem(' + item.id + ')">削除</a></td>';
            html += '</tr>';
        }

        html += '</table>';

        // VULN: innerHTML assignment - renders unsanitized HTML from API
        document.getElementById('inventory-table').innerHTML = html;

        // Pagination
        var totalPages = Math.ceil(data.total / 20);
        var pagHtml = '<div class="pagination">';
        if (page > 1) pagHtml += '<a href="#" onclick="loadInventory(' + (page - 1) + ')">&laquo; 前へ</a>';
        pagHtml += ' ページ ' + page + ' / ' + totalPages + ' ';
        if (page < totalPages) pagHtml += '<a href="#" onclick="loadInventory(' + (page + 1) + ')">次へ &raquo;</a>';
        pagHtml += '</div>';
        document.getElementById('inventory-pagination').innerHTML = pagHtml;

        setStatus(data.total + '件の在庫データ');
    });
}

function searchInventory() {
    loadInventory(1);
}

function viewItem(id) {
    API.getItem(id, function(err, data) {
        if (err) return;
        var item = data.item;

        // VULN: XSS - all item fields rendered as raw HTML
        var html = '<h3>' + item.product_name + '</h3>';
        html += '<table>';
        html += '<tr><td>SKU</td><td>' + item.sku + '</td></tr>';
        html += '<tr><td>説明</td><td>' + (item.description || '-') + '</td></tr>';
        html += '<tr><td>カテゴリ</td><td>' + item.category + '</td></tr>';
        html += '<tr><td>数量</td><td>' + item.quantity + '</td></tr>';
        html += '<tr><td>単価</td><td>&yen;' + item.unit_price + '</td></tr>';
        html += '<tr><td>最小在庫</td><td>' + item.min_stock + '</td></tr>';
        html += '<tr><td>倉庫</td><td>' + (item.warehouse_name || '-') + '</td></tr>';
        html += '</table>';
        html += '<button onclick="showSection(\'inventory\')">戻る</button>';

        $('#inventory-table').html(html);
    });
}

function deleteItem(id) {
    // VULN: No CSRF token, no confirmation dialog
    if (!confirm('本当に削除しますか？')) return;

    API.deleteItem(id, function(err) {
        if (err) {
            alert('削除に失敗しました');
            return;
        }
        loadInventory(currentPage);
        setStatus('アイテムを削除しました');
    });
}

// ========== Warehouses ==========

function loadWarehouses() {
    setStatus('倉庫データを読み込み中...');

    API.getWarehouses(function(err, data) {
        if (err) {
            $('#warehouses-table').html('<p class="error">データの読み込みに失敗しました</p>');
            return;
        }

        var html = '<table>';
        html += '<tr><th>ID</th><th>名称</th><th>所在地</th><th>管理者</th><th>アイテム数</th><th>総在庫数</th><th>操作</th></tr>';

        for (var i = 0; i < data.warehouses.length; i++) {
            var wh = data.warehouses[i];
            // VULN: XSS via warehouse name/location
            html += '<tr>';
            html += '<td>' + wh.id + '</td>';
            html += '<td class="clickable" onclick="viewWarehouse(' + wh.id + ')">' + wh.name + '</td>';
            html += '<td>' + (wh.location || '-') + '</td>';
            html += '<td>' + (wh.manager_name || '-') + '</td>';
            html += '<td>' + wh.item_count + '</td>';
            html += '<td>' + wh.total_stock + '</td>';
            html += '<td><a href="#" onclick="exportWarehouse(' + wh.id + ')">CSV出力</a></td>';
            html += '</tr>';
        }

        html += '</table>';
        document.getElementById('warehouses-table').innerHTML = html;
        setStatus(data.warehouses.length + '件の倉庫');
    });
}

function viewWarehouse(id) {
    setStatus('倉庫詳細を読み込み中...');
    // VULN: IDOR - no auth check, any warehouse accessible
    API.getWarehouse(id, function(err, data) {
        if (err) return;

        var wh = data.warehouse;
        // VULN: XSS - unescaped HTML
        var html = '<p>所在地: ' + (wh.location || '-') + '</p>';
        html += '<p>管理者: ' + (wh.manager_name || '-') + ' (' + (wh.manager_email || '') + ')</p>';
        html += '<p>容量: ' + wh.capacity + '</p>';

        html += '<h3>在庫</h3><table>';
        html += '<tr><th>SKU</th><th>商品名</th><th>カテゴリ</th><th>数量</th><th>単価</th></tr>';
        for (var i = 0; i < data.inventory.length; i++) {
            var item = data.inventory[i];
            html += '<tr><td>' + item.sku + '</td><td>' + item.product_name + '</td>';
            html += '<td>' + item.category + '</td><td>' + item.quantity + '</td>';
            html += '<td>&yen;' + item.unit_price + '</td></tr>';
        }
        html += '</table>';

        html += '<h3>最近の入出庫</h3><table>';
        html += '<tr><th>種別</th><th>商品</th><th>数量</th><th>備考</th><th>日時</th></tr>';
        for (var j = 0; j < data.recent_movements.length; j++) {
            var mov = data.recent_movements[j];
            html += '<tr>';
            html += '<td>' + (mov.movement_type === 'IN' ? '入庫' : '出庫') + '</td>';
            html += '<td>' + mov.product_name + '</td>';
            html += '<td>' + mov.quantity + '</td>';
            html += '<td>' + (mov.notes || '-') + '</td>';
            html += '<td>' + mov.created_at + '</td>';
            html += '</tr>';
        }
        html += '</table>';

        html += '<br><button onclick="showSection(\'warehouses\')">倉庫一覧に戻る</button>';

        $('#warehouse-detail-title').text('倉庫詳細: ' + wh.name);
        document.getElementById('warehouse-detail-content').innerHTML = html;
        $('.section').hide();
        $('#warehouse-detail-section').show();
        setStatus('倉庫: ' + wh.name);
    });
}

function exportWarehouse(id) {
    API.exportWarehouse(id);
    setStatus('CSVエクスポート中...');
}

// ========== Reports ==========

function loadReports() {
    setStatus('レポートを読み込み中...');

    API.getSummary(function(err, data) {
        if (err) {
            $('#reports-content').html('<p class="error">レポートの読み込みに失敗しました</p>');
            return;
        }

        var html = '<h3>在庫サマリ</h3>';
        html += '<div>';
        if (data.totals) {
            html += '<div class="summary-card"><div class="value">' + (data.totals.total_items || 0) + '</div><div class="label">総アイテム数</div></div>';
            html += '<div class="summary-card"><div class="value">' + (data.totals.total_quantity || 0) + '</div><div class="label">総在庫数</div></div>';
            html += '<div class="summary-card"><div class="value">&yen;' + Math.round(data.totals.total_value || 0).toLocaleString() + '</div><div class="label">総在庫金額</div></div>';
        }
        html += '</div>';

        html += '<h3 style="margin-top:15px;">倉庫別</h3>';
        html += '<table>';
        html += '<tr><th>倉庫</th><th>アイテム数</th><th>総数量</th><th>在庫金額</th><th>在庫不足</th></tr>';
        for (var i = 0; i < data.warehouses.length; i++) {
            var wh = data.warehouses[i];
            html += '<tr>';
            html += '<td>' + wh.warehouse_name + '</td>';
            html += '<td>' + wh.item_count + '</td>';
            html += '<td>' + (wh.total_quantity || 0) + '</td>';
            html += '<td>&yen;' + Math.round(wh.total_value || 0).toLocaleString() + '</td>';
            html += '<td' + (wh.low_stock_count > 0 ? ' class="low-stock"' : '') + '>' + wh.low_stock_count + '</td>';
            html += '</tr>';
        }
        html += '</table>';

        // VULN: innerHTML with data from API
        document.getElementById('reports-content').innerHTML = html;
        setStatus('レポート読み込み完了');
    });
}

// Keyboard shortcut
$(document).keydown(function(e) {
    if (e.key === 'F5') {
        e.preventDefault();
        if (currentSection === 'inventory') loadInventory(currentPage);
        if (currentSection === 'warehouses') loadWarehouses();
        if (currentSection === 'reports') loadReports();
        setStatus('データを更新しました');
    }
});

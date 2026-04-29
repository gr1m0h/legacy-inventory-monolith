var express = require('express');
var bodyParser = require('body-parser');
var cors = require('cors');
var request = require('request');
var path = require('path');
var ejs = require('ejs');
var cookieParser = require('cookie-parser');

var app = express();

// VULN: CORS wide open - allows any origin
app.use(cors({ origin: '*', credentials: true }));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(cookieParser());

// VULN: Using very old helmet with minimal protection
var helmet = require('helmet');
app.use(helmet());

// View engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// VULN: Hardcoded backend URL
var BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000';

// VULN: Logging all requests including sensitive data
app.use(function(req, res, next) {
    console.log('[' + new Date().toISOString() + '] ' + req.method + ' ' + req.url);
    if (req.body && Object.keys(req.body).length > 0) {
        // VULN: Logs request body which may contain passwords
        console.log('  Body:', JSON.stringify(req.body));
    }
    next();
});

// API Proxy - forwards all /api requests to backend
// VULN: No request validation, no rate limiting
app.use('/api', function(req, res) {
    var url = BACKEND_URL + req.originalUrl;
    var options = {
        url: url,
        method: req.method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': req.headers.authorization || ''
        },
        // VULN: No timeout configuration - can hang indefinitely
        json: req.body || true
    };

    // VULN: Proxies without any security checks
    request(options, function(error, response, body) {
        if (error) {
            console.error('Proxy error:', error);
            return res.status(502).json({ error: 'Backend unavailable', details: error.message });
        }
        res.status(response.statusCode).json(body);
    });
});

// Main page
app.get('/', function(req, res) {
    res.render('layout', {
        title: 'Legacy Inventory Management System',
        backendUrl: BACKEND_URL
    });
});

// VULN: Error handler exposes stack trace
app.use(function(err, req, res, next) {
    console.error('Unhandled error:', err.stack);
    res.status(500).json({
        error: 'Internal server error',
        stack: err.stack  // VULN: Stack trace in response
    });
});

var PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', function() {
    console.log('Frontend server running on port ' + PORT);
    console.log('Backend URL: ' + BACKEND_URL);
});

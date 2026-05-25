const API_ENDPOINTS = {
    health: "/api/health",
    networkSummary: "/api/network-summary",
    routeStations: "/api/stations",
    stationCatalog: "/api/station_list",
    edgeList: "/api/edge_list",
    findPath: "/api/find-path",
};

const STORAGE_KEYS = {
    role: "metro_user_role",
    username: "metro_username",
    blockedNodes: "metro_blocked_nodes",
    blockedEdges: "metro_blocked_edges",
    routeHistory: "metro_route_history",
};

let isLoginMode = true;

function toggleAuthMode() {
    isLoginMode = !isLoginMode;

    const title = document.getElementById("authTitle");
    const button = document.getElementById("authBtn");
    const toggleText = document.getElementById("authToggleText");

    if (!title || !button || !toggleText) {
        return;
    }

    title.innerText = isLoginMode ? "Đăng nhập hệ thống" : "Tạo tài khoản nhanh";
    button.innerText = isLoginMode ? "Đăng nhập" : "Đăng ký";
    toggleText.innerText = isLoginMode ? "Chưa có tài khoản? Đăng ký ngay" : "Đã có tài khoản? Đăng nhập";
}

function handleAuth(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username) {
        return;
    }

    if (username === "admin" && password === "admin12321") {
        localStorage.setItem(STORAGE_KEYS.role, "admin");
        localStorage.setItem(STORAGE_KEYS.username, "Administrator");
        window.location.href = "admin.html";
        return;
    }

    localStorage.setItem(STORAGE_KEYS.role, "user");
    localStorage.setItem(STORAGE_KEYS.username, username);
    window.location.href = "map.html";
}

function checkAlreadyLoggedIn() {
    const role = localStorage.getItem(STORAGE_KEYS.role);
    if (role === "admin") {
        window.location.href = "admin.html";
    } else if (role === "user") {
        window.location.href = "map.html";
    }
}

function requireAuth(allowedRole = null) {
    const role = localStorage.getItem(STORAGE_KEYS.role);
    if (!role) {
        window.location.href = "index.html";
        return null;
    }

    if (allowedRole && role !== allowedRole) {
        window.location.href = role === "admin" ? "admin.html" : "map.html";
        return null;
    }

    return localStorage.getItem(STORAGE_KEYS.username);
}

function getCurrentUsername() {
    return localStorage.getItem(STORAGE_KEYS.username) || "Guest";
}

function isAuthenticated() {
    return Boolean(localStorage.getItem(STORAGE_KEYS.role));
}

function logout() {
    localStorage.removeItem(STORAGE_KEYS.role);
    localStorage.removeItem(STORAGE_KEYS.username);
    window.location.href = "index.html";
}

function getBlockedConfig() {
    return {
        blockedNodes: JSON.parse(localStorage.getItem(STORAGE_KEYS.blockedNodes) || "[]"),
        blockedEdges: JSON.parse(localStorage.getItem(STORAGE_KEYS.blockedEdges) || "[]"),
    };
}

function saveBlockedConfig(config) {
    localStorage.setItem(STORAGE_KEYS.blockedNodes, JSON.stringify(config.blockedNodes || []));
    localStorage.setItem(STORAGE_KEYS.blockedEdges, JSON.stringify(config.blockedEdges || []));
}

function saveRouteHistory(entry) {
    const history = JSON.parse(localStorage.getItem(STORAGE_KEYS.routeHistory) || "[]");
    history.unshift(entry);
    localStorage.setItem(STORAGE_KEYS.routeHistory, JSON.stringify(history.slice(0, 12)));
}

async function fetchJson(url, options = {}) {
    let response;
    try {
        response = await fetch(url, options);
    } catch (networkErr) {
        throw new Error(`Không kết nối được server (${networkErr.message}). Hãy chạy: python run.py`);
    }

    let payload = null;
    try {
        payload = await response.json();
    } catch (_) {
        payload = null;
    }

    if (!response.ok) {
        const message = payload?.detail || payload?.error || `HTTP ${response.status} ${response.statusText}`;
        throw new Error(message);
    }

    return payload;
}

function dedupe(items) {
    return [...new Set(items)];
}

function formatNumber(value) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return "--";
    }
    return new Intl.NumberFormat("vi-VN").format(Number(value));
}

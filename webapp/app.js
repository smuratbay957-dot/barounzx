const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
const API_BASE = "https://zxmax.pythonanywhere.com";
const TOKEN_KEY = "barounzx_webapp_token";

let token = localStorage.getItem(TOKEN_KEY) || "";
let state = null;
let shopItems = [];
let spinning = false;

const $ = (id) => document.getElementById(id);

function toast(message) {
    const el = $("toast");
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.classList.remove("show"), 2400);
}

function haptic(type) {
    if (tg && tg.HapticFeedback && tg.HapticFeedback.notificationOccurred) {
        tg.HapticFeedback.notificationOccurred(type);
    }
}

function applyTheme() {
    if (!tg || !tg.themeParams) return;
    const p = tg.themeParams;
    const s = document.documentElement.style;
    if (p.bg_color) s.setProperty("--bg", p.bg_color);
    if (p.text_color) s.setProperty("--text", p.text_color);
    if (p.hint_color) s.setProperty("--muted", p.hint_color);
    if (p.button_color) s.setProperty("--accent", p.button_color);
    if (p.secondary_bg_color) s.setProperty("--surface", p.secondary_bg_color);
}

async function api(path, body, method = "POST") {
    const url = API_BASE + path + (
        method === "GET" && body ? "?" + new URLSearchParams(body).toString() : ""
    );
    const options = { method, cache: "no-store" };
    if (method !== "GET") {
        options.headers = { "Content-Type": "application/json" };
        options.body = JSON.stringify(body || {});
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
    options.signal = controller.signal;
    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (err) {
        return null;
    } finally {
        clearTimeout(timer);
    }
}

function xpToNext(level) {
    return 100 + (Math.max(1, level) - 1) * 50;
}

function applyState(res) {
    if (!res) return;
    state = state || {};
    ["tg_id", "site_username", "coins", "skills", "xp", "level"].forEach((key) => {
        if (typeof res[key] !== "undefined") state[key] = res[key];
    });
    if (typeof res.streak === "number") state.streak = res.streak;
    render();
}

function render() {
    if (!state) return;
    const level = Math.max(1, state.level || 1);
    const xp = Math.max(0, state.xp || 0);
    const need = xpToNext(level);

    $("coins").textContent = state.coins || 0;
    $("sp").textContent = state.skills || 0;
    $("level").textContent = level;
    $("xpText").textContent = `${xp} / ${need} XP`;
    $("xpFill").style.width = `${Math.min(100, (xp / need) * 100)}%`;

    $("profName").textContent = state.site_username || "—";
    $("profTg").textContent = state.tg_id || "—";
    $("profSp").textContent = state.skills || 0;
    $("profXp").textContent = xp;
    $("profLevel").textContent = level;
    $("profCoins").textContent = state.coins || 0;
    $("profStreak").textContent = state.streak || 0;

    const user = tg && tg.initDataUnsafe ? tg.initDataUnsafe.user : null;
    const name = (user && (user.first_name || user.username)) || state.site_username || "Barounzx";
    $("userName").textContent = name;
    $("userSub").textContent = user && user.username ? "@" + user.username : "Telegram Web App";
    $("avatar").textContent = String(name).charAt(0).toUpperCase();

    $("dailyHint").textContent = state.streak
        ? `Seriya: ${state.streak} kun. Har kuni tanga va XP oling.`
        : "Har kuni tanga va XP oling.";
}

function renderShop() {
    const list = $("shopList");
    if (!shopItems.length) {
        list.innerHTML = '<div class="card"><p class="muted">Hozircha item yo\'q.</p></div>';
        return;
    }
    list.innerHTML = shopItems.map((item) => `
        <div class="shop-item">
            <div class="info">
                <b>${escapeHtml(item.name)}</b>
                <span>${escapeHtml(item.rarity || "common")} · ${item.stock} dona · +${item.skill_value} SP</span>
            </div>
            <button data-buy="${item.id}">${item.price} 🪙</button>
        </div>`).join("");
}

function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[ch]);
}

function handleResponse(res, message) {
    if (!res) {
        toast("Server bilan aloqa yo'q. Keyinroq urinib ko'ring.");
        haptic("error");
        return;
    }
    applyState(res);
    if (res.ok) {
        toast(typeof message === "function" ? message(res) : message);
        haptic("success");
    } else {
        toast(res.error === "already"
            ? "Bugunlik bonusni allaqachon oldingiz."
            : (res.error === "no_money"
                ? "Tangalar yetarli emas."
                : (res.error === "no_sp"
                    ? "SP yo'q. Bot orqali SP yig'ing."
                    : "Xatolik yuz berdi.")));
        haptic("error");
    }
}

async function authenticate() {
    const initData = tg ? tg.initData : new URLSearchParams(location.search).get("initData");
    if (!initData) {
        $("loginGate").hidden = false;
        $("main").hidden = true;
        return;
    }
    const res = await api("/api/webapp/auth", { init_data: initData });
    if (res && res.ok && res.token) {
        token = res.token;
        localStorage.setItem(TOKEN_KEY, token);
        applyState(res);
        await Promise.all([refresh(), loadShop()]);
    } else {
        $("loginGate").hidden = false;
        $("main").hidden = true;
        toast("Telegram ma'lumotlari tasdiqlanmadi.");
    }
}

async function refresh() {
    if (!token || !state || !state.tg_id) return;
    const res = await api("/api/state", { token, tg_id: state.tg_id }, "GET");
    if (res && res.ok) applyState(res);
}

async function loadShop() {
    const res = await api("/api/items", null, "GET");
    if (res && res.ok) {
        shopItems = (res.items || []).filter((item) => item.active && item.stock > 0);
        renderShop();
    }
}

async function raiseSp() {
    if (!token || !state) return;
    const beforeXp = state.xp || 0;
    const res = await api("/api/raise", { token, tg_id: state.tg_id });
    handleResponse(res, (r) => `SP ko'tarildi: +${(r.xp || 0) - beforeXp} XP`);
}

async function claimDaily() {
    if (!token) return;
    const res = await api("/api/daily", { token });
    handleResponse(res, (r) => `Kunlik bonus: +${r.reward} tanga (seriya ${r.streak})`);
}

async function spin() {
    if (!token || spinning) return;
    spinning = true;
    $("spinBtn").disabled = true;
    const res = await api("/api/spin", { token });
    const wheel = $("wheel");
    wheel.style.transform = `rotate(${Math.floor(Math.random() * 5 + 5) * 360}deg)`;
    if (res && res.ok) {
        $("lotResult").textContent = `Yutdingiz: +${res.win} tanga!`;
    }
    handleResponse(res, (r) => `Super Lot: +${r.win} tanga!`);
    spinning = false;
    $("spinBtn").disabled = false;
    setTimeout(() => { $("lotResult").textContent = "Natija chiqadi"; }, 3500);
}

function setupEvents() {
    document.querySelectorAll(".tab").forEach((tab) => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
            tab.classList.add("active");
            $("tab-" + tab.dataset.tab).classList.add("active");
            if (tg && tg.HapticFeedback && tg.HapticFeedback.impactOccurred) {
                tg.HapticFeedback.impactOccurred("light");
            }
        });
    });

    $("raiseBtn").addEventListener("click", raiseSp);
    $("dailyBtn").addEventListener("click", claimDaily);
    $("spinBtn").addEventListener("click", spin);
    $("refreshBtn").addEventListener("click", async () => {
        await refresh();
        toast("Yangilandi.");
    });
    $("closeBtn").addEventListener("click", () => {
        if (tg) tg.close();
        else location.href = "https://t.me/zxmaxbot";
    });
    $("shopList").addEventListener("click", async (event) => {
        const btn = event.target.closest("[data-buy]");
        if (!btn) return;
        const res = await api("/api/buy", { token, item_id: Number(btn.dataset.buy) });
        handleResponse(res, (r) => `Sotib olindi: +${r.gained} SP`);
        await loadShop();
    });
}

async function init() {
    applyTheme();
    setupEvents();
    if (tg) {
        tg.ready();
        tg.expand();
    }
    await authenticate();
    setInterval(() => {
        if (!document.hidden && token) refresh();
    }, 15000);
}

init();

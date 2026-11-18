"use strict";

/* ============================================================
   Barounzx - o'yin platformasi
   - Hisoblar (ism + parol), ism takrorlanmaydi (case-insensitive)
   - Gmail ulash + 6 xonali kod orqali parolni tiklash
   - SP yig'ish: 1 SP = 20 XP
   - Telegram ulash (kod orqali) + SP/XP sinxron
   Tarmoq bo'lmasa hammasi localStorage'da offline ishlaydi.
   ============================================================ */

const STORE_KEY = "barounzx_v2";
const API_BASE = "https://zxmax.pythonanywhere.com";
const SPIN_COST = 50;
const DAILY_BONUS = 75;
const XP_PER_SKILL = 20;
const CODE_TTL = 5 * 60 * 1000;

const SKILL_CATEGORIES = [
    { id: "logic", name: "Mantiq", letter: "M" },
    { id: "speed", name: "Tezlik", letter: "T" },
    { id: "power", name: "Kuch", letter: "K" },
    { id: "focus", name: "Diqqat", letter: "D" },
    { id: "luck", name: "Omad", letter: "O" },
    { id: "team", name: "Jamoa", letter: "J" }
];

const SHOP_ITEMS = [
    { id: "boost_xp", icon: "3", name: "XP Boost", desc: "Keyingi SP 2x XP beradi.", price: 120 },
    { id: "theme_pink", icon: "4", name: "Pushti mavzu", desc: "Orqa fon pushti bo'ladi.", price: 300 },
    { id: "theme_blue", icon: "5", name: "Moviy mavzu", desc: "Orqa fon moviy bo'ladi.", price: 300 },
    { id: "badge_gold", icon: "1", name: "Oltin nishon", desc: "Profil uchun oltin nishon.", price: 150 },
    { id: "skin_neon", icon: "2", name: "Neon teri", desc: "Yorqin neon ko'rinish.", price: 220 },
    { id: "crown", icon: "6", name: "Toj", desc: "Eng zo'r o'yinchilar uchun.", price: 500 }
];

const WHEEL_VALUES = [50, 10, 200, 25, 100, 5, 500, 75];

/* ---------- Saqlash ---------- */
let store = loadStore();
let pendingReset = null;
let wheelAngle = 0;
let spinning = false;
let linkPollTimer = null;

function defaultStore() {
    return { accounts: {}, current: null };
}

function loadStore() {
    try {
        const raw = localStorage.getItem(STORE_KEY);
        if (!raw) return defaultStore();
        const parsed = JSON.parse(raw);
        return Object.assign(defaultStore(), parsed);
    } catch (err) {
        return defaultStore();
    }
}

function saveStore() {
    try {
        localStorage.setItem(STORE_KEY, JSON.stringify(store));
    } catch (err) {
        /* localStorage mavjud bo'lmasa jim */
    }
}

function newAccount(username, passHash, salt, email) {
    return {
        username: username,
        passHash: passHash,
        salt: salt,
        email: email || "",
        createdAt: Date.now(),
        level: 1,
        xp: 0,
        coins: 100,
        skillPoints: 0,
        raised: 0,
        owned: [],
        stats: { spins: 0, buys: 0, streak: 0 },
        lastBonus: "",
        theme: "default",
        boost: false,
        tgId: null,
        tgUsername: "",
        siteToken: null,
        linkCode: null
    };
}

function getAcc() {
    return store.current ? store.accounts[store.current] : null;
}

/* ---------- Parol xeshlash ---------- */
function randomSalt() {
    if (window.crypto && crypto.getRandomValues) {
        const a = new Uint8Array(16);
        crypto.getRandomValues(a);
        return Array.from(a).map((b) => b.toString(16).padStart(2, "0")).join("");
    }
    return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function fallbackHash(str) {
    let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
    for (let i = 0; i < str.length; i++) {
        const ch = str.charCodeAt(i);
        h1 = Math.imul(h1 ^ ch, 2654435761);
        h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return (h2 >>> 0).toString(16).padStart(8, "0") + (h1 >>> 0).toString(16).padStart(8, "0");
}

async function hashPassword(password, salt) {
    const data = salt + "::" + password;
    if (window.crypto && crypto.subtle && window.TextEncoder) {
        try {
            const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(data));
            return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
        } catch (err) {
            /* file:// da crypto.subtle ishlamasligi mumkin */
        }
    }
    return fallbackHash(data);
}

/* ---------- Yordamchi ---------- */
const $ = (sel) => document.querySelector(sel);

function xpToNext(level) {
    return 100 + (level - 1) * 50;
}

function todayKey() {
    return new Date().toISOString().slice(0, 10);
}

function isEmail(v) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
}

function toast(message, type = "info") {
    const box = $("#toasts");
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.textContent = message;
    box.appendChild(el);
    setTimeout(() => {
        el.classList.add("leaving");
        setTimeout(() => el.remove(), 300);
    }, 2600);
}

function setError(msg) {
    const el = $("#authError");
    if (el) el.textContent = msg || "";
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[ch]));
}

/* ---------- Sayt <-> bot API ---------- */
function apiUrl(path) {
    return API_BASE.replace(/\/$/, "") + path;
}

async function apiGet(path) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 12000);
    try {
        const resp = await fetch(apiUrl(path), { signal: ctrl.signal, cache: "no-store" });
        return await resp.json();
    } finally {
        clearTimeout(timer);
    }
}

async function apiPost(path, body, timeout = 12000) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeout);
    try {
        const resp = await fetch(apiUrl(path), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body || {}),
            signal: ctrl.signal
        });
        return await resp.json();
    } finally {
        clearTimeout(timer);
    }
}

async function refreshServerState() {
    const acc = getAcc();
    if (!acc || !acc.tgId || !acc.siteToken) {
        renderSettings();
        return;
    }
    let res = null;
    try {
        res = await apiGet(`/api/state?tg_id=${encodeURIComponent(acc.tgId)}&token=${encodeURIComponent(acc.siteToken)}`);
    } catch (err) {
        res = null;
    }
    if (res && res.ok) {
        acc.skillPoints = res.skills;
        acc.xp = res.xp;
        acc.level = res.level;
        if (typeof res.coins === "number") acc.coins = res.coins;
        saveStore();
    }
    render();
}

function pushServerState(acc) {
    if (!acc || !acc.tgId || !acc.siteToken) return;
    apiPost("/api/state", {
        tg_id: acc.tgId,
        token: acc.siteToken,
        xp: acc.xp,
        level: acc.level
    }).catch(() => {});
}

async function startTelegramLink() {
    const acc = getAcc();
    if (!acc) {
        showView("login");
        return;
    }
    toast("Kod olinmoqda...");
    let res = null;
    try {
        res = await apiPost("/api/link/start", { username: acc.username });
    } catch (err) {
        res = null;
    }
    if (!res || !res.ok) {
        toast("Server bilan aloqa yo'q. Keyinroq urinib ko'ring.", "danger");
        return;
    }
    acc.linkCode = res.code;
    acc.siteToken = res.token;
    saveStore();
    renderSettings();
    toast(`Kod: ${res.code}`, "success");
    pollLinkStatus(res.code);
}

function pollLinkStatus(code) {
    if (linkPollTimer) clearTimeout(linkPollTimer);
    linkPollTimer = setTimeout(async () => {
        const acc = getAcc();
        if (!acc || acc.linkCode !== code) return;
        let res = null;
        try {
            res = await apiGet(`/api/link/status?code=${encodeURIComponent(code)}`);
        } catch (err) {
            res = null;
        }
        if (res && res.linked) {
            acc.tgId = res.tg_id;
            acc.tgUsername = res.tg_username || "";
            acc.siteToken = res.site_token || acc.siteToken;
            acc.linkCode = null;
            saveStore();
            try {
                await apiPost("/api/state", {
                    tg_id: acc.tgId,
                    token: acc.siteToken,
                    xp: acc.xp,
                    level: acc.level,
                    coins: acc.coins,
                    skills: acc.skillPoints
                });
            } catch (err) {
                /* server bo'lmasa lokal holat saqlanadi */
            }
            await refreshServerState();
            toast("✅ Telegram ulandi!", "success");
            return;
        }
        if (res && res.ok === false && res.error === "kod topilmadi") {
            acc.linkCode = null;
            saveStore();
            renderSettings();
            toast("Kod muddati tugadi. Yangi kod oling.", "danger");
            return;
        }
        pollLinkStatus(code);
    }, 2500);
}

async function unlinkTelegram() {
    const acc = getAcc();
    if (!acc) return;
    if (acc.tgId && acc.siteToken) {
        try {
            await apiPost("/api/unlink", { tg_id: acc.tgId, token: acc.siteToken });
        } catch (err) {
            /* tarmoq bo'lmasa ham lokal uzamiz */
        }
    }
    if (linkPollTimer) {
        clearTimeout(linkPollTimer);
        linkPollTimer = null;
    }
    acc.tgId = null;
    acc.tgUsername = "";
    acc.siteToken = null;
    acc.linkCode = null;
    saveStore();
    render();
    toast("Telegram uzildi.");
}

function renderSettings() {
    const card = $("#settingsCard");
    if (!card) return;
    const acc = getAcc();

    if (!acc) {
        card.innerHTML = `
            <div class="settings-row">
                <div>
                    <div class="settings-title">Telegram ulash</div>
                    <p class="muted small">Avval saytga kiring, so'ng Telegram hisobingizni ulang.</p>
                </div>
                <button class="btn btn-primary" data-action="login">Kirish</button>
            </div>`;
        return;
    }

    if (acc.tgId && acc.siteToken) {
        const who = acc.tgUsername ? "@" + escapeHtml(acc.tgUsername) : "ID " + escapeHtml(acc.tgId);
        card.innerHTML = `
            <div class="settings-row">
                <div>
                    <div class="settings-title">✅ Telegram ulangan</div>
                    <p class="muted small">${who} · SP: ${acc.skillPoints} · XP: ${acc.xp} · Level: ${acc.level}</p>
                </div>
                <div class="settings-actions">
                    <button class="btn btn-ghost" data-action="refresh">Yangilash</button>
                    <button class="btn btn-ghost" data-action="unlink">Uzish</button>
                </div>
            </div>`;
        return;
    }

    if (acc.linkCode) {
        card.innerHTML = `
            <div class="settings-row">
                <div>
                    <div class="settings-title">Telegram ulash</div>
                    <p class="muted small">Botga quyidagi kodni yuboring:</p>
                    <div class="link-code">${escapeHtml(acc.linkCode)}</div>
                    <p class="muted small">Buyruq: <code>/ulash ${escapeHtml(acc.linkCode)}</code> · 15 daqiqa amal qiladi</p>
                </div>
                <div class="settings-actions">
                    <button class="btn btn-ghost" data-action="regen">Yangi kod</button>
                    <button class="btn btn-ghost" data-action="cancel">Bekor qilish</button>
                </div>
            </div>`;
        return;
    }

    card.innerHTML = `
        <div class="settings-row">
            <div>
                <div class="settings-title">Telegram ulash</div>
                <p class="muted small">Kod oling, botga <code>/ulash kod</code> yuboring — SP va XP sinxron bo'ladi.</p>
            </div>
            <button class="btn btn-primary" data-action="link">Kod olish</button>
        </div>`;
}

/* ---------- Kod yuborish (offline demo) ---------- */
function generateCode() {
    return String(Math.floor(100000 + Math.random() * 900000));
}

function sendVerificationCode(email, code) {
    /* OFFLINE DEMO: haqiqiy Gmail yuborilmaydi.
       Kelajakda Python backend paydo bo'lganda shu yerga:
       return fetch("/api/send-code", {method:"POST", body: JSON.stringify({email, code})})
       yozamiz. Hozircha kod ekranda ko'rsatiladi. */
    console.log("[Barounzx] Tasdiqlash kodi ->", email, code);
    return { demo: true, code: code };
}

/* ============================================================
   Modal ko'rinishlari
   ============================================================ */
function openModal() {
    $("#modal").classList.add("open");
    $("#modal").setAttribute("aria-hidden", "false");
}

function closeModal() {
    $("#modal").classList.remove("open");
    $("#modal").setAttribute("aria-hidden", "true");
}

function showView(view) {
    const body = $("#modalBody");
    if (view === "login") body.innerHTML = viewLogin();
    else if (view === "register") body.innerHTML = viewRegister();
    else if (view === "forgot") body.innerHTML = viewForgot();
    else if (view === "verify") body.innerHTML = viewVerify();
    else if (view === "reset") body.innerHTML = viewReset();
    else if (view === "profile") body.innerHTML = viewProfile();
    openModal();
    wireView(view);
    const first = body.querySelector("input");
    if (first) setTimeout(() => first.focus(), 120);
}

function tabs(active) {
    return `
        <div class="auth-tabs">
            <button type="button" class="${active === "login" ? "active" : ""}" data-view="login">Kirish</button>
            <button type="button" class="${active === "register" ? "active" : ""}" data-view="register">Ro'yxatdan o'tish</button>
        </div>`;
}

function viewLogin() {
    return `
        ${tabs("login")}
        <h3>Hisobingizga kiring</h3>
        <p class="muted small">Ism va parolingizni kiriting.</p>
        <form id="loginForm" autocomplete="off">
            <label class="field"><span>Ism</span><input id="loginName" maxlength="16" placeholder="Masalan: Baron"></label>
            <label class="field"><span>Parol</span><input type="password" id="loginPass" placeholder="Parol"></label>
            <button class="btn btn-primary btn-block" type="submit">Kirish</button>
        </form>
        <div class="link-row">
            <button class="link-btn" data-view="forgot">Parolni unutdingizmi?</button>
        </div>
        <p class="error" id="authError"></p>`;
}

function viewRegister() {
    return `
        ${tabs("register")}
        <h3>Ro'yxatdan o'tish</h3>
        <p class="muted small">Ism band bo'lsa, boshqasi o'sha nomni olmaydi.</p>
        <form id="registerForm" autocomplete="off">
            <label class="field"><span>Ism</span><input id="regName" maxlength="16" placeholder="Masalan: Baron"></label>
            <label class="field"><span>Gmail</span><input type="email" id="regEmail" placeholder="ism@gmail.com"></label>
            <label class="field"><span>Parol</span><input type="password" id="regPass" placeholder="Kamida 6 belgi"></label>
            <label class="field"><span>Parolni tasdiqlang</span><input type="password" id="regPass2" placeholder="Yana bir marta"></label>
            <p class="hint">Parol parolni tiklash uchun Gmail'ga bog'lanadi.</p>
            <button class="btn btn-primary btn-block" type="submit">Ro'yxatdan o'tish</button>
        </form>
        <p class="error" id="authError"></p>`;
}

function viewForgot() {
    return `
        <h3>Parolni tiklash</h3>
        <p class="muted small">Ismingizni kiriting, ulangan Gmail'ga 6 xonali kod yuboramiz.</p>
        <form id="forgotForm" autocomplete="off">
            <label class="field"><span>Ism</span><input id="forgotName" maxlength="16" placeholder="Ismingiz"></label>
            <button class="btn btn-primary btn-block" type="submit">Kod yuborish</button>
        </form>
        <div class="link-row"><button class="link-btn" data-view="login">Kirishga qaytish</button></div>
        <p class="error" id="authError"></p>`;
}

function viewVerify() {
    const email = pendingReset ? pendingReset.email : "";
    const demo = pendingReset ? pendingReset.demoCode : "";
    return `
        <h3>Kodni kiriting</h3>
        <p class="muted small">Kod <strong>${email}</strong> manziliga yuborildi.</p>
        <div class="info-box warn">
            Demo rejim (offline): haqiqiy Gmail yuborilmaydi.<br>
            Tasdiqlash kodi: <code>${demo}</code>
        </div>
        <form id="verifyForm" autocomplete="off">
            <label class="field"><span>6 xonali kod</span>
                <input id="codeInput" class="code-input" maxlength="6" inputmode="numeric" placeholder="000000">
            </label>
            <button class="btn btn-primary btn-block" type="submit">Tasdiqlash</button>
        </form>
        <div class="link-row"><button class="link-btn" data-view="forgot">Boshqa kod olish</button></div>
        <p class="error" id="authError"></p>`;
}

function viewReset() {
    return `
        <h3>Yangi parol o'rnatish</h3>
        <p class="muted small">Yangi parolingizni kiriting.</p>
        <form id="resetForm" autocomplete="off">
            <label class="field"><span>Yangi parol</span><input type="password" id="newPass" placeholder="Kamida 6 belgi"></label>
            <label class="field"><span>Tasdiqlang</span><input type="password" id="newPass2" placeholder="Yana bir marta"></label>
            <button class="btn btn-primary btn-block" type="submit">Parolni saqlash</button>
        </form>
        <p class="error" id="authError"></p>`;
}

function viewProfile() {
    const acc = getAcc();
    if (!acc) return viewLogin();
    const email = acc.email || "Ulanmagan";
    return `
        <h3>Profil</h3>
        <div class="profile-row">
            <div><div class="profile-label">Ism</div><div class="profile-value">${acc.username}</div></div>
            <div class="profile-value grad">Level ${acc.level}</div>
        </div>
        <div class="profile-row">
            <div><div class="profile-label">Gmail</div><div class="profile-value">${email}</div></div>
            <div class="profile-value">${acc.skillPoints} SP</div>
        </div>
        <div class="profile-row">
            <div><div class="profile-label">Telegram</div>
                <div class="profile-value">${acc.tgId ? (acc.tgUsername ? "@" + escapeHtml(acc.tgUsername) : "ID " + escapeHtml(acc.tgId)) : "ulanmagan"}</div></div>
            <div class="profile-value">${acc.xp} XP</div>
        </div>
        <div class="divider"></div>
        <form id="emailForm" autocomplete="off">
            <label class="field"><span>Gmail ulash / o'zgartirish</span>
                <input type="email" id="profileEmail" placeholder="ism@gmail.com" value="${acc.email || ""}">
            </label>
            <button class="btn btn-ghost btn-block" type="submit">Emailni saqlash</button>
        </form>
        <div class="divider"></div>
        <form id="changePassForm" autocomplete="off">
            <label class="field"><span>Hozirgi parol</span><input type="password" id="curPass"></label>
            <label class="field"><span>Yangi parol</span><input type="password" id="newPassP"></label>
            <button class="btn btn-primary btn-block" type="submit">Parolni o'zgartirish</button>
        </form>
        <p class="error" id="authError"></p>
        <div class="profile-actions">
            <button class="btn btn-ghost btn-block" id="logoutBtn">Hisobdan chiqish</button>
        </div>`;
}

/* ---------- Ko'rinishlarni ulash ---------- */
function wireView(view) {
    const body = $("#modalBody");

    body.querySelectorAll("[data-view]").forEach((btn) => {
        btn.addEventListener("click", () => {
            setError("");
            showView(btn.dataset.view);
        });
    });

    if (view === "login") {
        $("#loginForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            await doLogin($("#loginName").value.trim(), $("#loginPass").value);
        });
    } else if (view === "register") {
        $("#registerForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            await doRegister(
                $("#regName").value.trim(),
                $("#regEmail").value.trim(),
                $("#regPass").value,
                $("#regPass2").value
            );
        });
    } else if (view === "forgot") {
        $("#forgotForm").addEventListener("submit", (e) => {
            e.preventDefault();
            doForgot($("#forgotName").value.trim());
        });
    } else if (view === "verify") {
        const ci = $("#codeInput");
        ci.addEventListener("input", () => { ci.value = ci.value.replace(/\D/g, "").slice(0, 6); });
        $("#verifyForm").addEventListener("submit", (e) => {
            e.preventDefault();
            doVerify(ci.value.trim());
        });
    } else if (view === "reset") {
        $("#resetForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            await doReset($("#newPass").value, $("#newPass2").value);
        });
    } else if (view === "profile") {
        $("#emailForm").addEventListener("submit", (e) => {
            e.preventDefault();
            saveEmail($("#profileEmail").value.trim());
        });
        $("#changePassForm").addEventListener("submit", async (e) => {
            e.preventDefault();
            await changePassword($("#curPass").value, $("#newPassP").value);
        });
        $("#logoutBtn").addEventListener("click", logout);
    }
}

/* ---------- Auth amallari ---------- */
async function doRegister(name, email, pass, pass2) {
    setError("");
    if (name.length < 3) return setError("Ism kamida 3 ta belgidan iborat bo'lishi kerak.");
    if (!/^[A-Za-z0-9_ ]+$/.test(name)) return setError("Faqat harf, raqam va _ ishlatiladi.");
    if (!isEmail(email)) return setError("To'g'ri Gmail manzilini kiriting.");
    if (pass.length < 6) return setError("Parol kamida 6 ta belgi bo'lishi kerak.");
    if (pass !== pass2) return setError("Parollar mos kelmadi.");

    const key = name.toLowerCase();
    if (store.accounts[key]) return setError(`"${name}" ismi band. Boshqa nom tanlang.`);

    const salt = randomSalt();
    const passHash = await hashPassword(pass, salt);
    store.accounts[key] = newAccount(name, passHash, salt, email);
    store.current = key;
    saveStore();
    render();
    closeModal();
    toast(`Xush kelibsiz, ${name}!`, "success");
    refreshServerState();
}

async function doLogin(name, pass) {
    setError("");
    if (!name || !pass) return setError("Ism va parolni kiriting.");
    const acc = store.accounts[name.toLowerCase()];
    if (!acc) return setError("Bunday ism topilmadi.");
    const hash = await hashPassword(pass, acc.salt);
    if (hash !== acc.passHash) return setError("Parol xato.");
    store.current = name.toLowerCase();
    saveStore();
    render();
    closeModal();
    toast(`Xush kelibsiz, ${acc.username}!`, "success");
    refreshServerState();
}

function doForgot(name) {
    setError("");
    if (!name) return setError("Ismingizni kiriting.");
    const acc = store.accounts[name.toLowerCase()];
    if (!acc) return setError("Bunday ism topilmadi.");
    if (!acc.email) return setError("Bu hisobga Gmail ulanmagan. Profil orqali ulang.");

    const code = generateCode();
    const result = sendVerificationCode(acc.email, code);
    pendingReset = {
        key: name.toLowerCase(),
        email: acc.email,
        code: code,
        demoCode: result && result.demo ? result.code : "",
        expires: Date.now() + CODE_TTL
    };
    showView("verify");
    toast("Kod yuborildi (demo).", "success");
}

function doVerify(code) {
    setError("");
    if (!pendingReset) return showView("forgot");
    if (Date.now() > pendingReset.expires) {
        pendingReset = null;
        showView("forgot");
        return toast("Kod muddati tugadi. Qayta oling.", "danger");
    }
    if (code.length !== 6) return setError("6 xonali kodni kiriting.");
    if (code !== pendingReset.code) return setError("Kod noto'g'ri.");
    showView("reset");
}

async function doReset(pass, pass2) {
    setError("");
    if (!pendingReset) return showView("forgot");
    if (pass.length < 6) return setError("Parol kamida 6 ta belgi bo'lishi kerak.");
    if (pass !== pass2) return setError("Parollar mos kelmadi.");

    const acc = store.accounts[pendingReset.key];
    if (!acc) return showView("login");

    acc.salt = randomSalt();
    acc.passHash = await hashPassword(pass, acc.salt);
    saveStore();
    pendingReset = null;
    closeModal();
    toast("Parol yangilandi. Endi kiring.", "success");
    showView("login");
}

async function changePassword(cur, next) {
    setError("");
    const acc = getAcc();
    if (!acc) return;
    const curHash = await hashPassword(cur, acc.salt);
    if (curHash !== acc.passHash) return setError("Hozirgi parol xato.");
    if (next.length < 6) return setError("Yangi parol kamida 6 ta belgi.");
    acc.salt = randomSalt();
    acc.passHash = await hashPassword(next, acc.salt);
    saveStore();
    setError("");
    toast("Parol o'zgartirildi.", "success");
    $("#changePassForm").reset();
}

function saveEmail(email) {
    setError("");
    const acc = getAcc();
    if (!acc) return;
    if (!isEmail(email)) return setError("To'g'ri Gmail manzilini kiriting.");
    acc.email = email;
    saveStore();
    toast("Gmail saqlandi.", "success");
    showView("profile");
}

function logout() {
    if (linkPollTimer) {
        clearTimeout(linkPollTimer);
        linkPollTimer = null;
    }
    store.current = null;
    saveStore();
    render();
    closeModal();
    toast("Hisobdan chiqdingiz.");
}

/* ============================================================
   O'yin logikasi
   ============================================================ */
async function changeCoins(acc, delta) {
    if (!acc || !delta) return acc ? acc.coins : 0;
    if (acc.tgId && acc.siteToken) {
        try {
            const res = await apiPost("/api/coins", {
                tg_id: acc.tgId,
                token: acc.siteToken,
                delta: delta
            }, 5000);
            if (res && res.ok && typeof res.coins === "number") {
                acc.coins = res.coins;
                return acc.coins;
            }
        } catch (err) {
            /* tarmoq yo'q — lokal hisoblash */
        }
    }
    acc.coins = Math.max(0, acc.coins + delta);
    return acc.coins;
}

async function gainXp(acc, amount, rewardCoins = true) {
    acc.xp += amount;
    let leveled = false;
    while (acc.xp >= xpToNext(acc.level)) {
        acc.xp -= xpToNext(acc.level);
        acc.level += 1;
        leveled = true;
        const reward = 25 + acc.level * 10;
        if (rewardCoins) await changeCoins(acc, reward);
        toast(rewardCoins
            ? `Level ${acc.level}! +${reward} tanga`
            : `Level ${acc.level}!`, "success");
    }
    if (leveled) {
        document.body.classList.add("levelup-flash");
        setTimeout(() => document.body.classList.remove("levelup-flash"), 600);
    }
    pushServerState(acc);
}

function addSkillPoints(acc, count) {
    count = Math.max(1, parseInt(count, 10) || 1);
    acc.skillPoints += count;
    return count;
}

async function raiseSkill() {
    const acc = getAcc();
    if (!acc) {
        toast("SP ko'tarish uchun avval kiring.", "danger");
        showView("login");
        return;
    }

    if (acc.tgId && acc.siteToken) {
        const beforeLevel = acc.level;
        let res = null;
        try {
            res = await apiPost("/api/raise", { tg_id: acc.tgId, token: acc.siteToken });
        } catch (err) {
            res = null;
        }
        if (res && res.ok) {
            const boosted = !!acc.boost;
            const gained = boosted ? XP_PER_SKILL * 2 : XP_PER_SKILL;
            acc.skillPoints = res.skills;
            let newXp = res.xp;
            let newLevel = res.level;
            if (boosted) {
                acc.boost = false;
                newXp += XP_PER_SKILL;
                while (newXp >= xpToNext(newLevel)) {
                    newXp -= xpToNext(newLevel);
                    newLevel += 1;
                }
            }
            acc.xp = newXp;
            acc.level = newLevel;
            if (newLevel > beforeLevel) {
                let reward = 0;
                for (let lv = beforeLevel + 1; lv <= newLevel; lv++) reward += 25 + lv * 10;
                await changeCoins(acc, reward);
                toast(`Level ${newLevel}! +${reward} tanga`, "success");
                document.body.classList.add("levelup-flash");
                setTimeout(() => document.body.classList.remove("levelup-flash"), 600);
            }
            saveStore();
            render();
            if (newXp !== res.xp || newLevel !== res.level) pushServerState(acc);
            toast(`SP ko'tarildi: +${gained} XP`, "success");
            return;
        }
        if (res) {
            if (typeof res.skills === "number") acc.skillPoints = Math.max(0, res.skills);
            saveStore();
            render();
            toast(res.error === "no_sp"
                ? "SP yo'q. Bot orqali SP yig'ing."
                : "Server xatosi. Qayta urinib ko'ring.", "danger");
            return;
        }
        toast("Server bilan aloqa yo'q — offline hisoblandi.", "danger");
    }

    if (acc.skillPoints <= 0) {
        toast("SP yo'q. Bot orqali SP yig'ing.", "danger");
        return;
    }
    const mult = acc.boost ? 2 : 1;
    if (acc.boost) acc.boost = false;
    acc.skillPoints -= 1;
    acc.raised += 1;
    await gainXp(acc, XP_PER_SKILL * mult);
    saveStore();
    render();
    toast(`SP ko'tarildi: +${XP_PER_SKILL * mult} XP`, "success");
}

async function buy(itemId) {
    const acc = getAcc();
    if (!acc) { toast("Avval kiring.", "danger"); showView("login"); return; }
    const item = SHOP_ITEMS.find((i) => i.id === itemId);
    if (!item || acc.owned.includes(itemId)) return;
    if (acc.coins < item.price) { toast("Tangalar yetarli emas!", "danger"); return; }
    await changeCoins(acc, -item.price);
    acc.owned.push(itemId);
    acc.stats.buys += 1;
    if (itemId === "boost_xp") acc.boost = true;
    if (itemId === "theme_pink") applyTheme("pink");
    if (itemId === "theme_blue") applyTheme("blue");
    await gainXp(acc, 15);
    saveStore();
    render();
    toast(`${item.name} sotib olindi!`, "gold");
}

function applyTheme(theme) {
    const colors = { default: "#070a12", pink: "#1a0714", blue: "#04101f" };
    document.documentElement.style.setProperty("--bg", colors[theme] || colors.default);
    const acc = getAcc();
    if (acc) { acc.theme = theme; saveStore(); }
}

async function spin() {
    const acc = getAcc();
    if (!acc) { toast("Avval kiring.", "danger"); showView("login"); return; }
    if (spinning) return;
    if (acc.coins < SPIN_COST) { toast("Spin uchun 50 tanga kerak!", "danger"); return; }

    spinning = true;
    $("#spinBtn").disabled = true;
    await changeCoins(acc, -SPIN_COST);
    acc.stats.spins += 1;
    saveStore();
    render();

    const index = Math.floor(Math.random() * WHEEL_VALUES.length);
    const seg = 360 / WHEEL_VALUES.length;
    const targetCenter = index * seg + seg / 2;
    const desiredMod = (360 - (targetCenter % 360)) % 360;
    let final = wheelAngle + 5 * 360;
    final = final - (final % 360) + desiredMod;
    wheelAngle = final;
    $("#wheel").style.transform = `rotate(${final}deg)`;
    $("#lotResult").textContent = "Aylanmoqda...";

    setTimeout(async () => {
        const value = WHEEL_VALUES[index];
        await changeCoins(acc, value);
        await gainXp(acc, 20);
        saveStore();
        $("#lotResult").textContent = `Yutdingiz: +${value} tanga!`;
        toast(`Super Lot: +${value} tanga!`, "gold");
        spinning = false;
        $("#spinBtn").disabled = false;
        render();
    }, 4100);
}

async function claimDaily() {
    const acc = getAcc();
    if (!acc) { toast("Avval kiring.", "danger"); showView("login"); return; }
    if (acc.lastBonus === todayKey()) { toast("Bugun bonusni olgansiz.", "danger"); return; }
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    acc.stats.streak = acc.lastBonus === yesterday ? acc.stats.streak + 1 : 1;
    acc.lastBonus = todayKey();
    const reward = Math.min(acc.stats.streak, 4);
    await changeCoins(acc, reward);
    await gainXp(acc, 10, false);
    saveStore();
    render();
    toast(`Kunlik bonus: +${reward} tanga, +10 XP (seriya ${acc.stats.streak})`, "gold");
}

/* ============================================================
   Render
   ============================================================ */
function render() {
    const acc = getAcc();
    const level = acc ? acc.level : 1;
    const xp = acc ? acc.xp : 0;
    const coins = acc ? acc.coins : 0;
    const need = xpToNext(level);
    const pct = Math.min(100, (xp / need) * 100);
    const offset = 326.7 - (326.7 * pct) / 100;

    $("#heroRingFill").style.strokeDashoffset = offset;
    $("#levelRingFill").style.strokeDashoffset = offset;
    $("#heroRingLevel").textContent = level;
    $("#levelRingLevel").textContent = level;
    $("#xpBarFill").style.width = pct + "%";
    $("#xpCurrent").textContent = xp + " XP";
    $("#xpNeeded").textContent = need + " XP";
    $("#heroNextXp").textContent = (need - xp) + " XP";

    $("#heroLevel").textContent = level;
    $("#heroXp").textContent = xp;
    $("#heroCoins").textContent = coins;
    $("#coinCount").textContent = coins;

    $("#skillTotal").textContent = acc ? acc.skillPoints : 0;
    $("#statSkills").textContent = acc ? acc.skillPoints : 0;
    $("#statSpins").textContent = acc ? acc.stats.spins : 0;
    $("#statBuys").textContent = acc ? acc.stats.buys : 0;
    $("#statStreak").textContent = acc ? acc.stats.streak : 0;

    const raiseBtn = $("#raiseSkill");
    if (raiseBtn) raiseBtn.disabled = !acc || acc.skillPoints <= 0;

    const canBonus = !acc || acc.lastBonus !== todayKey();
    $("#dailyBonus").disabled = !acc || !canBonus;
    $("#dailyBonus").textContent = canBonus ? "Kunlik bonus olish" : "Bugun olindi";

    renderUser();
    renderShop();
    renderSettings();
}

function renderUser() {
    const acc = getAcc();
    const openBtn = $("#openLogin");
    const chip = $("#userChip");
    if (acc) {
        openBtn.classList.add("hidden");
        chip.classList.remove("hidden");
        $("#userName").textContent = acc.username;
        $("#avatar").textContent = acc.username.charAt(0).toUpperCase();
    } else {
        openBtn.classList.remove("hidden");
        chip.classList.add("hidden");
    }
}

function renderShop() {
    const acc = getAcc();
    const grid = $("#shopGrid");
    grid.innerHTML = "";
    SHOP_ITEMS.forEach((item) => {
        const owned = acc ? acc.owned.includes(item.id) : false;
        const card = document.createElement("div");
        card.className = "shop-card" + (owned ? " owned" : "");
        card.innerHTML = `
            ${owned ? '<span class="owned-tag">Sotib olingan</span>' : ""}
            <div class="shop-emoji">${item.icon}</div>
            <div class="shop-name">${item.name}</div>
            <div class="shop-desc">${item.desc}</div>
            <div class="shop-price">${item.price} tanga</div>
            <button class="btn ${owned ? "btn-ghost" : "btn-primary"}" data-buy="${item.id}" ${owned ? "disabled" : ""}>
                ${owned ? "Egasi siz" : "Sotib olish"}
            </button>`;
        grid.appendChild(card);
    });
    grid.querySelectorAll("[data-buy]").forEach((btn) => {
        btn.addEventListener("click", () => buy(btn.dataset.buy));
    });
}

/* ============================================================
   Navigatsiya / umumiy
   ============================================================ */
function setupNav() {
    const hamburger = $("#hamburger");
    const nav = $("#nav");
    hamburger.addEventListener("click", () => {
        hamburger.classList.toggle("open");
        nav.classList.toggle("open");
    });
    nav.querySelectorAll(".nav-link").forEach((link) => {
        link.addEventListener("click", () => {
            hamburger.classList.remove("open");
            nav.classList.remove("open");
        });
    });

    const sections = document.querySelectorAll("main section[id]");
    const links = document.querySelectorAll(".nav-link");
    const spy = () => {
        let current = "";
        const pos = window.scrollY + 120;
        sections.forEach((sec) => { if (sec.offsetTop <= pos) current = sec.id; });
        links.forEach((l) => l.classList.toggle("active", l.getAttribute("href") === "#" + current));
    };
    window.addEventListener("scroll", spy, { passive: true });
    spy();
}

function setupHeader() {
    const header = $("#header");
    const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
}

function setupReveal() {
    const els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
        els.forEach((el) => el.classList.add("visible"));
        return;
    }
    const io = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15 });
    els.forEach((el) => io.observe(el));
}

function setupEvents() {
    $("#openLogin").addEventListener("click", () => showView("login"));
    $("#userChip").addEventListener("click", () => showView("profile"));
    $("#openProfile").addEventListener("click", () => {
        if (getAcc()) showView("profile");
        else showView("login");
    });
    $("#heroStart").addEventListener("click", () => {
        if (getAcc()) document.querySelector("#skills").scrollIntoView({ behavior: "smooth" });
        else showView("register");
    });
    $("#raiseSkill").addEventListener("click", raiseSkill);
    $("#spinBtn").addEventListener("click", spin);
    $("#dailyBonus").addEventListener("click", claimDaily);

    const settingsCard = $("#settingsCard");
    if (settingsCard) {
        settingsCard.addEventListener("click", (e) => {
            const btn = e.target.closest("[data-action]");
            if (!btn) return;
            const action = btn.dataset.action;
            if (action === "login") {
                showView("login");
            } else if (action === "link" || action === "regen") {
                startTelegramLink();
            } else if (action === "cancel") {
                const acc = getAcc();
                if (acc) {
                    acc.linkCode = null;
                    saveStore();
                    renderSettings();
                }
            } else if (action === "refresh") {
                refreshServerState();
                toast("Yangilanmoqda...");
            } else if (action === "unlink") {
                unlinkTelegram();
            }
        });
    }

    $("#modal").querySelectorAll("[data-close]").forEach((el) => el.addEventListener("click", closeModal));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });
}

/* ============================================================
   Console/hook: SP qo'shish. Test uchun konsolda:
     Barounzx.addSkills(3)
   ============================================================ */
window.Barounzx = {
    addSkills(count = 1) {
        const acc = getAcc();
        if (!acc) return { ok: false, error: "not_logged_in" };
        addSkillPoints(acc, count);
        saveStore();
        render();
        return { ok: true, skillPoints: acc.skillPoints, xp: acc.xp, level: acc.level };
    },
    getState() {
        const acc = getAcc();
        return acc ? JSON.parse(JSON.stringify(acc)) : null;
    },
    categories: SKILL_CATEGORIES.map((c) => c.id)
};

function init() {
    applyTheme("default");
    setupNav();
    setupHeader();
    setupReveal();
    setupEvents();
    render();
    const acc = getAcc();
    if (acc && acc.tgId && acc.siteToken) {
        refreshServerState();
        setInterval(() => {
            const cur = getAcc();
            if (cur && cur.tgId && cur.siteToken && !document.hidden) refreshServerState();
        }, 15000);
    }
    if (acc && acc.linkCode) pollLinkStatus(acc.linkCode);
    document.addEventListener("visibilitychange", () => {
        const cur = getAcc();
        if (!document.hidden && cur && cur.tgId && cur.siteToken) refreshServerState();
    });
}

document.addEventListener("DOMContentLoaded", init);

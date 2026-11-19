/**
 * openwa_server/server.js  (Baileys WhatsApp Gateway)
 * ─────────────────────────────────────────────────────────────────
 * Local Baileys WhatsApp Gateway — Lancar Dynamic Admin
 *
 * Port API/Dashboard : 3000  (REST JSON + HTML status ringkas)
 *
 * Endpoint yang wajib ada (sesuai openwa_client.py):
 *   GET  /api/health
 *   POST /api/sessions                          — buat session (body: {name})
 *   POST /api/sessions/:sid/start               — koneksi Baileys + generate QR
 *   GET  /api/sessions/:sid/status              — cek status
 *   GET  /api/sessions/:sid/qr                  — ambil QR terbaru (data URL PNG)
 *   POST /api/sessions/:sid/logout              — logout + hapus credential
 *   POST /api/sessions/:sid/messages/send-text  — kirim pesan teks
 *
 * Catatan penamaan: key konfigurasi Python masih memakai openwa_*
 * agar kompatibel, namun engine sesungguhnya adalah Baileys.
 * ─────────────────────────────────────────────────────────────────
 */

'use strict';

const fs = require('fs');
const path = require('path');
const http = require('http');
const express = require('express');
const QRCode = require('qrcode');

// ── Logger (tidak bergantung pino-pretty) ───────────────────────
const logger = {
    info: (...a) => console.log('[INFO ]', new Date().toISOString(), ...a),
    warn: (...a) => console.warn('[WARN ]', new Date().toISOString(), ...a),
    error: (...a) => console.error('[ERROR]', new Date().toISOString(), ...a),
};

// ── Baileys (ESM-only, kita pakai dynamic import) ───────────────
let makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion;
let cachedBaileysVersion = null;

// ── Konstanta path ─────────────────────────────────────────────
const DATA_DIR = path.resolve(process.env.WA_GATEWAY_DATA_DIR || path.join(__dirname, 'data'));
const SESSIONS_DIR = path.join(DATA_DIR, 'sessions');

const API_PORT = Number(process.env.WA_GATEWAY_PORT || process.env.PORT || 3000);
const SHUTDOWN_TOKEN = String(process.env.WA_GATEWAY_SHUTDOWN_TOKEN || '');
const API_TOKEN = String(process.env.WA_GATEWAY_API_TOKEN || '');

// ── State runtime (Map: sid → session object) ─────────────────
const sessions = {};   // { status, sock, qr, qrDataUrl, saveCreds, startingPromise }

// Status ringkas untuk endpoint GET /wa-status.
// Di-update dari event connection.update Baileys.
let waStatus = 'disconnected';
let apiServer = null;
let shuttingDown = false;

function updateSimpleWaStatus(status) {
    if (status === 'qr' || status === 'qr_ready') waStatus = 'qr_ready';
    else if (status === 'connected') waStatus = 'connected';
    else if (['disconnected', 'logged_out', 'idle', 'connecting'].includes(status)) waStatus = 'disconnected';
}

// ── Helpers ──────────────────────────────────────────────────────
function sessionDir(sid) {
    return path.join(SESSIONS_DIR, sid.replace(/[^a-zA-Z0-9_\-]/g, '_'));
}

function cleanSessionId(value) {
    return String(value || '').trim().replace(/[^a-zA-Z0-9_\-]/g, '_').slice(0, 80);
}

function stateFile(sid) {
    return path.join(sessionDir(sid), 'state.json');
}

function clearSessionDir(sid) {
    try {
        fs.rmSync(sessionDir(sid), { recursive: true, force: true });
    } catch (_) { }
}

function resetSessionRuntime(sid, status = 'idle') {
    sessions[sid] = { status, sock: null, qr: null, qrDataUrl: null, qrBase64: null, saveCreds: null, startingPromise: null };
    updateSimpleWaStatus(status);
    writeState(sid, { status, updatedAt: new Date().toISOString() });
    return sessions[sid];
}

function writeState(sid, data) {
    try {
        fs.mkdirSync(sessionDir(sid), { recursive: true });
        const existing = readState(sid) || {};
        fs.writeFileSync(stateFile(sid), JSON.stringify({ ...existing, ...data }, null, 2), 'utf8');
    } catch (_) { }
}

function sessionAccountInfo(sid) {
    const mem = sessions[sid];
    const user = mem && mem.sock && mem.sock.user ? mem.sock.user : null;
    const id = user && user.id ? String(user.id) : '';
    const phone = id ? id.split(':')[0].split('@')[0] : '';
    return {
        id,
        phone,
        name: user && (user.name || user.verifiedName || user.notify) ? String(user.name || user.verifiedName || user.notify) : '',
    };
}

function resolveSession(sid) {
    const mem = sessions[sid];
    const saved = readState(sid);
    const status = (mem && mem.status) || (saved && saved.status) || 'idle';
    return { mem, saved, status };
}

function publicStatus(status) {
    if (status === 'qr') return 'qr_ready';
    if (status === 'logged_out' || status === 'idle') return 'disconnected';
    return status || 'disconnected';
}

function getSessionQr(mem) {
    return (mem && (mem.qrDataUrl || mem.qrBase64 || mem.qr)) || '';
}

function normalizeBaileysChatId(value) {
    const text = String(value || '').trim();
    if (!text) return '';
    if (text.endsWith('@s.whatsapp.net') || text.endsWith('@g.us') || text.endsWith('@broadcast')) return text;
    const phone = text.replace(/@c\.us$/i, '').replace(/\D+/g, '');
    return phone ? `${phone}@s.whatsapp.net` : '';
}

function readState(sid) {
    try { return JSON.parse(fs.readFileSync(stateFile(sid), 'utf8')); } catch (_) { return null; }
}

function hasAuthFiles(sid) {
    try {
        return fs.existsSync(path.join(sessionDir(sid), 'creds.json'));
    } catch (_) {
        return false;
    }
}

function isSocketLoggedIn(sock) {
    return !!(sock && sock.user && sock.ws && sock.ws.readyState === 1);
}

async function waitForConnected(sid, timeoutMs = 8000) {
    const started = Date.now();
    while (Date.now() - started < timeoutMs) {
        const mem = sessions[sid];
        if (mem && (mem.status === 'connected' || isSocketLoggedIn(mem.sock))) return true;
        await new Promise((resolve) => setTimeout(resolve, 500));
    }
    return false;
}

async function waitForReady(sid, timeoutMs = 25_000) {
    const started = Date.now();
    while (Date.now() - started < timeoutMs) {
        const mem = sessions[sid];
        if (mem && (mem.status === 'connected' || isSocketLoggedIn(mem.sock) || getSessionQr(mem))) return mem;
        await new Promise((resolve) => setTimeout(resolve, 500));
    }
    return sessions[sid] || null;
}

async function getBaileysVersion() {
    if (cachedBaileysVersion) return cachedBaileysVersion;
    try {
        const { version } = await fetchLatestBaileysVersion();
        cachedBaileysVersion = version;
    } catch (err) {
        logger.warn('Gagal mengambil versi Baileys terbaru, memakai fallback.', err.message || err);
        cachedBaileysVersion = [2, 3000, 1023223821];
    }
    return cachedBaileysVersion;
}

// ── Core: connect Baileys ────────────────────────────────────────
async function connectSession(sid) {
    if (!makeWASocket) throw new Error('Baileys belum di-load. Coba restart server.');

    const existing = sessions[sid];
    if (existing && existing.status === 'logged_out') {
        try { if (existing.sock) existing.sock.end(undefined); } catch (_) { }
        clearSessionDir(sid);
        resetSessionRuntime(sid, 'idle');
    }
    if (existing && existing.startingPromise) return existing.startingPromise;
    if (sessions[sid] && (sessions[sid].status === 'connected' || isSocketLoggedIn(sessions[sid].sock))) return sessions[sid];

    const startPromise = (async () => {

    const sDir = sessionDir(sid);
    fs.mkdirSync(sDir, { recursive: true });

    // Hapus state running lama jika ada
    if (sessions[sid] && sessions[sid].sock) {
        try { sessions[sid].sock.end(undefined); } catch (_) { }
    }

    const { state, saveCreds } = await useMultiFileAuthState(sDir);
    const version = await getBaileysVersion();

    // Null/silent logger untuk Baileys (tidak butuh pino-pretty)
    const silentLogger = { trace: () => { }, debug: () => { }, info: () => { }, warn: () => { }, error: () => { }, fatal: () => { }, child: () => silentLogger };
    const sock = makeWASocket({
        version,
        logger: silentLogger,
        printQRInTerminal: false,
        auth: state,
        browser: ['Lancar Dynamic Admin', 'Chrome', '1.0.0'],
        connectTimeoutMs: 60_000,
        defaultQueryTimeoutMs: 30_000,
        keepAliveIntervalMs: 25_000,
        retryRequestDelayMs: 2_000,
        maxRetries: 5,
    });

    sessions[sid] = {
        status: 'connecting',
        sock,
        qr: null,
        qrDataUrl: null,
        qrBase64: null,
        saveCreds,
        startingPromise: startPromise,
    };

    writeState(sid, { status: 'connecting', updatedAt: new Date().toISOString() });

    // ── Events ─────────────────────────────────────────────────────
    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (!sessions[sid]) {
            sessions[sid] = { status: 'connecting', sock, qr: null, qrDataUrl: null, qrBase64: null, saveCreds };
        }

        if (qr) {
            try {
                const qrDataUrl = await QRCode.toDataURL(qr, { margin: 1, scale: 8 });
                sessions[sid].qr = qr;
                sessions[sid].qrDataUrl = qrDataUrl;
                sessions[sid].qrBase64 = qrDataUrl;
                sessions[sid].status = 'qr_ready';
                updateSimpleWaStatus('qr_ready');
                writeState(sid, { status: 'qr_ready', updatedAt: new Date().toISOString() });
                logger.info({ sid }, 'QR tersedia — scan untuk login.');
            } catch (err) {
                logger.error({ sid, err: err.message }, 'Gagal generate QR.');
            }
        }

        if (connection === 'open') {
            sessions[sid].status = 'connected';
            sessions[sid].qr = null;
            sessions[sid].qrDataUrl = null;
            sessions[sid].qrBase64 = null;
            sessions[sid].startingPromise = null;
            updateSimpleWaStatus('connected');
            const account = sessionAccountInfo(sid);
            writeState(sid, { status: 'connected', account, updatedAt: new Date().toISOString() });
            logger.info({ sid }, 'Session Baileys connected.');
        }

        if (connection === 'close') {
            const reason = lastDisconnect?.error?.output?.statusCode;
            const DisconnectReasonValue = DisconnectReason || {};

            // Logged out — jangan reconnect otomatis, admin harus scan ulang
            if (reason === DisconnectReasonValue.loggedOut) {
                try { if (sessions[sid].sock) sessions[sid].sock.end(undefined); } catch (_) { }
                clearSessionDir(sid);
                resetSessionRuntime(sid, 'idle');
                logger.warn({ sid }, 'Session logout dari device. Credential lokal dihapus; jalankan start lagi untuk QR baru.');
            } else {
                // Koneksi putus sementara → auto reconnect
                sessions[sid].status = 'disconnected';
                sessions[sid].qr = null;
                sessions[sid].qrDataUrl = null;
                sessions[sid].qrBase64 = null;
                sessions[sid].startingPromise = null;
                updateSimpleWaStatus('disconnected');
                writeState(sid, { status: 'disconnected', updatedAt: new Date().toISOString() });
                logger.info({ sid }, `Koneksi putus (reason=${reason}), reconnect 5 detik...`);
                setTimeout(() => connectSession(sid).catch((err) => {
                    logger.error({ sid, err: err.message }, 'Auto-reconnect gagal.');
                }), 5_000);
            }
        }
    });

    return sessions[sid];
    })();

    if (!sessions[sid]) {
        sessions[sid] = { status: 'connecting', sock: null, qr: null, qrDataUrl: null, qrBase64: null, startingPromise: startPromise };
    } else {
        sessions[sid].startingPromise = startPromise;
    }

    try {
        return await startPromise;
    } catch (err) {
        if (sessions[sid]) {
            sessions[sid].status = 'disconnected';
            sessions[sid].startingPromise = null;
        }
        writeState(sid, { status: 'disconnected', lastError: err.message || String(err), updatedAt: new Date().toISOString() });
        throw err;
    }
}

// ── Express API ──────────────────────────────────────────────────
const api = express();
api.use(express.json());
api.use('/api', (req, res, next) => {
    if (req.path === '/_desktop/shutdown') return next();
    const browserRequest = Boolean(req.get('origin') || req.get('referer'));
    if (!API_TOKEN || browserRequest || req.get('x-gateway-token') !== API_TOKEN) {
        return res.status(403).json({ error: 'Forbidden' });
    }
    next();
});

api.get('/wa-status', (req, res) => {
    res.json({ status: waStatus });
});

/**
 * GET /api/health
 * Health check internal; Python mengirim token gateway.
 */
api.get('/api/health', (req, res) => {
    res.json({ status: 'ok' });
});

api.post('/api/_desktop/shutdown', (req, res) => {
    const browserRequest = Boolean(req.get('origin') || req.get('referer'));
    if (!SHUTDOWN_TOKEN || browserRequest || req.get('x-shutdown-token') !== SHUTDOWN_TOKEN) {
        return res.status(403).json({ error: 'Forbidden' });
    }
    res.json({ status: 'shutting_down' });
    setImmediate(() => shutdown());
});

/**
 * POST /api/sessions
 * Body: { name: string }
 * Buat entry session (belum connect ke Baileys).
 */
api.post('/api/sessions', (req, res) => {
    const sid = cleanSessionId((req.body && req.body.name) || '');
    if (!sid) return res.status(400).json({ error: 'Session name wajib diisi.' });

    fs.mkdirSync(sessionDir(sid), { recursive: true });

    if (!sessions[sid]) {
        const saved = readState(sid);
        const status = saved?.status || (hasAuthFiles(sid) ? 'disconnected' : 'idle');
        sessions[sid] = { status, sock: null, qr: null, qrDataUrl: null, qrBase64: null };
        writeState(sid, { status, createdAt: saved?.createdAt || new Date().toISOString() });
    }

    res.json({ status: 'ok', sessionId: sid, sessionStatus: publicStatus(sessions[sid].status), message: 'Session siap. Panggil /start untuk connect.' });
});

/**
 * POST /api/sessions/:sid/start
 * Mulai koneksi Baileys. Generate QR jika belum pernah login.
 */
api.post('/api/sessions/:sid/start', async (req, res) => {
    const sid = cleanSessionId(req.params.sid);
    if (!sid) return res.status(400).json({ error: 'Session ID wajib diisi.' });
    try {
        if (!makeWASocket) return res.status(503).json({ error: 'Baileys belum siap. Coba beberapa detik lagi.' });
        fs.mkdirSync(sessionDir(sid), { recursive: true });
        if (!sessions[sid]) {
            sessions[sid] = { status: 'idle', sock: null, qr: null, qrDataUrl: null, qrBase64: null };
        }
        // Jangan restart kalau sudah connected
        if (sessions[sid].status === 'connected') {
            return res.json({ status: 'ok', sessionId: sid, sessionStatus: 'connected', message: 'Session sudah aktif.' });
        }
        await connectSession(sid);
        const readySession = await waitForReady(sid, 25_000);
        const sessionStatus = publicStatus(readySession?.status || sessions[sid]?.status);
        res.json({
            status: 'ok',
            sessionId: sid,
            sessionStatus,
            qr: getSessionQr(readySession),
            message: sessionStatus === 'connected'
                ? 'Session sudah aktif.'
                : sessionStatus === 'qr_ready'
                    ? 'QR login siap. Scan dari WhatsApp di HP.'
                    : 'Session sedang dikoneksikan. Refresh status/QR beberapa detik lagi.',
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

/**
 * POST /api/sessions/:sid/logout
 * Logout dan hapus kredensial lokal agar QR baru bisa dibuat.
 */
api.post('/api/sessions/:sid/logout', async (req, res) => {
    const sid = cleanSessionId(req.params.sid);
    if (!sid) return res.status(400).json({ error: 'Session ID wajib diisi.' });
    const mem = sessions[sid];
    try {
        if (mem && mem.sock) {
            try { await mem.sock.logout(); } catch (_) { }
            try { mem.sock.end(undefined); } catch (_) { }
        }
        delete sessions[sid];
        clearSessionDir(sid);
        updateSimpleWaStatus('logged_out');
        res.json({ status: 'ok', sessionId: sid, sessionStatus: 'disconnected', message: 'WhatsApp berhasil logout. Klik Perbarui Status untuk menampilkan QR baru.' });
    } catch (err) {
        res.status(500).json({ error: err.message || 'Gagal logout WhatsApp.' });
    }
});

/**
 * GET /api/sessions/:sid/status
 */
api.get('/api/sessions/:sid/status', (req, res) => {
    const sid = cleanSessionId(req.params.sid);
    if (!sid) return res.status(400).json({ error: 'Session ID wajib diisi.' });
    const { mem, saved, status } = resolveSession(sid);
    const account = sessionAccountInfo(sid);
    const runtimeConnected = !!(mem && isSocketLoggedIn(mem.sock));
    const effectiveStatus = runtimeConnected ? 'connected' : publicStatus(status);
    if (runtimeConnected && mem.status !== 'connected') {
        mem.status = 'connected';
        updateSimpleWaStatus('connected');
        writeState(sid, { status: 'connected', account: account.id ? account : saved?.account || null, updatedAt: new Date().toISOString() });
    }
    res.json({
        sessionId: sid,
        status: effectiveStatus,
        sessionStatus: effectiveStatus,
        connected: effectiveStatus === 'connected',
        hasAuth: hasAuthFiles(sid),
        hasQr: !!getSessionQr(mem),
        qr: getSessionQr(mem),
        account: account.id ? account : (saved && saved.account) || null,
    });
});

/**
 * GET /api/sessions/:sid/qr
 * Return QR sebagai base64 data URL.
 */
api.get('/api/sessions/:sid/qr', async (req, res) => {
    const sid = cleanSessionId(req.params.sid);
    if (!sid) return res.status(400).json({ error: 'Session ID wajib diisi.' });
    let mem = sessions[sid];
    if ((!mem || !getSessionQr(mem)) && makeWASocket) {
        try {
            await connectSession(sid);
            mem = await waitForReady(sid, 25_000);
        } catch (err) {
            logger.warn({ sid, err: err.message }, 'Gagal auto-start saat mengambil QR.');
        }
    }
    const qr = getSessionQr(mem);
    if (!qr) {
        return res.status(404).json({ error: 'QR tidak tersedia. Pastikan session sudah di-start dan status "qr".' });
    }
    res.json({ sessionId: sid, qr, qrcode: qr, qrCode: qr, status: publicStatus(mem.status), sessionStatus: publicStatus(mem.status) });
});

/**
 * POST /api/sessions/:sid/messages/send-text
 * Body: { chatId: string, text: string }
 *
 * Format chatId: 628xxxxxxxxxx@c.us
 * Ini adalah endpoint utama yang dipanggil saat process-queue CRM.
 */
api.post('/api/sessions/:sid/messages/send-text', async (req, res) => {
    const sid = cleanSessionId(req.params.sid);
    if (!sid) return res.status(400).json({ error: 'Session ID wajib diisi.' });
    let { mem, status } = resolveSession(sid);

    if ((!mem || !mem.sock) && ['connected', 'disconnected'].includes(publicStatus(status)) && hasAuthFiles(sid) && makeWASocket) {
        sessions[sid] = { status: 'connecting', sock: null, qr: null, qrDataUrl: null, qrBase64: null };
        try {
            await connectSession(sid);
            await waitForConnected(sid, 8000);
            ({ mem, status } = resolveSession(sid));
        } catch (err) {
            logger.error({ sid, err: err.message }, 'Gagal restore session sebelum kirim pesan.');
        }
    }

    if (!mem || !(mem.status === 'connected' || isSocketLoggedIn(mem.sock))) {
        return res.status(400).json({
            error: 'WhatsApp belum terkoneksi.',
            status: publicStatus((mem && mem.status) || status || 'idle'),
            message: 'WhatsApp belum siap mengirim pesan. Klik Perbarui Status, tunggu sampai login tersambung, lalu coba lagi.',
        });
    }

    const chatId = normalizeBaileysChatId((req.body && req.body.chatId) || '');
    const text = String((req.body && req.body.text) || '').trim();

    if (!chatId) return res.status(400).json({ error: 'Nomor WhatsApp tujuan wajib diisi.' });
    if (!text) return res.status(400).json({ error: 'text/pesan wajib diisi.' });

    try {
        const result = await mem.sock.sendMessage(chatId, { text });
        const messageId = result && result.key && result.key.id ? result.key.id : '';
        logger.info({ sid, chatId, messageId }, 'Pesan terkirim via Baileys.');
        res.json({ status: 'sent', id: messageId, messageId, chatId, sessionId: sid });
    } catch (err) {
        logger.error({ sid, chatId, err: err.message }, 'Gagal kirim pesan Baileys.');
        res.status(500).json({ error: err.message, chatId, sessionId: sid });
    }
});

// ── Dashboard ────────────────────────────────────────────────────
api.get('/', (req, res) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.send(`<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>WhatsApp Baileys Gateway — Lancar Dynamic Admin</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; color: #111; }
    h1 { color: #128C7E; } h2 { color: #075E54; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { padding: .5rem .75rem; border: 1px solid #ddd; text-align: left; }
    th { background: #f5f5f5; }
    .badge-connected { color: #16a34a; font-weight: 600; }
    .badge-qr        { color: #ca8a04; font-weight: 600; }
    .badge-disconnected, .badge-logged_out { color: #dc2626; }
    code { background: #f0f0f0; padding: .1rem .3rem; border-radius: 4px; font-size: .85em; }
    pre  { background: #1e1e1e; color: #d4d4d4; padding: 1rem; border-radius: 8px; overflow: auto; font-size: .82em; }
  </style>
  <meta http-equiv="refresh" content="10" />
</head>
<body>
  <h1>🟢 WhatsApp Baileys Gateway</h1>
  <p>Server lokal berbasis <strong>@whiskeysockets/baileys</strong> untuk Lancar Dynamic Admin.<br/>
     Halaman ini refresh otomatis setiap 10 detik.</p>
  <h2>Status Gateway</h2>
  <p>Status: <strong>${escapeHtml(waStatus)}</strong>. Detail session dan QR hanya tersedia melalui aplikasi utama.</p>
  <h2>Informasi API</h2>
  <pre>API Port     : ${API_PORT}
    Dashboard    : ${API_PORT}
Login        : Scan QR Baileys
Uptime       : ${Math.round(process.uptime())}s</pre>
  <p style="opacity:.7;font-size:.86em">API gateway hanya dapat diakses oleh backend aplikasi.</p>
  <p style="opacity:.5;font-size:.8em">Flowchart: docs/flowcharts/17-whatsapp-baileys-gateway.md</p>
</body>
</html>`);
});

function escapeHtml(s) {
    return String(s || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ── Boot ─────────────────────────────────────────────────────────
(async () => {
    // Muat Baileys (ESM) secara dinamis
    try {
        const baileys = await import('@whiskeysockets/baileys');
        makeWASocket = baileys.default || baileys.makeWASocket;
        useMultiFileAuthState = baileys.useMultiFileAuthState;
        DisconnectReason = baileys.DisconnectReason;
        fetchLatestBaileysVersion = baileys.fetchLatestBaileysVersion;
        logger.info('Baileys berhasil di-load.');
    } catch (err) {
        logger.error('Gagal memuat Baileys!', err.message, '— Pastikan npm install sudah dijalankan di folder openwa_server/');
        // Server tetap jalan agar Python bisa cek port; endpoint session akan return 503
    }

    // Pastikan direktori data ada
    fs.mkdirSync(SESSIONS_DIR, { recursive: true });

    // Restore session dari disk (sessions yang sudah pernah connect)
    try {
        const existing = fs.readdirSync(SESSIONS_DIR, { withFileTypes: true })
            .filter(d => d.isDirectory())
            .map(d => d.name);
        for (const sid of existing) {
            const saved = readState(sid);
            if (saved && saved.status === 'connected') {
                logger.info({ sid }, 'Restore session from disk — mencoba reconnect...');
                sessions[sid] = { status: 'connecting', sock: null, qr: null, qrDataUrl: null, qrBase64: null };
                connectSession(sid).catch((err) => logger.warn({ sid, err: err.message }, 'Restore reconnect gagal.'));
            } else if (saved) {
                sessions[sid] = { status: saved.status || 'idle', sock: null, qr: null, qrDataUrl: null, qrBase64: null };
            }
        }
    } catch (_) { }

    // Start API + Dashboard server
    apiServer = http.createServer(api);
    apiServer.listen(API_PORT, '127.0.0.1', () => {
        logger.info(`API Baileys Gateway berjalan di http://127.0.0.1:${API_PORT}/api`);
        logger.info(`Dashboard berjalan di http://127.0.0.1:${API_PORT}`);
        logger.info('Login WhatsApp memakai QR Baileys; tidak ada API key.');
    });

    // Graceful shutdown
    process.on('SIGINT', () => shutdown());
    process.on('SIGTERM', () => shutdown());

})();

function shutdown() {
    if (shuttingDown) return;
    shuttingDown = true;
    logger.info('Shutdown - menutup semua session...');
    for (const [sid, s] of Object.entries(sessions)) {
        if (s.sock) {
            try { s.sock.end(undefined); } catch (_) { }
            writeState(sid, { status: 'disconnected', updatedAt: new Date().toISOString() });
        }
    }
    if (apiServer) {
        apiServer.close(() => process.exit(0));
        setTimeout(() => process.exit(0), 1500).unref();
        return;
    }
    process.exit(0);
}

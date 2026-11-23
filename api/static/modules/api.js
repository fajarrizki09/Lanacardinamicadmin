"use strict";
function isRecord(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}
function readApiMessage(payload) {
    if (typeof payload === "string")
        return payload.trim();
    if (!isRecord(payload))
        return "";
    const detail = payload.detail;
    const message = payload.message;
    if (typeof detail === "string")
        return detail.trim();
    if (typeof message === "string")
        return message.trim();
    if (detail !== undefined) {
        try {
            return JSON.stringify(detail);
        }
        catch (error) {
            return "";
        }
    }
    return "";
}
function getApiErrorMessage(payload, fallback = "Terjadi kesalahan saat memproses request.") {
    const message = readApiMessage(payload);
    return message || fallback;
}
function isApiSuccess(payload) {
    return payload.status === "success";
}
async function parseApiResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
        ? await response.json().catch(() => ({}))
        : await response.text().catch(() => "");
    if (!response.ok) {
        throw new Error(getApiErrorMessage(payload, 'Permintaan belum berhasil diproses.'));
    }
    return payload;
}
async function apiRequest(url, options = {}) {
    const { parseJson = true, timeoutMs = 10000, ...requestOptions } = options;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
        const response = await fetch(url, { ...requestOptions, signal: controller.signal });
        if (!parseJson)
            return response;
        return parseApiResponse(response);
    }
    finally {
        clearTimeout(timeoutId);
    }
}
function apiGetJson(url, options = {}) {
    return apiRequest(url, { ...options, method: options.method || "GET" });
}
function apiPostForm(url, formData, options = {}) {
    return apiRequest(url, {
        ...options,
        method: options.method || "POST",
        body: formData,
    });
}
function openExternalUrlFallback(url) {
    const formData = new FormData();
    formData.append("url", String(url || ""));
    return apiPostForm("/support/open_external_url", formData);
}
function getTauriInvoke() {
    const invoke = window.__TAURI__?.core?.invoke;
    return typeof invoke === "function" ? invoke : null;
}
function isNativeCommandUnavailable(error) {
    const message = String(error instanceof Error ? error.message : error || "").toLowerCase();
    return message.includes("unknown command")
        || message.includes("not found")
        || message.includes("is not a function")
        || message.includes("__tauri__")
        || message.includes("tidak ditemukan")
        || message.includes("tidak diizinkan");
}
async function openPathFallback(kind, path) {
    if (path && kind === "invoices") {
        return apiGetJson('/open_invoice?path=' + encodeURIComponent(path));
    }
    if (!path) {
        return apiRequest(`/support/open_folder?kind=${encodeURIComponent(kind)}`, { method: "POST" });
    }
    throw new Error("Fitur native belum tersedia.");
}
async function openDesktopPath(kind, path) {
    const invoke = getTauriInvoke();
    if (!invoke)
        return openPathFallback(kind, path);
    try {
        return await invoke("native_open_path", { kind, path: path || null });
    }
    catch (error) {
        if (isNativeCommandUnavailable(error))
            return openPathFallback(kind, path);
        throw error;
    }
}
async function revealDesktopPath(kind, path) {
    const invoke = getTauriInvoke();
    if (!invoke)
        throw new Error("Fitur reveal native belum tersedia.");
    try {
        return await invoke("native_reveal_path", { kind, path });
    }
    catch (error) {
        if (isNativeCommandUnavailable(error))
            throw new Error("Fitur reveal native belum tersedia.");
        throw error;
    }
}
async function openInvoiceFileFallback(path, action) {
    if (action === "open") {
        return apiGetJson('/open_invoice?path=' + encodeURIComponent(path));
    }
    throw new Error("Fitur reveal invoice native belum tersedia.");
}
async function openDesktopInvoiceFile(path, action = "open") {
    const invoke = getTauriInvoke();
    if (!invoke)
        return openInvoiceFileFallback(path, action);
    try {
        return await invoke("native_open_invoice_file", { path, action });
    }
    catch (error) {
        if (isNativeCommandUnavailable(error))
            return openInvoiceFileFallback(path, action);
        throw error;
    }
}
function printFileFallback(path) {
    return apiGetJson('/print_invoice?path=' + encodeURIComponent(path));
}
async function printDesktopFile(path, source) {
    const invoke = getTauriInvoke();
    if (!invoke)
        return printFileFallback(path);
    try {
        return await invoke("native_print_file", { path, source });
    }
    catch (error) {
        if (isNativeCommandUnavailable(error))
            return printFileFallback(path);
        throw error;
    }
}
async function openDesktopExternalUrl(url, source = "unknown") {
    const invoke = getTauriInvoke();
    if (!invoke)
        return openExternalUrlFallback(url);
    try {
        return await invoke("native_open_external_url", { url, source });
    }
    catch (error) {
        if (isNativeCommandUnavailable(error))
            return openExternalUrlFallback(url);
        throw error;
    }
}
window.LancarApi = {
    request: apiRequest,
    getJson: apiGetJson,
    postForm: apiPostForm,
    openExternalUrl: openDesktopExternalUrl,
    openPath: openDesktopPath,
    revealPath: revealDesktopPath,
    openInvoiceFile: openDesktopInvoiceFile,
    printFile: printDesktopFile,
    isSuccess: isApiSuccess,
    getErrorMessage: getApiErrorMessage,
};
window.apiGetJson = apiGetJson;
window.apiPostForm = apiPostForm;
window.openDesktopExternalUrl = openDesktopExternalUrl;
window.openDesktopPath = openDesktopPath;
window.revealDesktopPath = revealDesktopPath;
window.openDesktopInvoiceFile = openDesktopInvoiceFile;
window.printDesktopFile = printDesktopFile;

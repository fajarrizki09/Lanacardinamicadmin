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
        throw new Error(getApiErrorMessage(payload, `Request gagal (${response.status}).`));
    }
    return payload;
}
async function apiRequest(url, options = {}) {
    const { parseJson = true, ...requestOptions } = options;
    const response = await fetch(url, requestOptions);
    if (!parseJson)
        return response;
    return parseApiResponse(response);
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
window.LancarApi = {
    request: apiRequest,
    getJson: apiGetJson,
    postForm: apiPostForm,
    isSuccess: isApiSuccess,
    getErrorMessage: getApiErrorMessage,
};
window.apiGetJson = apiGetJson;
window.apiPostForm = apiPostForm;

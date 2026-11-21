type ApiRequestOptions = RequestInit & {
    parseJson?: boolean;
};

type LancarApiClient = {
    request: <T = unknown>(url: string, options?: ApiRequestOptions) => Promise<T>;
    getJson: <T = unknown>(url: string, options?: ApiRequestOptions) => Promise<T>;
    postForm: <T = unknown>(url: string, formData: FormData, options?: ApiRequestOptions) => Promise<T>;
    openExternalUrl: <T = unknown>(url: string, source?: NativeExternalUrlSource) => Promise<T>;
    openPath: <T = unknown>(kind: NativePathKind, path?: string) => Promise<T>;
    revealPath: <T = unknown>(kind: NativeRevealPathKind, path: string) => Promise<T>;
    openInvoiceFile: <T = unknown>(path: string, action?: NativeInvoiceFileAction) => Promise<T>;
    printFile: <T = unknown>(path: string, source: NativePrintFileSource) => Promise<T>;
    isSuccess: <T = unknown>(payload: ApiResponse<T>) => boolean;
    getErrorMessage: (payload: unknown, fallback?: string) => string;
};

interface Window {
    LancarApi?: LancarApiClient;
    apiGetJson?: LancarApiClient["getJson"];
    apiPostForm?: LancarApiClient["postForm"];
    openDesktopExternalUrl?: LancarApiClient["openExternalUrl"];
    openDesktopPath?: LancarApiClient["openPath"];
    revealDesktopPath?: LancarApiClient["revealPath"];
    openDesktopInvoiceFile?: LancarApiClient["openInvoiceFile"];
    printDesktopFile?: LancarApiClient["printFile"];
    __TAURI__?: {
        core?: {
            invoke?: <T = unknown>(command: string, args?: Record<string, unknown>) => Promise<T>;
        };
    };
}

type NativePathKind = "exports" | "logs" | "app_data" | "invoices" | "backups";
type NativeRevealPathKind = "exports" | "logs" | "invoices" | "backups";
type NativeExternalUrlSource = "payment" | "whatsapp_help" | "gateway_dashboard" | "support" | "unknown";
type NativeInvoiceFileAction = "open" | "reveal";
type NativePrintFileSource = "invoice" | "herbal_invoice" | "export" | "receipt";

function isRecord(value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}

function readApiMessage(payload: unknown): string {
    if (typeof payload === "string") return payload.trim();
    if (!isRecord(payload)) return "";

    const detail = payload.detail;
    const message = payload.message;
    if (typeof detail === "string") return detail.trim();
    if (typeof message === "string") return message.trim();
    if (detail !== undefined) {
        try {
            return JSON.stringify(detail);
        } catch (error) {
            return "";
        }
    }
    return "";
}

function getApiErrorMessage(payload: unknown, fallback = "Terjadi kesalahan saat memproses request."): string {
    const message = readApiMessage(payload);
    return message || fallback;
}

function isApiSuccess<T = unknown>(payload: ApiResponse<T>): boolean {
    return payload.status === "success";
}

async function parseApiResponse<T = unknown>(response: Response): Promise<T> {
    const contentType = response.headers.get("content-type") || "";
    const payload: unknown = contentType.includes("application/json")
        ? await response.json().catch(() => ({}))
        : await response.text().catch(() => "");

    if (!response.ok) {
        throw new Error(getApiErrorMessage(payload, 'Permintaan belum berhasil diproses.'));
    }

    return payload as T;
}

async function apiRequest<T = unknown>(url: string, options: ApiRequestOptions = {}): Promise<T> {
    const { parseJson = true, ...requestOptions } = options;
    const response = await fetch(url, requestOptions);
    if (!parseJson) return response as T;
    return parseApiResponse<T>(response);
}

function apiGetJson<T = unknown>(url: string, options: ApiRequestOptions = {}): Promise<T> {
    return apiRequest<T>(url, { ...options, method: options.method || "GET" });
}

function apiPostForm<T = unknown>(url: string, formData: FormData, options: ApiRequestOptions = {}): Promise<T> {
    return apiRequest<T>(url, {
        ...options,
        method: options.method || "POST",
        body: formData,
    });
}

function openExternalUrlFallback<T = unknown>(url: string): Promise<T> {
    const formData = new FormData();
    formData.append("url", String(url || ""));
    return apiPostForm<T>("/support/open_external_url", formData);
}

function getTauriInvoke(): (<T = unknown>(command: string, args?: Record<string, unknown>) => Promise<T>) | null {
    const invoke = window.__TAURI__?.core?.invoke;
    return typeof invoke === "function" ? invoke : null;
}

function isNativeCommandUnavailable(error: unknown): boolean {
    const message = String(error instanceof Error ? error.message : error || "").toLowerCase();
    return message.includes("unknown command")
        || message.includes("not found")
        || message.includes("is not a function")
        || message.includes("__tauri__")
        || message.includes("tidak ditemukan")
        || message.includes("tidak diizinkan");
}

async function openPathFallback<T = unknown>(kind: NativePathKind, path?: string): Promise<T> {
    if (path && kind === "invoices") {
        return apiGetJson<T>('/open_invoice?path=' + encodeURIComponent(path));
    }
    if (!path) {
        return apiRequest<T>(`/support/open_folder?kind=${encodeURIComponent(kind)}`, { method: "POST" });
    }
    throw new Error("Fitur native belum tersedia.");
}

async function openDesktopPath<T = unknown>(kind: NativePathKind, path?: string): Promise<T> {
    const invoke = getTauriInvoke();
    if (!invoke) return openPathFallback<T>(kind, path);

    try {
        return await invoke<T>("native_open_path", { kind, path: path || null });
    } catch (error) {
        if (isNativeCommandUnavailable(error)) return openPathFallback<T>(kind, path);
        throw error;
    }
}

async function revealDesktopPath<T = unknown>(kind: NativeRevealPathKind, path: string): Promise<T> {
    const invoke = getTauriInvoke();
    if (!invoke) throw new Error("Fitur reveal native belum tersedia.");

    try {
        return await invoke<T>("native_reveal_path", { kind, path });
    } catch (error) {
        if (isNativeCommandUnavailable(error)) throw new Error("Fitur reveal native belum tersedia.");
        throw error;
    }
}

async function openInvoiceFileFallback<T = unknown>(path: string, action: NativeInvoiceFileAction): Promise<T> {
    if (action === "open") {
        return apiGetJson<T>('/open_invoice?path=' + encodeURIComponent(path));
    }
    throw new Error("Fitur reveal invoice native belum tersedia.");
}

async function openDesktopInvoiceFile<T = unknown>(path: string, action: NativeInvoiceFileAction = "open"): Promise<T> {
    const invoke = getTauriInvoke();
    if (!invoke) return openInvoiceFileFallback<T>(path, action);

    try {
        return await invoke<T>("native_open_invoice_file", { path, action });
    } catch (error) {
        if (isNativeCommandUnavailable(error)) return openInvoiceFileFallback<T>(path, action);
        throw error;
    }
}

function printFileFallback<T = unknown>(path: string): Promise<T> {
    return apiGetJson<T>('/print_invoice?path=' + encodeURIComponent(path));
}

async function printDesktopFile<T = unknown>(path: string, source: NativePrintFileSource): Promise<T> {
    const invoke = getTauriInvoke();
    if (!invoke) return printFileFallback<T>(path);

    try {
        return await invoke<T>("native_print_file", { path, source });
    } catch (error) {
        if (isNativeCommandUnavailable(error)) return printFileFallback<T>(path);
        throw error;
    }
}

async function openDesktopExternalUrl<T = unknown>(url: string, source: NativeExternalUrlSource = "unknown"): Promise<T> {
    const invoke = getTauriInvoke();
    if (!invoke) return openExternalUrlFallback<T>(url);

    try {
        return await invoke<T>("native_open_external_url", { url, source });
    } catch (error) {
        if (isNativeCommandUnavailable(error)) return openExternalUrlFallback<T>(url);
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

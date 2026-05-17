type ApiRequestOptions = RequestInit & {
    parseJson?: boolean;
};

type LancarApiClient = {
    request: <T = unknown>(url: string, options?: ApiRequestOptions) => Promise<T>;
    getJson: <T = unknown>(url: string, options?: ApiRequestOptions) => Promise<T>;
    postForm: <T = unknown>(url: string, formData: FormData, options?: ApiRequestOptions) => Promise<T>;
    isSuccess: <T = unknown>(payload: ApiResponse<T>) => boolean;
    getErrorMessage: (payload: unknown, fallback?: string) => string;
};

interface Window {
    LancarApi?: LancarApiClient;
    apiGetJson?: LancarApiClient["getJson"];
    apiPostForm?: LancarApiClient["postForm"];
}

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
        throw new Error(getApiErrorMessage(payload, `Request gagal (${response.status}).`));
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

window.LancarApi = {
    request: apiRequest,
    getJson: apiGetJson,
    postForm: apiPostForm,
    isSuccess: isApiSuccess,
    getErrorMessage: getApiErrorMessage,
};

window.apiGetJson = apiGetJson;
window.apiPostForm = apiPostForm;

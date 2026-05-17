type StatusTone = "success" | "warning" | "danger" | "muted" | "info";

type StatusFormat = {
    label: string;
    tone: StatusTone;
};

type LancarFormatters = {
    currency: (amount: unknown) => string;
    date: (value: unknown, fallback?: string) => string;
    dateTime: (value: unknown, fallback?: string) => string;
    status: (value: unknown, fallback?: string) => StatusFormat;
};

interface Window {
    LancarFormatters?: LancarFormatters;
}

(() => {
    function toDate(value: unknown): Date | null {
        const text = String(value || '').trim();
        if (!text) return null;

        if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
            const [year, month, day] = text.split('-').map(Number);
            return new Date(year, month - 1, day);
        }

        const date = new Date(text);
        return Number.isNaN(date.getTime()) ? null : date;
    }

    function currency(amount: unknown): string {
        const value = Number(amount || 0);
        const safeValue = Number.isFinite(value) ? Math.round(value) : 0;
        return `Rp ${safeValue.toLocaleString('id-ID')}`;
    }

    function date(value: unknown, fallback = '-'): string {
        const parsed = toDate(value);
        if (!parsed) return fallback;
        return parsed.toLocaleDateString('id-ID', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
        });
    }

    function dateTime(value: unknown, fallback = '-'): string {
        const parsed = toDate(value);
        if (!parsed) return fallback;
        return parsed.toLocaleString('id-ID', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    function status(value: unknown, fallback = '-'): StatusFormat {
        const text = String(value || '').trim().toLowerCase();
        const map: Record<string, StatusFormat> = {
            active: { label: 'Aktif', tone: 'success' },
            inactive: { label: 'Nonaktif', tone: 'muted' },
            paid: { label: 'Lunas', tone: 'success' },
            unpaid: { label: 'Belum Bayar', tone: 'warning' },
            partial: { label: 'DP / Sebagian', tone: 'warning' },
            void: { label: 'Void', tone: 'danger' },
            success: { label: 'Berhasil', tone: 'success' },
            error: { label: 'Error', tone: 'danger' },
            pending: { label: 'Pending', tone: 'warning' },
        };
        if (map[text]) return map[text];
        return { label: text ? text.replace(/_/g, ' ') : fallback, tone: 'info' };
    }

    window.LancarFormatters = {
        currency,
        date,
        dateTime,
        status,
    };
})();

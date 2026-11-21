type LancarValidators = {
    isNonEmpty: (value: unknown) => boolean;
    isValidIndonesianPhone: (value: unknown) => boolean;
    normalizePhone: (value: unknown) => string;
    isPositiveNumber: (value: unknown) => boolean;
    parseNumberInput: (value: unknown) => number;
    requiredText: (value: unknown, fallback?: string) => string;
};

interface Window {
    LancarValidators?: LancarValidators;
}

(() => {
    function asTrimmedText(value: unknown): string {
        return String(value ?? '').trim();
    }

    function isNonEmpty(value: unknown): boolean {
        return asTrimmedText(value).length > 0;
    }

    function normalizePhone(value: unknown): string {
        const digits = asTrimmedText(value).replace(/\D/g, '');
        if (!digits) return '';
        if (digits.startsWith('62')) return digits;
        if (digits.startsWith('0')) return `62${digits.slice(1)}`;
        return digits;
    }

    function isValidIndonesianPhone(value: unknown): boolean {
        const phone = normalizePhone(value);
        return /^62[0-9]{8,13}$/.test(phone);
    }

    function parseNumberInput(value: unknown): number {
        if (typeof value === 'number') return Number.isFinite(value) ? value : 0;
        const text = asTrimmedText(value).replace(/\./g, '').replace(',', '.');
        const parsed = Number(text);
        return Number.isFinite(parsed) ? parsed : 0;
    }

    function isPositiveNumber(value: unknown): boolean {
        return parseNumberInput(value) > 0;
    }

    function requiredText(value: unknown, fallback = ''): string {
        const text = asTrimmedText(value);
        return text || fallback;
    }

    window.LancarValidators = {
        isNonEmpty,
        isValidIndonesianPhone,
        normalizePhone,
        isPositiveNumber,
        parseNumberInput,
        requiredText,
    };
})();

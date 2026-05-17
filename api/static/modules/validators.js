"use strict";
(() => {
    function asTrimmedText(value) {
        return String(value ?? '').trim();
    }
    function isNonEmpty(value) {
        return asTrimmedText(value).length > 0;
    }
    function normalizePhone(value) {
        const digits = asTrimmedText(value).replace(/\D/g, '');
        if (!digits)
            return '';
        if (digits.startsWith('62'))
            return digits;
        if (digits.startsWith('0'))
            return `62${digits.slice(1)}`;
        return digits;
    }
    function isValidIndonesianPhone(value) {
        const phone = normalizePhone(value);
        return /^62[0-9]{8,13}$/.test(phone);
    }
    function parseNumberInput(value) {
        if (typeof value === 'number')
            return Number.isFinite(value) ? value : 0;
        const text = asTrimmedText(value).replace(/\./g, '').replace(',', '.');
        const parsed = Number(text);
        return Number.isFinite(parsed) ? parsed : 0;
    }
    function isPositiveNumber(value) {
        return parseNumberInput(value) > 0;
    }
    function requiredText(value, fallback = '') {
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

"use strict";
const LANCAR_RAW_HTML_PATTERNS = [
    /<script\b/i,
    /\son[a-z]+\s*=/i,
    /javascript\s*:/i,
    /<iframe\b/i,
    /<object\b/i,
    /<embed\b/i,
];
(() => {
    function byId(id) {
        return document.getElementById(id);
    }
    function query(selector, root = document) {
        return root.querySelector(selector);
    }
    function queryAll(selector, root = document) {
        return Array.from(root.querySelectorAll(selector));
    }
    function resolveElement(elementOrId) {
        if (!elementOrId)
            return null;
        if (typeof elementOrId === 'string')
            return byId(elementOrId);
        return elementOrId;
    }
    function setText(elementOrId, value) {
        const element = resolveElement(elementOrId);
        if (!element)
            return false;
        element.textContent = value === null || value === undefined ? '' : String(value);
        return true;
    }
    function setHtml(elementOrId, value) {
        const element = resolveElement(elementOrId);
        if (!element)
            return false;
        const html = value === null || value === undefined ? '' : String(value);
        assertEscapedHtml(html, 'LancarDom.setHtml');
        element.innerHTML = html;
        return true;
    }
    function assertEscapedHtml(html, context = 'HTML render') {
        const text = String(html || '');
        const unsafe = LANCAR_RAW_HTML_PATTERNS.find(pattern => pattern.test(text));
        if (unsafe) {
            console.warn(`${context}: possible unsafe HTML pattern blocked`, unsafe.toString());
            throw new Error('Konten HTML tidak aman terdeteksi.');
        }
        return true;
    }
    function show(elementOrId) {
        const element = resolveElement(elementOrId);
        if (!element)
            return false;
        element.style.display = '';
        return true;
    }
    function hide(elementOrId) {
        const element = resolveElement(elementOrId);
        if (!element)
            return false;
        element.style.display = 'none';
        return true;
    }
    function getInputValue(elementOrId) {
        const element = resolveElement(elementOrId);
        return element ? element.value : '';
    }
    window.LancarDom = {
        byId,
        query,
        queryAll,
        setText,
        setHtml,
        assertEscapedHtml,
        show,
        hide,
        getInputValue,
    };
})();

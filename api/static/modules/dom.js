"use strict";
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
        element.innerHTML = value === null || value === undefined ? '' : String(value);
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
        show,
        hide,
        getInputValue,
    };
})();

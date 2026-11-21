type DomRoot = Document | DocumentFragment | Element;
type ElementOrId<T extends Element = HTMLElement> = T | string | null | undefined;

type LancarDom = {
    byId: <T extends HTMLElement = HTMLElement>(id: string) => T | null;
    query: <T extends Element = Element>(selector: string, root?: DomRoot) => T | null;
    queryAll: <T extends Element = Element>(selector: string, root?: DomRoot) => T[];
    setText: (elementOrId: ElementOrId, value: unknown) => boolean;
    setHtml: (elementOrId: ElementOrId, value: unknown) => boolean;
    show: (elementOrId: ElementOrId<HTMLElement>) => boolean;
    hide: (elementOrId: ElementOrId<HTMLElement>) => boolean;
    getInputValue: (elementOrId: ElementOrId<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => string;
    assertEscapedHtml: (html: string, context?: string) => boolean;
};

const LANCAR_RAW_HTML_PATTERNS = [
    /<script\b/i,
    /\son[a-z]+\s*=/i,
    /javascript\s*:/i,
    /<iframe\b/i,
    /<object\b/i,
    /<embed\b/i,
];

interface Window {
    LancarDom?: LancarDom;
}

(() => {
    function byId<T extends HTMLElement = HTMLElement>(id: string): T | null {
        return document.getElementById(id) as T | null;
    }

    function query<T extends Element = Element>(selector: string, root: DomRoot = document): T | null {
        return root.querySelector(selector) as T | null;
    }

    function queryAll<T extends Element = Element>(selector: string, root: DomRoot = document): T[] {
        return Array.from(root.querySelectorAll(selector)) as T[];
    }

    function resolveElement<T extends Element = HTMLElement>(elementOrId: ElementOrId<T>): T | null {
        if (!elementOrId) return null;
        if (typeof elementOrId === 'string') return byId<T & HTMLElement>(elementOrId) as unknown as T | null;
        return elementOrId;
    }

    function setText(elementOrId: ElementOrId, value: unknown): boolean {
        const element = resolveElement(elementOrId);
        if (!element) return false;
        element.textContent = value === null || value === undefined ? '' : String(value);
        return true;
    }

    function setHtml(elementOrId: ElementOrId, value: unknown): boolean {
        const element = resolveElement(elementOrId);
        if (!element) return false;
        const html = value === null || value === undefined ? '' : String(value);
        assertEscapedHtml(html, 'LancarDom.setHtml');
        element.innerHTML = html;
        return true;
    }

    function assertEscapedHtml(html: string, context = 'HTML render'): boolean {
        const text = String(html || '');
        const unsafe = LANCAR_RAW_HTML_PATTERNS.find(pattern => pattern.test(text));
        if (unsafe) {
            console.warn(`${context}: possible unsafe HTML pattern blocked`, unsafe.toString());
            throw new Error('Konten HTML tidak aman terdeteksi.');
        }
        return true;
    }

    function show(elementOrId: ElementOrId<HTMLElement>): boolean {
        const element = resolveElement(elementOrId);
        if (!element) return false;
        element.style.display = '';
        return true;
    }

    function hide(elementOrId: ElementOrId<HTMLElement>): boolean {
        const element = resolveElement(elementOrId);
        if (!element) return false;
        element.style.display = 'none';
        return true;
    }

    function getInputValue(elementOrId: ElementOrId<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>): string {
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

"use strict";
// CSP bootstrap: reads non-executable JSON config tags used by templates.
(function loadAppConfigFromJsonScript() {
    const configElement = document.getElementById('app-config');
    if (!configElement || configElement.tagName.toLowerCase() !== 'script')
        return;
    if (configElement.type !== 'application/json')
        return;
    try {
        const config = JSON.parse(configElement.textContent || '{}');
        window._appToken = typeof config.appToken === 'string' ? config.appToken : '';
        window._initialLicense = config.license || null;
    }
    catch (error) {
        window._appToken = '';
        window._initialLicense = null;
    }
})();

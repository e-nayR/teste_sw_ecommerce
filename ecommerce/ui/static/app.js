/*
 * P0912 ECOMMERCE — JavaScript mínimo da UI.
 *
 * Objetivos:
 * - Mostrar overlay de loading por 300ms ao submeter formulários
 *   (estado "loading" da spec §8.3).
 * - Configurar fetch para enviar cookies em requests same-origin
 *   (credentials: 'include') quando algum chamador precisar.
 *
 * Não há armazenamento de tokens em localStorage/sessionStorage —
 * a autenticação flui exclusivamente pelo cookie HttpOnly definido
 * por POST /api/login (e pelo POST /login da UI).
 */
(function () {
    "use strict";

    var overlay = document.getElementById("loading-overlay");

    // Estado loading: mostra overlay por ~300ms ao submeter formulários.
    function mostrarLoading() {
        if (!overlay) {
            return;
        }
        overlay.hidden = false;
        setTimeout(function () {
            overlay.hidden = true;
        }, 300);
    }

    // Hook em todos os formulários POST — exceto o form-preview-desconto
    // que é GET e renderiza no servidor (não precisa de overlay).
    var forms = document.querySelectorAll("form[method='POST'], form[method='post']");
    Array.prototype.forEach.call(forms, function (form) {
        form.addEventListener("submit", function () {
            mostrarLoading();
        });
    });

    // Wrapper de fetch que envia cookies same-origin.
    // Disponível em window.apiFetch para uso futuro (turnos com JS).
    window.apiFetch = function (url, options) {
        options = options || {};
        options.credentials = "include";
        options.headers = options.headers || {};
        if (!options.headers["Accept"]) {
            options.headers["Accept"] = "application/json";
        }
        return fetch(url, options);
    };
})();

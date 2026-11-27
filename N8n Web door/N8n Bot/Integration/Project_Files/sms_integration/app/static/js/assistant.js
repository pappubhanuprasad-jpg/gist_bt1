/* College Assistant widget.
   Talks only to /assistant/ask on this same application. The n8n address and
   key live on the server, in .env, and never reach the browser. */

(function () {
    "use strict";

    var panel = document.getElementById("assistantPanel");
    if (!panel) { return; }

    var launcher = document.getElementById("assistantLauncher");
    var closeBtn = document.getElementById("assistantClose");
    var log = document.getElementById("assistantLog");
    var chips = document.getElementById("assistantChips");
    var form = document.getElementById("assistantForm");
    var input = document.getElementById("assistantInput");
    var send = document.getElementById("assistantSend");

    var busy = false;

    function open() {
        panel.hidden = false;
        launcher.hidden = true;
        launcher.setAttribute("aria-expanded", "true");
        input.focus();
    }

    function close() {
        panel.hidden = true;
        launcher.hidden = false;
        launcher.setAttribute("aria-expanded", "false");
        launcher.focus();
    }

    function bubble(cls, text) {
        var el = document.createElement("div");
        el.className = cls;
        el.textContent = text;
        log.appendChild(el);
        log.scrollTop = log.scrollHeight;
        return el;
    }

    function thinking() {
        var el = document.createElement("div");
        el.className = "assistant-dots";
        el.innerHTML = "<i></i><i></i><i></i>";
        log.appendChild(el);
        log.scrollTop = log.scrollHeight;
        return el;
    }

    function ask(question) {
        question = (question || "").trim();
        if (busy || question === "") { return; }

        chips.hidden = true;
        bubble("assistant-msg me", question);
        input.value = "";
        input.style.height = "auto";
        busy = true;
        send.disabled = true;
        var wait = thinking();

        fetch("/assistant/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question }),
            credentials: "same-origin"
        }).then(function (res) {
            return res.json().catch(function () { return {}; });
        }).then(function (data) {
            wait.remove();
            var answer = data.answer || "";
            if (answer === "") {
                bubble("assistant-msg err",
                       "The assistant did not answer. Check the application log.");
            } else {
                bubble(data.ok === false ? "assistant-msg err" : "assistant-msg bot", answer);
            }
        }).catch(function () {
            wait.remove();
            bubble("assistant-msg err",
                   "The assistant is not responding. Is the application still running?");
        }).then(function () {
            busy = false;
            send.disabled = false;
            input.focus();
        });
    }

    launcher.addEventListener("click", open);
    closeBtn.addEventListener("click", close);

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        ask(input.value);
    });

    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            ask(input.value);
        }
    });

    input.addEventListener("input", function () {
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 110) + "px";
    });

    chips.addEventListener("click", function (e) {
        if (e.target.classList.contains("assistant-chip")) {
            ask(e.target.textContent);
        }
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && !panel.hidden) { close(); }
    });
})();

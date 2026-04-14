// content.js — injected into every page
(() => {
  let btn = null, popup = null, selectedText = "", currentLength = "medium";

  // ── Explain button on text selection ──
  document.addEventListener("mouseup", e => {
    // Ignore clicks inside our own UI
    if (e.target.closest("#qe-popup") || e.target.closest("#qe-explain-btn")) return;

    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel.toString().trim();

      if (text.length < 3) { removeBtn(); return; }

      selectedText = text;
      showBtn(e.pageX, e.pageY);
    }, 10);
  });

  document.addEventListener("mousedown", e => {
    if (e.target.closest("#qe-popup") || e.target.closest("#qe-explain-btn")) return;
    removeBtn();
    removePopup();
  });

  // ── Show the floating "Explain" button ──
  function showBtn(x, y) {
    removeBtn();
    btn = document.createElement("button");
    btn.id = "qe-explain-btn";
    btn.innerHTML = `<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>Explain`;
    btn.style.left = x + "px";
    btn.style.top = (y + 10) + "px";
    btn.addEventListener("click", onExplainClick);
    document.body.appendChild(btn);
  }

  function removeBtn() {
    if (btn) { btn.remove(); btn = null; }
  }

  // ── Popup creation ──
  function onExplainClick(e) {
    e.stopPropagation();
    const bx = parseInt(btn.style.left), by = parseInt(btn.style.top);
    removeBtn();
    showPopup(bx, by, selectedText);
  }

  function showPopup(x, y, text) {
    removePopup();
    popup = document.createElement("div");
    popup.id = "qe-popup";

    // Keep popup within viewport
    const vw = window.innerWidth, vh = window.innerHeight;
    const px = Math.min(x, vw - 420 + window.scrollX);
    const py = y + 10;
    popup.style.left = px + "px";
    popup.style.top = py + "px";

    popup.innerHTML = `
      <div id="qe-popup-header">
        <span>QuickExplain</span>
        <div class="qe-actions">
          <button id="qe-copy" title="Copy">📋</button>
          <button id="qe-close" title="Close">✕</button>
        </div>
      </div>
      <div id="qe-length-bar">
        <button data-len="short">Short</button>
        <button data-len="medium" class="active">Medium</button>
        <button data-len="detailed">Detailed</button>
      </div>
      <div id="qe-popup-body" class="loading">
        <div class="qe-spinner"></div> Explaining…
      </div>`;

    document.body.appendChild(popup);

    // Close
    popup.querySelector("#qe-close").addEventListener("click", removePopup);

    // Copy
    popup.querySelector("#qe-copy").addEventListener("click", () => {
      const body = popup.querySelector("#qe-popup-body");
      navigator.clipboard.writeText(body.textContent).then(() => {
        const btn = popup.querySelector("#qe-copy");
        btn.textContent = "✓";
        setTimeout(() => (btn.textContent = "📋"), 1500);
      });
    });

    // Length toggles
    popup.querySelectorAll("#qe-length-bar button").forEach(b => {
      b.addEventListener("click", () => {
        popup.querySelectorAll("#qe-length-bar button").forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        currentLength = b.dataset.len;
        fetchExplanation(text, currentLength);
      });
    });

    // Drag
    makeDraggable(popup, popup.querySelector("#qe-popup-header"));

    fetchExplanation(text, currentLength);
  }

  function removePopup() {
    if (popup) { popup.remove(); popup = null; }
  }

  // ── Fetch explanation from background ──
  function fetchExplanation(text, length) {
    const body = popup?.querySelector("#qe-popup-body");
    if (!body) return;
    body.className = "loading";
    body.innerHTML = `<div class="qe-spinner"></div> Explaining…`;

    chrome.runtime.sendMessage(
      { action: "explain", text, length, sourceUrl: location.href },
      res => {
        if (!popup) return;
        body.className = "";
        if (res?.error === "NO_API_KEY") {
          body.textContent = "⚠️ No API key set. Click the QuickExplain icon in the toolbar to add your Gemini API key.";
        } else if (res?.error) {
          body.textContent = "❌ " + res.error;
        } else {
          body.innerHTML = formatBullets(res.explanation);
        }
      }
    );
  }

  // ── Format response as styled bullets ──
  function formatBullets(text) {
    const lines = text.split("\n").map(l => l.replace(/^[\s•\-\*]+/, "").trim()).filter(Boolean);
    if (lines.length <= 1) {
      return `<div class="qe-bullet"><span>${escHtml(lines[0] || text)}</span></div>`;
    }
    return lines.map(l => `<div class="qe-bullet"><span>${escHtml(l)}</span></div>`).join("");
  }

  function escHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  // ── Draggable helper ──
  function makeDraggable(el, handle) {
    let ox, oy, sx, sy;
    handle.addEventListener("mousedown", e => {
      e.preventDefault();
      ox = e.clientX; oy = e.clientY;
      sx = parseInt(el.style.left); sy = parseInt(el.style.top);
      const onMove = e2 => {
        el.style.left = sx + (e2.clientX - ox) + "px";
        el.style.top  = sy + (e2.clientY - oy) + "px";
      };
      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
      };
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });
  }
})();
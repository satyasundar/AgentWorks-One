// popup.js — handles settings & history UI

const $ = s => document.querySelector(s);

// ── Tab switching ──
document.querySelectorAll(".tabs button").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    $(`#tab-${tab.dataset.tab}`).classList.add("active");
    if (tab.dataset.tab === "history") loadHistory();
  });
});

// ── Load saved settings ──
chrome.storage.local.get(["apiKey", "defaultLength"], data => {
  if (data.apiKey) $("#apiKey").value = data.apiKey;
  if (data.defaultLength) $("#defaultLength").value = data.defaultLength;
});

// ── Save settings ──
$("#saveBtn").addEventListener("click", () => {
  const key = $("#apiKey").value.trim();
  const len = $("#defaultLength").value;
  if (!key) {
    $("#status").textContent = "⚠️ Please enter an API key.";
    $("#status").style.color = "#ea4335";
    return;
  }
  chrome.storage.local.set({ apiKey: key, defaultLength: len }, () => {
    $("#status").textContent = "✓ Settings saved!";
    $("#status").style.color = "#0d904f";
    setTimeout(() => ($("#status").textContent = ""), 2000);
  });
});

// ── History ──
function loadHistory() {
  chrome.runtime.sendMessage({ action: "getHistory" }, history => {
    const list = $("#historyList");
    const clearBtn = $("#clearBtn");

    if (!history || history.length === 0) {
      list.innerHTML = `<div class="empty-state">No explanations yet. Select text on any page and click "Explain"!</div>`;
      clearBtn.style.display = "none";
      return;
    }

    clearBtn.style.display = "inline-block";
    list.innerHTML = history.map(h => `
      <div class="history-item" data-id="${h.id}">
        <div class="selected-text">"${escHtml(h.selectedText)}"</div>
        <div class="explanation">${escHtml(h.explanation)}</div>
        <div class="meta">${formatDate(h.timestamp)} · ${h.length} · ${shortUrl(h.sourceUrl)}</div>
      </div>
    `).join("");

    list.querySelectorAll(".history-item").forEach(item => {
      item.addEventListener("click", () => item.classList.toggle("expanded"));
    });
  });
}

$("#clearBtn").addEventListener("click", () => {
  chrome.runtime.sendMessage({ action: "clearHistory" }, () => loadHistory());
});

// ── Helpers ──
function escHtml(s) {
  const d = document.createElement("div");
  d.textContent = s || "";
  return d.innerHTML;
}

function formatDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
      " " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  } catch { return ""; }
}

function shortUrl(url) {
  try { return new URL(url).hostname; } catch { return ""; }
}
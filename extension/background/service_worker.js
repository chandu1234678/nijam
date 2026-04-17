/**
 * PiNE AI — Background Service Worker (Manifest V3)
 *
 * Responsibilities:
 *  - Keep backend alive (alarm-based ping every 4 min)
 *  - Context menu: "TruthScan this" on selected text
 *  - Keyboard shortcuts:
 *      Ctrl+Shift+Y  — open popup
 *      Ctrl+Shift+U  — fact-check selected text
 *      Ctrl+Shift+L  — fact-check visible page text
 *  - Message relay from content script
 */

// ── Backend URL (reads from storage if overridden in settings) ────────────────
// Default points to production Render deployment
let API_BASE = "https://fake-news-analyzer-j6ka.onrender.com";

chrome.storage.local.get("apiBase", ({ apiBase }) => {
  if (apiBase) API_BASE = apiBase;
});

// ── Keep-alive ────────────────────────────────────────────────────────────────
function pingBackend() {
  fetch(`${API_BASE}/health`, { method: "HEAD" }).catch(() => {});
}

// ── Install / update ──────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(({ reason }) => {
  // Context menu
  chrome.contextMenus.create({
    id:       "analyze-fake-news",
    title:    "🔍 TruthScan with PiNE AI",
    contexts: ["selection"],
  });

  // Alarm-based keep-alive (MV3 service workers can be suspended;
  // setInterval is unreliable — alarms survive suspension)
  chrome.alarms.create("keepAlive", { periodInMinutes: 4 });

  // Ping immediately on install/update
  pingBackend();

  if (reason === "install") {
    // Show a one-time welcome notification
    chrome.notifications.create("pine-welcome", {
      type:    "basic",
      iconUrl: chrome.runtime.getURL("icons/icon128.png"),
      title:   "PiNE AI installed",
      message: "Press Ctrl+Shift+Y to open, or right-click any text to fact-check.",
    });
  }
});

// ── Alarm handler ─────────────────────────────────────────────────────────────
chrome.alarms.onAlarm.addListener(({ name }) => {
  if (name === "keepAlive") pingBackend();
});

// ── Shared helpers ────────────────────────────────────────────────────────────

/**
 * Open the PiNE AI popup window anchored to the top-right of the current window.
 */
function openAnalysisPopup() {
  chrome.windows.getCurrent((win) => {
    const width  = 440;
    const height = 640;
    const left   = Math.max(0, (win.left + win.width) - width - 20);
    const top    = win.top + 60;
    chrome.windows.create({
      url:     chrome.runtime.getURL("popup/popup.html"),
      type:    "popup",
      width, height, left, top,
      focused: true,
    });
  });
}

/**
 * Store text in local storage and open the popup.
 * The popup reads selectedText + pendingAnalysis on load and auto-sends.
 */
function openPopupWithText(text) {
  const safeText = (text || "").trim();
  chrome.storage.local.set(
    { selectedText: safeText, pendingAnalysis: !!safeText },
    openAnalysisPopup
  );
}

/**
 * Get the currently selected text from a tab via scripting injection.
 */
async function getSelectedTextFromPage(tabId) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func:   () => (window.getSelection()?.toString() ?? "").trim(),
    });
    return results?.[0]?.result || "";
  } catch {
    return "";
  }
}

/**
 * Get the main visible text from a tab (article > main > body, max 1200 chars).
 */
async function getVisiblePageText(tabId) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        const el = document.querySelector("article, main, [role='main']") || document.body;
        return (el?.innerText || "").replace(/\s+/g, " ").trim().slice(0, 1200);
      },
    });
    return results?.[0]?.result || "";
  } catch {
    return "";
  }
}

/**
 * Get the currently active tab in the focused window.
 */
async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs?.[0] ?? null;
}

/**
 * Show a brief notification (used for shortcut feedback when no text found).
 */
function notify(message) {
  chrome.notifications.create({
    type:    "basic",
    iconUrl: chrome.runtime.getURL("icons/icon48.png"),
    title:   "PiNE AI",
    message,
  });
}

// ── Context menu ──────────────────────────────────────────────────────────────
chrome.contextMenus.onClicked.addListener((info) => {
  if (info.menuItemId === "analyze-fake-news") {
    openPopupWithText(info.selectionText || "");
  }
});

// ── Keyboard shortcuts ────────────────────────────────────────────────────────
chrome.commands.onCommand.addListener(async (command) => {
  // Ctrl+Shift+Y — just open the popup
  if (command === "open-factchecker") {
    openPopupWithText("");
    return;
  }

  const tab = await getActiveTab();

  // Ctrl+Shift+U — fact-check selected text
  if (command === "analyze-selected-text") {
    if (!tab?.id) { openPopupWithText(""); return; }
    const text = await getSelectedTextFromPage(tab.id);
    if (text) {
      openPopupWithText(text);
    } else {
      notify("No text selected. Select some text on the page first.");
      openPopupWithText("");
    }
    return;
  }

  // Ctrl+Shift+L — fact-check visible page text
  if (command === "analyze-current-page") {
    if (!tab?.id) { openPopupWithText(""); return; }
    const text = await getVisiblePageText(tab.id);
    if (text) {
      openPopupWithText(text);
    } else {
      notify("Could not extract text from this page.");
      openPopupWithText("");
    }
  }
});

// ── Messages from content script / popup ─────────────────────────────────────
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  switch (message.type) {
    case "TEXT_SELECTED":
      // Content script reports a text selection (passive — no popup)
      chrome.storage.local.set({ selectedText: message.payload || "" });
      break;

    case "OPEN_POPUP_WITH_TEXT":
      // Any page can request the popup with specific text
      openPopupWithText(message.text || "");
      break;

    case "PING_BACKEND":
      // Popup can request an immediate ping (e.g. on load to check connectivity)
      pingBackend();
      break;

    case "GET_API_BASE":
      // Popup asks for the current API base URL
      sendResponse({ apiBase: API_BASE });
      break;

    case "SET_API_BASE":
      // Settings page updates the API base URL
      if (message.apiBase) {
        API_BASE = message.apiBase;
        chrome.storage.local.set({ apiBase: API_BASE });
      }
      break;
  }
  // Return true to keep the message channel open for async sendResponse
  return true;
});

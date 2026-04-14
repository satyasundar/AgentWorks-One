// background.js — handles Gemini API calls and history

const LENGTH_MAP = {
  short: "in about 50 words",
  medium: "in about 100 words",
  detailed: "in about 200 words"
};

chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  if (req.action === "explain") {
    handleExplain(req.text, req.length || "medium", req.sourceUrl)
      .then(sendResponse)
      .catch(err => sendResponse({ error: err.message }));
    return true; // keep channel open for async
  }

  if (req.action === "getHistory") {
    chrome.storage.local.get({ history: [] }, data => sendResponse(data.history));
    return true;
  }

  if (req.action === "clearHistory") {
    chrome.storage.local.set({ history: [] }, () => sendResponse({ ok: true }));
    return true;
  }
});

async function handleExplain(text, length, sourceUrl) {
  const { apiKey } = await chrome.storage.local.get("apiKey");
  if (!apiKey) return { error: "NO_API_KEY" };

  const prompt = `You are a helpful technical explainer. Explain the following extract ${LENGTH_MAP[length]}. Format your response as bullet points for easy reading:\n- Start each bullet with "• "\n- Keep each bullet to 1-2 sentences\n- Use simple, clear language\n- If it contains code, explain what it does\n- Do not use markdown formatting, headers, or bold text\n- Just return the bullet points, no intro or summary line\n\nExtract:\n"""${text}"""`;

  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          generationConfig: {
            temperature: 0.4,
            maxOutputTokens: 512
          }
        })
      }
    );

    const data = await res.json();

    if (data.error) return { error: data.error.message || "Gemini API error" };

    const explanation =
      data.candidates?.[0]?.content?.parts?.[0]?.text || "No explanation returned.";

    // Save to history
    const { history = [] } = await chrome.storage.local.get("history");
    history.unshift({
      id: Date.now(),
      selectedText: text.substring(0, 200),
      explanation,
      length,
      sourceUrl: sourceUrl || "",
      timestamp: new Date().toISOString()
    });
    // Keep last 100 entries
    await chrome.storage.local.set({ history: history.slice(0, 100) });

    return { explanation };
  } catch (e) {
    return { error: "Network error: " + e.message };
  }
}
const MODELS = ["gemini-3.8-flash", "gemini-3-flash-preview"];

module.exports = async (req, res) => {
  if (req.method !== "POST") return res.status(405).json({ error: "Use POST" });

  const question = ((req.body && req.body.question) || "").trim();
  if (!question || question.length > 300) {
    return res.status(400).json({ error: "Enter a question under 300 characters." });
  }

  const system = `You are a calculus teacher who explains concepts, not memorized formulas.
Reply with ONLY a JSON object, no other text, in this exact shape:
{"explanation": "...", "visual": {"type": "tangent" or "area", "f": "...", "xmin": number, "xmax": number, "a": number, "b": number}}
Rules:
- explanation: under 120 words. Start with the intuition in plain words, then connect it to the formula.
- f: a function of x written for math.js, like "x^2" or "sin(x)". Use only x, numbers, + - * / ^, parentheses, sin, cos, exp, log, sqrt.
- tangent: "a" is where the tangent line starts. Pick a between xmin and xmax.
- area: "a" and "b" are the area bounds, with xmin <= a < b <= xmax.
- Always include all six visual fields.`;

  let lastError = "unknown";

  for (const model of MODELS) {
    try {
      const r = await fetch(
        "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent",
        {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "x-goog-api-key": process.env.GEMINI_API_KEY
          },
          body: JSON.stringify({
            systemInstruction: { parts: [{ text: system }] },
            contents: [{ role: "user", parts: [{ text: question }] }],
            generationConfig: { responseMimeType: "application/json" }
          })
        }
      );
      const data = await r.json();

      if (!r.ok) {
        lastError = model + ": " + ((data && data.error && data.error.message) || r.status);
        console.error("Gemini error:", lastError);
        continue; // try the next model
      }

      const text = data.candidates[0].content.parts.map(p => p.text || "").join("");
      const parsed = JSON.parse(text.replace(/```json|```/g, "").trim());

      const v = parsed.visual;
      const ok =
        parsed.explanation && v &&
        ["tangent", "area"].includes(v.type) &&
        typeof v.f === "string" && /^[0-9a-z+\-*\/^().\s]{1,60}$/i.test(v.f) &&
        [v.xmin, v.xmax, v.a, v.b].every(n => typeof n === "number") &&
        v.xmin < v.xmax;
      if (!ok) {
        lastError = model + ": unusable output";
        continue;
      }

      return res.status(200).json(parsed);
    } catch (e) {
      lastError = model + ": " + e.message;
      console.error(e);
    }
  }

  return res.status(502).json({ error: "AI service error: " + lastError });
};

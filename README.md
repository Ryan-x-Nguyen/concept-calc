# Concept Calc

A concept-first calculus explainer. Type a question like "Why does the derivative of x^2 equal 2x?" and get a short plain-language explanation plus an interactive graph you can play with.

**Live demo:** [([https://concept-calc.vercel.app/])]

## Why I built it
Most students memorize calculus formulas instead of understanding the ideas behind them. Concept Calc shows the intuition visually first, then connects it to the formula.

## What it does
- Takes a calculus question in plain English
- Returns a short explanation that starts with intuition, not formulas
- Draws an interactive visual:
  - **Tangent line:** drag a slider to move a point along the curve and watch the slope change
  - **Area (Riemann sum):** drag a slider to add rectangles and watch the estimate approach the true area

## How it works
Browser (index.html) → /api/explain (Vercel serverless function) → Gemini API → validated JSON → graph rendered with math.js and Plotly

1. The frontend sends the question to a serverless function on Vercel.
2. The function sends the question to the Gemini API with a system prompt that forces a strict JSON reply: an explanation plus visual settings (type, function, range).
3. The backend validates the reply (allowed visual types, safe function characters, numeric ranges) before sending it back, so the AI cannot make the page run arbitrary code.
4. The frontend plots the function with math.js and Plotly and adds the interactive slider.
5. If one model is busy or unavailable, the backend automatically tries a fallback model.

## Stack
- Gemini API (free tier)
- Vercel serverless functions (Node.js)
- HTML and JavaScript, math.js, Plotly
- GitHub for version control and deployment
- Built with AI assistance (Claude) for writing and debugging code

## Testing
I tested the app manually with test questions, including edge cases like gibberish and non-calculus input. Results are in [TESTS.md](TESTS.md): all passed.

## Known issues and what I learned
See [BUGS.md](BUGS.md) for the problems I hit (retired model name, high-demand errors) and how I fixed and verified each one.

## Limitations
- Only two visual types so far
- Free-tier rate limits and occasional slow responses
- No accounts or saved history
- Explanations are AI-generated and may contain mistakes, so double-check anything important

## Next steps
- Add more visuals (limits, derivatives as a graph, optimization)
- Step-by-step practice problems with feedback
- Automated tests instead of manual ones
- Better handling of questions outside the supported visuals

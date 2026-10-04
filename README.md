# Concept Calc

A concept-first calculus explainer. Type a question like "Why does the derivative of x^2 equal 2x?" and get a short plain-language explanation plus an interactive graph you can play with.

**Live demo:** (paste your Vercel link here)

## Why I built it
Most students memorize calculus formulas instead of understanding the ideas behind them. Concept Calc shows the intuition visually first, then connects it to the formula. It comes from tutoring AP Calculus students.

## What it does
- Takes a calculus question in plain English
- The AI calls real math tools to get exact numbers instead of guessing
- Returns a short explanation that starts with intuition, then quotes the tool results
- Draws an interactive visual:
  - **Tangent line:** drag a slider to move a point along the curve and watch the slope change
  - **Area (Riemann sum):** drag a slider to add rectangles and watch the estimate approach the true area
- Shows which tools the AI called and what they returned

## How it works
Browser (index.html) → /api/explain (Vercel Python serverless function) → Gemini API with tool calling → validated JSON → graph rendered with math.js and Plotly

1. The frontend sends the question to a Python serverless function on Vercel.
2. The function sends the question to the Gemini API, along with two tool definitions: `derivative_at` (slope of a function at a point) and `riemann_sum` (area estimate with n rectangles).
3. When the model calls a tool, the backend runs it with a safe expression evaluator (no `eval`, only allowed operations and functions) and sends the real result back to the model. This loop runs for a few steps at most.
4. The model writes its explanation using the tool results and returns strict JSON: the explanation plus visual settings (type, function, range).
5. The backend validates the reply (allowed visual types, safe function characters, numeric ranges) before returning it, so the model's output is never executed as code.
6. The frontend plots the function with math.js and Plotly and adds the interactive slider.
7. If one model is busy or unavailable, the backend automatically falls back to another.

## Stack
- Python (serverless backend, standard library only)
- Gemini API (free tier) with function calling
- Vercel serverless functions
- HTML and JavaScript, math.js, Plotly
- GitHub for version control and auto-deploy
- Built with AI assistance (Claude) for writing and debugging code

## Testing
I tested the app manually with (...) questions, including edge cases like gibberish and non-calculus input. Results are in [TESTS.md](TESTS.md): (...) of (...) passed.

## Bugs and lessons
See [BUGS.md](BUGS.md) for the problems I hit (retired model name, high-demand errors) and how I fixed and verified each one.

## Limitations
- Only two visual types so far
- Free-tier rate limits and occasional slow responses, since tool calling needs multiple model calls
- No accounts or saved history
- Explanations are AI-generated and may contain mistakes, so double-check anything important

## Next steps
- More tools and visuals (limits, optimization, second derivative)
- Step-by-step practice problems with feedback
- Automated tests instead of manual ones
- Better handling of questions outside the supported visuals

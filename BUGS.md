# Bug Log

## Bug 1: "AI service error" with no explanation
**What happened:** Every request to the live site returned a generic "AI service error". The page gave no clue why.
**How I found the cause:** I couldn't open Vercel's logs, so I changed the backend to pass the API's own error message through to the page. The message then said the model gemini-2.5-flash was no longer available to new users.
**Fix:** Updated the model name in api/explain.js to the replacement Google named in the error.
**Verified:** Redeployed on Vercel and asked "Why does the derivative of x^2 equal 2x?". It returned an explanation and a working graph.

## Bug 2: "High demand" errors from the free tier
**What happened:** Requests intermittently failed with "This model is currently experiencing high demand."
**How I found the cause:** The surfaced error text said the failure was on Google's side and temporary, not a bug in my code.
**Fix:** Rewrote the backend to loop through a list of models and fall back to the next one if a request fails or returns unusable output.
**Verified:** Redeployed and re-ran my test questions in TESTS.md.

## Bug 3: Slow responses
**What happened:** The app sometimes spun for a long time before answering.
**Suspected cause:** Free-tier load and the model's default extra reasoning time.
**Status:** (Write what you actually did. Delete this bug if it went away on its own and you changed nothing.)

## Lessons
- Never show users a generic error. Surface the real message while developing.
- AI model names get retired, so don't hardcode a single one.
- Validate AI output before using it, because the AI isn't guaranteed to return what you asked for.

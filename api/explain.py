from http.server import BaseHTTPRequestHandler
import json, os, re, ast, math
import urllib.request, urllib.error

MODELS = ["gemini-3.8-flash", "gemini-3-flash-preview"]
SAFE = re.compile(r"^[0-9a-z+\-*/^().\s]{1,60}$", re.I)
FUNCS = {"sin": math.sin, "cos": math.cos, "tan": math.tan,
         "exp": math.exp, "log": math.log, "sqrt": math.sqrt}

SYSTEM = """You are a calculus teacher who explains concepts, not memorized formulas.
You have tools. For a tangent/derivative question, call derivative_at. For an area/integral question, call riemann_sum with a small n like 4 and again with a large n like 100. Use the returned numbers in your explanation.
After using tools, reply with ONLY a JSON object, no other text, in this exact shape:
{"explanation": "...", "visual": {"type": "tangent" or "area", "f": "...", "xmin": number, "xmax": number, "a": number, "b": number}}
Rules:
- explanation: under 120 words. Start with intuition in plain words, then connect it to the formula and quote the tool results.
- f: a function of x, like "x^2" or "sin(x)". Use only x, numbers, + - * / ^, parentheses, sin, cos, exp, log, sqrt.
- tangent: "a" is where the tangent line starts, between xmin and xmax.
- area: "a" and "b" are the area bounds, with xmin <= a < b <= xmax.
- Always include all six visual fields."""

DECLARATIONS = [
    {
        "name": "derivative_at",
        "description": "Numerically compute f(x) and the slope of f at a point x.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "f": {"type": "STRING", "description": "Function of x, like x^2"},
                "x": {"type": "NUMBER", "description": "Point to evaluate at"},
            },
            "required": ["f", "x"],
        },
    },
    {
        "name": "riemann_sum",
        "description": "Estimate the area under f from a to b using n left rectangles.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "f": {"type": "STRING", "description": "Function of x"},
                "a": {"type": "NUMBER"},
                "b": {"type": "NUMBER"},
                "n": {"type": "NUMBER", "description": "Number of rectangles (1 to 1000)"},
            },
            "required": ["f", "a", "b", "n"],
        },
    },
]


# ---------- safe math evaluator (never uses eval) ----------
def make_f(expr):
    if not isinstance(expr, str) or not SAFE.match(expr):
        raise ValueError("bad function")
    tree = ast.parse(expr.replace("^", "**"), mode="eval")

    def ev(n, x):
        if isinstance(n, ast.Expression):
            return ev(n.body, x)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.Name) and n.id == "x":
            return x
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = ev(n.operand, x)
            return v if isinstance(n.op, ast.UAdd) else -v
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left, x), ev(n.right, x)
            if isinstance(n.op, ast.Add): return a + b
            if isinstance(n.op, ast.Sub): return a - b
            if isinstance(n.op, ast.Mult): return a * b
            if isinstance(n.op, ast.Div): return a / b
            if isinstance(n.op, ast.Pow):
                if abs(b) > 50:
                    raise ValueError("exponent too large")
                return a ** b
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id in FUNCS and len(n.args) == 1 and not n.keywords):
            return FUNCS[n.func.id](ev(n.args[0], x))
        raise ValueError("unsupported expression")

    def f(x):
        r = ev(tree, x)
        if isinstance(r, complex) or not math.isfinite(r):
            raise ValueError("not a real number at x=" + str(x))
        return r

    return f


# ---------- tools the AI can call ----------
def derivative_at(f, x):
    fn = make_f(f)
    h = 1e-5
    return {"f_at_x": fn(x), "slope": (fn(x + h) - fn(x - h)) / (2 * h)}


def riemann_sum(f, a, b, n):
    fn = make_f(f)
    n = max(1, min(int(n), 1000))
    dx = (b - a) / n
    total = sum(fn(a + i * dx) * dx for i in range(n))
    return {"estimate": total, "rectangles": n}


TOOLS = {"derivative_at": derivative_at, "riemann_sum": riemann_sum}


# ---------- Gemini calls ----------
def call_gemini(model, contents):
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + model + ":generateContent")
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": contents,
        "tools": [{"functionDeclarations": DECLARATIONS}],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json",
                 "x-goog-api-key": os.environ.get("GEMINI_API_KEY", "")},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read())["error"]["message"]
        except Exception:
            msg = str(e.code)
        raise RuntimeError(msg)
    return data["candidates"][0]["content"]


def run(model, question):
    contents = [{"role": "user", "parts": [{"text": question}]}]
    tools_used = []
    for _ in range(4):
        content = call_gemini(model, contents)
        parts = content.get("parts", [])
        calls = [p for p in parts if "functionCall" in p]
        if not calls:
            return "".join(p.get("text", "") for p in parts), tools_used
        contents.append(content)  # send the model's own turn back unchanged
        responses = []
        for p in calls:
            name = p["functionCall"]["name"]
            args = p["functionCall"].get("args", {})
            try:
                result = TOOLS[name](**args)
                tools_used.append({"name": name, "args": args, "result": result})
            except Exception as e:
                result = {"error": str(e)}
            responses.append({"functionResponse": {"name": name, "response": {"result": result}}})
        contents.append({"role": "user", "parts": responses})
    raise RuntimeError("too many tool steps")


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def valid(parsed):
    v = parsed.get("visual")
    return bool(
        parsed.get("explanation") and isinstance(v, dict)
        and v.get("type") in ("tangent", "area")
        and isinstance(v.get("f"), str) and SAFE.match(v["f"])
        and all(is_num(v.get(k)) for k in ("xmin", "xmax", "a", "b"))
        and v["xmin"] < v["xmax"]
    )


# ---------- Vercel handler ----------
class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
            question = str(body.get("question", "")).strip()
        except Exception:
            return self._send(400, {"error": "Bad request."})

        if not question or len(question) > 300:
            return self._send(400, {"error": "Enter a question under 300 characters."})

        last_error = "unknown"
        for model in MODELS:
            try:
                text, tools_used = run(model, question)
                parsed = json.loads(re.sub(r"```json|```", "", text).strip())
                if not valid(parsed):
                    last_error = model + ": unusable output"
                    continue
                parsed["tools"] = tools_used
                return self._send(200, parsed)
            except Exception as e:
                last_error = model + ": " + str(e)
                print(last_error)
        return self._send(502, {"error": "AI service error: " + last_error})

    def do_GET(self):
        self._send(405, {"error": "Use POST"})

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json

# ────────────────────────────────────
# App
# ────────────────────────────────────
app = FastAPI(title="Lashby Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────
# Paths
# ────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

OFFERS_FILE = STATIC_DIR / "offers_snapshot.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"
TOKENS_FILE = DATA_DIR / "tokens.json"

STATIC_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

if not BOOKINGS_FILE.exists():
    BOOKINGS_FILE.write_text("[]", encoding="utf-8")

if not TOKENS_FILE.exists():
    TOKENS_FILE.write_text("{}", encoding="utf-8")

# ────────────────────────────────────
# Models
# ────────────────────────────────────
class Booking(BaseModel):
    name: str
    service: str
    addon: str | None = None
    total_price: int
    date: str
    start_time: str
    end_time: str
    token: str

# ────────────────────────────────────
# Static
# ────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ────────────────────────────────────
# Helpers
# ────────────────────────────────────
def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path: Path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def booking_exists(date, start, end):
    bookings = load_json(BOOKINGS_FILE, [])
    for b in bookings:
        if (
            b.get("date") == date
            and b.get("start_time") == start
            and b.get("end_time") == end
        ):
            return True
    return False

# ────────────────────────────────────
# Routes
# ────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend kjører"}

@app.get("/booking", response_class=HTMLResponse)
def booking_page():
    file = STATIC_DIR / "booking.html"
    if not file.exists():
        raise HTTPException(404, "booking.html ikke funnet")
    return file.read_text(encoding="utf-8")

# ────────────────────────────────────
# SERVICES (ENDLIG, ROBUST)
# ────────────────────────────────────
@app.get("/services")
def services():
    try:
        snapshot = json.loads(OFFERS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "error": "Failed to parse offers_snapshot.json",
            "details": str(e)
        }
    result = []

    for s in snapshot.get("services", []):
        result.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "price": s.get("price", 0),
            "category": "Behandling"
        })

    for p in snapshot.get("packages", []):
        result.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "price": p.get("price", p.get("original_price", 0)),
            "category": "Pakke"
        })

    for a in snapshot.get("addons", []):
        result.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "price": a.get("price", 0),
            "category": "Tillegg"
        })

    return result

# ────────────────────────────────────
# Tokens
# ────────────────────────────────────
@app.post("/tokens/{token}")
def register_token(token: str):
    tokens = load_json(TOKENS_FILE, {})
    tokens[token] = "free"
    save_json(TOKENS_FILE, tokens)
    return {"ok": True}

# ────────────────────────────────────
# Booking
# ────────────────────────────────────
@app.post("/bookings")
def create_booking(b: Booking):
    tokens = load_json(TOKENS_FILE, {})

    if b.token not in tokens:
        raise HTTPException(400, "Ugyldig link")

    if tokens[b.token] == "used":
        raise HTTPException(400, "Link allerede brukt")

    if booking_exists(b.date, b.start_time, b.end_time):
        raise HTTPException(400, "Tiden er allerede booket")

    bookings = load_json(BOOKINGS_FILE, [])
    bookings.append(b.dict())
    save_json(BOOKINGS_FILE, bookings)

    tokens[b.token] = "used"
    save_json(TOKENS_FILE, tokens)

    return {"success": True}

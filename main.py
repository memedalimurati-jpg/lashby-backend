from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json

app = FastAPI(title="Lashby Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

OFFERS_FILE = STATIC_DIR / "offers_snapshot.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"
TOKENS_FILE = DATA_DIR / "tokens.json"

DATA_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

if not BOOKINGS_FILE.exists():
    BOOKINGS_FILE.write_text("[]", encoding="utf-8")

if not TOKENS_FILE.exists():
    TOKENS_FILE.write_text("{}", encoding="utf-8")

class Booking(BaseModel):
    name: str
    service: str
    addon: str | None = None
    total_price: int
    date: str
    start_time: str
    end_time: str
    token: str

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend kjører"}

@app.get("/services")
def services():
    snapshot = load_json(OFFERS_FILE, {})
    result = []

    for s in snapshot.get("services", []):
        result.append({**s, "category": "Behandling"})

    for p in snapshot.get("packages", []):
        result.append({**p, "category": "Pakke"})

    for a in snapshot.get("addons", []):
        result.append({**a, "category": "Tillegg"})

    return result

@app.post("/tokens/{token}")
def register_token(token: str):
    tokens = load_json(TOKENS_FILE, {})
    tokens[token] = "free"
    save_json(TOKENS_FILE, tokens)
    return {"ok": True}

@app.post("/bookings")
def create_booking(b: Booking):
    tokens = load_json(TOKENS_FILE, {})

    if b.token not in tokens:
        raise HTTPException(400, "Ugyldig link")

    if tokens[b.token] == "used":
        raise HTTPException(400, "Link allerede brukt")

    bookings = load_json(BOOKINGS_FILE, [])
    bookings.append(b.dict())
    save_json(BOOKINGS_FILE, bookings)

    tokens[b.token] = "used"
    save_json(TOKENS_FILE, tokens)

    return {"success": True}

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

OFFERS_FILE = STATIC_DIR / "offers_snapshot.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"
TOKENS_FILE = DATA_DIR / "tokens.json"

DATA_DIR.mkdir(exist_ok=True)

if not BOOKINGS_FILE.exists():
    BOOKINGS_FILE.write_text("[]", encoding="utf-8")

if not TOKENS_FILE.exists():
    TOKENS_FILE.write_text("{}", encoding="utf-8")

# ────────────────────────────────────
# Static files
# ────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ────────────────────────────────────
# Helpers
# ────────────────────────────────────
def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"JSON parse error: {str(e)}"
        )

def load_bookings():
    return load_json(BOOKINGS_FILE)

def save_bookings(data):
    BOOKINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def load_tokens():
    return load_json(TOKENS_FILE)

def save_tokens(data):
    TOKENS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def booking_exists(date, start, end):
    for b in load_bookings():
        if (
            b["date"] == date and
            b["start_time"] == start and
            b["end_time"] == end
        ):
            return True
    return False

# ────────────────────────────────────
# Routes
# ────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend kjører"}

# Booking side
@app.get("/booking", response_class=HTMLResponse)
def booking_page():
    file = STATIC_DIR / "booking.html"
    if not file.exists():
        raise HTTPException(status_code=404, detail="booking.html ikke funnet")
    return file.read_text(encoding="utf-8")

# ✅ OFFERS SNAPSHOT – DENNE ER KRITISK
@app.get("/offers_snapshot")
def offers_snapshot():
    if not OFFERS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="offers_snapshot.json ikke funnet"
        )
    return JSONResponse(load_json(OFFERS_FILE))

# Hent bookinger (debug/admin)
@app.get("/bookings")
def get_bookings():
    return load_bookings()

# Motta booking
@app.post("/bookings")
def create_booking(payload: dict):
    required = ["name", "service", "date", "start_time", "end_time", "token"]
    for r in required:
        if r not in payload:
            raise HTTPException(status_code=400, detail=f"Mangler felt: {r}")

    tokens = load_tokens()

    if payload["token"] not in tokens:
        raise HTTPException(status_code=400, detail="Ugyldig booking-link")

    if tokens[payload["token"]] == "used":
        raise HTTPException(status_code=400, detail="Link allerede brukt")

    if booking_exists(
        payload["date"],
        payload["start_time"],
        payload["end_time"]
    ):
        raise HTTPException(status_code=400, detail="Tiden er allerede booket")

    bookings = load_bookings()
    bookings.append({
        "name": payload["name"],
        "service": payload["service"],
        "date": payload["date"],
        "start_time": payload["start_time"],
        "end_time": payload["end_time"]
    })
    save_bookings(bookings)

    tokens[payload["token"]] = "used"
    save_tokens(tokens)

    return {"success": True, "message": "Booking bekreftet"}

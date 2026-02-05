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

# ────────────────────────────────────
# CORS
# ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────
# Paths (RENDER-SIKKER)
# ────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

BOOKINGS_FILE = DATA_DIR / "bookings.json"
TOKENS_FILE = DATA_DIR / "tokens.json"

# ────────────────────────────────────
# Ensure directories
# ────────────────────────────────────
if not STATIC_DIR.exists():
    raise RuntimeError(f"STATIC directory missing: {STATIC_DIR}")

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
    date: str
    start_time: str
    end_time: str
    token: str

# ────────────────────────────────────
# Static files
# ────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ────────────────────────────────────
# Helpers
# ────────────────────────────────────
def load_bookings():
    return json.loads(BOOKINGS_FILE.read_text(encoding="utf-8"))

def save_bookings(data):
    BOOKINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def load_tokens():
    return json.loads(TOKENS_FILE.read_text(encoding="utf-8"))

def save_tokens(data):
    TOKENS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def booking_exists(date, start, end):
    for b in load_bookings():
        if (
            b["date"] == date
            and b["start_time"] == start
            and b["end_time"] == end
        ):
            return True
    return False

# ────────────────────────────────────
# Routes
# ────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend kjører"}

# Server booking-siden
@app.get("/booking", response_class=HTMLResponse)
def booking_page():
    file = STATIC_DIR / "booking.html"
    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"booking.html ikke funnet ({file})"
        )
    return file.read_text(encoding="utf-8")

# OFFERS SNAPSHOT (STABIL, INGEN 500)
@app.get("/offers_snapshot")
def offers_snapshot():
    file = STATIC_DIR / "offers_snapshot.json"

    if not file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"offers_snapshot.json ikke funnet ({file})"
        )

    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"JSON parse error: {str(e)}"
        )

# Hent alle bookinger
@app.get("/bookings")
def get_bookings():
    return load_bookings()

# Motta booking
@app.post("/bookings")
def create_booking(booking: Booking):
    tokens = load_tokens()

    if booking.token not in tokens:
        raise HTTPException(status_code=400, detail="Ugyldig booking-link")

    if tokens[booking.token] == "used":
        raise HTTPException(status_code=400, detail="Linken er allerede brukt")

    if booking_exists(
        booking.date,
        booking.start_time,
        booking.end_time
    ):
        raise HTTPException(status_code=400, detail="Tiden er allerede booket")

    bookings = load_bookings()
    bookings.append({
        "name": booking.name,
        "service": booking.service,
        "date": booking.date,
        "start_time": booking.start_time,
        "end_time": booking.end_time
    })
    save_bookings(bookings)

    tokens[booking.token] = "used"
    save_tokens(tokens)

    return {"success": True}

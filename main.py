from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json

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
# Paths
# ────────────────────────────────────
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

BOOKINGS_FILE = DATA_DIR / "bookings.json"
TOKENS_FILE = DATA_DIR / "tokens.json"

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
    return (STATIC_DIR / "booking_v2.html").read_text(encoding="utf-8")

# ✅ RIKTIG ROUTE: OFFERS SNAPSHOT
@app.get("/offers_snapshot")
def get_offers_snapshot():
    offers_file = STATIC_DIR / "offers_snapshot.json"

    if not offers_file.exists():
        raise HTTPException(
            status_code=404,
            detail="offers_snapshot.json ikke funnet"
        )

    return json.loads(offers_file.read_text(encoding="utf-8"))

# Hent alle bookinger (admin / debug)
@app.get("/bookings")
def get_bookings():
    return load_bookings()

# Motta booking fra kunde
@app.post("/bookings")
def create_booking(booking: Booking):
    tokens = load_tokens()

    # 1️⃣ Token må finnes
    if booking.token not in tokens:
        raise HTTPException(status_code=400, detail="Ugyldig booking-link")

    # 2️⃣ Token må ikke være brukt
    if tokens[booking.token] == "used":
        raise HTTPException(status_code=400, detail="Denne linken er allerede brukt")

    # 3️⃣ Tid må være ledig
    if booking_exists(
        booking.date,
        booking.start_time,
        booking.end_time
    ):
        raise HTTPException(status_code=400, detail="Tiden er allerede booket")

    # 4️⃣ Lagre booking
    bookings = load_bookings()
    bookings.append({
        "name": booking.name,
        "service": booking.service,
        "date": booking.date,
        "start_time": booking.start_time,
        "end_time": booking.end_time
    })
    save_bookings(bookings)

    # 5️⃣ Marker token som brukt
    tokens[booking.token] = "used"
    save_tokens(tokens)

    return {
        "success": True,
        "message": "Booking bekreftet"
    }

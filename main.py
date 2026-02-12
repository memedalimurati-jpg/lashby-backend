import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# --------------------------------------------------
# APP
# --------------------------------------------------

app = FastAPI(title="Lashby Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_FILE = BASE_DIR / "data" / "bookings.json"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --------------------------------------------------
# MODEL
# --------------------------------------------------

class Booking(BaseModel):
    name: str
    phone: str
    service: str
    addon: str | None = None
    total_price: int
    date: str
    start_time: str
    end_time: str | None = ""

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def load_bookings():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_bookings(bookings):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(bookings, f, indent=2)

# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend running"}

@app.get("/booking", response_class=HTMLResponse)
def booking_page():
    file = STATIC_DIR / "booking.html"
    if not file.exists():
        raise HTTPException(404, "booking.html not found")
    return file.read_text(encoding="utf-8")

@app.get("/bookings")
def get_bookings():
    return load_bookings()

# --------------------------------------------------
# CREATE BOOKING
# --------------------------------------------------

@app.post("/bookings")
def create_booking(b: Booking):

    bookings = load_bookings()

    # 🔥 Sjekk om tiden allerede er brukt
    for existing in bookings:
        if existing["date"] == b.date and existing["start_time"] == b.start_time:
            raise HTTPException(400, "Timen er allerede booket")

    new_booking = {
        "name": b.name,
        "phone": b.phone,
        "service": b.service,
        "addon": b.addon,
        "total_price": b.total_price,
        "date": b.date,
        "start_time": b.start_time,
        "end_time": b.end_time
    }

    bookings.append(new_booking)
    save_bookings(bookings)

    return {"success": True}

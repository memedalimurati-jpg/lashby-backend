from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────
app = FastAPI(
    title="Lashby Backend",
    description="Backend for Lashby booking",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "bookings.json"

# ─────────────────────────────────────────────
# Ensure data folder & file exist
# ─────────────────────────────────────────────
DATA_DIR.mkdir(exist_ok=True)
if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")

# ─────────────────────────────────────────────
# Static files
# ─────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ─────────────────────────────────────────────
# Root / health check
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend is running"}

# ─────────────────────────────────────────────
# Booking page (HTML)
# ─────────────────────────────────────────────
@app.get("/booking", response_class=HTMLResponse)
def booking_page():
    booking_file = STATIC_DIR / "booking.html"
    return booking_file.read_text(encoding="utf-8")

# ─────────────────────────────────────────────
# Get all bookings (used by desktop app)
# ─────────────────────────────────────────────
@app.get("/bookings")
def get_bookings():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

# ─────────────────────────────────────────────
# Create booking (called from booking.html)
# ─────────────────────────────────────────────
@app.post("/bookings")
def create_booking(booking: dict):
    with open(DATA_FILE, encoding="utf-8") as f:
        bookings = json.load(f)

    bookings.append(booking)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(bookings, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "message": "Booking created",
        "booking": booking
    }

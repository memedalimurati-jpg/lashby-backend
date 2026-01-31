from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json

app = FastAPI(title="Lashby Backend")

# ── CORS ─────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths ────────────────────────────
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "bookings.json"

DATA_DIR.mkdir(exist_ok=True)
if not DATA_FILE.exists():
    DATA_FILE.write_text("[]", encoding="utf-8")

# ── Model ────────────────────────────
class Booking(BaseModel):
    name: str
    service: str
    date: str
    start_time: str
    end_time: str

# ── Static (IKKE /booking) ───────────
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ── Routes ───────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend kjører"}

@app.get("/booking", response_class=HTMLResponse)
def booking_page():
    return (STATIC_DIR / "booking.html").read_text(encoding="utf-8")

@app.get("/bookings")
def get_bookings():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

@app.post("/bookings")
def create_booking(booking: Booking):
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    data.append(booking.dict())
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"success": True}

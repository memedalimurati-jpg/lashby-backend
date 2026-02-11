from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json
import uuid

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

print("I AM THE REAL MAIN FILE")

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

STATIC_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

OFFERS_FILE = STATIC_DIR / "offers_snapshot.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"
TOKENS_FILE = DATA_DIR / "tokens.json"

if not BOOKINGS_FILE.exists():
    BOOKINGS_FILE.write_text("[]", encoding="utf-8")

if not TOKENS_FILE.exists():
    TOKENS_FILE.write_text("{}", encoding="utf-8")

# --------------------------------------------------
# MODELS
# --------------------------------------------------

class Booking(BaseModel):
    name: str
    phone: str
    service: str
    addon: str | None = None
    total_price: int
    date: str
    start_time: str
    end_time: str
    token: str

# --------------------------------------------------
# STATIC
# --------------------------------------------------

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print("JSON ERROR:", e)
        return default
def save_json(path: Path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend kjører"}


@app.get("/booking", response_class=HTMLResponse)
def booking_page():
    file = STATIC_DIR / "booking.html"
    if not file.exists():
        raise HTTPException(404, "booking.html ikke funnet")
    return file.read_text(encoding="utf-8")


@app.get("/services")
def services():
    snapshot = load_json(OFFERS_FILE, {})
    return snapshot


@app.get("/bookings")
def get_bookings():
    data = load_json(BOOKINGS_FILE, [])
    print("RETURNING BOOKINGS:", data)
    return data


# --------------------------------------------------
# TOKEN
# --------------------------------------------------

@app.post("/tokens/{token}")
def register_token(token: str):
    tokens = load_json(TOKENS_FILE, {})
    tokens[token] = "free"
    save_json(TOKENS_FILE, tokens)
    print("TOKEN REGISTERED:", token)
    return {"ok": True}


@app.get("/tokens/{token}")
def validate_token(token: str):
    tokens = load_json(TOKENS_FILE, {})

    if token not in tokens:
        raise HTTPException(400, "Ugyldig eller brukt link")

    if tokens[token] == "used":
        raise HTTPException(400, "Ugyldig eller brukt link")

    return {"valid": True}


# --------------------------------------------------
# BOOKING
# --------------------------------------------------

@app.post("/bookings")
def create_booking(b: Booking):

    print("BOOKING RECEIVED:", b)

    tokens = load_json(TOKENS_FILE, {})

    if b.token not in tokens:
        raise HTTPException(400, "Ugyldig link")

    if tokens[b.token] == "used":
        raise HTTPException(400, "Link allerede brukt")

    bookings = load_json(BOOKINGS_FILE, [])

    new_booking = {
        "id": str(uuid.uuid4()),
        "name": b.name,
        "phone": b.phone,
        "service": b.service,
        "addon": b.addon,
        "total_price": b.total_price,
        "date": b.date.strip(),
        "start_time": b.start_time,
        "end_time": b.end_time
    }

    bookings.append(new_booking)

    print("SAVING TO:", BOOKINGS_FILE)
    save_json(BOOKINGS_FILE, bookings)
    print("BOOKING SAVED")

    tokens[b.token] = "used"
    save_json(TOKENS_FILE, tokens)

    return {"success": True}

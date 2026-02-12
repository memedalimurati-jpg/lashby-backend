from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from supabase import create_client
import os

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

print("SUPABASE BACKEND STARTED")

# --------------------------------------------------
# SUPABASE CONFIG
# --------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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
    token: str  # dette er slot_id

# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "Lashby backend med Supabase kjører"}


@app.get("/booking", response_class=HTMLResponse)
def booking_page():
    file = STATIC_DIR / "booking.html"
    if not file.exists():
        raise HTTPException(404, "booking.html ikke funnet")
    return file.read_text(encoding="utf-8")


@app.get("/services")
def services():
    # Hvis du fortsatt bruker offers_snapshot.json kan du beholde dette
    # Eller returnere tom hvis du vil hardkode i HTML
    return {"services": [], "packages": [], "addons": []}


@app.get("/bookings")
def get_bookings():
    response = supabase.table("slots").select("*").execute()
    return response.data


# --------------------------------------------------
# BOOKING (FØRSTE I MØLLA)
# --------------------------------------------------

@app.post("/bookings")
def create_booking(b: Booking):

    print("BOOKING RECEIVED:", b)

    # Første i mølla:
    # Oppdater kun hvis status = available
    response = (
        supabase
        .table("slots")
        .update({
            "status": "booked",
            "name": b.name,
            "phone": b.phone,
            "treatment": b.service
        })
        .eq("id", b.token)
        .eq("status", "available")
        .execute()
    )

    if not response.data:
        raise HTTPException(400, "Link allerede brukt eller ugyldig")

    return {"success": True}

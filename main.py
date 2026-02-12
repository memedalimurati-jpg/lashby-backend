import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from supabase import create_client

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
# SUPABASE
# --------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase environment variables missing")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

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
    end_time: str | None = ""
    token: str

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

# --------------------------------------------------
# BOOKING
# --------------------------------------------------

@app.post("/bookings")
def create_booking(b: Booking):

    print("BOOKING RECEIVED:", b)

    token = b.token.strip()

    # 1️⃣ Finn slot
    slot_response = (
        supabase
        .table("slots")
        .select("*")
        .eq("id", token)
        .execute()
    )

    if not slot_response.data:
        raise HTTPException(400, "Link ugyldig")

    slot = slot_response.data[0]

    if slot["status"] != "available":
        raise HTTPException(400, "Link allerede brukt eller ugyldig")

    # 2️⃣ Oppdater slot
    update_response = (
        supabase
        .table("slots")
        .update({
            "status": "booked",
            "name": b.name,
            "phone": b.phone,
            "service": b.service
        })
        .eq("id", token)
        .execute()
    )

    if not update_response.data:
        raise HTTPException(500, "Kunne ikke oppdatere booking")

    return {"success": True}

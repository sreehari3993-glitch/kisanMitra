from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Farmer Authentication"])

# Default Demo Farmer Profile
DEFAULT_DEMO_USER = {
    "username": "kisan_demo",
    "email": "demo.farmer@krishimitra.gov.in",
    "password": "kisan2025",
    "name": "Ramesh Patel",
    "kisan_id": "IND-KISAN-9024",
    "role": "Verified Lead Farmer",
    "farm_sector": "Punjab Sector 4 / Palakkad Field #12",
    "soil_type": "Alluvial Clay Loam",
    "active_area_acres": 4.5,
    "joined_date": "March 2024",
}


class LoginRequest(BaseModel):
    username_or_email: Optional[str] = None
    username: Optional[str] = None
    name: Optional[str] = None
    password: str


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


@router.get("/demo-credentials", summary="Retrieve default demo user credentials")
def get_demo_credentials() -> Dict[str, Any]:
    """Returns the default pre-configured credentials for quick 1-click demo login."""
    return {
        "username": DEFAULT_DEMO_USER["username"],
        "email": DEFAULT_DEMO_USER["email"],
        "password": DEFAULT_DEMO_USER["password"],
        "name": DEFAULT_DEMO_USER["name"],
        "kisan_id": DEFAULT_DEMO_USER["kisan_id"],
        "farm_sector": DEFAULT_DEMO_USER["farm_sector"],
    }


@router.post("/login", response_model=LoginResponse, summary="Farmer portal login")
def login_farmer(payload: LoginRequest):
    """Authenticates farmer against default demo account or creates personalized session."""
    raw_name_or_user = (payload.name or payload.username or payload.username_or_email or "").strip()
    pwd = (payload.password or "").strip()

    if not raw_name_or_user or not pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name/Username and Password are required.",
        )

    user_lower = raw_name_or_user.lower()

    # 1. Check against primary demo user
    is_demo = (
        user_lower in [
            DEFAULT_DEMO_USER["username"].lower(),
            DEFAULT_DEMO_USER["email"].lower(),
            DEFAULT_DEMO_USER["name"].lower(),
            "ramesh",
            "ramesh patel",
            "demo",
            "kisan",
            "farmer",
            "admin",
        ]
        and (pwd == DEFAULT_DEMO_USER["password"] or pwd in ["demo", "kisan123", "password", "admin123"])
    )

    if is_demo:
        user_profile = {
            "name": DEFAULT_DEMO_USER["name"],
            "username": DEFAULT_DEMO_USER["username"],
            "email": DEFAULT_DEMO_USER["email"],
            "kisan_id": DEFAULT_DEMO_USER["kisan_id"],
            "role": DEFAULT_DEMO_USER["role"],
            "farm_sector": DEFAULT_DEMO_USER["farm_sector"],
            "soil_type": DEFAULT_DEMO_USER["soil_type"],
            "active_area_acres": DEFAULT_DEMO_USER["active_area_acres"],
            "joined_date": DEFAULT_DEMO_USER["joined_date"],
        }
        return LoginResponse(
            token="krishimitra_demo_jwt_token_verified",
            token_type="bearer",
            user=user_profile,
        )

    # 2. Allow personalized login with custom name and password (minimum 3 characters)
    if len(pwd) >= 3:
        clean_input = raw_name_or_user.split("@")[0].strip()
        words = clean_input.split()
        if len(words) == 1:
            display_name = f"Farmer {words[0].capitalize()}"
        else:
            display_name = " ".join(w.capitalize() for w in words)

        clean_slug = "".join(c for c in clean_input.lower() if c.isalnum() or c == "_")
        if not clean_slug:
            clean_slug = "farmer"

        user_profile = {
            "name": display_name,
            "username": clean_slug,
            "email": raw_name_or_user if "@" in raw_name_or_user else f"{clean_slug}@krishimitra.gov.in",
            "kisan_id": f"IND-KISAN-{abs(hash(raw_name_or_user)) % 9000 + 1000}",
            "role": "Registered Farmer",
            "farm_sector": "Field Cluster #7 - Precision Plot",
            "soil_type": "Alluvial Loam",
            "active_area_acres": 3.0,
            "joined_date": "September 2026",
        }
        return LoginResponse(
            token=f"krishimitra_user_token_{abs(hash(raw_name_or_user))}",
            token_type="bearer",
            user=user_profile,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Password must be at least 3 characters. Or click 'Auto-fill Demo' for instant access.",
    )


@router.get("/me", summary="Get authenticated profile details")
def get_current_user_profile(token: Optional[str] = None):
    """Returns profile for active session."""
    return DEFAULT_DEMO_USER

from fastapi import APIRouter


router = APIRouter(tags=["auth"])


@router.get("/auth/status")
async def auth_status() -> dict[str, str]:
    return {"status": "supabase-auth-planned"}

from fastapi import APIRouter

from ..dependencies.auth import CurrentUser

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/me")
def get_me(current_user: CurrentUser):
    return {
        "id": current_user.id,
        "subject": current_user.auth0_subject,
    }

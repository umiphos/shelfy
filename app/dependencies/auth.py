from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..security.auth0 import Auth0Principal, get_auth0_principal
from ..services.user_service import get_or_create_auth0_user


def get_current_user(
    principal: Annotated[Auth0Principal, Depends(get_auth0_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> models.User:
    return get_or_create_auth0_user(principal.subject, db)


CurrentUser = Annotated[models.User, Depends(get_current_user)]

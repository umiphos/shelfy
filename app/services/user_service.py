from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models


def get_or_create_auth0_user(subject: str, db: Session) -> models.User:
    user = db.query(models.User).filter(models.User.auth0_subject == subject).first()
    if user:
        return user

    user = models.User(auth0_subject=subject)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_user = (
            db.query(models.User).filter(models.User.auth0_subject == subject).first()
        )
        if existing_user:
            return existing_user
        raise
    db.refresh(user)
    return user

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {"message": "CATÁLOGO API funcionando"}


@router.get("/api/health")
def health():
    return {"status": "ok"}

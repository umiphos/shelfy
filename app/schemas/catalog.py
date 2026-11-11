from pydantic import BaseModel


class CatalogRequest(BaseModel):
    name: str
    user_id: int

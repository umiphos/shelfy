from pydantic import BaseModel


class ProductRequest(BaseModel):
    catalog_id: int
    name: str
    price: float
    category_id: int
    quantity: int
    status: str = "available"
    description: str | None = None
    characteristics: str | None = None
    color: str | None = None
    size: str | None = None
    shipping: bool = False
    whatsapp: str | None = None

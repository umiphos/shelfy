from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
    )

    password: Mapped[str] = mapped_column(
        String,
    )


class Catalog(Base):
    __tablename__ = "catalogs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String,
    )

    slug: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    catalog_id: Mapped[int] = mapped_column(
        ForeignKey("catalogs.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    price: Mapped[float] = mapped_column(
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    characteristics: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    color: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    size: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    shipping: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    whatsapp: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
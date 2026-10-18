from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_name", "name"),
        Index("ix_categories_code", "code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_barcode", "barcode"),
        Index("ix_products_name", "name"),
        Index("ix_products_is_active", "is_active"),
        Index("ix_products_current_stock", "current_stock"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    purchase_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    selling_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    min_stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_percent: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    supplier_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    valuation_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_purchase_price: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    reorder_point: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    max_stock: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    warehouse_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ProductWarehouse(Base):
    __tablename__ = "product_warehouse"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantity: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    reorder_point: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    max_stock: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    batch_number: Mapped[str] = mapped_column(Text, nullable=False)
    manufacturing_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expiry_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    purchase_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class StockMovement(Base):
    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_stock_movements_product_id", "product_id"),
        Index("ix_stock_movements_created_at", "created_at"),
        Index("ix_stock_movements_type", "movement_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    document_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    to_warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantity_received: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    quantity_issued: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    movement_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InventoryCount(Base):
    __tablename__ = "inventory_counts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    count_number: Mapped[str] = mapped_column(Text, nullable=False)
    warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    count_date: Mapped[str] = mapped_column(Text, nullable=False)
    count_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class InventoryCountLine(Base):
    __tablename__ = "inventory_count_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    count_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    system_quantity: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    actual_quantity: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    difference: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class StockTransfer(Base):
    __tablename__ = "stock_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_number: Mapped[str] = mapped_column(Text, nullable=False)
    from_warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    to_warehouse_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    transfer_date: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    batch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

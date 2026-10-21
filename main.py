from contextlib import asynccontextmanager
import os
import time

import psycopg
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://demo:demo@localhost:5432/demo_db",
)


def connect_with_retry():
    last_error = None
    for _ in range(30):
        try:
            return psycopg.connect(DATABASE_URL)
        except psycopg.OperationalError as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


def row_to_product(row):
    return {
        "id": str(row[0]),
        "nombre": row[1],
        "categoria": row[2],
        "precio": float(row[3]),
        "stock": row[4],
        "created_at": row[5],
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    with connect_with_retry() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS productos ("
            "id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, "
            "categoria TEXT NOT NULL, precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0), "
            "stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0), "
            "created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
        )
        conn.execute(
            "INSERT INTO productos (id, nombre, categoria, precio, stock) VALUES "
            "(1, 'Leche entera 1 L', 'Lácteos', 28.50, 40), "
            "(2, 'Pan integral', 'Panadería', 42.00, 18), "
            "(3, 'Manzana roja por kg', 'Frutas y verduras', 39.90, 25), "
            "(4, 'Arroz 1 kg', 'Abarrotes', 31.00, 32), "
            "(5, 'Café molido 250 g', 'Abarrotes', 86.50, 12), "
            "(6, 'Huevo blanco 12 piezas', 'Lácteos', 48.00, 20), "
            "(7, 'Aceite vegetal 1 L', 'Abarrotes', 46.50, 16), "
            "(8, 'Frijol negro 1 kg', 'Abarrotes', 39.00, 24), "
            "(9, 'Jugo de naranja 1 L', 'Bebidas', 32.00, 14), "
            "(10, 'Queso panela 400 g', 'Lácteos', 68.00, 10), "
            "(11, 'Plátano por kg', 'Frutas y verduras', 27.50, 30), "
            "(12, 'Pasta spaghetti 200 g', 'Abarrotes', 14.00, 35), "
            "(13, 'Agua embotellada 1.5 L', 'Bebidas', 16.50, 45), "
            "(14, 'Detergente en polvo 1 kg', 'Limpieza', 54.00, 11), "
            "(15, 'Galletas de avena 300 g', 'Botanas', 36.00, 17) "
            "ON CONFLICT (id) DO NOTHING"
        )
        conn.execute(
            "SELECT setval(pg_get_serial_sequence('productos', 'id'), "
            "GREATEST((SELECT MAX(id) FROM productos), 1))"
        )
    yield


app = FastAPI(
    title="API de productos del supermercado",
    description="API local de ejemplo conectada a PostgreSQL en Docker.",
    version="1.0.0",
    lifespan=lifespan,
)


class ProductoIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    categoria: str = Field(min_length=1, max_length=100)
    precio: float = Field(ge=0)
    stock: int = Field(ge=0)


@app.get("/")
def root():
    return {"mensaje": "API del supermercado local", "documentacion": "/docs"}


@app.get("/health")
def health():
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            conn.execute("SELECT 1")
        return {"api": "ok", "database": "ok"}
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Base de datos no disponible") from exc


@app.get("/api/productos")
def listar_productos():
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            "SELECT id, nombre, categoria, precio, stock, created_at "
            "FROM productos ORDER BY id"
        ).fetchall()
    return {"data": [row_to_product(row) for row in rows]}


@app.get("/api/productos/{producto_id}")
def obtener_producto(producto_id: int):
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "SELECT id, nombre, categoria, precio, stock, created_at "
            "FROM productos WHERE id = %s",
            (producto_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"data": row_to_product(row)}


@app.post("/api/productos", status_code=status.HTTP_201_CREATED)
def crear_producto(producto: ProductoIn):
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "INSERT INTO productos (nombre, categoria, precio, stock) "
            "VALUES (%s, %s, %s, %s) "
            "RETURNING id, nombre, categoria, precio, stock, created_at",
            (producto.nombre, producto.categoria, producto.precio, producto.stock),
        ).fetchone()
    return {"data": row_to_product(row)}


@app.put("/api/productos/{producto_id}")
def actualizar_producto(producto_id: int, producto: ProductoIn):
    with psycopg.connect(DATABASE_URL) as conn:
        row = conn.execute(
            "UPDATE productos SET nombre = %s, categoria = %s, precio = %s, stock = %s "
            "WHERE id = %s "
            "RETURNING id, nombre, categoria, precio, stock, created_at",
            (producto.nombre, producto.categoria, producto.precio, producto.stock, producto_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"data": row_to_product(row)}


@app.delete("/api/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int):
    with psycopg.connect(DATABASE_URL) as conn:
        result = conn.execute("DELETE FROM productos WHERE id = %s", (producto_id,))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")


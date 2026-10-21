# Demo local: API de productos + PostgreSQL en Docker

Este ejemplo simula el catálogo de un supermercado ficticio con productos inventados. La API usa FastAPI y guarda los datos en PostgreSQL. Docker Compose levanta ambos contenedores y conserva los datos en el volumen `postgres_data`.

## Requisitos

- Docker Desktop abierto y con el motor iniciado.
- Git (opcional, para sincronizar el proyecto después).

## Iniciar el proyecto

Abre PowerShell en esta carpeta y ejecuta:

```powershell
docker compose up --build -d
docker compose ps
```

La API queda disponible en http://localhost:8000 y su documentación interactiva en http://localhost:8000/docs. PostgreSQL escucha localmente en el puerto `5432`.

## Probar como en el ejemplo del profesor

Abre http://localhost:8000/docs y ejecuta `GET /api/productos/{producto_id}` con `producto_id` igual a `1`. Devuelve un producto ficticio en formato JSON, por ejemplo:

```json
{
  "data": {
    "id": "1",
    "nombre": "Leche entera 1 L",
    "categoria": "Lácteos",
    "precio": 28.5,
    "stock": 40,
    "created_at": "..."
  }
}
```

También puedes usar `GET /api/productos` para listar el catálogo o `GET /health` para confirmar que API y base de datos están conectadas.

## Operaciones disponibles

- `GET /api/productos`: listar productos.
- `GET /api/productos/{id}`: consultar un producto por ID.
- `POST /api/productos`: crear un producto.
- `PUT /api/productos/{id}`: actualizar un producto.
- `DELETE /api/productos/{id}`: eliminar un producto.

La API carga quince productos ficticios al iniciar. Si se reinician los contenedores, el volumen conserva los datos y los productos de ejemplo no se duplican; también completa los productos de muestra que falten.

## Demostrar contenedores e imagen

```powershell
docker compose ps
docker image ls
docker volume ls
```

Para demostrar persistencia, crea un producto desde `/docs`, detén los contenedores con `docker compose down`, vuelve a iniciarlos con `docker compose up -d` y consulta la lista otra vez. No uses `docker compose down -v` en la demostración: ese comando elimina también el volumen y los datos.

## Detener el proyecto

```powershell
docker compose down
```

## Continuación del proyecto

Esta entrega cubre la parte local. Para continuar con Git, Render y n8n se publicará esta API y se configurará la base de datos del entorno publicado; n8n consumirá su URL pública. Las credenciales `demo/demo` son únicamente para esta práctica local.

# Instrucciones Docker

## Requisitos
- Docker Desktop instalado
- Docker Compose v2+

## Iniciar el proyecto

```bash
# Clonar el repositorio
cd "C:\Users\Dario\Desktop\portal de alumnos"

# Iniciar todos los servicios
docker-compose up --build

# En segundo plano
docker-compose up -d --build
```

## Acceder
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

## Detener
```bash
docker-compose down
```

## Logs
```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio especifico
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Reconstruir
```bash
# Si cambiaste dependencias
docker-compose up -d --build

# Limpiar y reconstruir
docker-compose down
docker-compose up -d --build
```

## Notas
- La base de datos SQLite se monta como volumen, se persiste en `backend/portal.db`
- Los cambios en el código se reflejan automáticamente (volúmenes montados)
- Para producción, cambiar `FLASK_ENV=production` en el docker-compose.yml

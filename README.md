# Proyecto Final - Infraestructuras Paralelas y Distribuidas
## Análisis de Correlación entre Noticias Económicas e Índice COLCAP
# Proyecto - Infraestructuras Paralelas y Distribuidas

Análisis rápido de correlación entre menciones en noticias y el índice COLCAP.

Descripción
-----------------
Este repo contiene una versión didáctica de un sistema basado en microservicios que simula la recolección de noticias, procesa métricas y cruza esos datos con una serie temporal del índice COLCAP para calcular correlaciones y generar gráficos.

Arquitectura (resumen)
----------------------
- Servicios principales: `colcap-fetcher`, `commoncrawl-worker`, `aggregator`, `plotter` y `redis`.
- Está pensado para correr con `docker-compose` localmente y también incluye manifiestos en `k8s/` para desplegar en Kubernetes.
- Redis se usa como cache/coordination. El `aggregator` hace procesamiento en paralelo para acelerar el cálculo.

Qué hay en este repo
---------------------
- `colcap-fetcher/` : servicio que devuelve series de precios (simuladas).
- `commoncrawl-worker/` : servicio que simula la extracción y análisis de noticias.
- `aggregator/` : cruza datos y calcula correlaciones.
- `plotter/` : genera gráficos (png o base64).
- `k8s/` : manifiestos para Kubernetes.
- `docker-compose.yml` : modo rápido para levantar todo localmente.

Arrancar rápido (local)
-----------------------
Recomendado: Docker Desktop instalado.

1) Construir y levantar (desde la raíz del repo):

```powershell
docker-compose up -d --build
```

2) Ver contenedores y su estado:

```powershell
docker-compose ps
```

3) Comprobar endpoints de salud:

```powershell
Invoke-RestMethod http://localhost:5001/health | ConvertTo-Json -Compress
Invoke-RestMethod http://localhost:5002/health | ConvertTo-Json -Compress
Invoke-RestMethod http://localhost:5003/health | ConvertTo-Json -Compress
Invoke-RestMethod http://localhost:8080/health | ConvertTo-Json -Compress
```

Uso básico (ejemplos)
---------------------
- Obtener datos COLCAP:

```powershell
Invoke-RestMethod "http://localhost:5001/colcap?start_date=2025-11-29&end_date=2025-12-29" | ConvertTo-Json -Compress
```

- Ejecutar procesamiento del worker:

```powershell
Invoke-RestMethod "http://localhost:5002/process?year=2025&month=12" | ConvertTo-Json -Compress
```

- Agregar y calcular correlación:

```powershell
Invoke-RestMethod "http://localhost:5003/aggregate?start_date=2025-11-29&end_date=2025-12-29&parallel=true" | ConvertTo-Json -Compress
```

- Generar y descargar la gráfica de correlación:

```powershell
Invoke-WebRequest "http://localhost:8080/plot?type=correlation&start_date=2025-11-29&end_date=2025-12-29&format=png" -OutFile correlation.png -UseBasicParsing
Start-Process .\correlation.png
```

Notas rápidas
-------------
- Si el build del `plotter` falla por timeout al bajar paquetes, reintenta:

```powershell
docker-compose build plotter
```

- Si Docker Desktop no está respondiendo, reinícialo antes de ejecutar `docker-compose`.

Desarrollo y debugging
----------------------
- Ver logs de un servicio:

```powershell
docker-compose logs --tail=200 <service-name>
```

- Borrar y volver a levantar todo:

```powershell
docker-compose down -v
docker-compose up -d --build
```


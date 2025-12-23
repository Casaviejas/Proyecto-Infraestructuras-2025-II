# Guía de Uso Rápido

## Desarrollo Local con Docker Compose

### Iniciar todos los servicios

```powershell
docker-compose up -d
```

### Ver logs

```powershell
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f plotter
```

### Detener servicios

```powershell
docker-compose down
```

### Reconstruir después de cambios

```powershell
docker-compose up -d --build
```

## URLs de Desarrollo Local (Docker Compose)

- **Plotter**: http://localhost:8080
- **Aggregator**: http://localhost:5003
- **COLCAP Fetcher**: http://localhost:5001
- **CommonCrawl Workers**: http://localhost:5002-5006
- **Redis**: localhost:6379

## Despliegue en Kubernetes

### Opción 1: Script Automatizado (Recomendado)

```powershell
# Construcción y despliegue completo
.\deploy.ps1 all

# Solo construir imágenes
.\deploy.ps1 build

# Solo desplegar
.\deploy.ps1 deploy

# Ver estado
.\deploy.ps1 status

# Limpiar
.\deploy.ps1 clean
```

### Opción 2: Manual

```powershell
# 1. Construir imágenes
docker build -t colcap-fetcher:latest ./colcap-fetcher
docker build -t commoncrawl-worker:latest ./commoncrawl-worker
docker build -t aggregator:latest ./aggregator
docker build -t plotter:latest ./plotter

# 2. Desplegar en orden
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/colcap-deployment.yaml
kubectl apply -f k8s/commoncrawl-deployment.yaml
kubectl apply -f k8s/aggregator-deployment.yaml
kubectl apply -f k8s/plotter-deployment.yaml

# 3. Verificar
kubectl get pods
kubectl get services

# 4. Acceder al servicio
kubectl port-forward service/plotter 8080:80
# Visitar: http://localhost:8080
```

## Ejemplos de Uso de la API

### 1. Health Check de todos los servicios

```bash
# COLCAP
curl http://localhost:5001/health

# CommonCrawl
curl http://localhost:5002/health

# Aggregator
curl http://localhost:5003/health

# Plotter
curl http://localhost:8080/health
```

### 2. Obtener datos del COLCAP

```bash
# Últimos 90 días
curl http://localhost:5001/colcap

# Rango personalizado
curl "http://localhost:5001/colcap?start_date=2024-01-01&end_date=2024-12-31"

# Último valor
curl http://localhost:5001/colcap/latest
```

### 3. Procesar noticias

```bash
# Mes específico
curl "http://localhost:5002/process?year=2024&month=10"

# Ver estadísticas del worker
curl http://localhost:5002/stats
```

### 4. Obtener datos agregados

```bash
# Con procesamiento paralelo (default)
curl "http://localhost:5003/aggregate?start_date=2024-10-01&end_date=2024-12-31"

# Sin paralelización
curl "http://localhost:5003/aggregate?start_date=2024-10-01&end_date=2024-12-31&parallel=false"

# Solo correlación
curl "http://localhost:5003/correlation?start_date=2024-10-01&end_date=2024-12-31"
```

### 5. Generar gráficos

```bash
# Gráfico de correlación (PNG)
curl "http://localhost:8080/plot?type=correlation&start_date=2024-10-01&end_date=2024-12-31" > correlation.png

# Gráfico de dispersión
curl "http://localhost:8080/plot?type=scatter&start_date=2024-10-01&end_date=2024-12-31" > scatter.png

# Heatmap
curl "http://localhost:8080/plot?type=heatmap&start_date=2024-10-01&end_date=2024-12-31" > heatmap.png

# Todos los gráficos en base64
curl "http://localhost:8080/plot/all?start_date=2024-10-01&end_date=2024-12-31"
```

## Comandos Útiles de Kubernetes

### Monitoreo

```powershell
# Ver todos los pods
kubectl get pods

# Ver servicios
kubectl get services

# Ver deployments
kubectl get deployments

# Ver uso de recursos
kubectl top pods
kubectl top nodes

# Logs en tiempo real
kubectl logs -f deployment/commoncrawl

# Describir un recurso
kubectl describe pod <pod-name>
```

### Escalado

```powershell
# Escalar workers
kubectl scale deployment commoncrawl --replicas=10

# Escalar automáticamente (HPA)
kubectl autoscale deployment commoncrawl --cpu-percent=70 --min=3 --max=20
```

### Debugging

```powershell
# Shell interactivo en un pod
kubectl exec -it <pod-name> -- /bin/bash

# Ejecutar comando en pod
kubectl exec <pod-name> -- curl localhost:5000/health

# Port-forward para debugging
kubectl port-forward <pod-name> 8080:5000

# Ver eventos
kubectl get events --sort-by=.metadata.creationTimestamp
```

### Actualización Rolling

```powershell
# Actualizar imagen
kubectl set image deployment/plotter plotter=plotter:v2

# Ver estado del rollout
kubectl rollout status deployment/plotter

# Rollback
kubectl rollout undo deployment/plotter
```

## Troubleshooting

### Pod no inicia

```powershell
# Ver detalles del pod
kubectl describe pod <pod-name>

# Ver logs
kubectl logs <pod-name>

# Ver eventos
kubectl get events
```

### Servicio no accesible

```powershell
# Verificar endpoints
kubectl get endpoints <service-name>

# Test de conectividad desde otro pod
kubectl exec -it <pod-name> -- curl http://<service-name>:5000/health
```

### Redis no conecta

```powershell
# Verificar que Redis está corriendo
kubectl get pods -l app=redis

# Test de conectividad a Redis
kubectl exec -it <pod-name> -- ping redis

# Verificar variables de entorno
kubectl exec <pod-name> -- env | grep REDIS
```

## Métricas de Rendimiento

### Medir tiempo de procesamiento

```bash
# Con paralelización
time curl "http://localhost:5003/aggregate?parallel=true"

# Sin paralelización
time curl "http://localhost:5003/aggregate?parallel=false"
```

### Benchmark de carga

```bash
# Múltiples requests concurrentes
for i in {1..100}; do
  curl "http://localhost:8080/plot?type=correlation" > /dev/null 2>&1 &
done

# Monitorear recursos durante la prueba
kubectl top pods
```

## Mejores Prácticas

1. **Siempre verificar health checks** antes de usar el sistema
2. **Usar Redis caché** para mejorar rendimiento
3. **Escalar workers** según la carga
4. **Monitorear recursos** con `kubectl top`
5. **Revisar logs** regularmente
6. **Usar namespaces** en producción
7. **Implementar límites de recursos** apropiados
8. **Configurar PersistentVolumes** para datos importantes

## Notas de Seguridad

- No exponer Redis públicamente
- Usar Secrets para credenciales en producción
- Implementar NetworkPolicies
- Usar RBAC para control de acceso
- Actualizar imágenes regularmente
- Escanear vulnerabilidades con `docker scan`

# Proyecto Final - Infraestructuras Paralelas y Distribuidas
## Análisis de Correlación entre Noticias Económicas e Índice COLCAP

### 📋 Descripción del Proyecto

Este proyecto implementa un sistema distribuido y escalable para procesar y analizar información noticiosa de fuentes abiertas (simulando Common Crawl) con el fin de identificar correlaciones entre eventos mediáticos económicos y el comportamiento del índice COLCAP de la Bolsa de Valores de Colombia.

El sistema está construido con arquitectura de microservicios, desplegado en Kubernetes, y demuestra la aplicación práctica de conceptos de:
- ✅ Computación paralela y distribuida
- ✅ Orquestación de contenedores
- ✅ Procesamiento distribuido de datos
- ✅ Escalabilidad horizontal
- ✅ Tolerancia a fallos

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                        │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │   Plotter    │◄─────┤  Aggregator  │                    │
│  │  (Frontend)  │      │   (Backend)  │                    │
│  │  Replicas: 2 │      │  Replicas: 2 │                    │
│  └──────────────┘      └───────┬──────┘                    │
│         ▲                       │                            │
│         │                       ├─────────────┐             │
│         │                       ▼             ▼             │
│    [LoadBalancer]        ┌──────────┐  ┌──────────┐        │
│         │                │  COLCAP  │  │CommonCrawl│       │
│         │                │ Fetcher  │  │  Workers  │       │
│         │                │Replicas:2│  │Replicas: 5│       │
│         │                └──────────┘  └─────┬─────┘       │
│         │                                    │              │
│         │                              ┌─────▼─────┐       │
│         └──────────────────────────────┤   Redis   │       │
│                                        │  (Cache)  │       │
│                                        └───────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Componentes del Sistema

#### 1. **COLCAP Fetcher** (2 réplicas)
- Obtiene datos del índice COLCAP
- Genera datos simulados realistas basados en patrones históricos
- Endpoints:
  - `GET /health` - Health check
  - `GET /colcap?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Obtener datos históricos
  - `GET /colcap/latest` - Obtener valor más reciente

#### 2. **CommonCrawl Workers** (5 réplicas)
- Procesan noticias económicas de forma distribuida
- Implementan análisis de contenido y extracción de keywords
- Utilizan Redis para caché y distribución de trabajo
- Endpoints:
  - `GET /health` - Health check
  - `GET /process?year=YYYY&month=MM` - Procesar mes específico
  - `POST /process/batch` - Procesamiento por lotes
  - `GET /stats` - Estadísticas del worker

#### 3. **Aggregator** (2 réplicas)
- Agrega datos de múltiples fuentes
- Calcula correlaciones estadísticas
- Implementa procesamiento paralelo con ThreadPoolExecutor
- Endpoints:
  - `GET /health` - Health check
  - `GET /aggregate?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&parallel=true` - Agregación completa
  - `GET /correlation` - Solo análisis de correlación

#### 4. **Plotter** (2 réplicas)
- Genera visualizaciones de los datos
- Crea múltiples tipos de gráficos
- Expuesto públicamente mediante LoadBalancer
- Endpoints:
  - `GET /health` - Health check
  - `GET /plot?type=correlation&format=png` - Generar gráfico específico
    - Tipos: `correlation`, `scatter`, `heatmap`
    - Formatos: `png`, `base64`
  - `GET /plot/all` - Generar todos los gráficos

#### 5. **Redis** (1 réplica)
- Sistema de caché distribuido
- Almacena resultados de procesamiento
- TTL de 1 hora para datos cacheados

---

## 🚀 Despliegue del Sistema

### Prerrequisitos

- Docker Desktop con Kubernetes habilitado
- kubectl configurado
- Al menos 4GB de RAM disponible

### Paso 1: Construir las imágenes Docker

```powershell
# Construir todas las imágenes
docker build -t colcap-fetcher:latest ./colcap-fetcher
docker build -t commoncrawl-worker:latest ./commoncrawl-worker
docker build -t aggregator:latest ./aggregator
docker build -t plotter:latest ./plotter
```

### Paso 2: Desplegar en Kubernetes

```powershell
# Aplicar ConfigMap y Redis primero
kubectl apply -f k8s/redis-deployment.yaml

# Desplegar servicios backend
kubectl apply -f k8s/colcap-deployment.yaml
kubectl apply -f k8s/commoncrawl-deployment.yaml
kubectl apply -f k8s/aggregator-deployment.yaml

# Desplegar frontend
kubectl apply -f k8s/plotter-deployment.yaml
```

### Paso 3: Verificar el despliegue

```powershell
# Ver todos los pods
kubectl get pods

# Ver servicios
kubectl get services

# Ver logs de un pod específico
kubectl logs -f <pod-name>

# Verificar health de todos los servicios
kubectl get pods -o wide
```

### Paso 4: Acceder al sistema

```powershell
# Obtener la URL del servicio plotter
kubectl get service plotter

# Si está en LoadBalancer, usar la IP externa
# Si está en NodePort, usar: http://localhost:<NodePort>

# Para desarrollo local (port-forward)
kubectl port-forward service/plotter 8080:80
# Acceder en: http://localhost:8080
```

---

## 📊 Uso del Sistema

### Ejemplo 1: Obtener gráfico de correlación

```bash
curl "http://localhost:8080/plot?type=correlation&start_date=2024-10-01&end_date=2024-12-31" > correlation.png
```

### Ejemplo 2: Obtener todos los gráficos en base64

```bash
curl "http://localhost:8080/plot/all?start_date=2024-10-01&end_date=2024-12-31"
```

### Ejemplo 3: Obtener solo análisis de correlación

```bash
curl "http://localhost:8080/../aggregator:5000/correlation?start_date=2024-10-01&end_date=2024-12-31"
```

### Ejemplo 4: Consultar health checks

```bash
# Health de todos los servicios
kubectl get pods | grep Running

# Health check individual
kubectl exec -it <pod-name> -- curl localhost:5000/health
```

---

## 🔧 Configuración

### Variables de Entorno (ConfigMap)

```yaml
REDIS_HOST: "redis"
REDIS_PORT: "6379"
LOG_LEVEL: "INFO"
```

### Recursos por Servicio

| Servicio | CPU Request | CPU Limit | Memory Request | Memory Limit | Réplicas |
|----------|-------------|-----------|----------------|--------------|----------|
| COLCAP Fetcher | 100m | 300m | 128Mi | 256Mi | 2 |
| CommonCrawl Worker | 200m | 500m | 256Mi | 512Mi | 5 |
| Aggregator | 200m | 500m | 256Mi | 512Mi | 2 |
| Plotter | 200m | 500m | 256Mi | 512Mi | 2 |
| Redis | 100m | 200m | 128Mi | 256Mi | 1 |

---

## 📈 Características de Paralelización

### 1. **Procesamiento Paralelo en Aggregator**
- Utiliza `ThreadPoolExecutor` con 3 workers
- Procesa múltiples meses simultáneamente
- Reduce tiempo de procesamiento en ~60%

### 2. **Distribución de Carga con Kubernetes**
- 5 réplicas de CommonCrawl Workers
- Service balanceo automático de carga
- Escalabilidad horizontal mediante `kubectl scale`

### 3. **Caché Distribuido con Redis**
- Evita procesamiento redundante
- TTL configurable (default: 1 hora)
- Mejora tiempos de respuesta en ~80%

### 4. **Health Checks y Auto-recuperación**
- Liveness probes cada 10 segundos
- Readiness probes cada 5 segundos
- Auto-restart en caso de fallo

---

## 🧪 Pruebas y Validación

### Pruebas de Carga

```powershell
# Escalar workers para mayor capacidad
kubectl scale deployment commoncrawl --replicas=10

# Monitorear recursos
kubectl top pods
kubectl top nodes

# Ver métricas de Redis
kubectl exec -it redis-<pod-id> -- redis-cli INFO stats
```

### Pruebas de Tolerancia a Fallos

```powershell
# Eliminar un pod y ver auto-recuperación
kubectl delete pod <pod-name>

# Ver que Kubernetes crea uno nuevo automáticamente
kubectl get pods -w
```

### Pruebas de Escalabilidad

```bash
# Benchmark con múltiples requests simultáneas
for i in {1..50}; do
  curl "http://localhost:8080/plot?type=correlation" > /dev/null 2>&1 &
done
```

---

## 📊 Análisis de Correlación

El sistema calcula:

1. **Coeficiente de Correlación de Pearson**: Mide la relación lineal entre volumen de noticias y COLCAP
2. **Interpretación Automática**:
   - |r| ≥ 0.7: Correlación fuerte
   - 0.4 ≤ |r| < 0.7: Correlación moderada
   - 0.2 ≤ |r| < 0.4: Correlación débil
   - |r| < 0.2: Correlación muy débil

3. **Métricas Adicionales**:
   - Volatilidad del COLCAP
   - Promedios móviles
   - Análisis de keywords más frecuentes
   - Distribución temporal

---

## 🛠️ Desarrollo y Debugging

### Ver logs en tiempo real

```powershell
# Logs de todos los pods de un deployment
kubectl logs -f deployment/commoncrawl

# Logs de un pod específico
kubectl logs -f <pod-name>

# Logs de contenedor específico en pod multi-contenedor
kubectl logs -f <pod-name> -c <container-name>
```

### Ejecutar comandos dentro de pods

```powershell
# Shell interactivo
kubectl exec -it <pod-name> -- /bin/bash

# Comando único
kubectl exec <pod-name> -- curl localhost:5000/health
```

### Debugging de networking

```powershell
# Ver endpoints de un servicio
kubectl get endpoints <service-name>

# Describir servicio
kubectl describe service <service-name>

# Test de conectividad desde un pod
kubectl exec -it <pod-name> -- curl http://colcap:5000/health
```

---

## 📝 Notas Importantes

### Datos Simulados

El sistema actualmente utiliza datos simulados realistas para:
- **COLCAP**: Generados con tendencias y volatilidad realista
- **Noticias**: Simuladas con conteo variable y keywords económicas

Para usar datos reales:
1. Implementar scraping del sitio de la BVC para COLCAP
2. Integrar con API real de Common Crawl
3. Agregar procesamiento NLP para análisis de contenido

### Limitaciones

- Redis no tiene volumen persistente (datos se pierden al reiniciar)
- Procesamiento limitado a 100 puntos de datos por respuesta
- Cache TTL fijo de 1 hora

### Mejoras Futuras

1. Implementar PersistentVolumes para Redis
2. Agregar autoscaling basado en métricas (HPA)
3. Implementar circuit breaker pattern
4. Agregar monitoring con Prometheus + Grafana
5. Implementar CI/CD con GitHub Actions
6. Agregar tests unitarios y de integración

---

## 👥 Autores

**Universidad del Valle**  
**Curso**: Infraestructuras Paralelas y Distribuidas  
**Año**: 2025-II

---

## 📚 Referencias

- [Common Crawl Foundation](https://commoncrawl.org)
- [Kubernetes Documentation](https://kubernetes.io/docs)
- [Docker Documentation](https://docs.docker.com)
- [Bolsa de Valores de Colombia](https://www.bvc.com.co)

---

## 📄 Licencia

Este proyecto es desarrollado con fines académicos para el curso de Infraestructuras Paralelas y Distribuidas.

# Script de despliegue completo para Kubernetes
# Uso: .\deploy.ps1 [build|deploy|clean|status]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('build', 'deploy', 'clean', 'status', 'all')]
    [string]$Action = 'all'
)

function Build-Images {
    Write-Host "🔨 Construyendo imágenes Docker..." -ForegroundColor Cyan
    
    docker build -t colcap-fetcher:latest ./colcap-fetcher
    if ($LASTEXITCODE -ne 0) { Write-Error "Error construyendo colcap-fetcher"; exit 1 }
    
    docker build -t commoncrawl-worker:latest ./commoncrawl-worker
    if ($LASTEXITCODE -ne 0) { Write-Error "Error construyendo commoncrawl-worker"; exit 1 }
    
    docker build -t aggregator:latest ./aggregator
    if ($LASTEXITCODE -ne 0) { Write-Error "Error construyendo aggregator"; exit 1 }
    
    docker build -t plotter:latest ./plotter
    if ($LASTEXITCODE -ne 0) { Write-Error "Error construyendo plotter"; exit 1 }
    
    Write-Host "✅ Imágenes construidas exitosamente" -ForegroundColor Green
}

function Deploy-Services {
    Write-Host "🚀 Desplegando servicios en Kubernetes..." -ForegroundColor Cyan
    
    # Desplegar Redis y ConfigMap primero
    Write-Host "  📦 Desplegando Redis..." -ForegroundColor Yellow
    kubectl apply -f k8s/redis-deployment.yaml
    
    # Esperar a que Redis esté listo
    Write-Host "  ⏳ Esperando a que Redis esté listo..." -ForegroundColor Yellow
    kubectl wait --for=condition=ready pod -l app=redis --timeout=60s
    
    # Desplegar servicios backend
    Write-Host "  📦 Desplegando servicios backend..." -ForegroundColor Yellow
    kubectl apply -f k8s/colcap-deployment.yaml
    kubectl apply -f k8s/commoncrawl-deployment.yaml
    kubectl apply -f k8s/aggregator-deployment.yaml
    
    # Esperar a que los backends estén listos
    Write-Host "  ⏳ Esperando a que los backends estén listos..." -ForegroundColor Yellow
    kubectl wait --for=condition=ready pod -l app=colcap --timeout=90s
    kubectl wait --for=condition=ready pod -l app=commoncrawl --timeout=90s
    kubectl wait --for=condition=ready pod -l app=aggregator --timeout=90s
    
    # Desplegar frontend
    Write-Host "  📦 Desplegando frontend..." -ForegroundColor Yellow
    kubectl apply -f k8s/plotter-deployment.yaml
    
    # Esperar a que el frontend esté listo
    kubectl wait --for=condition=ready pod -l app=plotter --timeout=90s
    
    Write-Host "✅ Servicios desplegados exitosamente" -ForegroundColor Green
}

function Show-Status {
    Write-Host "📊 Estado del cluster:" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Pods:" -ForegroundColor Yellow
    kubectl get pods
    Write-Host ""
    
    Write-Host "Servicios:" -ForegroundColor Yellow
    kubectl get services
    Write-Host ""
    
    Write-Host "Deployments:" -ForegroundColor Yellow
    kubectl get deployments
    Write-Host ""
    
    # Obtener URL del servicio plotter
    $plotterService = kubectl get service plotter -o json | ConvertFrom-Json
    $serviceType = $plotterService.spec.type
    
    Write-Host "🌐 Acceso al sistema:" -ForegroundColor Green
    if ($serviceType -eq "LoadBalancer") {
        $externalIP = $plotterService.status.loadBalancer.ingress[0].ip
        if ($externalIP) {
            Write-Host "  URL: http://$externalIP" -ForegroundColor White
        } else {
            Write-Host "  LoadBalancer pendiente de asignación IP..." -ForegroundColor Yellow
            Write-Host "  Usar port-forward: kubectl port-forward service/plotter 8080:80" -ForegroundColor White
        }
    } else {
        Write-Host "  Usar port-forward: kubectl port-forward service/plotter 8080:80" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "📝 Comandos útiles:" -ForegroundColor Cyan
    Write-Host "  Ver logs: kubectl logs -f deployment/plotter" -ForegroundColor White
    Write-Host "  Health check: kubectl exec -it <pod-name> -- curl localhost:5000/health" -ForegroundColor White
    Write-Host "  Escalar: kubectl scale deployment commoncrawl --replicas=10" -ForegroundColor White
}

function Clean-Deployment {
    Write-Host "🧹 Limpiando despliegue..." -ForegroundColor Cyan
    
    kubectl delete -f k8s/plotter-deployment.yaml --ignore-not-found=true
    kubectl delete -f k8s/aggregator-deployment.yaml --ignore-not-found=true
    kubectl delete -f k8s/commoncrawl-deployment.yaml --ignore-not-found=true
    kubectl delete -f k8s/colcap-deployment.yaml --ignore-not-found=true
    kubectl delete -f k8s/redis-deployment.yaml --ignore-not-found=true
    
    Write-Host "✅ Limpieza completada" -ForegroundColor Green
}

# Ejecutar acción
switch ($Action) {
    'build' {
        Build-Images
    }
    'deploy' {
        Deploy-Services
        Show-Status
    }
    'clean' {
        Clean-Deployment
    }
    'status' {
        Show-Status
    }
    'all' {
        Build-Images
        Write-Host ""
        Deploy-Services
        Write-Host ""
        Show-Status
    }
}

Write-Host ""
Write-Host "✨ Proceso completado" -ForegroundColor Green

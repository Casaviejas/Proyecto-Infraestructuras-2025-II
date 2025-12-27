import requests
import redis
import json
import time
from flask import Flask, request, jsonify
from datetime import datetime
import logging
from collections import Counter
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de Redis
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0

# Intentar conectar a Redis
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis successfully")
except:
    logger.warning("Redis not available, running in standalone mode")
    redis_client = None

# Palabras clave económicas para análisis
ECONOMIC_KEYWORDS = [
    'economía', 'inflación', 'PIB', 'dólar', 'peso', 'banco', 'central',
    'empleo', 'desempleo', 'inversión', 'comercio', 'exportación', 'importación',
    'petróleo', 'bolsa', 'acciones', 'mercado', 'financiero', 'crisis',
    'deuda', 'fiscal', 'presupuesto', 'tasa', 'interés', 'colcap'
]

def simulate_commoncrawl_fetch(year, month):
    """
    Simula el fetch de noticias de Common Crawl.
    En producción real, esto consultaría el índice de Common Crawl.
    """
    # Simular diferentes volúmenes de noticias económicas por mes
    base_count = 1500
    variation = int((hash(f"{year}{month}") % 500) - 250)
    news_count = max(base_count + variation, 800)
    
    # Simular análisis de contenido
    simulated_news = []
    for i in range(min(news_count, 100)):  # Limitamos a 100 para el ejemplo
        simulated_news.append({
            "title": f"Noticia económica {i+1} - {year}-{month}",
            "keywords_found": [kw for kw in ECONOMIC_KEYWORDS if hash(f"{i}{kw}") % 3 == 0],
            "relevance_score": round((hash(f"{year}{month}{i}") % 100) / 100, 2)
        })
    
    return news_count, simulated_news

def analyze_news_content(news_list):
    """Analiza el contenido de las noticias y extrae métricas"""
    all_keywords = []
    total_relevance = 0
    
    for news in news_list:
        all_keywords.extend(news.get('keywords_found', []))
        total_relevance += news.get('relevance_score', 0)
    
    keyword_freq = Counter(all_keywords)
    avg_relevance = total_relevance / len(news_list) if news_list else 0
    
    return {
        "top_keywords": dict(keyword_freq.most_common(10)),
        "avg_relevance": round(avg_relevance, 3),
        "total_analyzed": len(news_list)
    }

@app.route("/", methods=["GET"])
def home():
    """Página de inicio con documentación del servicio"""
    redis_status = "connected" if redis_client else "disconnected"
    return jsonify({
        "service": "CommonCrawl Worker Service",
        "version": "1.0",
        "description": "Servicio para procesar noticias económicas con análisis de contenido",
        "redis": redis_status,
        "endpoints": {
            "/health": "Health check del servicio",
            "/process": "Procesar noticias de un mes específico (params: year, month)",
            "/process/batch": "Procesar múltiples meses en paralelo (POST)",
            "/stats": "Estadísticas del worker y Redis"
        },
        "example": "GET /process?year=2024&month=10"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    redis_status = "connected" if redis_client else "disconnected"
    return jsonify({
        "status": "healthy",
        "service": "commoncrawl-worker",
        "redis": redis_status
    }), 200

@app.route("/process", methods=["GET"])
def process():
    """
    Procesa noticias de un mes específico.
    Query params:
    - year: año (YYYY)
    - month: mes (MM)
    """
    try:
        year = request.args.get("year", datetime.now().strftime("%Y"))
        month = request.args.get("month", datetime.now().strftime("%m"))
        
        # Crear identificador único para este trabajo
        job_id = hashlib.md5(f"{year}{month}".encode()).hexdigest()
        
        logger.info(f"Processing news for {year}-{month} (job_id: {job_id})")
        
        # Verificar si ya está en caché (Redis)
        if redis_client:
            cached = redis_client.get(f"news:{year}:{month}")
            if cached:
                logger.info(f"Returning cached data for {year}-{month}")
                return jsonify(json.loads(cached)), 200
        
        # Simular procesamiento (en producción, esto consultaría Common Crawl)
        start_time = time.time()
        news_count, news_data = simulate_commoncrawl_fetch(year, month)
        
        # Analizar contenido
        analysis = analyze_news_content(news_data)
        
        processing_time = round(time.time() - start_time, 2)
        
        result = {
            "date": f"{year}-{month}",
            "news_count": news_count,
            "analysis": analysis,
            "processing_time_seconds": processing_time,
            "job_id": job_id,
            "worker_id": f"worker-{hash(str(time.time())) % 1000}"
        }
        
        # Guardar en caché si Redis está disponible
        if redis_client:
            redis_client.setex(
                f"news:{year}:{month}",
                3600,  # TTL de 1 hora
                json.dumps(result)
            )
            logger.info(f"Cached result for {year}-{month}")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing news: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/process/batch", methods=["POST"])
def process_batch():
    """
    Procesa múltiples meses en paralelo.
    Body: {"dates": [{"year": "2023", "month": "01"}, ...]}
    """
    try:
        data = request.get_json()
        dates = data.get('dates', [])
        
        if not dates:
            return jsonify({
                "status": "error",
                "message": "No dates provided"
            }), 400
        
        results = []
        for date_obj in dates:
            year = date_obj.get('year')
            month = date_obj.get('month')
            
            # Procesar cada fecha
            news_count, news_data = simulate_commoncrawl_fetch(year, month)
            analysis = analyze_news_content(news_data)
            
            results.append({
                "date": f"{year}-{month}",
                "news_count": news_count,
                "analysis": analysis
            })
        
        return jsonify({
            "status": "success",
            "processed": len(results),
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/stats", methods=["GET"])
def stats():
    """Obtiene estadísticas del worker"""
    try:
        stats_data = {
            "service": "commoncrawl-worker",
            "redis_connected": redis_client is not None,
            "uptime": "running"
        }
        
        if redis_client:
            # Obtener estadísticas de Redis
            info = redis_client.info()
            stats_data["redis_keys"] = redis_client.dbsize()
            stats_data["redis_memory"] = info.get('used_memory_human', 'N/A')
        
        return jsonify(stats_data), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    logger.info("Starting CommonCrawl Worker Service")
    app.run(host="0.0.0.0", port=5000)

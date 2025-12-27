import requests
import logging
import concurrent.futures
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

COMMONCRAWL_SERVICE = "http://commoncrawl:5000/process"
COLCAP_SERVICE = "http://colcap:5000/colcap"

def fetch_news_data(year, month):
    """Obtiene datos de noticias de un mes específico"""
    try:
        logger.info(f"Fetching news data for {year}-{month}")
        response = requests.get(
            COMMONCRAWL_SERVICE,
            params={
                "term": "inflacion",  # 👈 ESTE ES EL CAMBIO CLAVE
                "year": year,
                "month": month
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching news for {year}-{month}: {str(e)}")
        return None

def fetch_colcap_data(start_date, end_date):
    """Obtiene datos del COLCAP para un rango de fechas"""
    try:
        logger.info(f"Fetching COLCAP data from {start_date} to {end_date}")
        response = requests.get(
            COLCAP_SERVICE,
            params={"start_date": start_date, "end_date": end_date},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching COLCAP data: {str(e)}")
        return None

def calculate_correlation(news_data, colcap_data):
    """Calcula la correlación entre noticias y COLCAP"""
    try:
        if not news_data or not colcap_data:
            return None
        
        # Crear DataFrame para análisis
        df_news = pd.DataFrame(news_data)
        df_colcap = pd.DataFrame(colcap_data)
        
        # Asegurar que las columnas de fecha son del mismo tipo
        df_news['date'] = pd.to_datetime(df_news['date'])
        df_colcap['date'] = pd.to_datetime(df_colcap['date'])
        
        # Merge por fecha
        merged = pd.merge(
            df_news,
            df_colcap,
            on='date',
            how='inner'
        )
        
        if len(merged) < 2:
            return None
        
        # Calcular correlación
        correlation = merged['news_count'].corr(merged['value'])
        
        # Análisis adicional
        analysis = {
            "correlation_coefficient": round(float(correlation), 4) if not pd.isna(correlation) else 0,
            "data_points": len(merged),
            "avg_news_count": round(float(merged['news_count'].mean()), 2),
            "avg_colcap": round(float(merged['value'].mean()), 2),
            "colcap_volatility": round(float(merged['value'].std()), 2),
            "interpretation": interpret_correlation(correlation)
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error calculating correlation: {str(e)}")
        return None

def interpret_correlation(corr):
    """Interpreta el coeficiente de correlación"""
    if pd.isna(corr):
        return "Insuficientes datos para correlación"
    
    abs_corr = abs(corr)
    direction = "positiva" if corr > 0 else "negativa"
    
    if abs_corr >= 0.7:
        strength = "fuerte"
    elif abs_corr >= 0.4:
        strength = "moderada"
    elif abs_corr >= 0.2:
        strength = "débil"
    else:
        strength = "muy débil"
    
    return f"Correlación {direction} {strength}"

@app.route("/", methods=["GET"])
def home():
    """Página de inicio con documentación del servicio"""
    return jsonify({
        "service": "Aggregator Service",
        "version": "1.0",
        "description": "Servicio para agregar y correlacionar datos de noticias con el índice COLCAP",
        "features": [
            "Procesamiento paralelo con ThreadPoolExecutor",
            "Cálculo de correlación de Pearson",
            "Análisis estadístico automático"
        ],
        "endpoints": {
            "/health": "Health check del servicio",
            "/aggregate": "Agregar datos de noticias y COLCAP (params: start_date, end_date, parallel)",
            "/correlation": "Obtener solo análisis de correlación (params: start_date, end_date)"
        },
        "example": "GET /aggregate?start_date=2024-10-01&end_date=2024-12-31&parallel=true"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "aggregator"
    }), 200

@app.route("/aggregate", methods=["GET"])
def aggregate():
    """
    Agrega y correlaciona datos de noticias y COLCAP.
    Query params:
    - start_date: fecha inicial (YYYY-MM-DD), default: 90 días atrás
    - end_date: fecha final (YYYY-MM-DD), default: hoy
    - parallel: usar procesamiento paralelo (true/false), default: true
    """
    try:
        # Obtener parámetros
        end_date_str = request.args.get('end_date', datetime.now().strftime("%Y-%m-%d"))
        start_date_str = request.args.get('start_date', 
                                         (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"))
        use_parallel = request.args.get('parallel', 'true').lower() == 'true'
        
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        logger.info(f"Aggregating data from {start_date_str} to {end_date_str}")
        
        # Generar lista de meses a procesar
        current = start_date
        months_to_process = []
        while current <= end_date:
            months_to_process.append((current.strftime("%Y"), current.strftime("%m")))
            # Avanzar al próximo mes
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        logger.info(f"Processing {len(months_to_process)} months")
        
        # Obtener datos de noticias (con o sin paralelización)
        news_data = []
        if use_parallel and len(months_to_process) > 1:
            # Procesamiento paralelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_date = {
                    executor.submit(fetch_news_data, year, month): (year, month)
                    for year, month in months_to_process
                }
                
                for future in concurrent.futures.as_completed(future_to_date):
                    result = future.result()
                    if result:
                        news_data.append(result)
        else:
            # Procesamiento secuencial
            for year, month in months_to_process:
                result = fetch_news_data(year, month)
                if result:
                    news_data.append(result)
        
        # Obtener datos del COLCAP
        colcap_response = fetch_colcap_data(start_date_str, end_date_str)
        if not colcap_response or not isinstance(colcap_response, list):
            return jsonify({
                "status": "error",
                "message": "Failed to fetch COLCAP data"
            }), 500
        colcap_data = colcap_response
        
        # Preparar datos para merge
        news_by_date = {}
        for news in news_data:
            date = news.get('date')
            # Expandir a todos los días del mes
            year, month = date.split('-')
            days_in_month = pd.Period(f"{year}-{month}").days_in_month
            for day in range(1, days_in_month + 1):
                full_date = f"{year}-{month}-{day:02d}"
                news_by_date[full_date] = {
                    'date': full_date,
                    'news_count': news.get('news_count', 0),
                    'analysis': news.get('analysis', {})
                }
        
        # Merge de datos
        merged_data = []
        for colcap_entry in colcap_data:
            date = colcap_entry['date']
            if date in news_by_date:
                merged_entry = {
                    **news_by_date[date],
                    'colcap_value': colcap_entry['value'],
                    'colcap_change': colcap_entry['change'],
                    'colcap_volume': colcap_entry['volume']
                }
                merged_data.append(merged_entry)
        
        # Calcular correlación
        correlation_analysis = calculate_correlation(
            list(news_by_date.values()),
            colcap_data
        )
        
        result = {
            "status": "success",
            "period": {
                "start": start_date_str,
                "end": end_date_str
            },
            "summary": {
                "total_data_points": len(merged_data),
                "months_processed": len(news_data),
                "processing_method": "parallel" if use_parallel else "sequential"
            },
            "correlation": correlation_analysis,
            "data": merged_data[:100]  # Limitar a 100 puntos para la respuesta
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in aggregation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/correlation", methods=["GET"])
def get_correlation():
    """
    Endpoint simplificado para obtener solo el análisis de correlación.
    Query params iguales a /aggregate
    """
    try:
        # Reutilizar la lógica de aggregate
        response = aggregate()
        data = response[0].get_json()
        
        if data.get('status') == 'success':
            return jsonify({
                "status": "success",
                "correlation": data.get('correlation'),
                "summary": data.get('summary')
            }), 200
        else:
            return response
            
    except Exception as e:
        logger.error(f"Error getting correlation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    logger.info("Starting Aggregator Service")
    app.run(host="0.0.0.0", port=5000)


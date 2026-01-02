import pandas as pd
import numpy as np
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def generate_colcap_data(start_date, end_date):
    """
    Genera datos simulados del COLCAP basados en patrones realistas.
    En producción, esto debería obtener datos reales de la BVC o Yahoo Finance.
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Simular datos realistas del COLCAP (valores típicos entre 1200-1600)
    base_value = 1400
    trend = np.linspace(0, 50, len(dates))  # Tendencia alcista leve
    noise = np.random.normal(0, 20, len(dates))  # Volatilidad diaria
    
    colcap_values = base_value + trend + noise
    colcap_values = np.maximum(colcap_values, 1200)  # Piso mínimo
    
    data = []
    for date, value in zip(dates, colcap_values):
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": round(float(value), 2),
            "change": round(np.random.uniform(-2, 2), 2),  # Cambio porcentual
            "volume": int(np.random.uniform(1000000, 5000000))  # Volumen de transacciones
        })
    
    return data

@app.route("/", methods=["GET"])
def home():
    """Página de inicio con documentación del servicio"""
    return jsonify({
        "service": "COLCAP Fetcher Service",
        "version": "1.0",
        "description": "Servicio para obtener datos del índice COLCAP de la Bolsa de Valores de Colombia",
        "endpoints": {
            "/health": "Health check del servicio",
            "/colcap": "Obtener datos del COLCAP (params: start_date, end_date)",
            "/colcap/latest": "Obtener el valor más reciente del COLCAP"
        },
        "example": "GET /colcap?start_date=2024-01-01&end_date=2024-12-31"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "colcap-fetcher"}), 200

@app.route("/colcap", methods=["GET"])
def get_colcap():
    """
    Obtiene datos del COLCAP para un rango de fechas.
    Query params:
    - start_date: fecha inicial (YYYY-MM-DD), default: 90 días atrás
    - end_date: fecha final (YYYY-MM-DD), default: hoy
    """
    try:
        # Obtener parámetros de fecha
        end_date = request.args.get('end_date')
        start_date = request.args.get('start_date')
        
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        logger.info(f"Fetching COLCAP data from {start_date} to {end_date}")
        
        # Generar datos
        data = generate_colcap_data(start_date, end_date)
        
        return jsonify({
            "status": "success",
            "count": len(data),
            "data": data
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching COLCAP data: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/colcap/latest", methods=["GET"])
def get_latest_colcap():
    """Obtiene el valor más reciente del COLCAP"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        data = generate_colcap_data(today, today)
        
        return jsonify({
            "status": "success",
            "data": data[0] if data else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching latest COLCAP: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    logger.info("Starting COLCAP Fetcher Service")
    app.run(host="0.0.0.0", port=5000)
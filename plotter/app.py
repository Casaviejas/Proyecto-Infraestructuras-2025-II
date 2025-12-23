import requests
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask, jsonify, request, send_file
from datetime import datetime
import logging
import io
import base64
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurar estilo de gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

AGGREGATOR_URL = "http://aggregator:5000/aggregate"

def fetch_aggregated_data(start_date=None, end_date=None):
    """Obtiene datos agregados del servicio aggregator"""
    try:
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        logger.info(f"Fetching data from aggregator with params: {params}")
        response = requests.get(AGGREGATOR_URL, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        if data.get('status') == 'success':
            return data
        else:
            logger.error(f"Aggregator returned error: {data}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching aggregated data: {str(e)}")
        return None

def create_correlation_plot(data):
    """Crea gráfico de correlación entre noticias y COLCAP"""
    try:
        df = pd.DataFrame(data)
        
        if df.empty:
            return None
        
        fig, ax1 = plt.subplots(figsize=(14, 7))
        
        # Convertir fechas
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Eje izquierdo: Noticias
        color = 'tab:blue'
        ax1.set_xlabel('Fecha', fontsize=12)
        ax1.set_ylabel('Cantidad de Noticias', color=color, fontsize=12)
        ax1.plot(df['date'], df['news_count'], color=color, linewidth=2, label='Noticias Económicas', marker='o')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.grid(True, alpha=0.3)
        
        # Eje derecho: COLCAP
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('Índice COLCAP', color=color, fontsize=12)
        ax2.plot(df['date'], df['colcap_value'], color=color, linewidth=2, label='COLCAP', marker='s')
        ax2.tick_params(axis='y', labelcolor=color)
        
        # Título
        plt.title('Correlación entre Noticias Económicas e Índice COLCAP', fontsize=14, fontweight='bold', pad=20)
        
        # Leyendas
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Rotar fechas
        plt.xticks(rotation=45, ha='right')
        
        fig.tight_layout()
        
        # Guardar en buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
        
    except Exception as e:
        logger.error(f"Error creating correlation plot: {str(e)}")
        return None

def create_scatter_plot(data):
    """Crea gráfico de dispersión para visualizar correlación"""
    try:
        df = pd.DataFrame(data)
        
        if df.empty or len(df) < 2:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Scatter plot
        scatter = ax.scatter(
            df['news_count'],
            df['colcap_value'],
            c=df['colcap_change'],
            cmap='RdYlGn',
            s=100,
            alpha=0.6,
            edgecolors='black'
        )
        
        # Línea de tendencia
        z = np.polyfit(df['news_count'], df['colcap_value'], 1)
        p = np.poly1d(z)
        ax.plot(df['news_count'], p(df['news_count']), "r--", alpha=0.8, linewidth=2, label='Tendencia')
        
        # Etiquetas y título
        ax.set_xlabel('Cantidad de Noticias Económicas', fontsize=12)
        ax.set_ylabel('Índice COLCAP', fontsize=12)
        ax.set_title('Dispersión: Noticias vs COLCAP', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Barra de color
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Cambio % COLCAP', rotation=270, labelpad=20)
        
        fig.tight_layout()
        
        # Guardar en buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
        
    except Exception as e:
        logger.error(f"Error creating scatter plot: {str(e)}")
        return None

def create_heatmap(data):
    """Crea un heatmap de la actividad por día/semana"""
    try:
        df = pd.DataFrame(data)
        
        if df.empty:
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['week'] = df['date'].dt.isocalendar().week
        
        # Pivotear para heatmap
        pivot = df.pivot_table(
            values='news_count',
            index='day_of_week',
            columns='week',
            aggfunc='mean'
        )
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        sns.heatmap(
            pivot,
            annot=False,
            fmt='.0f',
            cmap='YlOrRd',
            ax=ax,
            cbar_kws={'label': 'Cantidad de Noticias'}
        )
        
        ax.set_title('Heatmap de Actividad Noticiosa por Día de la Semana', fontsize=14, fontweight='bold')
        ax.set_xlabel('Semana del Año', fontsize=12)
        ax.set_ylabel('Día de la Semana', fontsize=12)
        ax.set_yticklabels(['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'])
        
        fig.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
        
    except Exception as e:
        logger.error(f"Error creating heatmap: {str(e)}")
        return None

@app.route("/", methods=["GET"])
def home():
    """Página de inicio con documentación del servicio"""
    return jsonify({
        "service": "Plotter Service",
        "version": "1.0",
        "description": "Servicio para generar visualizaciones de correlación entre noticias y COLCAP",
        "plot_types": {
            "correlation": "Gráfico de líneas dual con noticias y COLCAP",
            "scatter": "Gráfico de dispersión con línea de tendencia",
            "heatmap": "Heatmap de actividad noticiosa por día/semana"
        },
        "endpoints": {
            "/health": "Health check del servicio",
            "/plot": "Generar un gráfico específico (params: type, start_date, end_date, format)",
            "/plot/all": "Generar todos los gráficos en base64 (params: start_date, end_date)"
        },
        "examples": [
            "GET /plot?type=correlation&start_date=2024-10-01&end_date=2024-12-31",
            "GET /plot?type=scatter&format=base64",
            "GET /plot/all?start_date=2024-10-01&end_date=2024-12-31"
        ]
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "plotter"
    }), 200

@app.route("/plot", methods=["GET"])
def plot():
    """
    Genera gráfico de correlación.
    Query params:
    - start_date: fecha inicial (YYYY-MM-DD)
    - end_date: fecha final (YYYY-MM-DD)
    - type: tipo de gráfico (correlation, scatter, heatmap), default: correlation
    - format: formato de salida (png, base64), default: png
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        plot_type = request.args.get('type', 'correlation')
        output_format = request.args.get('format', 'png')
        
        # Obtener datos
        aggregated_data = fetch_aggregated_data(start_date, end_date)
        
        if not aggregated_data or aggregated_data.get('status') != 'success':
            return jsonify({
                "status": "error",
                "message": "Failed to fetch aggregated data"
            }), 500
        
        data = aggregated_data.get('data', [])
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data available for plotting"
            }), 404
        
        # Crear gráfico según el tipo
        if plot_type == 'correlation':
            buf = create_correlation_plot(data)
        elif plot_type == 'scatter':
            buf = create_scatter_plot(data)
        elif plot_type == 'heatmap':
            buf = create_heatmap(data)
        else:
            return jsonify({
                "status": "error",
                "message": f"Unknown plot type: {plot_type}"
            }), 400
        
        if not buf:
            return jsonify({
                "status": "error",
                "message": "Failed to generate plot"
            }), 500
        
        # Retornar según formato
        if output_format == 'base64':
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            return jsonify({
                "status": "success",
                "plot_type": plot_type,
                "image": img_base64,
                "format": "base64"
            }), 200
        else:
            return send_file(buf, mimetype='image/png', as_attachment=False, download_name=f'{plot_type}_plot.png')
        
    except Exception as e:
        logger.error(f"Error generating plot: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/plot/all", methods=["GET"])
def plot_all():
    """
    Genera todos los tipos de gráficos y los retorna en base64.
    Query params: start_date, end_date
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Obtener datos
        aggregated_data = fetch_aggregated_data(start_date, end_date)
        
        if not aggregated_data or aggregated_data.get('status') != 'success':
            return jsonify({
                "status": "error",
                "message": "Failed to fetch aggregated data"
            }), 500
        
        data = aggregated_data.get('data', [])
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data available for plotting"
            }), 404
        
        # Generar todos los gráficos
        plots = {}
        
        correlation_buf = create_correlation_plot(data)
        if correlation_buf:
            plots['correlation'] = base64.b64encode(correlation_buf.read()).decode('utf-8')
        
        scatter_buf = create_scatter_plot(data)
        if scatter_buf:
            plots['scatter'] = base64.b64encode(scatter_buf.read()).decode('utf-8')
        
        heatmap_buf = create_heatmap(data)
        if heatmap_buf:
            plots['heatmap'] = base64.b64encode(heatmap_buf.read()).decode('utf-8')
        
        return jsonify({
            "status": "success",
            "plots": plots,
            "correlation_analysis": aggregated_data.get('correlation')
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating all plots: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    logger.info("Starting Plotter Service")
    app.run(host="0.0.0.0", port=5000)
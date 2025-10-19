# app.py - EcoVision: Climate Visualizer API
# This file contains basic Flask setup code to get you started.
# You may opt to use FastAPI or another framework if you prefer.

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mysqldb import MySQL
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

app = Flask(__name__)
CORS(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = os.getenv('MYSQL_CURSORCLASS')
mysql = MySQL(app)

# Quality weights to be used in calculations
QUALITY_WEIGHTS = {
    'excellent': 1.0,
    'good': 0.8,
    'questionable': 0.5,
    'poor': 0.3
}

# Debug purposes only
@app.get("/debug/counts")
def debug_counts():
    cur = mysql.connection.cursor()
    out = {}
    for t in ("locations","metrics","climate_data"):
        cur.execute(f"SELECT COUNT(*) AS n FROM {t}")
        out[t] = cur.fetchone()["n"]
    cur.close()
    return out, 200

@app.route('/api/v1/climate', methods=['GET'])
def get_climate_data():
    cur = mysql.connection.cursor()

    location_id = request.args.get('location_id', type=int)
    metric = request.args.get('metric')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    quality_threshold = request.args.get('quality_threshold')

    metric_norm = metric.lower().strip() if metric else None
    qt_norm = quality_threshold.lower().strip() if quality_threshold else None

    # "param is NULL OR condition" to avoid building SQL dynamically and making the filter optional!
    sql = """
    SELECT
      cd.id,
      cd.location_id,
      l.name AS location_name,
      l.latitude,
      l.longitude,
      cd.date,
      m.name AS metric,
      m.unit,
      cd.value,
      cd.quality
    FROM climate_data cd
    JOIN locations l ON l.id = cd.location_id
    JOIN metrics m ON m.id = cd.metric_id
    WHERE
      (%s IS NULL OR cd.location_id = %s) AND
      (%s IS NULL OR m.name = %s) AND
      (%s IS NULL OR cd.date >= %s) AND
      (%s IS NULL OR cd.date <= %s) AND
      (
        %s IS NULL OR
        FIELD(cd.quality, 'poor','questionable','good','excellent')
          >= FIELD(%s, 'poor','questionable','good','excellent')
      )
    ORDER BY cd.date ASC, cd.id ASC
    """

    params = [
        location_id, location_id,
        metric_norm, metric_norm,
        start_date, start_date,
        end_date, end_date,
        qt_norm, qt_norm
    ]

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()

    data = []
    for r in rows:
        item = dict(r)
        if item.get("date"):
            item["date"] = item["date"].isoformat()
        data.append(item)

    return jsonify({
        "data": data,
        "meta": {
            "total_count": len(data),
            "page": 1,
            "per_page": len(data)
        }
    }), 200

@app.route('/api/v1/locations', methods=['GET'])
def get_locations():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, name, country, latitude, longitude
        FROM locations
        ORDER BY id ASC
    """)
    rows = cur.fetchall()
    cur.close()
    return jsonify({"data": rows}), 200

@app.route('/api/v1/metrics', methods=['GET'])
def get_metrics():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, name, display_name, unit, description
        FROM metrics
        ORDER BY id ASC
    """)
    rows = cur.fetchall()
    cur.close()
    return jsonify({"data": rows}), 200
    

@app.route('/api/v1/summary', methods=['GET'])
def get_summary():
    """
    Retrieve quality-weighted summary statistics for climate data.
    Query parameters: location_id, start_date, end_date, metric, quality_threshold
    
    Returns weighted min, max, and avg values for each metric in the format specified in the API docs.
    """
    # TODO: Implement this endpoint
    # 1. Get query parameters from request.args
    # 2. Validate quality_threshold if provided
    # 3. Get list of metrics to summarize
    # 4. For each metric:
    #    - Calculate quality-weighted statistics using QUALITY_WEIGHTS
    #    - Calculate quality distribution
    #    - Apply proper filtering
    # 5. Format response according to API specification
    
    return jsonify({"data": {}})

@app.route('/api/v1/trends', methods=['GET'])
def get_trends():
    """
    Analyze trends and patterns in climate data.
    Query parameters: location_id, start_date, end_date, metric, quality_threshold
    
    Returns trend analysis including direction, rate of change, anomalies, and seasonality.
    """
    # TODO: Implement this endpoint
    # 1. Get query parameters from request.args
    # 2. Validate quality_threshold if provided
    # 3. For each metric:
    #    - Calculate trend direction and rate of change
    #    - Identify anomalies (values > 2 standard deviations)
    #    - Detect seasonal patterns if sufficient data
    #    - Calculate confidence scores
    # 4. Format response according to API specification
    
    return jsonify({"data": {}})

if __name__ == '__main__':
    app.run(debug=True)
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
    cur = mysql.connection.cursor()

    location_id = request.args.get('location_id', type=int)
    metric = request.args.get('metric')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    quality_threshold = request.args.get('quality_threshold')

    metric_norm = metric.lower().strip() if metric else None
    qt_norm = quality_threshold.lower().strip() if quality_threshold else None

    # CASE gives weights for weighted average
    # FIELD handles quality threshold rank
    sql = """
    SELECT
      m.name AS metric,
      m.unit AS unit,
      MIN(cd.value) AS min_value,
      MAX(cd.value) AS max_value,
      AVG(cd.value) AS avg_value,
      SUM(cd.value * CASE cd.quality
          WHEN 'excellent' THEN 1.0
          WHEN 'good' THEN 0.8
          WHEN 'questionable' THEN 0.5
          WHEN 'poor' THEN 0.3
          ELSE 0 END
      ) / NULLIF(SUM(CASE cd.quality
          WHEN 'excellent' THEN 1.0
          WHEN 'good' THEN 0.8
          WHEN 'questionable' THEN 0.5
          WHEN 'poor' THEN 0.3
          ELSE 0 END
      ), 0) AS weighted_avg,
      SUM(cd.quality = 'excellent') AS q_excellent,
      SUM(cd.quality = 'good') AS q_good,
      SUM(cd.quality = 'questionable') AS q_questionable,
      SUM(cd.quality = 'poor') AS q_poor,
      COUNT(*) AS total_count
    FROM climate_data cd
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
    GROUP BY m.id, m.name, m.unit
    ORDER BY m.name ASC
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

    result = {}
    for r in rows:
        total = r["total_count"] or 0
        if total <= 0:
            continue
        q_ex = r["q_excellent"] or 0
        q_go = r["q_good"] or 0
        q_qu = r["q_questionable"] or 0
        q_po = r["q_poor"] or 0

        result[r["metric"]] = {
            "min": r["min_value"],
            "max": r["max_value"],
            "avg": r["avg_value"],
            "weighted_avg": round(r["weighted_avg"], 1),
            "unit": r["unit"],
            "quality_distribution": {
                "excellent": round(q_ex / total, 1),
                "good": round(q_go / total, 1),
                "questionable": round(q_qu / total, 1),
                "poor": round(q_po / total, 1),
            },
        }

    return jsonify({"data": result}), 200



# Define an endpoint for the route "/api/v1/trends" which accepts only GET requests.
@app.route('/api/v1/trends', methods=['GET'])
def get_trends():
    """
    Trend analysis per metric:
    - trend: direction, rate (per month), confidence (|pearson r|)
    - anomalies: z-score > 2
    - seasonality: seasonal averages (winter/spring/summer/fall)
    Optional filters: location_id, start_date, end_date, metric, quality_threshold
    """
    # Create a new database cursor from the MySQL connection.
    cur = mysql.connection.cursor()

    # Extract optional query parameters from the HTTP GET request.
    location_id = request.args.get('location_id', type=int)    # Location filter
    metric = request.args.get('metric')                        # Metric filter
    start_date = request.args.get('start_date')                # Start date filter
    end_date = request.args.get('end_date')                    # End date filter
    quality_threshold = request.args.get('quality_threshold')  # Minimum quality filter

    # Normalize metric and quality threshold strings to lower-case and strip whitespace
    metric_norm = metric.lower().strip() if metric else None
    qt_norm = quality_threshold.lower().strip() if quality_threshold else None

    # SQL query to fetch date, metric, unit, value, and quality fields from the database.
    sql = """
    SELECT
      cd.date,
      m.name AS metric,
      m.unit AS unit,
      cd.value,
      cd.quality
    FROM climate_data cd
    JOIN metrics m ON m.id = cd.metric_id
    WHERE
      (%s IS NULL OR cd.location_id = %s) AND                     -- filter by location if provided
      (%s IS NULL OR m.name = %s) AND                             -- filter by metric name if provided
      (%s IS NULL OR cd.date >= %s) AND                           -- filter by minimum date if provided
      (%s IS NULL OR cd.date <= %s) AND                           -- filter by maximum date if provided
      (
        %s IS NULL OR
        FIELD(cd.quality, 'poor','questionable','good','excellent')
          >= FIELD(%s, 'poor','questionable','good','excellent')  -- minimum quality threshold (ordered)
      )
    ORDER BY m.name ASC, cd.date ASC, cd.id ASC                   -- sort results
    """
    # List of parameter values in order to be inserted into the SQL query.
    params = [
        location_id, location_id,
        metric_norm, metric_norm,
        start_date, start_date,
        end_date, end_date,
        qt_norm, qt_norm
    ]
    # Execute the prepared SQL statement with the provided parameters.
    cur.execute(sql, params)
    # Retrieve all rows from the executed query.
    rows = cur.fetchall()
    # Close the database cursor to release resources.
    cur.close()

    # Group fetched data points by metric name (one entry per metric)
    groups = {}
    for r in rows:
        mname = r["metric"]                        # metric name
        unit = r["unit"]                           # unit for the metric
        d = r["date"]                              # date
        v = float(r["value"])                      # value (converted to float)
        q = r["quality"]                           # quality label
        groups.setdefault(mname, {"unit": unit, "points": []})
        groups[mname]["points"].append((d, v, q))  # Store tuple of (date, value, quality) for each metric

    # Function to compute linear trend (slope and abs(pearson r)) per month for a metric's points.
    def linear_trend_months(points):
        # If there aren't enough points, return 0, 0.
        if len(points) < 2:
            return 0.0, 0.0  # slope, |r|
        xs = []
        ys = []
        for d, v, _ in points:
            xm = d.year * 12 + d.month  # Convert date to "months since year 0"
            xs.append(xm)
            ys.append(v)
        # Set the start month to zero for x values
        x0 = xs[0]
        xs = [x - x0 for x in xs]

        n = len(xs)                      # number of samples
        sx = sum(xs)                     # sum of x
        sy = sum(ys)                     # sum of y
        sxy = sum(x*y for x, y in zip(xs, ys))  # sum of x*y
        sx2 = sum(x*x for x in xs)       # sum of x^2
        sy2 = sum(y*y for y in ys)       # sum of y^2

        denom = n * sx2 - sx * sx        # denominator for slope and r
        if denom == 0:
            slope = 0.0
        else:
            slope = (n * sxy - sx * sy) / denom  # Regression slope (rate per month)

        denom_x = denom
        denom_y = n * sy2 - sy * sy
        if denom_x > 0 and denom_y > 0:
            r = (n * sxy - sx * sy) / ((denom_x * denom_y) ** 0.5)  # pearson r
            conf = abs(r)  # confidence as absolute value of correlation coefficient
        else:
            conf = 0.0
        return slope, conf

    # Function to calculate mean and standard deviation for a list of points.
    def basic_stats(points):
        ys = [v for _, v, _ in points]         # extract values only
        n = len(ys)
        if n == 0:
            return 0.0, 0.0
        mean = sum(ys) / n
        var = (sum(y*y for y in ys) - (sum(ys) ** 2) / n) / n if n > 0 else 0.0
        std = var ** 0.5
        return mean, std

    # Function to detect and describe seasonality for each metric.
    def seasonality(points):
        # If there are no points, return not detected.
        if not points:
            return {"detected": False, "period": "yearly", "confidence": 0.0, "pattern": {}}
        # Create a bucket for each month (1 to 12).
        month_buckets = {m: [] for m in range(1, 13)}
        for d, v, _ in points:
            month_buckets[d.month].append(v)             # Assign value to the appropriate month
        # Calculate mean for each month, or None if there is no data.
        mavg = {m: (sum(vals) / len(vals)) if vals else None for m, vals in month_buckets.items()}

        # Helper: compute average for a group of months (e.g., for each season).
        def avg_months(ms):
            vals = [mavg[m] for m in ms if mavg[m] is not None]
            return (sum(vals) / len(vals)) if vals else None

        winter = avg_months([12, 1, 2])      # mean for Dec/Jan/Feb
        spring = avg_months([3, 4, 5])       # mean for Mar/Apr/May
        summer = avg_months([6, 7, 8])       # mean for Jun/Jul/Aug
        fall = avg_months([9, 10, 11])       # mean for Sep/Oct/Nov

        # List of seasonal means (filter out None values)
        vals = [x for x in [winter, spring, summer, fall] if x is not None]
        # If no seasonal means, return not detected.
        if not vals:
            return {"detected": False, "period": "yearly", "confidence": 0.0, "pattern": {}}
        rng = max(vals) - min(vals)       # range of the seasonal averages
        mean, std = basic_stats(points)   # global stats for the metric
        conf = 0.0 if std == 0 else min(0.99, (rng / (std * 4.0)))    # confidence score
        detected = rng > (0.5 if std == 0 else 0.5 * std)  # simple detection rule

        # Helper to compare seasonal means for trend label between seasons.
        def tlabel(a, b):
            if a is None or b is None:
                return "stable"
            delta = b - a
            return "increasing" if delta > 0.05 else ("decreasing" if delta < -0.05 else "stable")

        # Build a pattern dictionary showing average and trend from one season to the next.
        pattern = {
            "winter": {"avg": round(winter, 1) if winter is not None else None, "trend": "stable"},
            "spring": {"avg": round(spring, 1) if spring is not None else None, "trend": tlabel(winter, spring)},
            "summer": {"avg": round(summer, 1) if summer is not None else None, "trend": tlabel(spring, summer)},
            "fall": {"avg": round(fall, 1) if fall is not None else None, "trend": tlabel(summer, fall)},
        }
        # Return seasonality info in a dict.
        return {"detected": bool(detected), "period": "yearly", "confidence": round(conf, 2), "pattern": pattern}

    # Prepare output: a dict with an entry for each metric.
    out = {}
    for metric_name, meta in groups.items():
        pts = meta["points"]              # list of (date, value, quality) for this metric
        unit = meta["unit"]               # unit for this metric

        # Trend calculation: get slope and confidence per month
        slope, conf = linear_trend_months(pts)
        direction = "increasing" if slope > 0.05 else ("decreasing" if slope < -0.05 else "stable")

        # Detect anomalies based on z-score (>2 standard deviations from mean)
        mean, std = basic_stats(pts)
        anomalies = []
        if std and std > 0:
            for d, v, q in pts:
                z = (v - mean) / std
                if abs(z) > 2:
                    anomalies.append({
                        "date": d.isoformat(),           # date as string
                        "value": round(v, 1),            # round value
                        "deviation": round(abs(z), 1),   # z-score, abs and rounded
                        "quality": q                     # quality label
                    })

        # Compute seasonality for this metric's points.
        seas = seasonality(pts)

        # Store all analysis results for this metric in the output dictionary.
        out[metric_name] = {
            "trend": {
                "direction": direction,                 # trend direction string
                "rate": round(slope, 1),                # slope, rounded to 1 decimal point
                "unit": f"{unit}/month" if unit else None,    # e.g., "°C/month"
                "confidence": round(conf, 2),           # correlation, 2 decimals
            },
            "anomalies": anomalies,       # list of anomaly dicts
            "seasonality": seas           # seasonality summary
        }

    # Return the result as a JSON response with HTTP status 200.
    return jsonify({"data": out}), 200

if __name__ == '__main__':
    app.run(debug=True)
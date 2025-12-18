import requests
from flask import Flask, jsonify

app = Flask(__name__)

COMMONCRAWL_SERVICE = "http://commoncrawl:5000/process"
COLCAP_SERVICE = "http://colcap:5000/colcap"

@app.route("/aggregate", methods=["GET"])
def aggregate():
    term = "inflacion"
    dates = [("2023", "03"), ("2023", "04"), ("2023", "05")]

    news_data = []
    for y, m in dates:
        r = requests.get(COMMONCRAWL_SERVICE, params={
            "term": term,
            "year": y,
            "month": m
        })
        news_data.append(r.json())

    colcap_data = requests.get(COLCAP_SERVICE).json()

    merged = []
    for n in news_data:
        for c in colcap_data:
            if n["date"] == c["date"]:
                merged.append({
                    "date": n["date"],
                    "news": n["count"],
                    "colcap": c["colcap"]
                })

    return jsonify(merged)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
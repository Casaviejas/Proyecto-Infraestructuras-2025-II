import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ✅ CC-NEWS (dataset especializado en noticias)
COMMON_CRAWL_INDEX = "https://index.commoncrawl.org/CC-NEWS-2023-index"

@app.route("/process", methods=["GET"])
def process():
    term = request.args.get("term")
    year = request.args.get("year")
    month = request.args.get("month")

    if not term or not year or not month:
        return jsonify({"error": "Missing parameters"}), 400

    # Query al índice CC-NEWS
    url = (
        f"{COMMON_CRAWL_INDEX}"
        f"?url=*"
        f"&from={year}{month}01"
        f"&to={year}{month}31"
        f"&output=json"
    )

    response = requests.get(url, timeout=30)
    count = 0

    if response.status_code == 200:
        for line in response.text.splitlines():
            # Cada línea es un JSON con metadata de una noticia
            if term.lower() in line.lower():
                count += 1

    return jsonify({
        "date": f"{year}-{month}",
        "term": term,
        "news_count": count
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
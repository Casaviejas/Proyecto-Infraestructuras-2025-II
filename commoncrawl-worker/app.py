import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

COMMON_CRAWL_INDEX = "https://index.commoncrawl.org/CC-NEWS-2023-index"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (academic project; Universidad)"
}

@app.route("/process", methods=["GET"])
def process():
    year = request.args.get("year")
    month = request.args.get("month")

    url = (
        f"{COMMON_CRAWL_INDEX}"
        f"?url=*"
        f"&from={year}{month}01"
        f"&to={year}{month}31"
        f"&limit=1000"
        f"&output=json"
    )

    response = requests.get(url, headers=HEADERS, timeout=30)

    count = 0
    if response.status_code == 200 and response.text:
        count = len(response.text.splitlines())

    return jsonify({
        "date": f"{year}-{month}",
        "news_count": count
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

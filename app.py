import os
import requests
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2025-07"

@app.route("/api/collections")
def get_collection_ids():
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/custom_collections.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        collection_ids = [
            {"id": c["id"], "title": c["title"]} for c in data.get("custom_collections", [])
        ]
        return jsonify(collection_ids)
    except requests.RequestException as e:
        print(f"Shopify API error: {e}")
        return jsonify([]), 500

@app.route("/api/schedule", methods=["POST"])
def set_shuffle_schedule():
    data = request.get_json()
    collection_id = data.get("collectionId")
    interval = data.get("interval")
    print(f"Scheduled shuffle for collection {collection_id} every {interval}")
    # TODO: Add cronjob logic or database queueing
    return jsonify({"success": True})

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

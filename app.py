import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
API_VERSION = "2025-07"

@app.route("/api/collections")
def get_collection_ids():
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/custom_collections.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        collection_ids = [c["id"] for c in data.get("custom_collections", [])]
        return jsonify(collection_ids)
    except requests.RequestException as e:
        print(f"Shopify API error: {e}")
        return jsonify([]), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    
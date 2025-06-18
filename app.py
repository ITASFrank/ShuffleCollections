import os
import requests
import random
import re
from flask import Flask, jsonify, redirect, request, session, send_from_directory
from flask_cors import CORS
from urllib.parse import urlencode

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")
CORS(app)

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")
API_VERSION = "2025-07"
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://shufflecollections.onrender.com/api/auth/callback")

@app.route("/api/auth")
def auth():
    params = {
        "client_id": SHOPIFY_API_KEY,
        "scope": "read_products,write_products,read_custom_collections,write_custom_collections",
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
    }
    url = f"https://{SHOPIFY_STORE}/admin/oauth/authorize?{urlencode(params)}"
    return redirect(url)

@app.route("/api/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return "Missing code parameter", 400

    token_url = f"https://{SHOPIFY_STORE}/admin/oauth/access_token"
    payload = {
        "client_id": SHOPIFY_API_KEY,
        "client_secret": SHOPIFY_API_SECRET,
        "code": code
    }
    try:
        response = requests.post(token_url, json=payload)
        response.raise_for_status()
        session["shopify_token"] = response.json()["access_token"]
        return redirect("/")
    except Exception as e:
        print("OAuth callback failed:", e)
        return "Auth error", 500

@app.route("/api/collections")
def get_collection_ids():
    access_token = session.get("shopify_token")
    if not access_token:
        return jsonify({"error": "Unauthorized"}), 401

    base_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    try:
        custom_res = requests.get(f"{base_url}/custom_collections.json", headers=headers)
        smart_res = requests.get(f"{base_url}/smart_collections.json", headers=headers)

        custom_res.raise_for_status()
        smart_res.raise_for_status()

        custom_data = custom_res.json().get("custom_collections", [])
        smart_data = smart_res.json().get("smart_collections", [])

        return jsonify({
            "manual": [{"id": c["id"], "title": c["title"]} for c in custom_data],
            "smart": [{"id": c["id"], "title": c["title"]} for c in smart_data]
        })
    except requests.RequestException as e:
        print(f"Shopify API error: {e}")
        return jsonify({"error": "API failure"}), 500

@app.route("/api/shuffle-all", methods=["POST"])
def shuffle_all_collections():
    access_token = session.get("shopify_token")
    if not access_token:
        return jsonify({"error": "Unauthorized"}), 401

    base_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}"
    gql_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/graphql.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    def fetch_collects(cid):
        collects_url = f"{base_url}/collects.json?collection_id={cid}&limit=250"
        res = requests.get(collects_url, headers=headers)
        res.raise_for_status()
        return [c["product_id"] for c in res.json().get("collects", [])]

    def reorder_collection(cid):
        gid = f"gid://shopify/Collection/{cid}"
        product_ids = fetch_collects(cid)
        random.shuffle(product_ids)
        moves = [{"id": f"gid://shopify/Product/{pid}", "newPosition": str(i)} for i, pid in enumerate(product_ids)]
        query = """
        mutation collectionReorder($id: ID!, $moves: [MoveInput!]!) {
            collectionReorderProducts(id: $id, moves: $moves) {
                job { id }
                userErrors { field message }
            }
        }
        """
        res = requests.post(gql_url, headers=headers, json={"query": query, "variables": {"id": gid, "moves": moves}})
        return res.json()

    try:
        res = requests.get(f"{base_url}/custom_collections.json", headers=headers)
        res.raise_for_status()
        collections = res.json().get("custom_collections", [])
        results = {}
        for col in collections:
            cid = col["id"]
            results[cid] = reorder_collection(cid)
        return jsonify(results)
    except Exception as e:
        print("Shuffle all failed:", e)
        return jsonify({"error": "Shuffle all failed"}), 500

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

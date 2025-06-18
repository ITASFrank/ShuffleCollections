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

@app.route("/api/shuffle-now", methods=["POST"])
def shuffle_collection_now():
    access_token = session.get("shopify_token")
    if not access_token:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    collection_id = data.get("collectionId")
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    # Always use GraphQL to fetch product GIDs
    gid = f"gid://shopify/Collection/{collection_id}"
    gql_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/graphql.json"

    # GraphQL query to fetch product IDs in the collection
    query = """
    query getCollectionProducts($id: ID!) {
        collection(id: $id) {
            products(first: 250) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
    }
    """

    try:
        gql_res = requests.post(
            gql_url,
            headers=headers,
            json={"query": query, "variables": {"id": gid}}
        )
        gql_res.raise_for_status()
        edges = gql_res.json()["data"]["collection"]["products"]["edges"]
        product_ids = [edge["node"]["id"] for edge in edges]
        random.shuffle(product_ids)

        # Build moves array
        moves = [{"id": pid, "newPosition": str(idx)} for idx, pid in enumerate(product_ids)]

        # Reorder mutation
        mutation = """
        mutation collectionReorder($id: ID!, $moves: [MoveInput!]!) {
            collectionReorderProducts(id: $id, moves: $moves) {
                job { id }
                userErrors { field message }
            }
        }
        """

        reorder_res = requests.post(
            gql_url,
            headers=headers,
            json={"query": mutation, "variables": {"id": gid, "moves": moves}}
        )
        reorder_res.raise_for_status()
        result = reorder_res.json()
        return jsonify({"success": True, "response": result})

    except Exception as e:
        print("Shuffle failed:", e)
        return jsonify({"error": "Shuffle failed"}), 500

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

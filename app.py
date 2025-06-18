import os
import requests
import random
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

@app.route("/api/mirror", methods=["POST"])
def create_mirror():
    access_token = session.get("shopify_token")
    if not access_token:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    smart_id = data.get("smart_id")
    manual_id = data.get("manual_id")
    title = data.get("title") or "Shuffle Mirror"

    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }

    if not manual_id:
        create_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/custom_collections.json"
        payload = {"custom_collection": {"title": title}}
        try:
            res = requests.post(create_url, headers=headers, json=payload)
            res.raise_for_status()
            manual_id = res.json()["custom_collection"]["id"]
        except Exception as e:
            print("Mirror creation failed:", e)
            return jsonify({"error": "Failed to create mirror collection"}), 500

    try:
        gql_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/graphql.json"
        query = """
        query getProducts($collectionId: ID!) {
            collection(id: $collectionId) {
                products(first: 100, published_status: ANY) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
        """

        variables = {"collectionId": f"gid://shopify/Collection/{smart_id}"}

        gql_res = requests.post(gql_url, headers=headers, json={"query": query, "variables": variables})
        gql_res.raise_for_status()
        products = gql_res.json()["data"]["collection"]["products"]["edges"]
        product_ids = [edge["node"]["id"].split("/")[-1] for edge in products]
        random.shuffle(product_ids)

        # Clear existing collects from mirror collection
        clear_collects = requests.get(f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/collects.json?collection_id={manual_id}&limit=250", headers=headers)
        if clear_collects.ok:
            for c in clear_collects.json().get("collects", []):
                requests.delete(f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/collects/{c['id']}.json", headers=headers)

        for position, pid in enumerate(product_ids):
            collect_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/collects.json"
            collect_payload = {
                "collect": {
                    "collection_id": manual_id,
                    "product_id": pid,
                    "position": position + 1
                }
            }
            requests.post(collect_url, headers=headers, json=collect_payload)

        return jsonify({"success": True, "mirror_created": True, "mirror_id": manual_id})
    except Exception as e:
        print("Error syncing products:", e)
        return jsonify({"error": "Failed syncing products to mirror"}), 500

@app.route("/api/schedule", methods=["POST"])
def set_shuffle_schedule():
    data = request.get_json()
    collection_id = data.get("collectionId")
    interval = data.get("interval")
    print(f"Scheduled shuffle for collection {collection_id} every {interval}")
    return jsonify({"success": True})

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

    gid = f"gid://shopify/Collection/{collection_id}"
    collects_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/collects.json?collection_id={collection_id}&limit=250"
    try:
        res = requests.get(collects_url, headers=headers)
        res.raise_for_status()
        collects = res.json().get("collects", [])
        product_ids = [c["product_id"] for c in collects]
        random.shuffle(product_ids)

        moves = [{
            "id": f"gid://shopify/Product/{pid}",
            "newPosition": str(idx)
        } for idx, pid in enumerate(product_ids)]

        gql_url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/graphql.json"
        query = """
        mutation collectionReorder($id: ID!, $moves: [MoveInput!]!) {
            collectionReorderProducts(id: $id, moves: $moves) {
                job { id }
                userErrors { field message }
            }
        }
        """

        gql_payload = {
            "query": query,
            "variables": {
                "id": gid,
                "moves": moves
            }
        }

        gql_res = requests.post(gql_url, headers=headers, json=gql_payload)
        gql_res.raise_for_status()
        result = gql_res.json()
        print("GraphQL Response:", result)
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

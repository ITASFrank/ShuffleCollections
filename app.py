import os
import requests
from flask import Flask, jsonify, redirect, request, session, send_from_directory
from flask_cors import CORS
from urllib.parse import urlencode

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
CORS(app, supports_credentials=True)

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE")  # e.g. testforcsvpdf.myshopify.com
API_VERSION = "2025-07"
REDIRECT_URI = os.getenv(
    "REDIRECT_URI",
    f"https://shufflecollections.onrender.com/auth/callback"
)

SCOPES = "read_products,write_products"  # adjust as needed

@app.route("/api/auth")
def auth():
    params = {
        "client_id": SHOPIFY_API_KEY,
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code"
    }
    auth_url = f"https://{SHOPIFY_STORE}/admin/oauth/authorize?{urlencode(params)}"
    return redirect(auth_url)

@app.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return "Missing code from Shopify", 400

    token_resp = requests.post(
        f"https://{SHOPIFY_STORE}/admin/oauth/access_token",
        json={
            "client_id": SHOPIFY_API_KEY,
            "client_secret": SHOPIFY_API_SECRET,
            "code": code
        }
    )
    token_resp.raise_for_status()
    token = token_resp.json()["access_token"]
    session["shopify_token"] = token

    return redirect("/")

@app.route("/api/collections")
def get_collections():
    token = session.get("shopify_token")
    if not token:
        return jsonify({"error": "not_authenticated"}), 401

    resp = requests.get(
        f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/custom_collections.json",
        headers={"X-Shopify-Access-Token": token}
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print("Shopify collection fetch error:", resp.text)
        return jsonify({"error": "api_error"}), resp.status_code

    data = resp.json().get("custom_collections", [])
    return jsonify([{"id": c["id"], "title": c["title"]} for c in data])

@app.route("/api/schedule", methods=["POST"])
def schedule():
    if "shopify_token" not in session:
        return jsonify({"error": "not_authenticated"}), 401

    payload = request.get_json()
    # your scheduling logic here
    return jsonify({"success": True})

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def static_serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

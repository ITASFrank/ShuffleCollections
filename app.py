import os, random, requests
from flask import Flask, request, session, jsonify, send_from_directory, redirect, url_for
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")
SHOP = os.getenv("SHOPIFY_STORE")
API_VER = "2025-07"
KEY, SECRET = os.getenv("SHOPIFY_API_KEY"), os.getenv("SHOPIFY_API_SECRET")
REDIRECT = os.getenv("REDIRECT_URI")

def headers(token): return {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

@app.route("/api/auth")
def auth():
    params = {"client_id": KEY, "scope": "read_products,write_products,read_custom_collections,write_custom_collections", "redirect_uri": REDIRECT}
    return redirect(f"https://{SHOP}/admin/oauth/authorize?{urlencode(params)}")

@app.route("/api/auth/callback")
def cb():
    code = request.args.get("code")
    resp = requests.post(f"https://{SHOP}/admin/oauth/access_token", json={"client_id":KEY,"client_secret":SECRET,"code":code})
    session["token"] = resp.json()["access_token"]
    return redirect("/")

def get_smart_products(smart_id):
    r = requests.get(f"https://{SHOP}/admin/api/{API_VER}/collections/{smart_id}/products.json", headers=headers(session["token"]))
    r.raise_for_status()
    return [p["id"] for p in r.json().get("products",[])]

def clear_collects(custom_id):
    c = requests.get(f"https://{SHOP}/admin/api/{API_VER}/collects.json", params={"collection_id":custom_id}, headers=headers(session["token"]))
    for col in c.json().get("collects", []):
        requests.delete(f"https://{SHOP}/admin/api/{API_VER}/collects/{col['id']}.json",
                        headers=headers(session["token"]))

def create_collects(custom_id, ids):
    for i, pid in enumerate(ids,1):
        requests.post(f"https://{SHOP}/admin/api/{API_VER}/collects.json", headers=headers(session["token"]),
                      json={"collect":{"collection_id":custom_id,"product_id":pid,"position":i}})

@app.route("/api/mirror-shuffle", methods=["POST"])
def mirror_shuffle():
    data = request.json
    smart_id = data["smartId"]; custom_id = data.get("customId"); title = data.get("title","Shuffle Mirror")
    # fetch products
    ids = get_smart_products(smart_id)
    random.shuffle(ids)
    # create custom collection if needed
    if not custom_id:
        resp = requests.post(f"https://{SHOP}/admin/api/{API_VER}/custom_collections.json", headers=headers(session["token"]),
                             json={"custom_collection":{"title":title}})
        custom_id = resp.json()["custom_collection"]["id"]
    # rebuild mirror
    clear_collects(custom_id)
    create_collects(custom_id, ids)
    return jsonify({"success":True, "customId":custom_id, "count":len(ids)})

@app.route("/", defaults={"p":""})
@app.route("/<path:p>")
def spa(p):
    return send_from_directory(app.static_folder, "index.html")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)

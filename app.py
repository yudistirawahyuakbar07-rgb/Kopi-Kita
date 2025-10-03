from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = "kopikita_secret"

# data menu (sama seperti sebelumnya). pastikan nama gambar cocok di static/img/
MENU = {
    "best_seller": [
        {"id": 1, "name": "Latte", "price": 25000, "img": "latte.jpg"},
        {"id": 2, "name": "Kopi Susu", "price": 18000, "img": "kopi_susu.jpg"},
        {"id": 3, "name": "Americano", "price": 20000, "img": "americano.jpg"},
    ],
    "kalcer": [
        {"id": 4, "name": "Spaghetti", "price": 35000, "img": "spaghetti.jpg"},
        {"id": 5, "name": "French Fries", "price": 15000, "img": "french_fries.jpg"},
        {"id": 6, "name": "Seafood AlaCarte", "price": 45000, "img": "seafood_alacarte.jpg"},
        {"id": 7, "name": "Croissant", "price": 12000, "img": "croissant.jpg"},
        {"id": 8, "name": "Sourdough", "price": 20000, "img": "sourdough.jpg"},
    ],
    "drinks": [
        {"id": 9, "name": "Matcha Hakkon", "price": 28000, "img": "matcha_hakkon.jpg"},
        {"id": 10, "name": "Chocolate Hazelnut", "price": 30000, "img": "chocolate_hazelnut.jpg"},
        {"id": 11, "name": "Espresso", "price": 14000, "img": "espresso.jpg"},
        {"id": 12, "name": "Affogato", "price": 32000, "img": "affogato.jpg"},
        {"id": 13, "name": "Wedang Jahe", "price": 18000, "img": "wedang_jahe.jpg"},
    ],
    "meals": [
        {"id": 14, "name": "Nasi Goreng Cakalang", "price": 40000, "img": "nasi_goreng_cakalang.jpg"},
        {"id": 15, "name": "Nasi Bebek Madura", "price": 42000, "img": "nasi_bebek_madura.jpg"},
        {"id": 16, "name": "Pangsit Khas Kopi-Kita", "price": 22000, "img": "pangsit_kopikita.jpg"},
        {"id": 17, "name": "Nasi Lemak Kari", "price": 38000, "img": "nasi_lemak_kari.jpg"},
        {"id": 18, "name": "Nasi Goreng Kambing", "price": 45000, "img": "nasi_goreng_kambing.jpg"},
    ]
}



# simple in-memory reservations (for demo). In production use DB.
RESERVATIONS = []

def compute_discounts(subtotal, day, is_member):
    total = subtotal
    details = []
    if subtotal > 50000:
        total -= 5000
        details.append(("Promo Spesial", 5000))
    if day and day.lower() == "rabu":
        disc = int(total * 0.1)
        total -= disc
        details.append(("Diskon Rabu 10%", disc))
    if is_member:
        disc = int(total * 0.05)
        total -= disc
        details.append(("Diskon Member 5%", disc))
    return total, details

def safe_cart():
    c = session.get("cart", [])
    for i in c:
        i.setdefault("price", 0)
        i.setdefault("qty", 0)
        i["subtotal"] = i.get("price", 0) * i.get("qty", 0)
    return c

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/main")
def main():
    cart = safe_cart()
    return render_template("main.html", menu=MENU, cart_count=len(cart))

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    try:
        item_id = int(request.form.get("item_id", 0))
        qty = int(request.form.get("qty", 1))
    except Exception:
        return redirect(url_for("main"))
    item = None
    for cat in MENU.values():
        for it in cat:
            if it["id"] == item_id:
                item = it
                break
    if not item:
        return redirect(url_for("main"))
    cart = session.get("cart", [])
    found = False
    for c in cart:
        if c.get("id") == item_id:
            c["qty"] = c.get("qty", 0) + qty
            c["subtotal"] = c.get("price", 0) * c.get("qty", 0)
            found = True
            break
    if not found:
        cart.append({"id": item["id"], "name": item["name"], "price": item["price"], "qty": qty, "subtotal": item["price"]*qty})
    session["cart"] = cart
    return redirect(url_for("main"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = safe_cart()
    subtotal = sum(i["subtotal"] for i in cart)
    if request.method == "POST":
        name = request.form.get("name", "Tamu").strip()
        whatsapp = request.form.get("whatsapp", "-").strip()
        is_member = request.form.get("is_member") == "yes"
        day = request.form.get("day") or datetime.now().strftime("%A")
        total, discounts = compute_discounts(subtotal, day, is_member)
        receipt = {
            "name": name,
            "whatsapp": whatsapp,
            "is_member": is_member,
            "day": day,
            "cart": cart,
            "subtotal": subtotal,
            "discounts": discounts,
            "total": total,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        session["receipt"] = receipt
        session["cart"] = []
        return redirect(url_for("final"))
    return render_template("checkout.html", cart=cart, subtotal=subtotal)

@app.route("/final")
def final():
    r = session.get("receipt")
    if not r:
        return redirect(url_for("main"))
    # safe defaults
    r.setdefault("subtotal", 0)
    r.setdefault("discounts", [])
    r.setdefault("total", 0)
    r.setdefault("cart", [])
    for c in r["cart"]:
        c.setdefault("price", 0)
        c.setdefault("qty", 0)
        c["subtotal"] = c.get("price", 0) * c.get("qty", 0)
    return render_template("final.html", r=r)

# reservation endpoint
@app.route("/reserve", methods=["POST"])
def reserve():
    name = request.form.get("res_name", "").strip()
    phone = request.form.get("res_phone", "").strip()
    date = request.form.get("res_date", "").strip()
    pax = int(request.form.get("res_pax", "1"))
    min_spend = int(request.form.get("res_min_spend", "350000"))
    notes = request.form.get("res_notes", "").strip()

    # simple validation
    if not name or not phone or not date:
        return jsonify({"ok": False, "msg": "Nama, phone, dan tanggal wajib"}), 400
    # store reservation
    RESERVATIONS.append({
        "name": name, "phone": phone, "date": date, "pax": pax, "min_spend": min_spend, "notes": notes, "created": datetime.now().isoformat()
    })
    return jsonify({"ok": True, "msg": "Reservasi diterima. Kami akan konfirmasi via WA."})

# small api to return cart count (optional)
@app.route("/cart_count")
def cart_count():
    return jsonify({"count": len(session.get("cart", []))})

if __name__ == "__main__":
    app.run(debug=True, port=5000)

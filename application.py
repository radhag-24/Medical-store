
from flask import Flask, render_template, request, jsonify  
from controllers import purchase_bp, inventory_bp
import models


app = Flask(__name__)

app.register_blueprint(purchase_bp, url_prefix="/purchase")
app.register_blueprint(inventory_bp, url_prefix="/inventory")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/billing")
def billing_page():
    from models import cart
    total_amount = sum(item["amount"] for item in cart)
    return render_template("billing.html", cart=cart, total_amount=total_amount)

@app.route("/paymentSummary")
def payment_summary():
    invoice_no = request.args.get("invoice_no", "INV12345")
    total_amount = request.args.get("total_amount", 0)
    return render_template("payment_summary.html", 
                         invoice_no=invoice_no, 
                         total_amount=total_amount)

@app.route("/inventory/list")
def inventory_list():
    inventory = models.get_inventory_list()
    return render_template("inventory_list.html", inventory=inventory)
@app.route("/inventory/add-product")
def add_product_page():
    from models import get_types
    types = get_types()
    return render_template("add_product.html", types=types)

@app.route("/inventory/add-existing-product-form")
def add_existing_product_form():
    from models import get_types
    types = get_types()
    return render_template("add_existing_product.html", types=types)

@app.route("/inventory/add-new-product-type-form")
def add_new_product_type_form():
    return render_template("add_new_product_type.html")
if __name__ == "__main__":
    app.run(debug=True)

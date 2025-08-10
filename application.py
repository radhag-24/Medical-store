
from flask import Flask, render_template, request  
from controllers import bp as purchase_bp
import models


app = Flask(__name__)

app.register_blueprint(purchase_bp, url_prefix="/purchase")


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

@app.route("/inventory/update", methods=["GET"])
def inventory_update_form():
    from models import get_types, get_products
    types = get_types()
    selected_type = request.args.get('type_nr')
    products = []
    
    if selected_type:
        products = get_products(int(selected_type))
    
    return render_template("inventory.html", 
                         types=types, 
                         products=products,
                         selected_type=selected_type)

@app.route("/inventory/update-stock", methods=["POST"])
def update_stock():
    from models import update_stock, get_types, get_products

    type_nr = request.form.get("type_nr")
    product_nr = request.form.get("product_nr")
    quantity = request.form.get("quantity")
    stock_status = request.form.get("stock_status")

    if None in (type_nr, product_nr, quantity, stock_status) or "" in (type_nr, product_nr, quantity, stock_status):
        types = get_types()
        products = get_products(int(type_nr)) if type_nr else []
        return render_template("inventory.html", 
                               types=types,
                               products=products,
                               selected_type=type_nr,
                               message="Please fill all fields",
                               success=False)

    result = update_stock(int(type_nr), int(product_nr), int(quantity), None)  


    types = get_types()
    products = get_products(int(type_nr))

    if result["success"]:
        message = "Stock updated successfully"
        success = True
    else:
        message = result["error"]
        success = False

    return render_template("inventory.html", 
                           types=types,
                           products=products,
                           selected_type=type_nr,
                           message=message,
                           success=success)


if __name__ == "__main__":
    app.run(debug=True)

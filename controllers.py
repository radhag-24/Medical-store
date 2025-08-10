
from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import models

bp = Blueprint("purchase", __name__)

inventory_bp = Blueprint("inventory", __name__)


@bp.route("/")
def purchase_page():
    types = models.get_types()
    cart = models.view_cart()
    selected_type = request.args.get('type_nr')
    products = []
    
    if selected_type:
        products = models.get_products_with_details(int(selected_type))
    
    return render_template("purchase.html", 
                         types=types, 
                         products=products, 
                         cart=cart,
                         selected_type=selected_type)

@bp.route("/types", methods=["GET"])
def get_types():
    return jsonify(models.get_types())

@bp.route("/products/<int:type_nr>", methods=["GET"])
def get_products(type_nr):
    return jsonify(models.get_products(type_nr))

@bp.route("/product-stock/<int:type_nr>/<int:product_nr>", methods=["GET"])
def get_stock(type_nr, product_nr):
    return jsonify(models.get_stock(type_nr, product_nr))

@bp.route("/invoice-items/add", methods=["POST"])
def add_to_cart():
    try:
        product_id = int(request.form.get("product_id"))
        product_name = request.form.get("product_name")
        price = float(request.form.get("price"))
        quantity = int(request.form.get("quantity"))
        
        if not all([product_id, product_name, price, quantity]):
            return jsonify({"error": "Missing required fields"}), 400
            
        if quantity <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400
            
        data = {
            "product_id": product_id,
            "product_name": product_name,
            "price": price,
            "quantity": quantity
        }
        
        models.add_to_cart(data)
        return redirect(url_for("purchase.purchase_page"))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/invoice-items/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    models.remove_from_cart(product_id)
    return redirect(url_for("purchase.purchase_page"))


@bp.route("/invoice-items", methods=["GET"])
def view_cart():
    return jsonify(models.view_cart())

@bp.route("/invoice/generate", methods=["POST"])
def generate_invoice():
    mode_of_payment = request.form.get("mode_of_payment")
    
    if not mode_of_payment:
        return jsonify({"error": "Mode of payment is required"}), 400
    
    result = models.generate_invoice({"mode_of_payment": mode_of_payment})
    
    return redirect(url_for("payment_summary", 
                          invoice_no=result["invoice_no"],
                          total_amount=result["total_amount"]))

@inventory_bp.route("/inventory/list")
def inventory_list():
    inventory = models.get_inventory_list()
    return render_template("inventory_list.html", inventory=inventory)


@bp.route("/inventory/update-stock", methods=["POST"])
def update_stock():
    data = request.get_json()

    type_nr = data.get("type_nr")
    product_nr = data.get("product_nr")
    quantity = data.get("quantity")
    stock_status = data.get("stock_status")

    if None in (type_nr, product_nr, quantity, stock_status):
        return jsonify({"error": "Missing required fields"}), 400

    result = models.update_stock(type_nr, product_nr, quantity, stock_status)

    if result["success"]:
        return jsonify({"message": "Stock updated successfully"})
    else:
        return jsonify({"error": result["error"]}), 400
    

@bp.route("/inventory/update", methods=["GET"])
def inventory_update_form():
    return render_template("inventory.html")


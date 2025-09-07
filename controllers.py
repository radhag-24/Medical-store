from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import models


purchase_bp = Blueprint("purchase", __name__)
inventory_bp = Blueprint("inventory", __name__)


@purchase_bp.route("/")
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

@purchase_bp.route("/types", methods=["GET"])
def get_types():
    return jsonify(models.get_types())

@purchase_bp.route("/products/<int:type_nr>", methods=["GET"])
def get_products(type_nr):
    return jsonify(models.get_products(type_nr))

@purchase_bp.route("/product-stock/<int:type_nr>/<int:product_nr>", methods=["GET"])
def get_stock(type_nr, product_nr):
    return jsonify(models.get_stock(type_nr, product_nr))

@purchase_bp.route("/invoice-items/add", methods=["POST"])
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

@purchase_bp.route("/invoice-items/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):
    models.remove_from_cart(product_id)
    return redirect(url_for("purchase.purchase_page"))

@purchase_bp.route("/invoice/generate", methods=["POST"])
def generate_invoice():
    mode_of_payment = request.form.get("mode_of_payment")
    
    if not mode_of_payment:
        return jsonify({"error": "Mode of payment is required"}), 400
    
    result = models.generate_invoice({"mode_of_payment": mode_of_payment})
    
    return redirect(url_for("payment_summary", 
                          invoice_no=result["invoice_no"],
                          total_amount=result["total_amount"]))

@purchase_bp.route("/history")
def purchase_history():
    rows = models.get_purchase_history()
    return render_template("purchase_history.html", rows=rows)

@purchase_bp.route("/purchase/delete/<int:row_id>", methods=["POST"])
def delete_purchase(row_id):
    models.delete_purchase_item(row_id)
    return redirect(url_for("purchase.purchase_history"))


@inventory_bp.route("/list")
def inventory_list():
    inventory = models.get_inventory_list()
    return render_template("inventory_list.html", inventory=inventory)

@inventory_bp.route("/update", methods=["GET"])
def inventory_update_form():
    types = models.get_types()
    selected_type = request.args.get('type_nr')
    products = []
    
    if selected_type:
        products = models.get_products(int(selected_type))
    
    return render_template("inventory.html", 
                         types=types, 
                         products=products,
                         selected_type=selected_type)

@inventory_bp.route("/update-stock", methods=["POST"])
def update_stock():
    type_nr = request.form.get("type_nr")
    product_nr = request.form.get("product_nr")
    quantity = request.form.get("quantity")
    stock_status = request.form.get("stock_status")

    if None in (type_nr, product_nr, quantity, stock_status):
        types = models.get_types()
        products = models.get_products(int(type_nr)) if type_nr else []
        return render_template("inventory.html", 
                             types=types,
                             products=products,
                             selected_type=type_nr,
                             message="Please fill all fields",
                             success=False)

    result = models.update_stock(int(type_nr), int(product_nr), int(quantity), stock_status)
    
    types = models.get_types()
    products = models.get_products(int(type_nr))

    return render_template("inventory.html", 
                         types=types,
                         products=products,
                         selected_type=type_nr,
                         message="Stock updated successfully" if result["success"] else result["error"],
                         success=result["success"])



@inventory_bp.route("/add-product")
def add_product_page():
    types = models.get_types()
    return render_template("add_product.html", types=types)

@inventory_bp.route("/add-existing-product-form")
def add_existing_product_form():
    types = models.get_types()
    return render_template("add_existing_product.html", types=types)

@inventory_bp.route("/add-new-product-type-form")
def add_new_product_type_form():
    return render_template("add_new_product_type.html")


@inventory_bp.route("/add-existing-product", methods=["POST"])
def add_existing_product():
    try:
        type_nr = int(request.form.get("type_nr"))
        product_name = request.form.get("product_name")
        price = float(request.form.get("price"))
        quantity = int(request.form.get("quantity"))
        
        result = models.add_product_existing_type(type_nr, product_name, price, quantity)
        
        if result['success']:
            return render_template("add_existing_product.html", 
                                types=models.get_types(),
                                message="Product added successfully",
                                success=True)
        return render_template("add_existing_product.html", 
                            types=models.get_types(),
                            message=result['error'],
                            success=False)
    except Exception as e:
        return render_template("add_existing_product.html", 
                            types=models.get_types(),
                            message=str(e),
                            success=False)

@inventory_bp.route("/add-new-product-type", methods=["POST"])
def add_new_product_type():
    try:
        new_type_name = request.form.get("new_type_name")
        product_name = request.form.get("product_name")
        price = float(request.form.get("price"))
        quantity = int(request.form.get("quantity"))
        
        result = models.add_new_product_with_type(new_type_name, product_name, price, quantity)
        
        if result['success']:
            return render_template("add_new_product_type.html",
                                message="New product type and product added successfully",
                                success=True)
        return render_template("add_new_product_type.html",
                            message=result['error'],
                            success=False)
    except Exception as e:
        return render_template("add_new_product_type.html",
                            message=str(e),
                            success=False)
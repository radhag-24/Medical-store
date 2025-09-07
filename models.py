import mysql.connector
import json
from datetime import datetime

with open("config.json") as f:
    db_config = json.load(f)

cart = []



def get_connection():
    return mysql.connector.connect(**db_config)

def get_types():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nr, type FROM hc_product_type ORDER BY type ASC;")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_products(type_nr):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT pm.nr, pm.name, IFNULL(i.available_stock, 0) AS available_stock
        FROM hc_product_master pm
        LEFT JOIN hc_inventory i ON pm.nr = i.product_nr
        WHERE pm.type_nr = %s
        ORDER BY pm.name ASC;
    """, (type_nr,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_stock(type_nr, product_nr):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.available_stock AS quantity
        FROM hc_product_master pm
        JOIN hc_inventory i ON pm.nr = i.product_nr
        JOIN hc_product_type pt ON pt.nr = i.type_nr
        WHERE i.type_nr = %s AND i.product_nr = %s 
          AND i.stock_status = 'in-stock';
    """, (type_nr, product_nr))
    row = cursor.fetchone()
    conn.close()
    return row

def add_to_cart(data):
    product_id = data["product_id"]
    product_name = data["product_name"]
    price = data["price"]
    quantity = data["quantity"]
    amount = price * quantity
    cart.append({
        "product_id": product_id,
        "product_name": product_name,
        "price": price,
        "quantity": quantity,
        "amount": amount
    })
    return {"message": "Item added to cart", "cart": cart}

def remove_from_cart(product_id):
    global cart
    cart = [item for item in cart if item["product_id"] != product_id]
    return {"message": "Item removed", "cart": cart}

def get_products_with_details(type_nr):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT pm.nr, pm.name, pm.price, pm.type_nr
        FROM hc_product_master pm
        JOIN hc_inventory i ON pm.nr = i.product_nr
        WHERE pm.type_nr = %s AND i.stock_status = 'in-stock'
        ORDER BY pm.name ASC;
    """, (type_nr,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def view_cart():
    return cart

def get_inventory_list():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            pt.type AS product_type,
            pm.name AS product_name,
            IFNULL(i.available_stock, 0) AS stock,
            IFNULL(i.stock_status, 'out-of-stock') AS status
        FROM 
            hc_product_master pm
        JOIN 
            hc_product_type pt ON pm.type_nr = pt.nr
        LEFT JOIN 
            hc_inventory i ON pm.nr = i.product_nr
        ORDER BY 
    stock DESC, pt.type, pm.name;
    """
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()
    return result

def update_stock(type_nr, product_nr, quantity, stock_status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nr FROM hc_inventory
        WHERE type_nr = %s AND product_nr = %s
    """, (type_nr, product_nr))
    record = cursor.fetchone()

    if not record:
        return {"success": False, "error": "Inventory record not found for given product type and product."}

    new_status = 'out-of-stock' if quantity == 0 else 'in-stock'

    cursor.execute("""
        UPDATE hc_inventory
        SET available_stock = available_stock + %s,
            stock_status = %s
        WHERE type_nr = %s AND product_nr = %s
    """, (quantity, new_status, type_nr, product_nr))



    conn.commit()
    conn.close()
    return {"success": True}


def generate_invoice(data):
    mode_of_payment = data.get("mode_of_payment")
    if not cart:
        return {"error": "Cart is empty"}

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT MAX(CAST(SUBSTRING(invoice_no, 5) AS UNSIGNED)) 
            FROM hc_payment_history 
            WHERE invoice_no LIKE 'INV-%'
        """)
        last_invoice_num = cursor.fetchone()[0]

        new_num = 1 if last_invoice_num is None else last_invoice_num + 1
        invoice_no = f"INV-{str(new_num).zfill(3)}"

        cursor.execute("""
            SELECT MAX(CAST(SUBSTRING(shipping_no, 5) AS UNSIGNED)) 
            FROM hc_invoice_item_history 
            WHERE shipping_no LIKE 'SHI-%'
        """)
        last_shipping_num = cursor.fetchone()[0]
        new_shipping_num = 1 if last_shipping_num is None else last_shipping_num + 1

        total_amount = sum(item["amount"] for item in cart)

        cursor.execute("""
            INSERT INTO hc_payment_history (invoice_no, amount, mode_of_payment, create_date)
            VALUES (%s, %s, %s, NOW())
        """, (invoice_no, total_amount, mode_of_payment))
        payment_nr = cursor.lastrowid

        for item in cart:
            shipping_no = f"SHI-{str(new_shipping_num).zfill(3)}"
            new_shipping_num += 1 
            cursor.execute("""
                INSERT INTO hc_invoice_item_history 
                (payment_nr, inv_no, shipping_no, product_id, product_name, amount, quantity, total_amount, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                payment_nr,
                invoice_no,
                shipping_no,
                item["product_id"],
                item["product_name"],
                item["price"],
                item["quantity"],
                item["amount"]
            ))

            cursor.execute("SELECT available_stock FROM hc_inventory WHERE product_nr = %s", (item["product_id"],))
            current_stock = cursor.fetchone()[0]
            new_stock = current_stock - item["quantity"]

            if new_stock < 0:
                raise ValueError(f"Insufficient stock for product {item['product_name']}")

            new_status = 'in-stock' if new_stock > 0 else 'out-of-stock'

            cursor.execute("""
                UPDATE hc_inventory 
                SET available_stock = %s, stock_status = %s 
                WHERE product_nr = %s
            """, (new_stock, new_status, item["product_id"]))

        conn.commit()
        return {"message": "Invoice generated", "invoice_no": invoice_no, "total_amount": total_amount}

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cart.clear()
        conn.close()

def get_purchase_history():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        h.create_date AS date,
        pt.type AS product_type,
        h.product_name,
        h.quantity,
        h.total_amount,
        ph.mode_of_payment,
        h.shipping_no,
        h.shipping_status,
        h.nr AS row_id
    FROM hc_invoice_item_history h
    LEFT JOIN hc_inventory inv ON h.product_id = inv.product_nr
    LEFT JOIN hc_product_type pt ON inv.type_nr = pt.nr
    LEFT JOIN hc_payment_history ph ON h.inv_no = ph.invoice_no
    ORDER BY h.nr DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_purchase_item(row_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM hc_invoice_item_history WHERE nr = %s", (row_id,))
    conn.commit()
    conn.close()



def add_product_existing_type(type_nr, product_name, price, quantity):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
       
        cursor.execute("SELECT nr FROM hc_product_type WHERE nr = %s", (type_nr,))
        if not cursor.fetchone():
            return {"success": False, "error": "Product type does not exist"}
        
    
        cursor.execute("""
            INSERT INTO hc_product_master (name, price, type_nr)
            VALUES (%s, %s, %s)
        """, (product_name, price, type_nr))
        product_nr = cursor.lastrowid
        
     
        stock_status = 'in-stock' if quantity > 0 else 'out-of-stock'
        cursor.execute("""
            INSERT INTO hc_inventory (type_nr, product_nr, available_stock, stock_status)
            VALUES (%s, %s, %s, %s)
        """, (type_nr, product_nr, quantity, stock_status))
        
        conn.commit()
        return {"success": True, "product_id": product_nr}
        
    except mysql.connector.Error as err:
        if conn and conn.in_transaction:
            conn.rollback()
        return {"success": False, "error": f"Database error: {err}"}
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def add_new_product_with_type(new_type_name, product_name, price, quantity):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
       
        conn.start_transaction()
        
        cursor.execute("""
            INSERT INTO hc_product_type (type)
            VALUES (%s)
        """, (new_type_name,))
        type_nr = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO hc_product_master (name, price, type_nr)
            VALUES (%s, %s, %s)
        """, (product_name, price, type_nr))
        product_nr = cursor.lastrowid
        
        stock_status = 'in-stock' if quantity > 0 else 'out-of-stock'
        cursor.execute("""
            INSERT INTO hc_inventory (type_nr, product_nr, available_stock, stock_status)
            VALUES (%s, %s, %s, %s)
        """, (type_nr, product_nr, quantity, stock_status))
        
        conn.commit()
        return {
            "success": True,
            "type_id": type_nr,
            "product_id": product_nr
        }
        
    except mysql.connector.Error as err:
        if conn and conn.in_transaction:
            conn.rollback()
        return {"success": False, "error": f"Database error: {err}"}
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
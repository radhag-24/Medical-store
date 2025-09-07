# 🏥 Health Care Store Billing System

A **mini full-stack project** for managing products, inventory, cart, and billing in a healthcare store.  
Built with **Flask (Python)**, **MySQL**, **HTML/CSS/JavaScript**.

---

## 🚀 Features
- Add products to cart and manage quantities  
- View and remove items from cart  
- Generate invoice with **unique invoice number**  
- Track payment method (Cash, Card, UPI)  
- Store purchase history and inventory in MySQL  
- Inventory management: add products, update stock, track product types  

---

## 🏗️ Tech Stack
- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Flask (Python)  
- **Database:** MySQL  

---

## 📂 Project Structure
HEALTH_CARE/
│
├─ static/
│ ├─ cart.css
│ ├─ home.css
│ ├─ inventory_list.css
│ ├─ inventory.css
│ ├─ payment.css
│ ├─ purchase_history.css
│
├─ templates/
│ ├─ add_existing_product.html
│ ├─ add_new_product_type.html
│ ├─ add_product.html
│ ├─ billing.html
│ ├─ cart.html
│ ├─ home.html
│ ├─ index.html
│ ├─ inventory_list.html
│ ├─ inventory.html
│ ├─ items.html
│ ├─ payment.html
│ ├─ payment_summary.html
│ ├─ purchase_history.html
│ └─ purchase.html
│
├─ application.py # Main Flask application
├─ controllers.py # Request handlers / routes
├─ models.py # Database queries and models
├─ config.json # Database credentials
├─ config.example.json # Example config template
└─ .gitignore
---

## 🗄️ Database Schema (MySQL)

**Tables used:**
-- Database: health_care_db
CREATE DATABASE IF NOT EXISTS health_care_db;
USE health_care_db;

-- Table: hc_product_type
CREATE TABLE IF NOT EXISTS hc_product_type (
    nr INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(100) UNIQUE NOT NULL
);

-- Table: hc_product_master
CREATE TABLE IF NOT EXISTS hc_product_master (
    nr INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    type_nr INT,
    FOREIGN KEY (type_nr) REFERENCES hc_product_type(nr)
);

-- Table: hc_inventory
CREATE TABLE IF NOT EXISTS hc_inventory (
    nr INT AUTO_INCREMENT PRIMARY KEY,
    type_nr INT,
    product_nr INT,
    available_stock INT DEFAULT 0,
    stock_status ENUM('in-stock','out-of-stock') DEFAULT 'out-of-stock',
    FOREIGN KEY (type_nr) REFERENCES hc_product_type(nr),
    FOREIGN KEY (product_nr) REFERENCES hc_product_master(nr)
);

-- Table: hc_payment_history
CREATE TABLE IF NOT EXISTS hc_payment_history (
    nr INT AUTO_INCREMENT PRIMARY KEY,
    invoice_no VARCHAR(50) UNIQUE,
    amount DECIMAL(10,2),
    mode_of_payment VARCHAR(50),
    create_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table: hc_invoice_item_history
CREATE TABLE IF NOT EXISTS hc_invoice_item_history (
    nr INT AUTO_INCREMENT PRIMARY KEY,
    payment_nr INT,
    inv_no VARCHAR(50),
    shipping_no VARCHAR(50),
    product_id INT,
    product_name VARCHAR(255),
    amount DECIMAL(10,2),
    quantity INT,
    total_amount DECIMAL(10,2),
    create_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    shipping_status VARCHAR(50) DEFAULT 'pending',
    FOREIGN KEY (payment_nr) REFERENCES hc_payment_history(nr),
    FOREIGN KEY (product_id) REFERENCES hc_product_master(nr)
);

## Running the Project
1.Install dependencies:
  pip install flask mysql-connector-python
2.Run the Flask app:
  python application.py
3.Open the app in browser:
  http://127.0.0.1:5000/

Notes

This is a mini project; no virtual environment or requirements file included.
All CRUD operations for products, inventory, cart, and invoices are handled via Flask routes.
Frontend pages use HTML, CSS, and JS with DOM manipulation for dynamic cart and stock updates.

## License

MIT License
© 2025 Radha G

**Author: Radha G**


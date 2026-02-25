from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
from io import BytesIO
from reportlab.pdfgen import canvas
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secretkey'  # For session management

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password TEXT)''')
    # Cart table
    c.execute('''CREATE TABLE IF NOT EXISTS cart 
                 (id INTEGER PRIMARY KEY, username TEXT, item TEXT, quantity INTEGER, price REAL)''')
    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY, username TEXT, items TEXT, total_price REAL, 
                  payment_status TEXT, order_status TEXT, payment_method TEXT, order_date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Route: Welcome Page
@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

# Route: Home Page (with category filtering and search)
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Sample product list with categories
    products = [
        {"name": "Apples", "price": 50, "image": "images/apple.jpg", "category": "Food"},
        {"name": "Playstation", "price": 35000.0, "image": "images/playstation.jpg", "category": "Electronics"},
        {"name": "Water", "price": 28.0, "image": "images/water.jpg", "category": "Food"},
        {"name": "Microwave", "price": 5000.0, "image": "images/microwave.png", "category": "Electronics"},
        {"name": "Milk", "price": 68.0, "image": "images/milk.png", "category": "Food"},
        {"name": "Shower Gel", "price": 1090.0, "image": "images/showergel.jpg", "category": "Health & Beauty"},
        {"name": "Tissue", "price": 323.0, "image": "images/Tissue.png", "category": "Household"},
        {"name": "Oraimo Charger", "price": 830.0, "image": "images/Oraimo charger.jpg", "category": "Electronics"},
        {"name": "TV", "price": 134990.0, "image": "images/tv.png", "category": "Electronics"},
        {"name": "Dettol Soap", "price": 249.0, "image": "images/dettol.jpg", "category": "Health & Beauty"},
        {"name": "Matches", "price": 33.0, "image": "images/matches.jpg", "category": "Household"},
        {"name": "Fridge", "price": 39000.0, "image": "images/fridge.png", "category": "Electronics"},
        {"name": "Mattress", "price": 26000.0, "image": "images/matress.jpg", "category": "Bedding"},
        {"name": "Cooking set", "price": 8500.0, "image": "images/cooking pots.png", "category": "Household"},
        {"name": "3 Pillow set", "price": 900.0, "image": "images/pillow.jpg", "category": "Bedding"},
        {"name": "Duvet", "price": 3000.0, "image": "images/duvets.png", "category": "Bedding"},
        {"name": "Maize flour", "price": 190.0, "image": "images/maize flour.jpg", "category": "Food"},
        {"name": "Baking flour", "price": 210.0, "image": "images/baking flour.jpg", "category": "Food"},
        {"name": "Toothpaste", "price": 345.0, "image": "images/toothpaste.jpg", "category": "Health & Beauty"},
        {"name": "Lotion", "price": 310.0, "image": "images/lotion.jpg", "category": "Health & Beauty"},

    ]
    
    # Group products by category
    categories = {}
    for product in products:
        category = product['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(product)
    
    # Handle search and category filtering
    filtered_products = products
    selected_category = None
    search_query = None

    if request.method == 'POST':
        selected_category = request.form.get('category')
        search_query = request.form.get('search')

        # Filter by category
        if selected_category and selected_category != "All":
            filtered_products = [product for product in products if product['category'] == selected_category]

        # Search within the category
        if search_query:
            filtered_products = [product for product in filtered_products if search_query.lower() in product['name'].lower()]

    # Pass filtered products and categories to the template
    return render_template('index.html', categories=categories, products=filtered_products, selected_category=selected_category, search_query=search_query)

# Route: Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                  (username, email, hashed_password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[3], password):
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            return "Invalid credentials. Please try again."
    return render_template('login.html')

# Route: Logout
@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear the session
    return redirect(url_for('welcome'))  # Redirect to Welcome Page

# Route: Add to Cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    item = request.form['item']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO cart (username, item, quantity, price) VALUES (?, ?, ?, ?)", 
              (username, item, quantity, price * quantity))
    conn.commit()
    conn.close()

    # Flash message for success notification
    flash(f"'{item}' has been added to your cart!", "success")
    return redirect(url_for('index'))

# Route: View Cart
@app.route('/cart')
def cart():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, item, quantity, price FROM cart WHERE username = ?", (username,))
    items = c.fetchall()
    conn.close()
    
    total = sum(item[3] for item in items)
    return render_template('cart.html', items=items, total=total)

# Route: Remove Item from Cart
@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM cart WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('cart'))

# Route: Checkout
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    
    if request.method == 'POST':
        # Capture billing and payment details
        name = request.form['name']
        payment_method = request.form['payment_method']
        phone = request.form.get('phone', None)

        # Retrieve cart items
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT item, quantity, price FROM cart WHERE username = ?", (username,))
        cart_items = c.fetchall()
        
        items = ", ".join([f"{item[1]}x {item[0]}" for item in cart_items])
        total_price = sum([item[2] for item in cart_items])
        
        # Save the order as "Pending Payment"
        c.execute('''INSERT INTO orders 
                     (username, items, total_price, payment_status, order_status, payment_method, order_date) 
                     VALUES (?, ?, ?, ?, ?, ?, DATE('now'))''', 
                  (username, items, total_price, "Pending Payment", "Pending", payment_method))
        conn.commit()
        conn.close()

        flash(f"Order has been placed. Your payment is now pending.", "info")
        return redirect(url_for('track_orders'))  # Redirect to track_orders to see the pending order
    
    return render_template('checkout.html')

# Route: Track Orders
@app.route('/track_orders')
def track_orders():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    username = session['username']  # Get the logged-in username
    
    # Retrieve orders from the database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT id, items, total_price, payment_status, order_status, order_date 
                 FROM orders WHERE username = ?''', (username,))
    orders = c.fetchall()
    conn.close()

    # Pass the orders to the template
    return render_template('track_orders.html', orders=orders)

# Route: Verify Payment and Mark Order as Verified
@app.route('/verify_payment/<int:order_id>', methods=['POST'])
def verify_payment(order_id):
    if 'username' not in session or session['username'] != 'admin':  # Only admin can verify payment
        return redirect(url_for('login'))
    
    # Mark payment as approved and order as shipped
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''UPDATE orders 
                 SET payment_status = ?, order_status = ?, served_by = ? 
                 WHERE id = ?''', 
              ("Payment Approved", "Shipped", session['username'], order_id))
    conn.commit()
    conn.close()

    # Flash message to notify admin and user
    flash("Payment has been verified and order is marked as shipped.", "success")
    return redirect(url_for('track_orders'))

# Route: Download Receipt
@app.route('/download_receipt/<int:order_id>')
def download_receipt(order_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE id = ? AND username = ?", (order_id, username))
    order = c.fetchone()
    conn.close()

    # Ensure the order exists and payment is approved
    if not order or order[3] != "Payment Approved":
        flash("Receipt is not available for this order.", "danger")
        return redirect(url_for('track_orders'))
    
    # Generate PDF receipt
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 800, f"Receipt for Order ID: {order[0]}")
    pdf.drawString(100, 780, f"Customer Name: {order[1]}")
    pdf.drawString(100, 760, f"Items: {order[2]}")
    pdf.drawString(100, 740, f"Total Price: Ksh {order[3]}")
    pdf.drawString(100, 720, f"Payment Status: {order[3]}")
    pdf.drawString(100, 700, f"Order Status: {order[4]}")
    pdf.drawString(100, 680, f"Order Date: {order[5]}")
    pdf.save()
    buffer.seek(0)

    # Return the generated PDF as a downloadable file
    return send_file(buffer, as_attachment=True, download_name=f"receipt_order_{order[0]}.pdf", mimetype="application/pdf")

if __name__ == '__main__':
    app.run(debug=True)

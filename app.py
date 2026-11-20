from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
import random
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)
# 设置会话有效期为1小时
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Product data file paths
PRODUCTS_FILE = 'data/products.json'
ORDERS_FILE = 'data/orders.json'

# Initialize product data
def init_products():
    if not os.path.exists(PRODUCTS_FILE):
        # Get product names from static image folder
        product_images = os.listdir('static/images/products')
        
        # Create product data
        products = []
        categories = {
            "Food": ["Fresh Food", "Frozen Food"],
            "Beverages": ["Juice", "Soda", "Coffee"],
            "Household": ["Cleaning", "Kitchen"],
            "Personal Care": ["Bath & Body"],
            "Pet Supplies": ["Pet Food", "Pet Treats"]
        }
        
        # Product category mapping
        product_categories = {
            "Fresh Spinach.jpeg": {"category": "Food", "subcategory": "Fresh Food"},
            "Chicken Breast.jpeg": {"category": "Food", "subcategory": "Fresh Food"},
            "Organic Bananas.jpeg": {"category": "Food", "subcategory": "Fresh Food"},
            "Frozen Mixed Vegetables.jpeg": {"category": "Food", "subcategory": "Frozen Food"},
            "Frozen Pizza.jpeg": {"category": "Food", "subcategory": "Frozen Food"},
            "Ice Cream - Vanilla.jpeg": {"category": "Food", "subcategory": "Frozen Food"},
            "Orange Juice.jpeg": {"category": "Beverages", "subcategory": "Juice"},
            "Cola .jpeg": {"category": "Beverages", "subcategory": "Soda"},
            "Premium Coffee.jpeg": {"category": "Beverages", "subcategory": "Coffee"},
            "All-Purpose Cleaner.jpeg": {"category": "Household", "subcategory": "Cleaning"},
            "Kitchen Towels.jpeg": {"category": "Household", "subcategory": "Kitchen"},
            "Shower Gel.jpeg": {"category": "Personal Care", "subcategory": "Bath & Body"},
            "Premium Dog Food.jpeg": {"category": "Pet Supplies", "subcategory": "Pet Food"},
            "Cat Food - Salmon.jpeg": {"category": "Pet Supplies", "subcategory": "Pet Food"},
            "Pet Treats.jpeg": {"category": "Pet Supplies", "subcategory": "Pet Treats"}
        }
        
        for image in product_images:
            name = image.split('.')[0]
            category_info = product_categories.get(image, {"category": "Other", "subcategory": "Other"})
            
            product = {
                "id": str(len(products) + 1),
                "name": name,
                "image": f"products/{image}",
                "price": round(random.uniform(1.99, 15.99), 2),
                "unit": random.choice(["kg", "pack", "item", "bottle", "box"]),
                "stock": 5,
                "category": category_info["category"],
                "subcategory": category_info["subcategory"],
                "description": f"Premium quality {name.lower()}"
            }
            products.append(product)
        
        # Save product data to JSON file
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump({"products": products, "categories": categories}, f, indent=4)
    
    # Load product data
    with open(PRODUCTS_FILE, 'r') as f:
        return json.load(f)

# Get product data
def get_products():
    if not os.path.exists(PRODUCTS_FILE):
        return init_products()
    
    with open(PRODUCTS_FILE, 'r') as f:
        return json.load(f)

# Save order
def save_order(order_data):
    orders = []
    if os.path.exists(ORDERS_FILE) and os.path.getsize(ORDERS_FILE) > 0:
        try:
            with open(ORDERS_FILE, 'r') as f:
                orders = json.load(f)
        except json.JSONDecodeError:
            # 文件存在但不是有效的JSON，则初始化为空数组
            orders = []
    
    orders.append(order_data)
    
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=4)

# Update product stock
def update_stock(cart_items):
    data = get_products()
    products = data["products"]
    
    for item in cart_items:
        for product in products:
            if product["id"] == item["id"]:
                product["stock"] -= item["quantity"]
                break
    
    with open(PRODUCTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Validate if products in cart have enough stock
def validate_cart(cart_items):
    data = get_products()
    products = {product["id"]: product for product in data["products"]}
    
    unavailable_items = []
    
    for item in cart_items:
        product = products.get(item["id"])
        if not product:
            unavailable_items.append({
                "name": item["name"],
                "requested": item["quantity"],
                "available": 0,
                "reason": "Product not found"
            })
        elif product["stock"] < item["quantity"]:
            unavailable_items.append({
                "name": item["name"],
                "requested": item["quantity"],
                "available": product["stock"],
                "reason": "Insufficient stock"
            })
    
    return unavailable_items

# Route: Home page
@app.route('/')
def home():
    data = get_products()
    return render_template('index.html', data=data)

# Route: Search
@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    data = get_products()
    
    if not query:
        return render_template('search.html', products=[], query=query, data=data)
    
    results = []
    for product in data["products"]:
        # 搜索产品名称、描述和分类
        if (query in product["name"].lower() or 
            query in product.get("description", "").lower() or
            query in product["category"].lower() or 
            query in product["subcategory"].lower()):
            results.append(product)
    
    return render_template('search.html', products=results, query=query, data=data)

# Route: View products by category
@app.route('/category/<category>')
@app.route('/category/<category>/<subcategory>')
def category(category, subcategory=None):
    data = get_products()
    products = data["products"]
    
    if subcategory:
        filtered_products = [p for p in products if p["category"] == category and p["subcategory"] == subcategory]
    else:
        filtered_products = [p for p in products if p["category"] == category]
    
    return render_template('category.html', 
                          products=filtered_products, 
                          category=category, 
                          subcategory=subcategory,
                          data=data)

# API: Get cart
@app.route('/api/cart', methods=['GET'])
def get_cart():
    cart = session.get('cart', [])
    return jsonify(cart)

# API: Add to cart
@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    # 设置会话为永久性
    session.permanent = True
    
    data = request.json
    product_id = data.get('id')
    
    if not product_id:
        return jsonify({"success": False, "message": "Missing product ID"}), 400
    
    # Get product details and data
    products_data = get_products()
    products_list = products_data["products"]
    product = next((p for p in products_list if p['id'] == product_id), None)
    
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404
    
    # Check stock
    if product['stock'] <= 0:
        return jsonify({"success": False, "message": "Product out of stock"}), 400
    
    cart = session.get('cart', [])
    
    # Check if product is already in cart
    product_in_cart = False
    cart_quantity = 0
    
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += 1
            product_in_cart = True
            cart_quantity = item['quantity']
            break
    
    # If product is not in cart, add it
    if not product_in_cart:
        if product['stock'] > 0:
            cart.append({
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image'],
                'unit': product['unit'],
                'quantity': 1
            })
            cart_quantity = 1
        else:
            return jsonify({"success": False, "message": "Product out of stock"}), 400
    
    # Check if cart quantity exceeds stock
    if cart_quantity > product['stock']:
        return jsonify({"success": False, "message": "Insufficient stock to add more"}), 400
    
    # Calculate effective stock (actual stock minus cart quantity)
    effective_stock = max(0, product['stock'] - cart_quantity)
    
    session['cart'] = cart
    return jsonify({
        "success": True, 
        "cart": cart, 
        "stock": product['stock'],
        "effective_stock": effective_stock
    })

# API: Update product quantity in cart
@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    data = request.json
    product_id = data.get('id')
    quantity = data.get('quantity', 0)
    
    if not product_id:
        return jsonify({"success": False, "message": "Missing product ID"}), 400
    
    cart = session.get('cart', [])
    
    if quantity <= 0:
        # Remove product
        cart = [item for item in cart if item['id'] != product_id]
        
        # Get product stock information
        products_data = get_products()
        products_list = products_data["products"]
        product = next((p for p in products_list if p['id'] == product_id), None)
        
        if product:
            # Product removed from cart, return current stock
            session['cart'] = cart
            return jsonify({
                "success": True, 
                "cart": cart,
                "stock": product['stock'],
                "effective_stock": product['stock']
            })
    else:
        # Get product stock information
        products_data = get_products()
        products_list = products_data["products"]
        product = next((p for p in products_list if p['id'] == product_id), None)
        
        if not product:
            return jsonify({"success": False, "message": "Product not found"}), 404
        
        # Check stock
        if quantity > product['stock']:
            return jsonify({
                "success": False, 
                "message": f"Insufficient stock. Only {product['stock']} items available",
                "available_stock": product['stock']
            }), 400
            
        # Update quantity
        for item in cart:
            if item['id'] == product_id:
                item['quantity'] = quantity
                break
        
        # Calculate effective stock
        effective_stock = max(0, product['stock'] - quantity)
    
    session['cart'] = cart
    return jsonify({
        "success": True, 
        "cart": cart,
        "stock": product['stock'] if product else 0,
        "effective_stock": effective_stock if product else 0
    })

# API: Clear cart
@app.route('/api/cart/clear', methods=['POST'])
def clear_cart():
    # Get previous cart to determine which products need stock updates
    previous_cart = session.get('cart', [])
    
    # Clear cart
    session['cart'] = []
    
    # Get product IDs that were in the cart
    product_ids = [item['id'] for item in previous_cart]
    
    # Get current stock for these products
    products_data = get_products()
    products_list = products_data["products"]
    
    stock_updates = {}
    for product_id in product_ids:
        product = next((p for p in products_list if p['id'] == product_id), None)
        if product:
            stock_updates[product_id] = {
                "stock": product['stock'],
                "effective_stock": product['stock']
            }
    
    return jsonify({
        "success": True, 
        "cart": [],
        "stock_updates": stock_updates
    })

# Route: Cart page
@app.route('/cart')
def cart():
    data = get_products()
    return render_template('cart.html', data=data)

# Route: Delivery details page
@app.route('/delivery')
def delivery():
    cart = session.get('cart', [])
    data = get_products()
    
    if not cart:
        return redirect(url_for('cart'))
    
    return render_template('delivery.html', data=data)

# API: Submit order
@app.route('/api/order/submit', methods=['POST'])
def submit_order():
    cart = session.get('cart', [])
    
    if not cart:
        return jsonify({"success": False, "message": "Your cart is empty"}), 400
    
    # Get form data
    form_data = request.json
    
    # 验证必填字段
    required_fields = ['name', 'email', 'phone', 'street', 'city', 'state']
    missing_fields = [field for field in required_fields if not form_data.get(field)]
    
    if missing_fields:
        return jsonify({
            "success": False, 
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Validate stock
    unavailable_items = validate_cart(cart)
    if unavailable_items:
        return jsonify({
            "success": False, 
            "message": "The following items are unavailable",
            "unavailable_items": unavailable_items
        }), 400
    
    try:
        # Create order ID
        order_id = str(uuid.uuid4())
        
        # Create order
        order_data = {
            "id": order_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer": {
                "name": form_data.get("name"),
                "email": form_data.get("email"),
                "phone": form_data.get("phone"),
                "address": {
                    "street": form_data.get("street"),
                    "city": form_data.get("city"),
                    "state": form_data.get("state")
                }
            },
            "items": cart,
            "total": sum(item["price"] * item["quantity"] for item in cart)
        }
        
        # Save order
        save_order(order_data)
        
        # Update stock
        update_stock(cart)
        
        # Clear cart
        session['cart'] = []
        
        return jsonify({"success": True, "order": order_data})
    except Exception as e:
        app.logger.error(f"Error creating order: {str(e)}")
        return jsonify({"success": False, "message": f"Error processing order: {str(e)}"}), 500

# Route: Order confirmation page
@app.route('/confirmation/<order_id>')
def confirmation(order_id):
    data = get_products()
    return render_template('confirmation.html', order_id=order_id, data=data)

# Route: Product detail page
@app.route('/product/<product_id>')
def product_detail(product_id):
    data = get_products()
    products = data["products"]
    
    # Find the product by ID
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return redirect(url_for('home'))
    
    # Get related products (same category or subcategory)
    related_products = [p for p in products if (p['category'] == product['category'] or p['subcategory'] == product['subcategory']) and p['id'] != product_id]
    
    # Limit to 4 related products
    related_products = related_products[:4]
    
    return render_template('product.html', 
                          product=product, 
                          related_products=related_products,
                          data=data)

# API: Get product stock
@app.route('/api/product/stock/<product_id>', methods=['GET'])
def get_product_stock(product_id):
    products_data = get_products()
    products_list = products_data["products"]
    product = next((p for p in products_list if p['id'] == product_id), None)
    
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404
        
    # Calculate effective stock (actual stock minus items in cart)
    effective_stock = product['stock']
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == product_id:
            effective_stock = max(0, product['stock'] - item['quantity'])
            break
            
    return jsonify({
        "success": True, 
        "stock": product['stock'],
        "effective_stock": effective_stock
    })

if __name__ == '__main__':
    app.run(debug=True) 
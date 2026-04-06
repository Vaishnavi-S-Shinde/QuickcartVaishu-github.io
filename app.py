from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import random
import os
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'quickcart_secret_key_2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quickcart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============ DATABASE MODELS ============
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, default=0)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(500), nullable=False)
    badge = db.Column(db.String(50), default='New')
    rating = db.Column(db.Float, default=4.5)
    stock = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(50), primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(200), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(100), nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Confirmed')
    items_json = db.Column(db.Text, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_spent = db.Column(db.Float, default=0)

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(200), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

# ============ CREATE TABLES WITH 10,000 PRODUCTS ============
with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Database tables created!")
    
    # Create admin user
    if not User.query.filter_by(email='admin@quickcart.com').first():
        admin = User(name='Admin', email='admin@quickcart.com', password='admin123', is_admin=True)
        db.session.add(admin)
    
    # Create 10,000 unique products with different images
    if Product.query.count() == 0:
        categories = ['Electronics', 'Clothing', 'Furniture', 'Home & Living', 'Accessories', 
                      'Sports', 'Books', 'Toys', 'Beauty', 'Automotive', 'Health', 'Grocery',
                      'Jewelry', 'Shoes', 'Bags', 'Watches', 'Cameras', 'Gaming', 'Music', 'Tools']
        
        badges = ['Bestseller', 'New', 'Trending', 'Premium', 'Popular', 'Limited', 'Eco', 
                  'Hot Deal', 'Staff Pick', 'Sale', 'Discounted', 'Featured', 'Top Rated']
        
        brand_names = ['Apple', 'Samsung', 'Sony', 'Nike', 'Adidas', 'Puma', 'LG', 'Boat', 
                       'Noise', 'Fastrack', 'Titan', 'Ray-Ban', 'Dell', 'HP', 'Lenovo', 'Asus',
                       'Mi', 'OnePlus', 'Realme', 'Vivo', 'Oppo', 'Google', 'Microsoft', 'Intel']
        
        product_types = ['Pro', 'Max', 'Ultra', 'Plus', 'Elite', 'Premium', 'Deluxe', 'Smart',
                         'Wireless', 'Bluetooth', 'Digital', 'Advanced', 'Professional', 'Classic']
        
        # Unsplash high-quality image categories for variety
        image_categories = [
            'electronics', 'clothing', 'furniture', 'home-decor', 'accessories', 
            'sports', 'books', 'toys', 'beauty', 'cars', 'health', 'food',
            'jewelry', 'shoes', 'bags', 'watches', 'cameras', 'gaming', 'music'
        ]
        
        print("🔄 Creating 10,000 products... This may take a minute...")
        
        for i in range(1, 10001):
            # Assign category
            category = categories[i % len(categories)]
            
            # Calculate price based on category
            if category in ['Electronics', 'Cameras', 'Gaming', 'Music']:
                price = random.randint(2000, 80000)
                original_price = price + random.randint(500, 10000)
            elif category in ['Furniture', 'Jewelry', 'Watches']:
                price = random.randint(3000, 60000)
                original_price = price + random.randint(500, 8000)
            elif category in ['Clothing', 'Shoes', 'Bags']:
                price = random.randint(500, 8000)
                original_price = price + random.randint(100, 2000)
            else:
                price = random.randint(500, 20000)
                original_price = price + random.randint(100, 3000)
            
            # Generate unique product name
            brand = brand_names[i % len(brand_names)]
            product_type = product_types[i % len(product_types)]
            
            if i % 3 == 0:
                name = f"{brand} {category} {product_type} {i//10 + 1}"
            elif i % 3 == 1:
                name = f"{category} {product_type} {i} by {brand}"
            else:
                name = f"{brand} {product_type} {category} Edition {i}"
            
            # Generate unique image URL (different for each product)
            image_category = image_categories[i % len(image_categories)]
            image_id = 1000 + i  # Unique ID for each product
            image = f"https://source.unsplash.com/featured/300x200?{image_category}&sig={image_id}"
            
            # Fallback images if Unsplash fails
            fallback_images = [
                f"https://picsum.photos/id/{i % 1000 + 1}/300/200",
                f"https://random.imagecdn.app/300/200?img={i}",
                f"https://picsum.photos/seed/{i}/300/200"
            ]
            
            # Generate unique description
            descriptions = [
                f"Experience premium quality with this {category.lower()} product. Features advanced technology and superior build quality.",
                f"Upgrade your lifestyle with this {category.lower()} item. Perfect for daily use with long-lasting durability.",
                f"Top-rated {category.lower()} product with excellent customer reviews. Best value for money in its class.",
                f"Limited edition {category.lower()} piece. Get it before it's gone! Includes 1 year warranty.",
                f"Professional grade {category.lower()} equipment. Trusted by experts worldwide for reliability."
            ]
            
            product = Product(
                name=name[:100],
                category=category,
                price=price,
                original_price=original_price,
                description=descriptions[i % len(descriptions)],
                image=image,
                badge=badges[i % len(badges)],
                rating=round(3 + (i % 20) / 10, 1),
                stock=random.randint(5, 200)
            )
            db.session.add(product)
            
            # Progress indicator
            if i % 1000 == 0:
                print(f"   Created {i} products...")
                db.session.commit()
        
        db.session.commit()
        print("✅ 10,000 products created successfully with unique images!")
    
    # Create sample users
    if User.query.filter(User.is_admin == False).count() == 0:
        for i in range(1, 101):
            user = User(
                name=f"Customer {i}",
                email=f"customer{i}@example.com",
                password="password123",
                is_admin=False,
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)),
                total_spent=random.randint(1000, 50000)
            )
            db.session.add(user)
        db.session.commit()
        print("✅ 100 sample users created!")
    
    # Create sample orders
    if Order.query.count() == 0:
        users = User.query.filter(User.is_admin == False).all()
        for i in range(1, 501):
            user = random.choice(users)
            order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            total = random.randint(500, 20000)
            order = Order(
                id=f"ORD{1000000 + i}",
                order_date=order_date,
                customer_name=user.name,
                customer_email=user.email,
                customer_address=f"Address {i}, Main Street, City",
                payment_method=random.choice(['Credit Card', 'UPI', 'Cash on Delivery', 'Debit Card']),
                subtotal=total,
                discount=random.randint(0, 500),
                total=total - random.randint(0, 500),
                status=random.choice(['Confirmed', 'Shipped', 'Delivered', 'Processing']),
                items_json=json.dumps([
                    {'name': f'Product {random.randint(1, 1000)}', 'quantity': random.randint(1, 3), 
                     'price': random.randint(100, 5000)} for _ in range(random.randint(1, 4))
                ])
            )
            db.session.add(order)
        db.session.commit()
        print("✅ 500 sample orders created!")

    print("\n" + "="*60)
    print("🚀 DATABASE READY!")
    print("="*60)
    print(f"📦 Products: {Product.query.count()}")
    print(f"👥 Users: {User.query.count()}")
    print(f"📋 Orders: {Order.query.count()}")
    print("="*60)

# ============ ROUTES ============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    products = Product.query.all()
    orders = Order.query.order_by(Order.order_date.desc()).all()
    users = User.query.all()
    
    total_users = User.query.filter(User.is_admin == False).count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total)).scalar() or 0
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.stock < 10).count()
    
    return render_template('admin.html', 
                         products=products, orders=orders, users=users,
                         total_users=total_users, total_orders=total_orders,
                         total_revenue=total_revenue, total_products=total_products,
                         low_stock=low_stock)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email, password=password, is_admin=True).first()
        if user:
            session['is_admin'] = True
            session['admin_name'] = user.name
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html', error='Invalid credentials! Use admin@quickcart.com / admin123')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/api/products')
def get_products():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 24
    
    query = Product.query
    if category != 'all':
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))
    
    products = query.offset((page-1)*per_page).limit(per_page).all()
    total = query.count()
    
    return jsonify({
        'products': [{
            'id': p.id, 'name': p.name, 'category': p.category,
            'price': p.price, 'original_price': p.original_price,
            'description': p.description[:100], 'image': p.image,
            'badge': p.badge, 'rating': p.rating, 'stock': p.stock
        } for p in products],
        'total': total,
        'page': page,
        'has_more': page * per_page < total
    })

@app.route('/api/place_order', methods=['POST'])
def place_order():
    data = request.json
    order_id = f"ORD{int(datetime.now().timestamp() * 1000)}"
    
    order = Order(
        id=order_id,
        customer_name=data['customer']['name'],
        customer_email=data['customer']['email'],
        customer_address=data['customer']['address'],
        payment_method=data['customer']['payment'],
        subtotal=data['subtotal'],
        discount=data.get('discount', 0),
        total=data['total'],
        items_json=json.dumps(data['items'])
    )
    db.session.add(order)
    db.session.commit()
    
    # Update user total spent
    user = User.query.filter_by(email=data['customer']['email']).first()
    if user:
        user.total_spent += data['total']
        db.session.commit()
    
    return jsonify({'success': True, 'order_id': order_id})

@app.route('/api/get_orders')
def get_orders():
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return jsonify([{
        'id': o.id, 'date': o.order_date.strftime('%Y-%m-%d %H:%M:%S'),
        'customer_name': o.customer_name, 'customer_email': o.customer_email,
        'customer_address': o.customer_address, 'payment_method': o.payment_method,
        'subtotal': o.subtotal, 'discount': o.discount, 'total': o.total,
        'status': o.status, 'items': json.loads(o.items_json)
    } for o in orders])

@app.route('/api/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    data = request.json
    user_email = data.get('user_email', 'guest@quickcart.com')
    product_id = data.get('product_id')
    
    existing = Wishlist.query.filter_by(user_email=user_email, product_id=product_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'action': 'removed'})
    else:
        wish = Wishlist(user_email=user_email, product_id=product_id)
        db.session.add(wish)
        db.session.commit()
        return jsonify({'action': 'added'})

@app.route('/api/get_wishlist')
def get_wishlist():
    user_email = request.args.get('email', 'guest@quickcart.com')
    wishlist = Wishlist.query.filter_by(user_email=user_email).all()
    product_ids = [w.product_id for w in wishlist]
    products = Product.query.filter(Product.id.in_(product_ids)).all() if product_ids else []
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'image': p.image} for p in products])

@app.route('/api/update_order_status', methods=['POST'])
def update_order_status():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    order = Order.query.filter_by(id=data['order_id']).first()
    if order:
        order.status = data['status']
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Order not found'}), 404

@app.route('/api/add_product', methods=['POST'])
def add_product():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    product = Product(
        name=data['name'], category=data['category'], price=data['price'],
        description=data['description'], image=data['image'], badge=data.get('badge', 'New'),
        rating=data.get('rating', 4.5), stock=data.get('stock', 50)
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({'success': True, 'id': product.id})

@app.route('/api/delete_product', methods=['POST'])
def delete_product():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    product = Product.query.get(request.json['product_id'])
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 QuickCart Pro Server Starting...")
    print("="*60)
    print("📱 Website: http://localhost:5000")
    print("🔐 Admin Login: http://localhost:5000/admin")
    print("📧 Email: admin@quickcart.com")
    print("🔑 Password: admin123")
    print("="*60)
    print(f"✨ Features:")
    print(f"   • {Product.query.count()} Premium Products")
    print(f"   • {User.query.count()} Registered Users")
    print(f"   • {Order.query.count()} Orders Placed")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
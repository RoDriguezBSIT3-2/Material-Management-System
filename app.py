from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Configure PostgreSQL Database
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgresql_20_user:n5GdVSXQVZ7NWJlnqHWX8hxG6SYjfFjg@dpg-csva2mlumphs7382nreg-a/postgresql_20'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database connection
db = SQLAlchemy(app)


# Define Inventory model
class Inventory(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    uoi = db.Column(db.String(50), nullable=False)
    beginning = db.Column(db.Integer, nullable=False)
    incoming = db.Column(db.Integer, nullable=False)
    outgoing = db.Column(db.Integer, nullable=False)
    waste = db.Column(db.Integer, nullable=False)
    ending = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Inventory {self.item}>"

class Transactions(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    uoi = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    
# Define PurchaseRecord model
class PurchaseRecord(db.Model):
    __tablename__ = 'purchase_records'

    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    receipt_url = db.Column(db.String(200), nullable=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)


class TotalExpenses(db.Model):
    __tablename__ = 'total_expenses'

    id = db.Column(db.Integer, primary_key=True)
    total_amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)


# Define Material model
class Material(db.Model):
    __tablename__ = 'material'
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    uoi = db.Column(db.String(50), nullable=False)
    beginning = db.Column(db.Integer, nullable=False)
    incoming = db.Column(db.Integer, nullable=False)
    outgoing = db.Column(db.Integer, nullable=False)
    waste = db.Column(db.Integer, nullable=False)
    ending = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Material {self.item}>"


class WasteLog(db.Model):
    __tablename__ = 'waste_log'

    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(255), nullable=False)
    uoi = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)


class MaterialLog(db.Model):
    __tablename__ = 'material_log'

    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(255), nullable=False)
    uoi = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)


# Define your models here
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), unique=True, nullable=False)
    prepared_by = db.Column(db.String(50))
    checked_by = db.Column(db.String(50))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    store_branch = db.Column(db.String(100))
    status = db.Column(db.String(50))
    wet_items = db.Column(db.JSON)
    sauce_items = db.Column(db.JSON)
    ice_cream_items = db.Column(db.JSON)
    shakes_items = db.Column(db.JSON)
    vegetables_items = db.Column(db.JSON)
    packaging_items = db.Column(db.JSON)
    groceries_items = db.Column(db.JSON)
    manual_items = db.Column(db.JSON)


# Create database tables
with app.app_context():
    db.create_all()


@app.route('/')
def dashboard():
    # Fetch total inventory value
    total_inventory_value = db.session.query(
        func.sum(Inventory.price * Inventory.ending).label('total_value')
    ).scalar() or 0

    # Fetch low stock alerts with calculated reorder levels
    low_stock_alerts = [
        {
            'item': item.item,
            'ending': item.ending,
            'reorder_level': max(0, 20 - item.ending)  # Calculate reorder level to reach 20
        }
        for item in Inventory.query.filter(Inventory.ending <= 10).all()
    ]

    # Fetch fast-moving items (example: outgoing is high)
    fast_moving_items = Inventory.query.order_by(Inventory.outgoing.asc()).limit(6).all()

    # Prepare data for charts
    inventory_chart_data = {
        'labels': [item.item for item in Inventory.query.all()],
        'data': [item.ending for item in Inventory.query.all()],
    }

    fast_moving_chart_data = {
        'labels': [item.item for item in fast_moving_items],
        'data': [item.outgoing for item in fast_moving_items],
    }

    return render_template(
        'dashboard.html',
        total_inventory_value=total_inventory_value,
        low_stock_alerts=low_stock_alerts,
        fast_moving_items=fast_moving_items,
        inventory_chart_data=inventory_chart_data,
        fast_moving_chart_data=fast_moving_chart_data,
    )


@app.route('/api/inventory_summary', methods=['GET'])
def get_inventory_summary():
    # Query item, ending, price, id, and image_url fields from each record
    inventory_data = Inventory.query.with_entities(Inventory.id, Inventory.item, Inventory.ending, Inventory.price,
                                                   Inventory.image_url).all()

    # Format the data with stock status
    data = []
    for record in inventory_data:
        status = "In Stock"  # Default status
        if record.ending == 0:
            status = "Out of Stock"
        elif record.ending <= 10:
            status = "Low Stock"

        data.append({
            'id': record.id,
            'item': record.item,
            'ending': record.ending,
            'price': record.price,
            'status': status,
            'image_url': record.image_url
        })

    # Return the data as JSON
    return jsonify(data)

@app.route('/inventory', methods=['GET'])
def inventory():
    search_query = request.args.get('search', '').strip().lower()
    if search_query:
        filtered_inventory = Inventory.query.filter(Inventory.item.ilike(f'%{search_query}%')).all()
    else:
        filtered_inventory = Inventory.query.all()

    # Define the threshold for stock levels
    stock_threshold = 10
    alerts = []

    # Check for items that are below the threshold and add to alerts
    for item in filtered_inventory:
        if item.ending <= stock_threshold:
            alerts.append({
                'item': item.item,
                'current_stock': item.ending
            })

    date_today = datetime.now().strftime('%d %B %Y')

    return render_template('inventory.html', inventory=filtered_inventory, date_today=date_today, alerts=alerts)


@app.route('/view_inventory', methods=['GET'])
def view_inventory():
    # Get the date from query parameters
    date = request.args.get('date')

    # Default to today's date if no date is provided
    if date:
        try:
            search_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d %B %Y')
        except ValueError:
            search_date = None
    else:
        search_date = datetime.now().strftime('%d %B %Y')

    # Filter inventory based on the search_date
    filtered_inventory = Inventory.query.filter_by(date=search_date).all()

    return render_template('view_inventory.html', inventory=filtered_inventory,
                           date_today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/add_inventory', methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        item = request.form['item']
        price = float(request.form['price'])
        uoi = request.form['uoi']
        beginning = int(request.form['beginning'])
        incoming = int(request.form['incoming'])
        outgoing = int(request.form['outgoing'])
        waste = int(request.form['waste'])

        # Automatically calculate the ending balance
        ending = beginning + incoming - outgoing - waste

        # Handle file upload
        image = request.files.get('image')
        image_url = ''
        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            image_url = url_for('uploaded_file', filename=image_filename)

        new_item = Inventory(
            item=item,
            price=price,
            uoi=uoi,
            beginning=beginning,
            incoming=incoming,
            outgoing=outgoing,
            waste=waste,
            ending=ending,
            date=datetime.now().strftime('%d %B %Y'),
            image_url=image_url
        )

        # Add to the database and commit
        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for('inventory'))

    return render_template('add_inventory.html')


@app.route('/edit_inventory/<int:item_id>', methods=['GET', 'POST'])
def edit_inventory(item_id):
    item = Inventory.query.get_or_404(item_id)

    if request.method == 'POST':
        item.item = request.form['item']
        item.price = float(request.form['price'])
        item.uoi = request.form['uoi']
        item.beginning = int(request.form['beginning'])
        item.incoming = int(request.form['incoming'])
        item.outgoing = int(request.form['outgoing'])
        item.waste = int(request.form['waste'])

        # Automatically calculate the ending balance
        item.ending = item.beginning + item.incoming - item.outgoing - item.waste

        # Handle file upload
        image = request.files.get('image')
        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            item.image_url = url_for('uploaded_file', filename=image_filename)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('inventory'))

    return jsonify({
        'id': item.id,
        'item': item.item,
        'price': item.price,
        'uoi': item.uoi,
        'beginning': item.beginning,
        'incoming': item.incoming,
        'outgoing': item.outgoing,
        'waste': item.waste,
        'ending': item.ending,
        'image_url': item.image_url
    })


@app.route('/delete_inventory/<int:item_id>', methods=['POST'])
def delete_inventory(item_id):
    item = Inventory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/transactions', methods=['GET'])
def inventory_transactions():
    search_query = request.args.get('search', '').strip().lower()
    if search_query:
        filtered_transactions = Transactions.query.filter(Transactions.item.ilike(f'%{search_query}%')).all()
    else:
        filtered_transactions = Transactions.query.all()

    date_today = datetime.now().strftime('%d %B %Y')

    return render_template('inventory_transactions.html',
                           transactions=filtered_transactions,
                           date_today=date_today)


@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        # Extract form data
        item = request.form['item']
        uoi = request.form['uoi']
        date = request.form['date']
        time = request.form['time']
        transaction_type = request.form['transaction_type']
        quantity = int(request.form['quantity'])
        stock = int(request.form['stock'])

        # Create new transaction
        new_transaction = Transactions(
            item=item,
            uoi=uoi,
            date=date,
            time=time,
            transaction_type=transaction_type,
            quantity=quantity,
            stock=stock
        )

        # Add to the database and commit
        db.session.add(new_transaction)
        db.session.commit()

        return redirect(url_for('inventory_transactions'))

    return render_template('add_transaction.html')


@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    transaction = Transactions.query.get_or_404(transaction_id)

    if request.method == 'POST':
        # Update transaction details
        transaction.item = request.form['item']
        transaction.uoi = request.form['uoi']
        transaction.date = request.form['date']
        transaction.time = request.form['time']
        transaction.transaction_type = request.form['transaction_type']
        transaction.quantity = int(request.form['quantity'])
        transaction.stock = int(request.form['stock'])

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('inventory_transactions'))

    return jsonify({
        'id': transaction.id,
        'item': transaction.item,
        'uoi': transaction.uoi,
        'date': transaction.date,
        'time': transaction.time,
        'transaction_type': transaction.transaction_type,
        'quantity': transaction.quantity,
        'stock': transaction.stock
    })


@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    transaction = Transactions.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('inventory_transactions'))


# Define the path to store uploaded images
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/get_waste_log', methods=['GET', 'POST'])
def get_waste_log():
    search_query = request.args.get('search', '').strip().lower()

    if search_query:
        filtered_waste_log = WasteLog.query.filter(WasteLog.item.ilike(f"%{search_query}%")).all()
    else:
        filtered_waste_log = WasteLog.query.all()

    date_today = datetime.now().strftime('%d %B %Y')

    return render_template('waste_log.html', waste_log=filtered_waste_log, date_today=date_today)


@app.route('/view_waste', methods=['GET'])
def view_waste():
    date = request.args.get('date')

    if date:
        try:
            search_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d %B %Y')
        except ValueError:
            search_date = None
    else:
        search_date = datetime.now().strftime('%d %B %Y')

    filtered_waste = WasteLog.query.filter_by(date=search_date).all()

    return render_template('view_waste.html', waste_log=filtered_waste, date_today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/add_waste', methods=['GET', 'POST'])
def add_waste():
    if request.method == 'POST':
        item = request.form['item']
        uoi = request.form['uoi']
        quantity = int(request.form['quantity'])
        description = request.form['description']

        # Handle file upload
        image = request.files.get('image')
        image_url = ''
        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            image_url = url_for('uploaded_file', filename=image_filename)

        new_waste = WasteLog(
            item=item,
            uoi=uoi,
            quantity=quantity,
            description=description,
            date=datetime.now().strftime('%d %B %Y'),
            image_url=image_url
        )

        # Add to the database and commit
        db.session.add(new_waste)
        db.session.commit()

        return redirect(url_for('get_waste_log'))


@app.route('/edit_waste/<int:item_id>', methods=['GET', 'POST'])
def edit_waste(item_id):
    item = WasteLog.query.get_or_404(item_id)

    if request.method == 'POST':
        item.item = request.form['item']
        item.uoi = request.form['uoi']
        item.quantity = int(request.form['quantity'])
        item.description = request.form['description']

        # Handle file upload
        image = request.files.get('image')
        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            item.image_url = url_for('uploaded_file', filename=image_filename)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('get_waste_log'))

    return jsonify({
        'id': item.id,
        'item': item.item,
        'uoi': item.uoi,
        'quantity': item.quantity,
        'description': item.description,
        'date': item.date,
        'image_url': item.image_url
    })


@app.route('/delete_waste/<int:item_id>', methods=['POST'])
def delete_waste(item_id):
    item = WasteLog.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('get_waste_log'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/material', methods=['GET', 'POST'])
def material():
    search_query = request.args.get('search', '').strip().lower()

    # Query the Material table
    if search_query:
        filtered_material = Material.query.filter(Material.item.ilike(f"%{search_query}%")).all()
    else:
        filtered_material = Material.query.all()

    stock_threshold = 10
    alerts = []

    for item in filtered_material:
        if item.ending <= stock_threshold:
            alerts.append({
                'item': item.item,
                'current_stock': item.ending
            })

    date_today = datetime.now().strftime('%d %B %Y')

    return render_template('material.html', material=filtered_material, date_today=date_today, alerts=alerts)


@app.route('/view_material', methods=['GET'])
def view_material():
    date = request.args.get('date')

    # Default to today's date if no date is provided
    if date:
        try:
            search_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d %B %Y')
        except ValueError:
            search_date = None
    else:
        search_date = datetime.now().strftime('%d %B %Y')

    # Filter material based on the search_date
    filtered_material = Material.query.filter_by(date=search_date).all()

    return render_template('view_material.html', material=filtered_material,
                           date_today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    if request.method == 'POST':
        item = request.form['item']
        uoi = request.form['uoi']
        beginning = int(request.form['beginning'])
        incoming = int(request.form['incoming'])
        outgoing = int(request.form['outgoing'])
        waste = int(request.form['waste'])

        # Automatically calculate the ending balance
        ending = beginning + incoming - outgoing - waste

        # Create a new Material instance
        new_material = Material(
            item=item,
            uoi=uoi,
            beginning=beginning,
            incoming=incoming,
            outgoing=outgoing,
            waste=waste,
            ending=ending,
            date=datetime.now().strftime('%d %B %Y')
        )

        # Add to the database and commit
        db.session.add(new_material)
        db.session.commit()

        return redirect(url_for('material'))

    return render_template('add_material.html')


@app.route('/edit_material/<int:item_id>', methods=['GET', 'POST'])
def edit_material(item_id):
    item = Material.query.get_or_404(item_id)

    if request.method == 'POST':
        beginning = int(request.form['beginning'])
        incoming = int(request.form['incoming'])
        outgoing = int(request.form['outgoing'])
        waste = int(request.form['waste'])
        ending = beginning + incoming - outgoing - waste

        # Update the material fields
        item.item = request.form['item']
        item.uoi = request.form['uoi']
        item.beginning = beginning
        item.incoming = incoming
        item.outgoing = outgoing
        item.waste = waste
        item.ending = ending

        # Commit changes to the database
        db.session.commit()

        return redirect(url_for('material'))

    # For GET request, return the item data as a JSON response
    return jsonify({
        'id': item.id,
        'item': item.item,
        'uoi': item.uoi,
        'beginning': item.beginning,
        'incoming': item.incoming,
        'outgoing': item.outgoing,
        'waste': item.waste,
        'ending': item.ending,
        'date': item.date
    })


@app.route('/delete_material/<int:item_id>', methods=['POST'])
def delete_material(item_id):
    item = Material.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('material'))


@app.route('/get_material_log', methods=['GET', 'POST'])
def get_material_log():
    search_query = request.args.get('search', '').strip().lower()

    if search_query:
        filtered_material_log = MaterialLog.query.filter(MaterialLog.item.ilike(f"%{search_query}%")).all()
    else:
        filtered_material_log = MaterialLog.query.all()

    date_today = datetime.now().strftime('%d %B %Y')

    return render_template('material_log.html', material_log=filtered_material_log, date_today=date_today)


@app.route('/view_material_log', methods=['GET'])
def view_material_log():
    date = request.args.get('date')

    if date:
        try:
            search_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d %B %Y')
        except ValueError:
            search_date = None
    else:
        search_date = datetime.now().strftime('%d %B %Y')

    filtered_material_log = MaterialLog.query.filter_by(date=search_date).all()

    return render_template('view_material_log.html', material_log=filtered_material_log,
                           date_today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/add_material_log', methods=['GET', 'POST'])
def add_material_log():
    if request.method == 'POST':
        item = request.form['item']
        uoi = request.form['uoi']
        quantity = int(request.form['quantity'])
        description = request.form['description']

        # Handle file upload
        image = request.files.get('image')
        image_url = ''
        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            image_url = url_for('uploaded_file', filename=image_filename)

        new_material_log = MaterialLog(
            item=item,
            uoi=uoi,
            quantity=quantity,
            description=description,
            date=datetime.now().strftime('%d %B %Y'),
            image_url=image_url
        )

        db.session.add(new_material_log)
        db.session.commit()

        return redirect(url_for('get_material_log'))


@app.route('/edit_material_log/<int:item_id>', methods=['GET', 'POST'])
def edit_material_log(item_id):
    item = MaterialLog.query.get_or_404(item_id)

    if request.method == 'POST':
        item.item = request.form['item']
        item.uoi = request.form['uoi']
        item.quantity = int(request.form['quantity'])
        item.description = request.form['description']

        # Handle file upload
        image = request.files.get('image')
        if image:
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
            item.image_url = url_for('uploaded_file', filename=image_filename)

        db.session.commit()

        return redirect(url_for('get_material_log'))

    return jsonify({
        'id': item.id,
        'item': item.item,
        'uoi': item.uoi,
        'quantity': item.quantity,
        'description': item.description,
        'date': item.date,
        'image_url': item.image_url
    })


@app.route('/delete_material_log/<int:item_id>', methods=['POST'])
def delete_material_log(item_id):
    item = MaterialLog.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('get_material_log'))


@app.route('/order_report')
def order_report():
    date_today = datetime.now().strftime('%d %B %Y')
    search_query = request.args.get('search', '').strip()

    # Filter orders based on search query
    if search_query:
        filtered_orders = Order.query.filter(Order.order_id.like(f"%{search_query}%")).all()
    else:
        filtered_orders = Order.query.all()

    return render_template('order_report.html', date_today=date_today, orders=filtered_orders,
                           search_query=search_query)


@app.route('/delete_order/<string:order_id>', methods=['POST'])
def delete_order(order_id):
    order = Order.query.filter_by(order_id=order_id).first()
    if order:
        db.session.delete(order)
        db.session.commit()
    return redirect(url_for('order_report'))


@app.route('/order-form', methods=['GET', 'POST'])
def order_form():
    if request.method == 'POST':
        # Retrieve form data
        order_id = request.form.get('order_id')
        prepared_by = request.form.get('prepared_by')
        checked_by = request.form.get('checked_by')
        date = request.form.get('date')
        time = request.form.get('time')
        store_branch = request.form.get('store_branch')
        status = request.form.get('status')

        # Collect items in JSON format
        wet_items = list(zip(request.form.getlist('wet_item[]'),
                             request.form.getlist('wet_item_uoi[]'),
                             request.form.getlist('wet_item_qty[]'),
                             request.form.getlist('wet_item_prepared[]'),
                             request.form.getlist('wet_item_received[]')))

        # Repeat for each item category in the same way
        sauce_items = list(zip(request.form.getlist('sauce_item[]'),
                               request.form.getlist('sauce_item_uoi[]'),
                               request.form.getlist('sauce_item_qty[]'),
                               request.form.getlist('sauce_item_prepared[]'),
                               request.form.getlist('sauce_item_received[]')))

        # Similar for other categories
        ice_cream_items = list(zip(request.form.getlist('ice_cream_item[]'),
                                   request.form.getlist('ice_cream_item_uoi[]'),
                                   request.form.getlist('ice_cream_item_qty[]'),
                                   request.form.getlist('ice_cream_item_prepared[]'),
                                   request.form.getlist('ice_cream_item_received[]')))

        # Create a new Order instance
        order = Order(
            order_id=order_id,
            prepared_by=prepared_by,
            checked_by=checked_by,
            date=date,
            time=time,
            store_branch=store_branch,
            status=status,
            wet_items=wet_items,
            sauce_items=sauce_items,
            ice_cream_items=ice_cream_items,
            shakes_items=list(zip(request.form.getlist('shakes_item[]'),
                                  request.form.getlist('shakes_item_uoi[]'),
                                  request.form.getlist('shakes_item_qty[]'),
                                  request.form.getlist('shakes_item_prepared[]'),
                                  request.form.getlist('shakes_item_received[]'))),
            vegetables_items=list(zip(request.form.getlist('vegetables_item[]'),
                                      request.form.getlist('vegetables_item_uoi[]'),
                                      request.form.getlist('vegetables_item_qty[]'),
                                      request.form.getlist('vegetables_item_prepared[]'),
                                      request.form.getlist('vegetables_item_received[]'))),
            packaging_items=list(zip(request.form.getlist('packaging_item[]'),
                                     request.form.getlist('packaging_item_uoi[]'),
                                     request.form.getlist('packaging_item_qty[]'),
                                     request.form.getlist('packaging_item_prepared[]'),
                                     request.form.getlist('packaging_item_received[]'))),
            groceries_items=list(zip(request.form.getlist('groceries_item[]'),
                                     request.form.getlist('groceries_item_uoi[]'),
                                     request.form.getlist('groceries_item_qty[]'),
                                     request.form.getlist('groceries_item_prepared[]'),
                                     request.form.getlist('groceries_item_received[]'))),
            manual_items=list(zip(request.form.getlist('manual_item[]'),
                                  request.form.getlist('manual_item_uoi[]'),
                                  request.form.getlist('manual_item_qty[]'),
                                  request.form.getlist('manual_item_prepared[]'),
                                  request.form.getlist('manual_item_received[]')))
        )

        # Add and commit the new order to the database
        db.session.add(order)
        db.session.commit()

        # Redirect to the order report page or another page after submission
        return redirect(url_for('order_report'))

    # Render the order form template
    return render_template('order_form.html')


@app.route('/view_order/<order_id>', methods=['GET'])
def view_order(order_id):
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return "Order not found", 404
    return render_template('view_order.html', order=order)


@app.route('/commissary')
def commissary():
    date_today = datetime.now().strftime('%d %B %Y')
    return render_template('commissary.html', date_today=date_today)


@app.route('/purchase_records')
def purchase_records():
    date_today = datetime.now().strftime('%d %B %Y')
    purchases = PurchaseRecord.query.all()

    # Get total expenses for today
    total_expenses_today = TotalExpenses.query.filter_by(date=datetime.utcnow().date()).first()
    total_expenses = total_expenses_today.total_amount if total_expenses_today else 0

    return render_template('purchase_records.html', date_today=date_today, purchase_records=purchases,
                           total_expenses=total_expenses)


@app.route('/api/purchase_records', methods=['GET'])
def get_purchase_records():
    records = PurchaseRecord.query.all()
    data = [{
        'id': record.id,
        'item': record.item,
        'quantity': record.quantity,
        'unit_price': record.unit_price,
        'total_price': record.total_price,
        'receipt_url': record.receipt_url,
        'date': record.date.isoformat()
    } for record in records]
    return jsonify(data)


@app.route('/api/purchase_records', methods=['POST'])
def add_purchase_record_api():
    data = request.get_json()

    # Get data from the JSON payload
    item = data.get('item')
    quantity = int(data.get('quantity'))
    unit_price = float(data.get('unit_price'))

    # Calculate the total price
    total_price = quantity * unit_price

    # Handle receipt file URL if provided (for simplicity, assume a URL here; handling file uploads via API requires multipart/form-data)
    receipt_url = data.get('receipt_url', '')

    # Add the new purchase to the database
    new_purchase = PurchaseRecord(
        item=item,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        receipt_url=receipt_url
    )
    db.session.add(new_purchase)

    # Update total expenses for today
    today_date = datetime.utcnow().date()
    total_expenses_today = TotalExpenses.query.filter_by(date=today_date).first()
    if total_expenses_today:
        # Update existing total
        total_expenses_today.total_amount += total_price
    else:
        # Create a new total record
        total_expenses_today = TotalExpenses(date=today_date, total_amount=total_price)
        db.session.add(total_expenses_today)

    db.session.commit()

    # Return a response with the created purchase record details
    return jsonify({
        'id': new_purchase.id,
        'item': new_purchase.item,
        'quantity': new_purchase.quantity,
        'unit_price': new_purchase.unit_price,
        'total_price': new_purchase.total_price,
        'receipt_url': new_purchase.receipt_url,
        'date': today_date.isoformat()
    }), 201


@app.route('/add_purchase', methods=['GET', 'POST'])
def add_purchase():
    if request.method == 'POST':
        # Get the form data
        item = request.form['item']
        quantity = int(request.form['quantity'])
        unit_price = float(request.form['unit_price'])

        # Calculate the total price
        total_price = quantity * unit_price

        # Handle receipt file upload
        receipt = request.files.get('receipt')
        receipt_url = ''
        if receipt:
            receipt_filename = secure_filename(receipt.filename)
            receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
            receipt.save(receipt_path)
            receipt_url = url_for('uploaded_file', filename=receipt_filename)

        # Add the new purchase to the database
        new_purchase = PurchaseRecord(
            item=item,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            receipt_url=receipt_url
        )
        db.session.add(new_purchase)

        # Update total expenses
        total_expenses_today = TotalExpenses.query.filter_by(date=datetime.utcnow().date()).first()
        if total_expenses_today:
            # Update existing total
            total_expenses_today.total_amount += total_price
        else:
            # Create a new total record
            total_expenses_today = TotalExpenses(date=datetime.utcnow().date(), total_amount=total_price)
            db.session.add(total_expenses_today)

        db.session.commit()

        return redirect(url_for('purchase_records'))

    return render_template('add_purchase.html')


@app.route('/edit_purchase/<int:purchase_id>', methods=['GET', 'POST'])
def edit_purchase(purchase_id):
    # Find the purchase record by its ID
    purchase = PurchaseRecord.query.get_or_404(purchase_id)

    if request.method == 'POST':
        # Retrieve the existing total price for adjustment
        existing_total_price = purchase.total_price

        # Update the form data
        purchase.item = request.form['item']
        purchase.quantity = int(request.form['quantity'])
        purchase.unit_price = float(request.form['unit_price'])

        # Calculate the updated total price
        purchase.total_price = purchase.quantity * purchase.unit_price

        # Update the total expenses
        total_expenses_today = TotalExpenses.query.filter_by(date=datetime.utcnow().date()).first()

        if total_expenses_today:
            # Adjust the total amount based on the change
            total_expenses_today.total_amount += (purchase.total_price - existing_total_price)
        else:
            # Create a new total record if it does not exist
            total_expenses_today = TotalExpenses(date=datetime.utcnow().date(), total_amount=purchase.total_price)
            db.session.add(total_expenses_today)

        # Handle receipt file upload (if a new one is provided)
        receipt = request.files.get('receipt')
        if receipt:
            receipt_filename = secure_filename(receipt.filename)
            receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
            receipt.save(receipt_path)
            purchase.receipt_url = url_for('uploaded_file', filename=receipt_filename)

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('purchase_records'))

    # If GET request, return data for editing
    return render_template('edit_purchase.html', purchase=purchase)


@app.route('/delete_purchase/<int:purchase_id>', methods=['POST'])
def delete_purchase(purchase_id):
    # Find the purchase record by its ID
    purchase = PurchaseRecord.query.get_or_404(purchase_id)

    # Retrieve the total expenses for the date of the purchase
    total_expenses_today = TotalExpenses.query.filter_by(date=purchase.date).first()

    if total_expenses_today:
        # Subtract the purchase total from the daily total expenses
        total_expenses_today.total_amount -= purchase.total_price

        # If the total amount becomes zero or negative, consider deleting the TotalExpenses record
        if total_expenses_today.total_amount <= 0:
            db.session.delete(total_expenses_today)

    # Delete the purchase record
    db.session.delete(purchase)

    # Commit the changes to the database
    db.session.commit()

    return redirect(url_for('purchase_records'))


@app.route('/logout')
def logout():
    return "Logged out"


if __name__ == '__main__':
    app.run(debug=True)

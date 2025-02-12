from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from sqlalchemy import func
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
# Configure PostgreSQL Database
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgresql_25_user:zRP3Suxm2hFjHMuoeixT9qv5w3A69mx8@dpg-cuin378gph6c73ad177g-a.oregon-postgres.render.com/postgresql_25'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database connection
db = SQLAlchemy(app)



# Define Inventory model
class Inventory(db.Model):
    __tablename__ = 'inventory'
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
        return f"<Inventory {self.item}>"


class ProcessedOrder(db.Model):
    __tablename__ = 'processed_order'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(255), nullable=False)  # Track the order ID
    item = db.Column(db.String(100), nullable=False)  # Track the specific item name
    __table_args__ = (db.UniqueConstraint('order_id', 'item', name='unique_order_item'),)  # Ensure unique pair


class Transactions(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    uoi = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)


class MaterialTransactions(db.Model):
    __tablename__ = 'material_transactions'
    id = db.Column(db.Integer, primary_key=True)
    material = db.Column(db.String(100), nullable=False)
    uoi = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)


class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    uoi = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False, default=datetime.now().strftime('%d %B %Y'))

    def __repr__(self):
        return f'<Order {self.id} - {self.item}>'


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


class MaterialLog(db.Model):
    __tablename__ = 'material_log'

    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(255), nullable=False)
    uoi = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(50), nullable=False)


# Create database tables
with app.app_context():
    db.create_all()


@app.route('/')
def dashboard():
    # Fetch total items in inventory
    total_items = Inventory.query.count()

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
    fast_moving_items = Inventory.query.order_by(Inventory.outgoing.desc()).limit(5).all()

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
        total_items=total_items,  # Replaced total_inventory_value
        low_stock_alerts=low_stock_alerts,
        fast_moving_items=fast_moving_items,
        inventory_chart_data=inventory_chart_data,
        fast_moving_chart_data=fast_moving_chart_data,
    )


@app.route('/api/inventory_summary', methods=['GET'])
def get_inventory_summary():
    # Query item, ending, price, id, image_url, uoi, and date fields from each record
    inventory_data = Inventory.query.with_entities(
        Inventory.id,
        Inventory.item,
        Inventory.ending,
        Inventory.uoi,
        Inventory.date  # Include the date field
    ).all()

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
            'status': status,
            'uoi': record.uoi,  # Add unit of issue to the output
            'date': record.date  # Include date in the output
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

    # Fetch external orders
    try:
        response = requests.get('https://hospitality-pos1.onrender.com/get_orders')
        if response.status_code == 200:
            orders_data = response.json()
            orders = orders_data.get('orders', []) if orders_data.get('success') else []
        else:
            orders = []
    except Exception as e:
        print(f"Error fetching orders: {e}")
        orders = []

    # Fetch processed orders and transactions
    processed_orders = {f"{po.order_id}-{po.item}" for po in ProcessedOrder.query.all()}
    existing_transactions = {(t.item, t.transaction_type, t.date): t for t in Transactions.query.all()}

    new_transactions = []
    for order in orders:
        order_id = order.get('order_id')

        for item in order.get('items', []):
            item_name = item.get('item_name')
            quantity = item.get('quantity', 0)

            if f"{order_id}-{item_name}" in processed_orders:
                continue

            inventory_item = Inventory.query.filter_by(item=item_name).first()
            if inventory_item:
                inventory_item.outgoing += quantity
                inventory_item.ending = (
                        inventory_item.beginning + inventory_item.incoming
                        - inventory_item.outgoing - inventory_item.waste
                )

                if (item_name, 'sales', datetime.now().strftime('%Y-%m-%d')) not in existing_transactions:
                    new_transactions.append(Transactions(
                        item=item_name,
                        uoi=inventory_item.uoi,
                        date=datetime.now().strftime('%Y-%m-%d'),
                        time=datetime.now().strftime('%H:%M:%S'),
                        transaction_type='sales',
                        quantity=quantity,
                        stock=inventory_item.ending
                    ))

            db.session.add(ProcessedOrder(order_id=order_id, item=item_name))

    # Log Incoming, Waste, and Outgoing transactions
    for inventory_item in filtered_inventory:
        for tx_type in ['incoming', 'waste', 'outgoing']:
            quantity = getattr(inventory_item, tx_type, 0)
            if quantity > 0:
                existing_transaction = Transactions.query.filter_by(
                    item=inventory_item.item,
                    uoi=inventory_item.uoi,
                    transaction_type=tx_type,
                    date=datetime.now().strftime('%Y-%m-%d'),
                    quantity=quantity,
                    stock=inventory_item.ending
                ).first()

                if not existing_transaction:
                    transaction = Transactions(
                        item=inventory_item.item,
                        uoi=inventory_item.uoi,
                        date=datetime.now().strftime('%Y-%m-%d'),
                        time=datetime.now().strftime('%H:%M:%S'),
                        transaction_type=tx_type,
                        quantity=quantity,
                        stock=inventory_item.ending
                    )
                    db.session.add(transaction)

    # Commit all transactions at once
    db.session.commit()

    # **Automatic Reordering System Based on "Beginning" Stock**
    stock_threshold = 10
    low_stock_items = [item for item in filtered_inventory if item.ending <= stock_threshold]

    new_orders = []
    alerts = []
    for item in low_stock_items:
        reorder_quantity = max(0, item.beginning - item.ending)  # Reorder up to the "Beginning" stock level

        existing_order = Orders.query.filter(
            func.lower(Orders.item) == item.item.lower(),
            Orders.status == 'pending'
        ).first()

        if not existing_order and reorder_quantity > 0:
            new_orders.append(Orders(
                item=item.item,
                uoi=item.uoi,
                quantity=reorder_quantity,
                status='pending',
                date=datetime.now().strftime('%d %B %Y')
            ))
        
        # Add alerts for low stock
        alerts.append({
            'item': item.item,
            'current_stock': item.ending
        })

    if new_orders:
        db.session.add_all(new_orders)
        db.session.commit()

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


@app.route('/validate_item', methods=['POST'])
def validate_item():
    data = request.get_json()
    item_name = data.get('item', '').strip().lower()

    if not item_name:
        return jsonify({"exists": False, "error": "Item name is required"}), 400

    # Check if the item exists in the Inventory model
    exists = Inventory.query.filter(Inventory.item.ilike(f'%{item_name}%')).first() is not None

    return jsonify({"exists": exists})


@app.route('/add_inventory', methods=['GET', 'POST'])
def add_inventory():
    if request.method == 'POST':
        item = request.form['item']
        uoi = request.form['uoi']
        beginning = int(request.form['beginning'])
        incoming = int(request.form['incoming'])
        outgoing = int(request.form['outgoing'])
        waste = int(request.form['waste'])

        # Automatically calculate the ending balance
        ending = beginning + incoming - outgoing - waste

        new_item = Inventory(
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
        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for('inventory'))

    return render_template('add_inventory.html')


@app.route('/edit_inventory/<int:item_id>', methods=['GET', 'POST'])
def edit_inventory(item_id):
    item = Inventory.query.get_or_404(item_id)

    if request.method == 'POST':
        item.item = request.form['item']
        item.uoi = request.form['uoi']
        item.beginning = int(request.form['beginning'])
        item.incoming = int(request.form['incoming'])
        item.outgoing = int(request.form['outgoing'])
        item.waste = int(request.form['waste'])

        # Automatically calculate the ending balance
        item.ending = item.beginning + item.incoming - item.outgoing - item.waste

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('inventory'))

    return jsonify({
        'id': item.id,
        'item': item.item,
        'uoi': item.uoi,
        'beginning': item.beginning,
        'incoming': item.incoming,
        'outgoing': item.outgoing,
        'waste': item.waste,
        'ending': item.ending
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

@app.route('/validate_waste', methods=['POST'])
def validate_waste():
    data = request.get_json()
    item_name = data.get('item', '').strip().lower()

    if not item_name:
        return jsonify({"exists": False, "error": "Item name is required"}), 400

    exists = WasteLog.query.filter(WasteLog.item.ilike(f'%{item_name}%')).first() is not None

    return jsonify({"exists": exists})

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

        new_waste = WasteLog(
            item=item,
            uoi=uoi,
            quantity=quantity,
            description=description,
            date=datetime.now().strftime('%d %B %Y')
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

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('get_waste_log'))

    return jsonify({
        'id': item.id,
        'item': item.item,
        'uoi': item.uoi,
        'quantity': item.quantity,
        'description': item.description,
        'date': item.date
    })


@app.route('/delete_waste/<int:item_id>', methods=['POST'])
def delete_waste(item_id):
    item = WasteLog.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('get_waste_log'))


@app.route('/material_transactions', methods=['GET'])
def material_transactions():
    search_query = request.args.get('search', '').strip().lower()
    if search_query:
        filtered_transactions = MaterialTransactions.query.filter(
            MaterialTransactions.material.ilike(f'%{search_query}%')).all()
    else:
        filtered_transactions = MaterialTransactions.query.all()

    date_today = datetime.now().strftime('%d %B %Y')

    return render_template('material_transactions.html',
                           transactions=filtered_transactions,
                           date_today=date_today)


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

    for material_item in filtered_material:
        # Check stock threshold and prepare alerts
        if material_item.ending <= stock_threshold:
            alerts.append({
                'item': material_item.item,
                'current_stock': material_item.ending
            })

        for tx_type in ['incoming', 'waste', 'outgoing']:
            quantity = getattr(material_item, tx_type, 0)
            if quantity > 0:
                # Check if a similar transaction already exists
                existing_transaction = MaterialTransactions.query.filter_by(
                    material=material_item.item,  # Updated from 'item' to 'material'
                    uoi=material_item.uoi,
                    transaction_type=tx_type,
                    date=datetime.now().strftime('%Y-%m-%d'),
                    quantity=quantity,
                    stock=material_item.ending
                ).first()

                # If no duplicate found, add the transaction
                if not existing_transaction:
                    new_transaction = MaterialTransactions(
                        material=material_item.item,  # Updated from 'item' to 'material'
                        uoi=material_item.uoi,
                        date=datetime.now().strftime('%Y-%m-%d'),
                        time=datetime.now().strftime('%H:%M:%S'),
                        transaction_type=tx_type,
                        quantity=quantity,
                        stock=material_item.ending
                    )
                    db.session.add(new_transaction)

    # Commit all transaction logs at once
    db.session.commit()

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


@app.route('/validate_material', methods=['POST'])
def validate_material():
    data = request.get_json()
    material_name = data.get('material', '').strip().lower()  # Clean input

    if not material_name:
        return jsonify({"exists": False, "error": "Material name is required"}), 400

    # Check if the material exists in the Material table
    exists = Material.query.filter(Material.item.ilike(f'%{material_name}%')).first() is not None

    return jsonify({"exists": exists})


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

@app.route("/validate_material_waste", methods=["POST"])
def validate_material_waste():
    data = request.get_json()
    item_name = data.get('item', '').strip().lower()

    if not item_name:
        return jsonify({"exists": False, "error": "Item name is required"}), 400

    exists = MaterialLog.query.filter(MaterialLog.item.ilike(f'%{item_name}%')).first() is not None

    return jsonify({"exists": exists})

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

        new_material_log = MaterialLog(
            item=item,
            uoi=uoi,
            quantity=quantity,
            description=description,
            date=datetime.now().strftime('%d %B %Y')
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

        db.session.commit()

        return redirect(url_for('get_material_log'))

    return jsonify({
        'id': item.id,
        'item': item.item,
        'uoi': item.uoi,
        'quantity': item.quantity,
        'description': item.description,
        'date': item.date
    })


@app.route('/delete_material_log/<int:item_id>', methods=['POST'])
def delete_material_log(item_id):
    item = MaterialLog.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('get_material_log'))


@app.route('/validate_item_request', methods=['POST'])
def validate_item_request():
    data = request.get_json()
    item_name = data.get('item')

    # Check if the item already exists in the database
    existing_item = Orders.query.filter_by(item=item_name).first()  # Adjust the model query as needed

    if existing_item:
        return jsonify({"exists": True})  # Item exists
    else:
        return jsonify({"exists": False})  # Item doesn't exist


@app.route('/orders_request', methods=['GET', 'POST'])
def orders_request():
    search_query = request.args.get('search', '').strip().lower()

    if search_query:
        filtered_orders = Orders.query.filter(Orders.item.ilike(f"%{search_query}%")).all()
    else:
        filtered_orders = Orders.query.all()

    date_today = datetime.now().strftime('%d %B %Y')

    return render_template('orders_request.html', orders=filtered_orders, date_today=date_today)


@app.route('/add_orders_request', methods=['GET', 'POST'])
def add_orders_request():
    if request.method == 'POST':
        item = request.form['item'].strip().lower()
        uoi = request.form['uoi']
        quantity = int(request.form['quantity'])
        status = request.form['status']

        # Check if item already exists in the database
        existing_order = Orders.query.filter(func.lower(Orders.item) == item).first()

        if existing_order:
            return redirect(url_for('orders_request'))

        new_order = Orders(
            item=item,
            uoi=uoi,
            quantity=quantity,
            status=status,
            date=datetime.now().strftime('%d %B %Y')
        )

        db.session.add(new_order)
        db.session.commit()

        return redirect(url_for('orders_request'))


@app.route('/edit_orders_request/<int:order_id>', methods=['GET', 'POST'])
def edit_orders_request(order_id):
    order = Orders.query.get_or_404(order_id)

    if request.method == 'POST':
        order.item = request.form['item']
        order.uoi = request.form['uoi']
        order.quantity = int(request.form['quantity'])
        order.status = request.form['status']

        db.session.commit()

        return redirect(url_for('orders_request'))

    return jsonify({
        'id': order.id,
        'item': order.item,
        'uoi': order.uoi,
        'quantity': order.quantity,
        'status': order.status,
        'date': order.date
    })


@app.route('/delete_orders_request/<int:order_id>', methods=['POST'])
def delete_orders_request(order_id):
    order = Orders.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('orders_request'))

@app.route('/validate_purchase', methods=['POST'])
def validate_purchase():
    data = request.get_json()
    item_name = data.get('item', '').strip().lower()

    if not item_name:
        return jsonify({"exists": False, "error": "Item name is required"}), 400

    exists = PurchaseRecord.query.filter(PurchaseRecord.item.ilike(f'%{item_name}%')).first() is not None

    return jsonify({"exists": exists})

@app.route('/purchase_records')
def purchase_records():
    date_today = datetime.now().strftime('%d %B %Y')
    purchases = PurchaseRecord.query.all()

    # Get total expenses for today
    total_expenses_today = TotalExpenses.query.filter_by(date=datetime.utcnow().date()).first()
    total_expenses = total_expenses_today.total_amount if total_expenses_today else 0

    # Format total_expenses with a comma and two decimal places
    formatted_total_expenses = "{:,.2f}".format(total_expenses)

    return render_template(
        'purchase_records.html',
        date_today=date_today,
        purchase_records=purchases,
        total_expenses=formatted_total_expenses  # Pass the formatted value
    )


@app.route('/api/purchase_records', methods=['GET'])
def get_purchase_records():
    records = PurchaseRecord.query.all()
    data = [{
        'id': record.id,
        'item': record.item,
        'quantity': record.quantity,
        'unit_price': record.unit_price,
        'total_price': record.total_price,
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

    # Add the new purchase to the database
    new_purchase = PurchaseRecord(
        item=item,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
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

        # Add the new purchase to the database
        new_purchase = PurchaseRecord(
            item=item,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price
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


@app.route('/view_record', methods=['GET'])
def view_record():
    date = request.args.get('date')
    search_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d') if date else datetime.now().strftime(
        '%Y-%m-%d')
    records = PurchaseRecord.query.filter_by(date=search_date).all()
    return render_template('view_record.html', record_details=records, date_today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/logout')
def logout():
    return "Logged out"


if __name__ == '__main__':
    app.run(debug=True)

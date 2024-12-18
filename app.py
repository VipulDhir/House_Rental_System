from flask import Flask, render_template, request, redirect, session, url_for , jsonify
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.regex import Regex
import base64
from werkzeug.utils import secure_filename
import pandas as pd


# Initialize Flask app and other dependencies
app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['rental_platform']
users_collection = db['users']
properties_collection = db['properties']


csv_file_path = 'cleaned_file_2.csv'  # Path to your CSV file
df_properties = pd.read_csv(csv_file_path)


# Routes
@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        roles = request.form.getlist('roles')

        # Check if the user already exists
        if users_collection.find_one({'email': email}):
            return "User already exists!"

        # Hash the password and store user data
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({
            'email': email,
            'password': hashed_password,
            'roles': roles
        })

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        role = request.form['role']

        user = users_collection.find_one({'email': email})

        if user and bcrypt.check_password_hash(user['password'], password):
            if role in user['roles']:
                session['email'] = email
                session['role'] = role

                if role == 'landlord':
                    return redirect(url_for('landlord_dashboard'))
                elif role == 'tenant':
                    return redirect(url_for('tenant_dashboard'))
            else:
                return "Role not registered for this user!"

    return render_template('login.html')


@app.route('/landlord_dashboard', methods=['GET', 'POST'])
def landlord_dashboard():
    if 'email' in session and session['role'] == 'landlord':
        properties = db['properties'].find({'landlord_email': session['email']})
        return render_template('landlord_dashboard.html', properties=properties)
    return redirect(url_for('login'))


@app.route('/add_property', methods=['GET', 'POST'])
def add_property():
    if 'email' in session and session['role'] == 'landlord':
        if request.method == 'POST':
            title = request.form['title']
            location = request.form['location']
            price = int(request.form['price'])
            property_type = request.form['type']

            # Handle Image Upload
            image_file = request.files['image']
            if image_file:
                filename = secure_filename(image_file.filename)
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            else:
                image_data = None

            # Insert into MongoDB
            db['properties'].insert_one({
                'title': title,
                'location': location,
                'price': price,
                'type': property_type,
                'landlord_email': session['email'],
                'image': image_data
            })

            return redirect(url_for('landlord_dashboard'))
        
        return render_template('add_property.html')
    return redirect(url_for('login'))



@app.route('/edit_property/<property_id>', methods=['GET', 'POST'])
def edit_property(property_id):
    if 'email' in session and session['role'] == 'landlord':
        property = db['properties'].find_one({'_id': ObjectId(property_id)})
        if request.method == 'POST':
            updated_data = {
                'title': request.form['title'],
                'description': request.form['description'],
                'price': request.form['price'],
                'location': request.form['location'],
                'type': request.form['type'],
            }
            db['properties'].update_one({'_id': ObjectId(property_id)}, {'$set': updated_data})
            return redirect(url_for('landlord_dashboard'))
        return render_template('edit_property.html', property=property)
    return redirect(url_for('login'))


@app.route('/delete_property/<property_id>', methods=['POST'])
def delete_property(property_id):
    if 'email' in session and session['role'] == 'landlord':
        db['properties'].delete_one({'_id': ObjectId(property_id)})
        return redirect(url_for('landlord_dashboard'))
    return redirect(url_for('login'))


@app.route('/tenant_dashboard', methods=['GET', 'POST'])
def tenant_dashboard():
    if 'email' in session and session['role'] == 'tenant':
        properties = db['properties'].find()  # Fetch all properties
        return render_template('tenant_dashboard.html', properties=properties)
    return redirect(url_for('login'))




@app.route('/search_properties', methods=['GET', 'POST'])
def search_properties():
    filtered_properties = []

    if 'email' in session and session['role'] == 'tenant':
        if request.method == 'POST':
            # Retrieve search filters from the form
            location = request.form.get('location', '').strip().lower()
            min_price = request.form.get('min_price', '').strip()
            max_price = request.form.get('max_price', '').strip()
            min_bathrooms = request.form.get('min_bathrooms', '').strip()
            size = request.form.get('size', '').strip().lower()

            # Filter the DataFrame
            filtered_df = df_properties.copy()

            if location:
                filtered_df = filtered_df[filtered_df['location'].str.lower().str.contains(location)]
            if min_price:
                filtered_df = filtered_df[filtered_df['price'] >= float(min_price)]
            if max_price:
                filtered_df = filtered_df[filtered_df['price'] <= float(max_price)]
            if min_bathrooms:
                filtered_df = filtered_df[filtered_df['bath'] >= int(min_bathrooms)]
            if size:
                filtered_df = filtered_df[filtered_df['size'].str.lower().str.contains(size)]

            # Convert filtered results to a list of dictionaries
            filtered_properties = filtered_df.to_dict(orient='records')

        return render_template('search_properties.html', properties=filtered_properties)

    return redirect(url_for('login'))


@app.route('/send_inquiry/<property_id>', methods=['POST'])
def send_inquiry(property_id):
    if 'email' in session and session['role'] == 'tenant':
        property = db['properties'].find_one({'_id': ObjectId(property_id)})
        inquiry = {
            'property_id': property_id,
            'property_title': property['title'],
            'tenant_email': session['email'],
            'landlord_email': property['landlord_email'],
            'message': request.form['message'],
        }
        db['inquiries'].insert_one(inquiry)  # Save inquiry to the database
        return '<script>alert("Inquiry has been sent!"); window.location.href="/tenant_dashboard";</script>'    
    return redirect(url_for('login'))


@app.route('/landlord_inquiries', methods=['GET'])
def landlord_inquiries():
    if 'email' in session and session['role'] == 'landlord':
        # Fetch inquiries for properties belonging to the logged-in landlord
        properties = db['properties'].find({'landlord_email': session['email']})
        property_ids = [str(property['_id']) for property in properties]
        inquiries = db['inquiries'].find({'property_id': {'$in': property_ids}})
        return render_template('landlord_inquiries.html', inquiries=inquiries, properties=properties)
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

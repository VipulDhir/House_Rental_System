from flask import render_template, request, redirect, session, url_for , jsonify
import base64
from werkzeug.utils import secure_filename
from database import db
from bson.objectid import ObjectId


def landlord_dashboard():
    if 'email' in session and session['role'] == 'landlord':
        properties = db['properties'].find({'landlord_email': session['email']})
        return render_template('landlord_dashboard.html', properties=properties)
    return redirect(url_for('login'))


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


def delete_property(property_id):
    if 'email' in session and session['role'] == 'landlord':
        db['properties'].delete_one({'_id': ObjectId(property_id)})
        return redirect(url_for('landlord_dashboard'))
    return redirect(url_for('login'))


def landlord_inquiries():
    if 'email' in session and session['role'] == 'landlord':
        # Fetch inquiries for properties belonging to the logged-in landlord
        properties = db['properties'].find({'landlord_email': session['email']})
        property_ids = [str(property['_id']) for property in properties]
        inquiries = db['inquiries'].find({'property_id': {'$in': property_ids}})
        return render_template('landlord_inquiries.html', inquiries=inquiries, properties=properties)
    return redirect(url_for('login'))
from flask import render_template, request, redirect, session, url_for , jsonify
import base64
from werkzeug.utils import secure_filename
from database import db
from bson.objectid import ObjectId
import pandas as pd

csv_file_path = 'cleaned_file_2.csv'  # Path to your CSV file
df_properties = pd.read_csv(csv_file_path)

def tenant_dashboard():
    if 'email' in session and session['role'] == 'tenant':
        properties = db['properties'].find()  # Fetch all properties
        return render_template('tenant_dashboard.html', properties=properties)
    return redirect(url_for('login'))


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
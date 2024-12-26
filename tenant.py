from flask import render_template, request, redirect, session, url_for
from database import db
from bson.objectid import ObjectId
import pandas as pd
from math import ceil
from database import properties_collection
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

csv_file_path = 'cleaned_file_2.csv'  # Path to your CSV file
df_properties = pd.read_csv(csv_file_path)



def tenant_dashboard():
    if 'email' in session and session['role'] == 'tenant':
        properties = list(db['properties'].find())  # Fetch all properties
        # Convert ObjectId to string for JSON serialization
        for property in properties:
            property['_id'] = str(property['_id'])
        return render_template('tenant_dashboard.html', properties=properties)
    return redirect(url_for('login'))



def search_properties():
    if 'email' in session and session['role'] == 'tenant':
        filtered_properties = []

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

        return render_template('search_properties.html', properties=filtered_properties, total_properties=len(filtered_properties))

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



def buy_property(property_id):
    if 'email' in session and session['role'] == 'tenant':
        # Fetch property details from the database
        property_data = properties_collection.find_one({'_id': ObjectId(property_id)})
        if not property_data:
            return "Property not found!", 404

        landlord_email = property_data['landlord_email']
        tenant_email = session['email']  
        property_title = property_data['title']

        # Send email to the landlord
        send_email_to_landlord(landlord_email, tenant_email, property_title)

        return "Email sent to the landlord!"
    return redirect(url_for('login'))


def send_email_to_landlord(landlord_email, tenant_email, property_title):
    try:
        sender_email = "xyz@gmail.com"  # Replace with your email
        sender_password = "password"  # App generated Password

        # Set up the email
        subject = f"Purchase Inquiry for Property: {property_title}"
        body = f"""
        Hello,

        A tenant ({tenant_email}) is interested in purchasing your property titled "{property_title}."

        Please reach out to them for further details.

        Regards,
        Rental Platform Team
        """

        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = landlord_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        # Send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)

        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


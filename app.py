from flask import Flask, render_template, request, redirect, session, url_for
from flask_bcrypt import Bcrypt


from landlord import landlord_dashboard,add_property,edit_property,delete_property,landlord_inquiries
from tenant import tenant_dashboard,search_properties,send_inquiry,buy_property
from database import users_collection


# Initialize Flask app and other dependencies
app = Flask(__name__)
app.secret_key = 'hello'
bcrypt = Bcrypt(app)


#LANDLORD_API
app.add_url_rule('/landlord_dashboard', view_func=landlord_dashboard, methods=['GET', 'POST'])
app.add_url_rule('/add_property',view_func=add_property, methods=['GET', 'POST'])
app.add_url_rule('/edit_property/<property_id>',view_func=edit_property, methods=['GET', 'POST'])
app.add_url_rule('/delete_property/<property_id>',view_func=delete_property, methods=['POST'])
app.add_url_rule('/landlord_inquiries',view_func=landlord_inquiries, methods=['GET'])


#TENANT_API
app.add_url_rule('/tenant_dashboard',view_func=tenant_dashboard, methods=['GET', 'POST'])
app.add_url_rule('/search_properties',view_func=search_properties, methods=['GET', 'POST'])
app.add_url_rule('/send_inquiry/<property_id>',view_func=send_inquiry, methods=['POST'])
app.add_url_rule('/buy_property/<property_id>', view_func=buy_property ,methods=['POST'])


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


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

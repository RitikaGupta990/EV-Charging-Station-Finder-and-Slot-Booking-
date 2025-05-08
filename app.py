import random
from datetime import datetime
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from flask import Flask, render_template, url_for, request, redirect, session, jsonify, flash # type: ignore
from DBConnection import Db


from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key="123"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # For Gmail
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'your-email-password'  # Your email password or app-specific password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'


mail = Mail(app)



@app.route('/')
def home():
    return render_template('index.html')


@app.route('/find_your_charger')
def find_your_charger():
    return render_template('find_your_charger.html')

@app.route('/about')
def about():
    return render_template('about.html')












@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        feedback = request.form['message']
        db = Db()
        sql = db.insert("INSERT INTO contact_us (Name, Email, feedback_date, feedback) VALUES (%s, %s, NOW(), %s)", (name, email, feedback))
        return render_template('contact_us.html', message='Thank you for your feedback!')
    else:
        return render_template('contact_us.html')





@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == "POST":
        # Validate email input
        email = request.form.get('email', '').strip()
        if not email:
            return "Email is required", 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return "Invalid email format", 400

        # Check if email exists in database
        db = Db()
        user = db.selectOne("SELECT * FROM login WHERE email=%s", (email,))
        if not user:
            return "Sorry, we couldn't find an account associated with that email address.", 400

         # Send email with passw    ord reset instructions or link
        password = user['password']
        sender_email = "a97298570@gmail.com"
        sender_password = "56B50C32C322385ED3009518610638823005"
        recipient_email = email
        subject = "Password Reset for EV STATION BOOKING WEBSITE"
        content = "Your password for EV STATION BOOKING WEBSITE has been reset. Please login with your new password."
        host = "smtp.gmail.com"
        port = 465
        message = MIMEMultipart()
        message['From'] = Header(sender_email)
        message['To'] = Header(recipient_email)
        message['Subject'] = Header(subject)
        message.attach(MIMEText(content, 'plain', 'utf-8'))
        try:
            with smtplib.SMTP_SSL(host, port) as server:            
                server.login("a97298570@gmail.com", "56B50C32C322385ED3009518610638823005")
                server.sendmail("a97298570@gmail.com", recipient_email, message.as_string())

                return "An email has been sent to your email address with instructions on how to reset your password."
        except smtplib.SMTPAuthenticationError:
            return "Failed to authenticate with the email server. Please check your email credentials.", 500
        except smtplib.SMTPException as e:
            return f"An error occurred while sending the email: {str(e)}", 500

    return render_template("forgot_password.html")







@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_type' in session and session['user_type'] == "admin":
        return redirect('/admin-home')

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        db = Db()
        
        # Use parameterized query to avoid SQL injection
        ss = db.selectOne("SELECT * FROM login WHERE username = %s", (username,))

        if ss is not None and check_password_hash(ss['password'], password):
            session['username'] = username  # set the username key in the session
            session['user_type'] = ss['usertype']
            session['uid'] = ss['login_id'] if ss['usertype'] == 'user' else None
            
            if ss['usertype'] == 'admin':
                return redirect('/admin-home')
            elif ss['usertype'] == 'user':
                return redirect('/user-dashboard')
        else:
            flash("Invalid username or password. Please try again.", "danger")
            return redirect('/login')

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()  # Clears all session data
    return redirect('/login')




    # =========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get the form data
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']
        usertype = request.form['usertype']

        # Validate passwords match
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template("login.html")

        db = Db()
        # Check if user already exists
        existing = db.selectOne(f"SELECT * FROM login WHERE username = '{email}'")
        if existing:
            flash("User already exists with this email", "danger")
            return render_template("login.html")

        # Save registration data in session
        session['reg_data'] = {
            'name': name,
            'email': email,
            'phone': phone,
            'password': password,
            'usertype': usertype
        }

        # Generate OTP (random 6-digit number)
        otp = random.randint(100000, 999999)
        session['otp'] = str(otp)

        # Send OTP via email (you need to use your configured email sending code)
        send_otp_email(email, otp)

        # Redirect to OTP verification page
        flash("OTP sent to your email. Please verify.", "info")
        return redirect('/verify_otp')

    return render_template("login.html")




def send_otp_email(to_email, otp):
    # Your email credentials
    sender_email = "your_email@example.com"
    sender_password = "your_email_password"
    
    # Email server configuration (For Gmail, use Gmail SMTP server)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    # Create the email message
    subject = "Your OTP Code"
    body = f"Your OTP code is {otp}. Please use it to complete your registration."
    
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    
    message.attach(MIMEText(body, "plain"))
    
    # Connect to the SMTP server and send the email
    try:
        # Connect to the server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Encrypt the connection
        
        # Login to your email account
        server.login(sender_email, sender_password)
        
        # Send the email
        server.sendmail(sender_email, to_email, message.as_string())
        
        print(f"OTP sent to {to_email}")
    except Exception as e:
        print(f"Failed to send OTP: {e}")
    finally:
        # Close the connection to the server
        server.quit()

        

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    # Handle POST request when user submits OTP
    if request.method == 'POST':
        user_otp = request.form['otp']
        
        if user_otp == session.get('otp'):
            data = session.get('reg_data')
            db = Db()

            # Insert new user into login and user tables
            login_id = db.insert("INSERT INTO login(username, password, usertype) VALUES(%s, %s, 'user')", 
                                 (data['email'], data['password']))
            
            db.insert("INSERT INTO user(login_id, name, phone, email) VALUES(%s, %s, %s, %s)", 
                      (login_id, data['name'], data['phone'], data['email']))

            flash("Registered successfully. Please login.", "success")
            return redirect('/login')  # Redirect to login after successful registration
        else:
            flash("Invalid OTP. Please try again.", "danger")  # Flash error message for invalid OTP

    # Handle GET request when user first lands on the OTP page
    return render_template("user/verify_otp.html")  # Render the OTP verification page



    







#////////////////////////////////////////////////////////////ADMIN///////////////////////////////////////////////////////////////////////////////////////////////////////////////////



@app.route('/admin-home')
def admin_home():
    print('session ', session)
    if session['user_type'] == 'admin':
        username = session['username'] # get the username from the session
        return render_template('admin/admin-login-dashboard.html', username=username)
    else:
        return redirect('/')



@app.route('/Manage_station')
def Manage_station():
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.select("""
            SELECT 
                id AS station_id, 
                station_name, 
                address, 
                city, 
                charger_type, 
                available_ports, 
                status 
            FROM charging_station_list
        """)
        return render_template("admin/Manage_station.html", data=qry)
    else:
        return redirect('/')


# =============================contact_us
@app.route('/view_feedback')
def view_feedback():
    print('session ', session)
    if session['user_type'] == 'admin':
        db=Db()
        ss=db.select("select * from contact_us")
        return render_template("admin/view_feedback.html",data=ss)
    else:
        return redirect('/')

# 


# ==================delete station=======
@app.route("/adm_delete_station/<station_name>")
def adm_delete_station(station_name):
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.delete("DELETE FROM admin_charging_station_list WHERE Station_name = %s", (station_name,))
        return '''<script>alert('station deleted');window.location="/Manage_station"</script>'''
    else:
        return redirect('/')
# =======================================





@app.route("/adm_delete_feedback/<feedback>")
def adm_delete_feedback(feedback):
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.delete("delete from contact_us where Sl_no='"+feedback+"'")
        return '''<script>alert('feedback deleted');window.location="/view_feedback"</script>'''
    else:
        return redirect('/')


@app.route('/user-list')
def user_list():
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.select("SELECT * FROM user")
        print('User list fetched:', qry)  # Debugging line to check the result of the query
        return render_template("admin/user-list.html", data=qry)
    else:
        return redirect('/')

# ==================delete user===========
@app.route("/adm_delete_user/<user_id>")
def adm_delete_user(user_id):
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.delete("delete from user where user_id='"+user_id+"'")
        return '''<script>alert('user deleted');window.location="/user-list"</script>'''
    else:
        return redirect('/')
# ==============view booking=========================

@app.route('/view_booking')
def view_booking():
    print('session ', session)
    if session['user_type'] == 'admin':
        db=Db()
        bookings = db.select("select Booking_id	, Booking_date, Time_from, Time_to, City, Station_name, Available_ports, login_id  from booking  order by Booking_date desc;")
        return render_template('admin/view_booking.html', bookings=bookings)
    else:
        return redirect('/')

# ===========delete booking

@app.route("/adm_delete_booking/<Booking_id>")
def adm_delete_booking(Booking_id):
    print('session ', session)
    if session['user_type'] == 'admin':
        db = Db()
        qry = db.delete("delete from booking where Booking_id='"+Booking_id+"'")
        return '''<script>alert('booking deleted');window.location="/view_booking"</script>'''
    else:
        return redirect('/')



#//////////////////////////////////////////////////////////////USER//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# -----------

@app.route('/user-dashboard')
def user_dashboard():
    if 'user_type' in session and session['user_type'] == "user":
        username = session['username'] # get the username from the session
        db = Db()
        bookings = db.select("select * from booking where login_id = '%s' order by Booking_date desc;", (session['uid'],))
        # print(bookings)  # print out the value of the bookings variable
        return render_template("user/user-login-dashboard.html", bookings=bookings, username=username)
    else:
        return redirect('/')


@app.route('/usr_delete_booking/<int:booking_id>')
def usr_delete_booking(booking_id):
    if 'user_type' in session and session['user_type'] == "user":
        db = Db()
        
        # Delete the booking for the specific user and booking_id
        db.delete("DELETE FROM booking WHERE booking_id = %s AND login_id = %s", (booking_id, session['uid']))
        
        return '''<script>alert('Booking deleted');window.location="/user-dashboard"</script>'''
    else:
        return redirect('/user-dashboard')



# TODO: Fix the DB (FK, table etc) and frontend field and backend Field

# @app.route('/user-profile', methods=['GET', 'POST'])
# def user_profile():
#     if request.method == 'POST':
#         name = request.form['name']
#         email = request.form['email']
#         password = request.form['password']
#         confirm_password = request.form['confirm-password']
        
#         if password != confirm_password:
#             return redirect(url_for('user_profile', error='Passwords do not match'))
        
#         db = Db()
#         qry = db.update("UPDATE login SET name = %s, email = %s, password = %s WHERE username = %s", (name, email, password, session['username']))  # Assuming you have stored the logged-in user's username in the session
#         return '<script>alert("Account details updated"); window.location.href="/user-profile";</script>'

#     error = request.args.get('error')
#     return render_template('user/user-profile.html', error=error)


# @app.route('/user-profile', methods=['GET', 'POST'])
#def user_profile():
    if 'user_type' in session and session['user_type'] == 'user':
        db = Db()
        login_id = session['uid']

        if request.method == 'POST':
            username = request.form['name']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm-password']

            if password != confirm_password:
                return redirect(url_for('user_profile', error='Passwords do not match'))

            # Update the login table with new values
            db.update("UPDATE login SET username = %s, email = %s, password = %s WHERE login_id = %s", 
                      (username, email, password, login_id))
            session['username'] = username
            return '<script>alert("Account details updated"); window.location.href="/user-profile";</script>'

        # Fetch current user data to pre-fill form
        user = db.selectOne("SELECT * FROM login WHERE login_id = %s", (login_id,))
        error = request.args.get('error')
        return render_template('user/user-profile.html', user=user, error=error)
    else:
        return redirect('/')   

@app.route('/user-profile')
def user_profile():
    if 'user_type' in session and session['user_type'] == 'user':
        db = Db()
        login_id = session['uid']
        user = db.selectOne("""
            SELECT login_id AS id, username AS name 
            FROM login 
            WHERE login_id = %s
        """, (login_id,))
        return render_template('user/user-profile.html', user=user)
    return redirect('/')






@app.route('/user_find_your_charger', methods=['GET', 'POST'])
def user_find_your_charger():
    if 'user_type' in session and session['user_type'] == 'user':
        if request.method == 'POST':
            # Get form data
            city = request.form.get('City', '').strip()
            charger_type = request.form.get('Charger_type', '').strip()

            print("City Input:", city)
            print("Charger Type Input:", charger_type)

            # Query if both fields are provided
            if city and charger_type:
                db = Db()
                qry = db.select(
                    """
                    SELECT Station_name, Address, Charger_type, Available_ports 
                    FROM admin_charging_station_list 
                    WHERE LOWER(city) = LOWER(%s) AND LOWER(charger_type) = LOWER(%s)
                    """, 
                    (city, charger_type)
                )

                # Render the results
                return render_template('user/station_search.html', data=qry, City=city, Charger_type=charger_type)
            else:
                # Handle case if city or charger type is missing
                flash("Please enter both City and Charger Type", "error")
                return redirect(url_for('user_find_your_charger'))

        else:
            # On GET, render the search form
            return render_template('user/user_find_your_charger.html')
    else:
        # Redirect if not logged in
        return redirect('/')





@app.route('/search_stations', methods=['POST'])
def search_stations():
    City = request.form.get('City')
    Charger_type = request.form.get('Charger_type')
    return redirect(url_for('station_search', City=City, Charger_type=Charger_type))

@app.route('/station_search', methods=['GET'])
def station_search():
    if 'user_type' in session and session['user_type'] == 'user':
        # Get the query parameters
        City = request.args.get('City')
        Charger_type = request.args.get('Charger_type')

        if not City or not Charger_type:
            # You may want to return an error message or redirect back to the previous page
            return "City or Charger Type is missing", 400  # HTTP 400 Bad Request

        # Log for debugging purposes
        print(f"Searching stations with City: {City}, Charger_type: {Charger_type}")

        # Query the database for the list of stations matching the search criteria
        db = Db()
        sql = """
            SELECT * FROM charging_station_list 
            WHERE TRIM(LOWER(City)) = TRIM(LOWER(%s)) 
            AND TRIM(LOWER(Charger_type)) = TRIM(LOWER(%s))
        """
        stations = db.select(sql, (City, Charger_type))

        # If data exists, render the search page
        if stations:
            return render_template('user/station_search.html', data=stations, City=City, Charger_type=Charger_type)
        else:
            return render_template('user/station_search.html', data=[], City=City, Charger_type=Charger_type, message="No stations found.")
    else:
        return redirect('/')



@app.route('/booking', methods=['POST'])
def booking():
    station_name = request.form.get('Station_name')
    city = request.form.get('City')
    available_ports = request.form.get('Available_ports')

    # Check if the required parameters are present
    if not station_name or not city or not available_ports:
        return "Missing required information", 400  # Return error if any parameter is missing

    print(f"Booking info: {station_name}, {city}, {available_ports}")

    # Logic for booking or redirection to booking form
    return redirect(url_for('booking_form', Station_name=station_name, City=city, Available_ports=available_ports))



@app.route('/booking-form', methods=['GET'])
def booking_form():
    station_name = request.args.get('Station_name')
    city = request.args.get('City')
    available_ports = request.args.get('Available_ports')

    # Validate if parameters are present
    if not station_name or not city or not available_ports:
        return "Missing parameters", 400  # Handle missing parameters

    # Further processing, e.g., render the booking form
    return render_template('user/booking_form.html', station_name=station_name, city=city, available_ports=available_ports)





# ====================from booking to dashboard

@app.route('/book', methods=['POST'])
def book():
    if 'user_type' in session and session['user_type'] == 'user':
        # Get the form data submitted by the user
        station_name = request.form['Station_name']
        city = request.form['City']
        available_ports = request.form['Available_ports']
        booking_date = request.form['Booking_date']
        time_from = request.form['Time_from']
        time_to = request.form['Time_to']
        login_id = session['uid']

        db = Db()

        # Get the current timestamp
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert the booking data into the MySQL table
        sql = "insert into booking (Station_name, City, Available_ports, Booking_date, Time_from, Time_to, Created_id, login_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        booking_id = db.insert(sql, (station_name, city, available_ports, booking_date, time_from, time_to, created_at, login_id))

        # Redirect the user to their dashboard with booking details
        return render_template("user/user-login-dashboard.html", data={
            'Station_name': station_name,
            'City': city,
            'Available_ports': available_ports,
            'Booking_date': booking_date,
            'Time_from': time_from,
            'Time_to': time_to,
            'Created_id': created_at,
            'Booking_id': booking_id
        })
    else:
        return redirect('/booking-form')







if __name__ == '__main__':        
    app.run(host='127.0.0.1', port=5000, debug=True)
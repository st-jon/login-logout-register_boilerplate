import os


from flask import Flask, session, render_template, redirect, url_for, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from validate_email import validate_email
import bcrypt


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=='GET':
        render_template('login.html')
    if request.method=='POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if len(password) == 0 or len(firstname) == 0 or len(lastname) == 0 or len(email) == 0 :
            return render_template('register.html', message="All fields needed")

        if validate_email(email) == False:
            return render_template('register.html', message="Please provide a correct email")

        if password != confirm :
            return render_template('register.html', message="please confirm password")

        user = db.execute("SELECT email FROM users WHERE email = :email",{"email": email}).fetchone()

        if user is None :
            hashed = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
            db.execute("INSERT INTO users (firstname, lastname, email, password) \
                                VALUES (:firstname, :lastname, :email, :password)",
                                {"firstname": firstname, "lastname": lastname, "email": email, "password": hashed.decode('utf-8')})
            db.commit()
            return render_template('login.html', email=email, password=password, message_good="You have been registered")
        else:
            return render_template('register.html', message="This user already exist")

    return render_template('login.html')

@app.route("/register")
def register():
    return render_template('register.html')

@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        user = db.execute("SELECT * FROM users WHERE email = :email",
            {"email": email}).fetchone()
        if user is None:
            return render_template("login.html", message="Email is incorrect !")
            
        hashed = user.password.encode('utf-8')

        if bcrypt.checkpw(password.encode('utf8'), hashed):
            session["lastname"] = user.lastname
            session["firstname"] = user.firstname
            session["email"] = user.email
            session["user_id"] = user.id
            return render_template('welcome.html', login=True, email=user.email)

        else :
            return render_template("login.html", message="Password is incorrect !")

    if request.method=='GET':
        if (session["user_id"]):
            return render_template('welcome.html', login=True, email=session["email"])
        else:
            return render_template('index.html', message="You have to log in !")

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method=='GET':
        return render_template('edit.html', firstname=session["firstname"], lastname=session["lastname"], email=session["email"], login=True)
    if request.method=='POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if len(password) == 0 or len(firstname) == 0 or len(lastname) == 0 or len(email) == 0 :
            return render_template('edit.html', message="All fields needed")

        if validate_email(email) == False:
            return render_template('edit.html', message="Please provide a correct email")

        if password != confirm :
            return render_template('edit.html', message="please confirm password")

        hashed = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        db.execute("UPDATE users SET firstname = :firstname, lastname = :lastname, email = :email, password = :password WHERE id = :id",
                    {"firstname": firstname, "lastname": lastname, "email": email, "password": hashed.decode('utf-8'), "id": session['user_id']})
        db.commit()
        return render_template('welcome.html', message="Your profile has been updated", login=True, email=email)

@app.route("/logout")
def logout():
    session["lastname"] = None
    session["firstname"] = None
    session["email"]= None
    session["user_id"] = None
    return redirect(url_for('index')) 
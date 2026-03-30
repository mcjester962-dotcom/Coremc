from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
import requests
import base64
import re

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

# USER MODEL

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))


# DOWNLOAD

@app.route("/download/<int:plugin_id>")
def download(plugin_id):

    return redirect(f"https://api.spiget.org/v2/resources/{plugin_id}/download")


# HOME

@app.route("/")
def home():
    return render_template("index.html")


# REGISTER

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            validate_email(email)
        except EmailNotValidError:
            return "Invalid email!"

        hashed_password = generate_password_hash(password)

        new_user = User(username=username,email=email,password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# LOGIN

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password,password):
            return redirect(url_for("home"))
        else:
            return "Wrong username or password"

    return render_template("login.html")


# PLUGINS SEARCH

@app.route("/plugins", methods=["GET","POST"])
def plugins():

    plugins = []

    if request.method == "POST":

        query = request.form["search"]

        url = f"https://api.spiget.org/v2/search/resources/{query}?size=12"

        try:
            r = requests.get(url)

            if r.status_code == 200:
                plugins = r.json()

        except:
            plugins = []

    return render_template("plugins.html", plugins=plugins)


# PLUGIN PAGE

@app.route("/plugin/<int:plugin_id>")
def plugin_page(plugin_id):

    url = f"https://api.spiget.org/v2/resources/{plugin_id}"
    versions_url = f"https://api.spiget.org/v2/resources/{plugin_id}/versions"

    r = requests.get(url)
    v = requests.get(versions_url)

    plugin = None
    description = ""
    versions = []

    if r.status_code == 200:

        plugin = r.json()

        if plugin.get("description"):

            description = base64.b64decode(plugin["description"]).decode("utf-8")

            # [IMG] -> <img>
            description = re.sub(
                r'\[IMG\](.*?)\[/IMG\]',
                r'<img src="\1" class="plugin-img">',
                description,
                flags=re.IGNORECASE
            )

    if v.status_code == 200:
        versions = v.json()[:5]

    return render_template(
        "plugin.html",
        plugin=plugin,
        description=description,
        versions=versions
    )

# SECTIONS

@app.route("/mods")
def mods():
    return render_template("mods.html")


@app.route("/maps")
def maps():
    return render_template("maps.html")


@app.route("/skins")
def skins():
    return render_template("skins.html")


# START SERVER

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)

from flask import Flask, redirect, url_for, session, render_template
from authlib.integrations.flask_client import OAuth
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv("FLASK_KEY")

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params={"access_type": "offline", "prompt": "consent"},
client_kwargs={"scope": "email profile"},
    api_base_url="https://www.googleapis.com/oauth2/v2/"
)

@app.route("/")
def index():
    user = session.get("user")
    if user:
        ist = pytz.timezone("Asia/Kolkata")
        current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
        return render_template("home.html", user=user, current_time=current_time)
    return render_template("index.html")

@app.route("/login")
def login():
    redirect_uri = url_for("auth", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/auth")
def auth():
    token = google.authorize_access_token()
    resp = google.get("userinfo", token=token)
    user_info = resp.json()
    session["user"] = user_info
    return redirect("/")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

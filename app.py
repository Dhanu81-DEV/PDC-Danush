from flask import Flask, redirect, url_for, session, render_template, request
from authlib.integrations.flask_client import OAuth
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
from PIL import Image
from google import genai

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("FLASK_KEY")

client = genai.Client(api_key=os.getenv("GOOGLE_GENAI_API_KEY"))

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


@app.route("/generate_thumbnail", methods=["POST"])
def generate_thumbnail():
    user = session.get("user")
    if not user:
        return "Unauthorized", 401

    uploaded_files = request.files.getlist("images")
    if len(uploaded_files) == 0:
        return "No images uploaded!", 400
    if len(uploaded_files) > 5:
        return "You can upload up to 5 images only!", 400

    try:
        pil_images = []
        for f in uploaded_files:
            img = Image.open(f.stream).convert("RGB")
            pil_images.append(img)

        prompt_text = "Generate a fun, creative news thumbnail combining these images."

        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[prompt_text] + pil_images
        )

        generated_part = response.candidates[0].content.parts[0]
        if generated_part.inline_data is not None:
            thumbnail_bytes = generated_part.inline_data.data
            thumbnail_path = "static/images/generated_thumbnail.png"
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail_bytes)
        else:
            return "No image returned by Gemini.", 500

        return render_template(
            "home.html",
            user=user,
            thumbnail_url=url_for('static', filename='images/generated_thumbnail.png')
        )

    except Exception as e:
        return f"Error generating thumbnail: {e}", 500


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

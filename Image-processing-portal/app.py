from flask import Flask, render_template, request, redirect, flash
from PIL import Image
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import sqlite3
import boto3
import os
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

DATABASE = "images.db"
PROCESSED_FOLDER = "processed"

S3_BUCKET = os.environ.get("S3_BUCKET_NAME")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

os.makedirs(PROCESSED_FOLDER, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT NOT NULL,
            processed_filename TEXT NOT NULL,
            original_size INTEGER,
            processed_size INTEGER,
            s3_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_to_s3(file_path, s3_key):
    s3 = boto3.client("s3")
    s3.upload_file(file_path, S3_BUCKET, s3_key)


@app.route("/")
def dashboard():
    conn = get_db_connection()
    images = conn.execute("SELECT * FROM images ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("dashboard.html", images=images)


@app.route("/upload", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        file = request.files.get("image")

        if not file or file.filename == "":
            flash("No image selected.")
            return redirect("/upload")

        if not allowed_file(file.filename):
            flash("Only PNG, JPG, and JPEG files are allowed.")
            return redirect("/upload")

        file.seek(0, os.SEEK_END)
        original_size = file.tell()
        file.seek(0)

        if original_size > MAX_FILE_SIZE:
            flash("File is too large. Maximum size is 5MB.")
            return redirect("/upload")

        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit(".", 1)[1].lower()

        unique_name = f"{uuid.uuid4()}.{file_extension}"
        temp_path = os.path.join(PROCESSED_FOLDER, f"temp_{unique_name}")
        processed_filename = f"processed_{unique_name}"
        processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)

        file.save(temp_path)

        with Image.open(temp_path) as image:
            image.thumbnail((800, 800))
            image.save(processed_path, optimize=True, quality=80)

        processed_size = os.path.getsize(processed_path)

        s3_key = f"processed-images/{processed_filename}"

        if S3_BUCKET:
            upload_to_s3(processed_path, s3_key)
        else:
            flash("S3 bucket name is missing. Image processed locally but not uploaded to S3.")

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO images (
                original_filename,
                processed_filename,
                original_size,
                processed_size,
                s3_key
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            original_filename,
            processed_filename,
            original_size,
            processed_size,
            s3_key
        ))
        conn.commit()
        conn.close()

        os.remove(temp_path)

        return redirect("/")

    return render_template("upload.html")


if __name__ == "__main__":
    create_table()
    app.run(host="0.0.0.0", port=5000)
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import os
import sys

app = Flask(__name__)

# Get MongoDB URI and Secret Key from environment variables
mongo_uri = os.environ.get("MONGO_URI")
secret_key = os.environ.get("SECRET_KEY")

# Fallback to .env file if environment variables are not set
if not mongo_uri or not secret_key:
    from dotenv import load_dotenv
    load_dotenv()
    mongo_uri = os.environ.get("MONGO_URI")
    secret_key = os.environ.get("SECRET_KEY")

# Configure Flask
if not mongo_uri:
    print("ERROR: MONGO_URI environment variable is not set!", file=sys.stderr)
    raise ValueError("MONGO_URI environment variable is not set!")
if not secret_key:
    print("ERROR: SECRET_KEY environment variable is not set!", file=sys.stderr)
    raise ValueError("SECRET_KEY environment variable is not set!")

app.config["MONGO_URI"] = mongo_uri
app.secret_key = secret_key

# Initialize MongoDB
try:
    mongo = PyMongo(app)
    print("MongoDB connected successfully!", flush=True)
except Exception as e:
    print(f"MongoDB connection failed: {e}", file=sys.stderr, flush=True)
    raise

# Home page -> list students
@app.route('/')
def index():
    try:
        print("Accessing home page...", flush=True)
        students = list(mongo.db.students.find())
        print(f"Found {len(students)} students", flush=True)
        return render_template('index.html', students=students)
    except Exception as e:
        print(f"ERROR in index route: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

# Add student
@app.route('/add', methods=['GET', 'POST'])
def add_student():
    try:
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            course = request.form['course']
            mongo.db.students.insert_one({
                "name": name,
                "email": email,
                "course": course
            })
            return redirect(url_for('index'))
        return render_template('add_student.html')
    except Exception as e:
        print(f"ERROR in add_student route: {e}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}", 500

# Update student
@app.route('/update/<student_id>', methods=['GET', 'POST'])
def update_student(student_id):
    try:
        student = mongo.db.students.find_one({"_id": ObjectId(student_id)})
        if request.method == 'POST':
            new_name = request.form['name']
            new_email = request.form['email']
            new_course = request.form['course']
            mongo.db.students.update_one(
                {"_id": ObjectId(student_id)},
                {"$set": {"name": new_name, "email": new_email, "course": new_course}}
            )
            return redirect(url_for('index'))
        return render_template('update_student.html', student=student)
    except Exception as e:
        print(f"ERROR in update_student route: {e}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}", 500

# Delete student
@app.route('/delete/<student_id>')
def delete_student(student_id):
    try:
        mongo.db.students.delete_one({"_id": ObjectId(student_id)})
        return redirect(url_for('index'))
    except Exception as e:
        print(f"ERROR in delete_student route: {e}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    print("Starting Flask application...", flush=True)
    app.run(debug=False, port=8000, host='0.0.0.0')

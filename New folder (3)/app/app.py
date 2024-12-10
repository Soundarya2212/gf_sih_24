from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import os
import json
from extraction import main as extract_text_main
from verification import verify_data
from pdf2image import convert_from_path

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client['drdo_data']
collection = db['details']

UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        # Extract form data
        form_data = request.form.to_dict()
        form_json_path = os.path.join(RESULTS_FOLDER, 'form_data.json')
        
        # Save form data to JSON
        with open(form_json_path, 'w') as json_file:
            json.dump(form_data, json_file)

        # Store in MongoDB
        collection.insert_one(form_data)

        return redirect(url_for('index'))
    except Exception as e:
        return f"Error saving form data: {str(e)}"

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        file = request.files['file']
        if not file or file.filename == '':
            return "No file selected."

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Process the image and extract text
        extracted_json_path = extract_text_main(file_path)
        
        # Verify the extracted data against the form data
        form_json_path = os.path.join(RESULTS_FOLDER, 'form_data.json')
        mismatches = verify_data(form_json_path, extracted_json_path)

        return jsonify({"mismatches": mismatches})
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    try:
        file = request.files['file']
        if not file or file.filename == '':
            return "No file selected."

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Convert PDF to images and process each page
        images = convert_from_path(file_path)
        extracted_text = ""
        for i, image in enumerate(images):
            image_path = f"{UPLOAD_FOLDER}/temp_image_{i}.jpg"
            image.save(image_path, 'JPEG')
            extracted_json_path = extract_text_main(image_path)
            with open(extracted_json_path, 'r') as json_file:
                extracted_data = json.load(json_file)
                extracted_text += extracted_data.get("extracted_text", "")

        # Verify the extracted data
        form_json_path = os.path.join(RESULTS_FOLDER, 'form_data.json')
        mismatches = verify_data(form_json_path, extracted_json_path)

        return jsonify({"mismatches": mismatches})
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)

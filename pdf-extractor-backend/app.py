# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import re
import spacy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_phone_number(text):
    """Extract phone numbers from text using regex."""
    # Common phone number patterns
    patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Format: 123-456-7890
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',     # Format: (123) 456-7890
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    return ""

def extract_address(doc):
    """Extract address using spaCy named entities."""
    address_entities = []
    address_labels = {"GPE", "LOC", "FAC"}
    
    for ent in doc.ents:
        if ent.label_ in address_labels:
            address_entities.append(ent.text)
    
    # Try to find zip codes
    zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
    zip_codes = re.findall(zip_pattern, doc.text)
    if zip_codes:
        address_entities.extend(zip_codes)
    
    return " ".join(address_entities)

def extract_name(doc):
    """Extract person names using spaCy."""
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    return names[0] if names else ""

def clean_text(text):
    """Clean and normalize text."""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove special characters (keeping basic punctuation)
    text = re.sub(r'[^a-zA-Z0-9\s.,()-]', '', text)
    return text

def process_pdf(file_path):
    """Process PDF file and extract information."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        # Clean extracted text
        text = clean_text(text)
        
        # Process with spaCy
        doc = nlp(text)
        
        # Extract information
        result = {
            "name": extract_name(doc),
            "phone": extract_phone_number(text),
            "address": extract_address(doc)
        }
        
        return result, None
    
    except Exception as e:
        return None, str(e)

@app.route('/api/extract', methods=['POST'])
def extract_info():
    """Handle PDF upload and information extraction."""
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and file.filename.endswith('.pdf'):
        try:
            # Save file temporarily
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process PDF
            result, error = process_pdf(filepath)
            
            # Clean up - remove uploaded file
            os.remove(filepath)
            
            if error:
                return jsonify({'error': error}), 500
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
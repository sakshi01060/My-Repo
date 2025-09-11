from flask import Flask, request, send_file
import os
import logging
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import re
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
import webbrowser
from threading import Timer

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
logging.basicConfig(level=logging.INFO)

@app.errorhandler(413)
def request_entity_too_large(error):
    return "File too large. Max size is 10MB.", 413

ALLOWED_EXTENSIONS = {'.xml', '.pdf'}

def is_allowed(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# Postal code regex
postal_patterns = [
    r"\b[A-Z]{1,8}\d{1,2}[A-Z]?\s*\d[A-Z]{8}\b",  # UK mock
    r"\b\d{5}(?:-\d{4})?\b",                     # US ZIP
    r"\b\d{6}\b"                                  # India PIN
]
postal_regex = re.compile("|".join(postal_patterns))

# ---------- Presidio AnalyzerEngine Setup ----------
analyzer = AnalyzerEngine()

# Custom Recognizer: Location/Road 
location_pattern = Pattern(name="road_location", regex=r"\b(?:[A-Z][a-z]+\s)+(?:Road|Street|Avenue|Lane|Boulevard)\b", score=0.6)
location_recognizer = PatternRecognizer(supported_entity="LOCATION", patterns=[location_pattern])
analyzer.registry.add_recognizer(location_recognizer)

# Custom Recognizer: GPE
gpe_pattern = Pattern(name="gpe", regex=r"\b(New York|London|Mumbai|Delhi|Paris|Tokyo)\b", score=0.6)
gpe_recognizer = PatternRecognizer(supported_entity="GPE", patterns=[gpe_pattern])
analyzer.registry.add_recognizer(gpe_recognizer)

# Custom Recognizer: NORP 
norp_pattern = Pattern(name="norp", regex=r"\b(Indian|American|Muslim|Christian|Democrat|Republican)\b", score=0.5)
norp_recognizer = PatternRecognizer(supported_entity="NORP", patterns=[norp_pattern])
analyzer.registry.add_recognizer(norp_recognizer)

# Custom Recognizer: Account Numbers (8 to 16 digits)
account_pattern = Pattern(name="account", regex=r"\b\d{6,16}\b", score=0.8)
account_recognizer = PatternRecognizer(supported_entity="Account_number", patterns=[account_pattern])
analyzer.registry.add_recognizer(account_recognizer)

pii_entities = [
    "PERSON", "GPE", "LOCATION", "NORP",
    "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
    "US_SSN", "IBAN", "IP_ADDRESS", "Account_number"
]

# PDF Redaction
def process_pdf(file_stream):
    output_stream = BytesIO()
    try:
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        for page in doc:
            text = page.get_text("text")

            for match in postal_regex.finditer(text):
                for area in page.search_for(match.group()):
                    page.add_redact_annot(area, text="*", fill=(1, 1, 1))

            results = analyzer.analyze(text=text, entities=pii_entities, language='en')
            for res in sorted(results, key=lambda r: r.start, reverse=True):
                pii_text = text[res.start:res.end]
                for area in page.search_for(pii_text):
                    masked = "*" * len(pii_text)
                    page.add_redact_annot(area, text=masked, fill=(1, 1, 1))

            page.apply_redactions()

        doc.save(output_stream)
        doc.close()
        output_stream.seek(0)
        return output_stream

    except Exception as e:
        logging.error(f"Error while processing PDF: {e}")
        return None

# XML Redaction
def process_xml(file_stream):
    try:
        tree = ET.parse(file_stream)
        root = tree.getroot()

        def clean(text):
            if not text:
                return text
            text = postal_regex.sub("*", text)
            results = analyzer.analyze(text=text, entities=pii_entities, language='en')
            for res in sorted(results, key=lambda r: r.start, reverse=True):
                pii_text = text[res.start:res.end]
                text = text[:res.start] + "*" * len(pii_text) + text[res.end:]
            return text

        for elem in root.iter():
            elem.text = clean(elem.text)
            for attr in elem.attrib:
                elem.attrib[attr] = clean(elem.attrib[attr])

        output_stream = BytesIO()
        tree.write(output_stream, encoding='utf-8', xml_declaration=True)
        output_stream.seek(0)
        return output_stream

    except Exception as e:
        logging.error(f"XML processing error: {e}")
        return None

@app.route('/')
def home():
    return '''
   <!DOCTYPE html>
<html>
<head>
    <title>PII Redactor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 40px;
            background-color: #f9f9f9;
            text-align: center;
        }
        h1 {
            color: #6c63ff;
            font-size: 36px;
            margin-bottom: 10px;
        }
        h2 {
            color: #333;
            font-size: 20px;
            margin-top: 0;
            margin-bottom: 30px;
        }
        .file-upload-wrapper {
            display: inline-flex;
            align-items: center;
            gap: 15px;
            justify-content: center;
            margin-bottom: 20px;
        }
        .custom-file-upload {
            padding: 12px 24px;
            display: inline-block;
            background-color: #6c63ff;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .custom-file-upload:hover {
            background-color: #4b43cc;
        }
        input[type="file"] {
            display: none;
        }
        #file-names-inline {
            font-size: 14px;
            color: #555;
            max-width: 300px;
            text-align: left;
        }
        button {
            padding: 12px 24px;
            font-size: 16px;
            color: white;
            background-color: #007BFF;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <h1>PII Redactor</h1>
    <h2>Upload PDF/XML Files or Folder</h2>

    <form method="POST" action="/Download" enctype="multipart/form-data">
        <div class="file-upload-wrapper">
            <label for="file-upload" class="custom-file-upload">Choose Files or Folder</label>
            <input id="file-upload" type="file" name="files" multiple required accept=".pdf,.xml" onchange="displayFileNamesInline()">
            <div id="file-names-inline"></div>
        </div>
        <br>
        <button type="submit">Redact & Download ZIP</button>
    </form>

    <script>
        function displayFileNamesInline() {
            const input = document.getElementById('file-upload');
            const fileNamesDiv = document.getElementById('file-names-inline');
            const files = input.files;

            let names = '';
            for (let i = 0; i < files.length; i++) {
                names += files[i].name;
                if (i !== files.length - 1) names += ', ';
            }

            fileNamesDiv.textContent = names || 'No files selected.';
        }
    </script>
</body>
</html>
'''

@app.route('/Download', methods=['POST'])
def download():
    files = request.files.getlist('files')
    if not files:
        return "No files uploaded."

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, 'w') as zipf:
        for file in files:
            if file and is_allowed(file.filename):
                raw_path = file.filename.replace("\\", "/")
                base, ext = os.path.splitext(raw_path)
                redacted_name = base + "_Redacted" + ext

                logging.info(f"Processing: {raw_path}")
                result_stream = None

                if ext == '.pdf':
                    result_stream = process_pdf(file.stream)
                elif ext == '.xml':
                    result_stream = process_xml(file.stream)

                if result_stream:
                    zipf.writestr(redacted_name, result_stream.read())

    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name="Redacted_Files.zip", mimetype='application/zip')

if __name__ == '__main__':
    port = 5000
    url = f'http://127.0.0.1:{port}/'
    Timer(1, lambda: webbrowser.open(url)).start()
    app.run(debug=False, port=port, threaded=True)

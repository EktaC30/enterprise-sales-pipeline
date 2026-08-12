import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from app.etl import upload_to_blob_storage, process_operational_etl

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', message="No file selected.", alert_type="danger")
    
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', message="No file selected.", alert_type="danger")

    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # 1. Upload to Azure Blob Storage (Triggers Snowflake Snowpipe)
            upload_to_blob_storage(file_path, filename)
            
            # 2. Execute Operational ETL (Loads into Azure PostgreSQL)
            process_operational_etl(file_path)

            os.remove(file_path) # Clean up local copy
            return render_template('index.html', message=f"Successfully uploaded {filename}! Blob storage and PostgreSQL updated.", alert_type="success")
        
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return render_template('index.html', message=f"Pipeline Error: {str(e)}", alert_type="danger")
            
    return render_template('index.html', message="Only .csv files are supported.", alert_type="warning")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify, send_file
import pandas as pd
import sqlite3
import os
from werkzeug.utils import secure_filename
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
DATABASE = 'database.db'
ALLOWED_EXTENSIONS = {'csv'}

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.close()
    logger.info(f"Database initialized at {DATABASE}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/upload', methods=['POST'])
def upload_csv():
    logger.debug("Upload request received")
    logger.debug(f"Files in request: {request.files}")
    
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    logger.debug(f"Received file: {file.filename}")
    
    if file.filename == '':
        logger.error("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        table_name = os.path.splitext(filename)[0]
        logger.debug(f"Processing file: {filename}, table name will be: {table_name}")
        
        # Save CSV temporarily
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        logger.debug(f"File saved temporarily to: {filepath}")
        
        try:
            # Read CSV with pandas
            logger.debug("Reading CSV with pandas")
            df = pd.read_csv(filepath)
            logger.debug(f"CSV read successfully, shape: {df.shape}")
            
            # Convert to SQL table
            logger.debug("Converting to SQL table")
            conn = get_db_connection()
            df.to_sql(table_name, conn, if_exists='replace', index=True, index_label='id')
            conn.close()
            logger.info(f"Table {table_name} created successfully")
            
            return jsonify({
                'message': 'File uploaded and converted successfully',
                'table_name': table_name,
                'rows': len(df)
            })
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
        
        finally:
            # Clean up the temporary CSV file
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.debug(f"Temporary file removed: {filepath}")
    
    logger.error("Invalid file type")
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/tables', methods=['GET'])
def list_tables():
    logger.debug("Listing tables")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    conn.close()
    logger.debug(f"Found tables: {[table['name'] for table in tables]}")
    return jsonify({'tables': [table['name'] for table in tables]})

@app.route('/table/<table_name>', methods=['GET'])
def get_table_data(table_name):
    try:
        conn = get_db_connection()
        # Read the entire table into a pandas DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        return jsonify(df.to_dict(orient='records'))
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/table/<table_name>/<int:row_id>', methods=['GET'])
def get_row(table_name, row_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get specific row by ID
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (row_id,))
        row = cursor.fetchone()
        
        if row is None:
            return jsonify({'error': 'Row not found'}), 404
        
        # Convert row to dictionary
        columns = [description[0] for description in cursor.description]
        result = dict(zip(columns, row))
        
        conn.close()
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/table/<table_name>/download', methods=['GET'])
def download_table(table_name):
    try:
        conn = get_db_connection()
        
        # Read the table into a pandas DataFrame
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        
        # Save to temporary CSV file
        temp_csv = os.path.join(UPLOAD_FOLDER, f'{table_name}.csv')
        df.to_csv(temp_csv, index=False)
        
        # Send the file
        return send_file(
            temp_csv,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{table_name}.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/table/<table_name>', methods=['DELETE'])
def delete_table(table_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Drop the table
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Table {table_name} deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
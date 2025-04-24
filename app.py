from flask import Flask, request, jsonify, send_file, send_from_directory
import pandas as pd
import sqlite3
import os
import re
import shutil
from datetime import datetime
from graphene import ObjectType, String, List, Schema, Argument
from graphql_server.flask import GraphQLView
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder = 'build',template_folder='build')

# Configuration
UPLOAD_FOLDER = 'uploads'
BOAT_UPLOADS = 'boat_uploads'
HEATMAP_UPLOADS = 'heatmap_uploads'
DATABASE = 'database.db'
ALLOWED_EXTENSIONS = {'csv'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BOAT_UPLOADS, exist_ok=True)
os.makedirs(HEATMAP_UPLOADS, exist_ok=True)

# Define valid tables and their associated upload directories
VALID_TABLES = {
    'boat_data': BOAT_UPLOADS,
    'heatmap_data': HEATMAP_UPLOADS
}

# SQLite Connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database and create tables if they don't exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS boat_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin_file TEXT
    );
                   
    CREATE TABLE IF NOT EXISTS heatmap_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin_file TEXT
    );
    
    ''') 
    conn.commit()
    conn.close()

# Function to sanitize column names
def sanitize_column_name(name):
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    return name.strip('_')

# Function to add missing columns dynamically with sanitized names
def add_missing_columns(conn, df, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {col[1] for col in cursor.fetchall()}
    
    sanitized_columns = {sanitize_column_name(col) for col in df.columns}
    new_columns = sanitized_columns - existing_columns
    
    for col in new_columns:
        print(f"Adding missing column to {table_name}: {col}")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} TEXT")
    
    conn.commit()

# Validate table name
def validate_table(table_name):
    return table_name in VALID_TABLES

# Get upload directory for a table
def get_upload_dir(table_name):
    return VALID_TABLES.get(table_name) 

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


# List all valid tables endpoint
@app.route('/tables', methods=['GET'])
def list_tables():    
    return jsonify({
        'tables': list(VALID_TABLES.keys()),
    })

# Upload file to requested table. If exists, return error.
@app.route('/upload/<table_name>', methods=['POST'])
def upload_csv(table_name):
    # Validate table name
    if not validate_table(table_name):
        return jsonify({'error': 'Invalid table name'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file type'}), 400

    filename = secure_filename(file.filename)
    
    # Check if file already exists in the appropriate directory
    upload_dir = get_upload_dir(table_name)
    permanent_filepath = os.path.join(upload_dir, filename)
    if os.path.exists(permanent_filepath):
        return jsonify({'error': 'File already exists, please delete existing file and try again'}), 409
    
    # Save temporary file for processing
    temp_filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(temp_filepath)
    
    try:
        # Read the CSV
        df = pd.read_csv(temp_filepath)
        df.columns = [sanitize_column_name(col) for col in df.columns]
        df['origin_file'] = filename  # Use original filename
        
        # Save to database
        conn = get_db_connection()
        add_missing_columns(conn, df, table_name)
        df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.close()
        
        # Save a permanent copy in the appropriate directory
        shutil.copy2(temp_filepath, permanent_filepath)
        
        # Remove temporary file
        os.remove(temp_filepath)
        
        return jsonify({
            'message': f'File uploaded successfully to {table_name}', 
            'rows': len(df),
            'saved_as': filename,
            'storage_path': permanent_filepath
        })
    except Exception as e:
        # Clean up temporary file in case of error
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return jsonify({'error': str(e)}), 500

# List unique sources
@app.route('/sources/<table_name>', methods=['GET'])
def list_sources(table_name):
    # Validate table name
    if not validate_table(table_name):
        return jsonify({'error': 'Invalid table name'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT origin_file FROM {table_name}")
    sources = [row['origin_file'] for row in cursor.fetchall()]
    conn.close()
    
    # Also check files saved in the upload directory
    upload_dir = get_upload_dir(table_name)
    
    return jsonify({
        'sources': sources, 
        'table': table_name,
    })

# Download CSV by origin_file
@app.route('/download/<table_name>/<origin_file>', methods=['GET'])
def download_source(table_name, origin_file):
    # Validate table name
    if not validate_table(table_name):
        return jsonify({'error': 'Invalid table name'}), 400
    
    # Check if the file exists in the upload directory
    upload_dir = get_upload_dir(table_name)
    direct_filepath = os.path.join(upload_dir, origin_file)
    
    if os.path.exists(direct_filepath):
        # If the file exists directly, return it
        return send_file(direct_filepath, mimetype='text/csv', as_attachment=True)
    
    # Otherwise, generate it from the database
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE origin_file = ?", conn, params=(origin_file,))
    conn.close()
    
    if df.empty:
        return jsonify({'error': f'No data found for this source in {table_name}'}), 404
    
    # Create a temporary file to return
    temp_csv = os.path.join(UPLOAD_FOLDER, f'{origin_file}_{table_name}.csv')
    df.to_csv(temp_csv, index=False)
    return send_file(temp_csv, mimetype='text/csv', as_attachment=True)

# Delete data by origin_file
@app.route('/delete/<table_name>/<origin_file>', methods=['DELETE'])
def delete_source(table_name, origin_file):
    # Validate table name
    if not validate_table(table_name):
        return jsonify({'error': 'Invalid table name'}), 400
    
    # Delete from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE origin_file = ?", (origin_file,))
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    
    # Try to delete the file if it exists
    file_deleted = False
    upload_dir = get_upload_dir(table_name)
    file_path = os.path.join(upload_dir, origin_file)
    if os.path.exists(file_path):
        os.remove(file_path)
        file_deleted = True
    
    return jsonify({
        'message': f'Data from {origin_file} in table {table_name} deleted successfully',
        'rows_deleted': affected_rows,
        'file_deleted': file_deleted
    })

# Dynamically generate GraphQL schema on each request with filtering
@app.route('/graphql/<table_name>', methods=['POST'])
def graphql(table_name):
    # Validate table name
    if not validate_table(table_name):
        return jsonify({'error': 'Invalid table name'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    conn.close()
    
    # Use original column names with underscores
    fields = {col: String() for col in columns}
    filter_args = {col: Argument(String) for col in columns}
    
    # Create GraphQL ObjectType with snake_case field names
    DynamicRow = type('DynamicRow', (ObjectType,), fields)
    
    class Query(ObjectType):
        data = List(DynamicRow, **filter_args)
        
        def resolve_data(self, info, **kwargs):
            conn = get_db_connection()
            query = f"SELECT * FROM {table_name}"
            conditions = []
            params = []
            
            for col, value in kwargs.items():
                conditions.append(f"{col} = ?")
                params.append(value)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            # Ensure the correct number of bindings are supplied
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return [DynamicRow(**row) for row in df.to_dict(orient='records')]
    
    schema = Schema(query=Query, auto_camelcase=False)  # Disable auto-camelcase
    view = GraphQLView.as_view('graphql', schema=schema, graphiql=True)
    return view()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1',port=5000)

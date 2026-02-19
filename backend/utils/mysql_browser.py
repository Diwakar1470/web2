#!/usr/bin/env python3
"""
Quick MySQL Browser - Web interface to view database
Access at http://localhost:8888
"""

from flask import Flask, render_template_string, request, jsonify
import mysql.connector  # type: ignore
from mysql.connector import Error  # type: ignore
import json

app = Flask(__name__)

# Database connection config
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '1234',
    'database': 'school_db'
}

def get_db():
    """Get database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        return None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MySQL Database Browser</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { opacity: 0.8; }
        
        .sidebar { float: left; width: 250px; margin-right: 20px; }
        .table-list { background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .table-item { padding: 12px 15px; border-bottom: 1px solid #eee; cursor: pointer; }
        .table-item:hover { background: #f9f9f9; }
        .table-item.active { background: #3498db; color: white; }
        
        .content { overflow: auto; margin-left: 270px; }
        .table-viewer { background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .table-header { padding: 15px; border-bottom: 2px solid #3498db; }
        .table-header h2 { margin: 0; color: #2c3e50; }
        
        table { width: 100%; border-collapse: collapse; }
        th { background: #34495e; color: white; padding: 12px; text-align: left; }
        td { padding: 10px 12px; border-bottom: 1px solid #eee; }
        tr:hover { background: #f5f5f5; }
        
        .record-count { color: #7f8c8d; font-size: 12px; margin-top: 10px; }
        .loading { text-align: center; padding: 40px; color: #7f8c8d; }
        
        .json-view { background: #f9f9f9; padding: 10px; border-radius: 3px; font-family: monospace; font-size: 12px; max-width: 300px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗄️ MySQL Database Browser</h1>
            <p>Database: <strong>school_db</strong> | Host: <strong>127.0.0.1:3306</strong></p>
        </div>
        
        <div class="sidebar">
            <div class="table-list" id="tableList">
                <div style="padding: 20px; text-align: center; color: #7f8c8d;">Loading tables...</div>
            </div>
        </div>
        
        <div class="content">
            <div class="table-viewer" id="tableViewer">
                <div class="table-header">
                    <p style="color: #7f8c8d;">Select a table from the left to view its contents</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Load all tables
        fetch('/api/tables')
            .then(r => r.json())
            .then(tables => {
                const list = document.getElementById('tableList');
                list.innerHTML = '';
                tables.forEach(t => {
                    const div = document.createElement('div');
                    div.className = 'table-item';
                    div.textContent = t;
                    div.onclick = () => loadTable(t);
                    list.appendChild(div);
                });
                if (tables.length > 0) loadTable(tables[0]);
            });
        
        function loadTable(tableName) {
            document.querySelectorAll('.table-item').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
            
            fetch(`/api/table/${tableName}`)
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('tableViewer').innerHTML = 
                            `<div class="table-header" style="color: red;">${data.error}</div>`;
                        return;
                    }
                    
                    let html = `<div class="table-header"><h2>${tableName}</h2>
                        <div class="record-count">${data.rows.length} records</div></div>
                        <div style="overflow-x: auto;">
                        <table><thead><tr>`;
                    
                    if (data.rows.length > 0) {
                        Object.keys(data.rows[0]).forEach(col => {
                            html += `<th>${col}</th>`;
                        });
                        html += '</tr></thead><tbody>';
                        
                        data.rows.forEach(row => {
                            html += '<tr>';
                            Object.values(row).forEach(val => {
                                if (typeof val === 'object' && val !== null) {
                                    html += `<td><div class="json-view">${JSON.stringify(val, null, 1).substring(0, 100)}...</div></td>`;
                                } else {
                                    html += `<td>${String(val).substring(0, 100)}</td>`;
                                }
                            });
                            html += '</tr>';
                        });
                        html += '</tbody></table>';
                    } else {
                        html += '<div style="padding: 20px; color: #7f8c8d;">No records found</div>';
                    }
                    html += '</div>';
                    document.getElementById('tableViewer').innerHTML = html;
                });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tables')
def list_tables():
    """List all tables in database"""
    conn = get_db()
    if not conn:
        return jsonify({"error": "Cannot connect to database"}), 500
    
    cursor = conn.cursor()
    cursor.execute(f"SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_SCHEMA = DATABASE()")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify(tables)

@app.route('/api/table/<tableName>')
def view_table(tableName):
    """View table contents"""
    # Basic SQL injection prevention
    if not tableName.replace('_', '').isalnum():
        return jsonify({"error": "Invalid table name"}), 400
    
    conn = get_db()
    if not conn:
        return jsonify({"error": "Cannot connect to database"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) as cnt FROM `{tableName}`")
        count = cursor.fetchone()['cnt']
        
        # Get all data (limit to 100 rows for performance)
        cursor.execute(f"SELECT * FROM `{tableName}` LIMIT 100")
        rows = cursor.fetchall()
        
        # Parse JSON columns if they exist
        for row in rows:
            for key, val in row.items():
                if isinstance(val, str) and val.startswith('{'):
                    try:
                        row[key] = json.loads(val)
                    except:
                        pass
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "table": tableName,
            "total_records": count,
            "displayed": len(rows),
            "rows": rows
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌐 MySQL Database Browser")
    print("="*60)
    print("📱 Open your browser and go to: http://localhost:8888")
    print("🗄️  Database: school_db")
    print("🔌 Host: 127.0.0.1:3306")
    print("="*60 + "\n")
    app.run(host='localhost', port=8888, debug=False)

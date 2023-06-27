from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database Initialization
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL)''')
c.execute('''CREATE TABLE IF NOT EXISTS files
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                file_content BLOB NOT NULL)''')
conn.commit()

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        
        return redirect('/login')
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        
        if user:
            session['username'] = username
            return redirect('/')
        else:
            return redirect('/login')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

# File upload route
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    username = session['username']
    filename = file.filename
    time_created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    file_content = file.read()

    c.execute("INSERT INTO files (filename, username, created_at, file_content) VALUES (?, ?, ?, ?)",
              (filename, username, time_created, file_content))
    conn.commit()

    return redirect('/')


# File download route
@app.route('/download/<int:file_id>')
def download(file_id):
    c.execute("SELECT filename, file_content FROM files WHERE id = ?", (file_id,))
    file_data = c.fetchone()

    if file_data:
        filename = file_data[0]
        file_content = file_data[1]
        
        return send_file(
            io.BytesIO(file_content),
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    else:
        return redirect('/')



# Main route
@app.route('/')
def main():
    if 'username' not in session:
        return redirect('/login')
    
    c.execute("SELECT * FROM files ORDER BY created_at DESC")
    files = c.fetchall()

    return render_template('main.html', files=files)
# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    return render_template('404.html'), 500


if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0")

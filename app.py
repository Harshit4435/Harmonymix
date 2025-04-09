from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config['DATABASE'] = 'music_app.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()

        db = get_db()
        cursor = db.cursor()

        # Check if the username is already registered
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        data = cursor.fetchone()

        if data:
            return "Username already registered. Please choose a different username."

        # Insert new user into the database
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode()).hexdigest()

        db = get_db()
        cursor = db.cursor()

        # Check if the username and password match
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user_data = cursor.fetchone()

        if user_data:
            session['username'] = username
            return redirect(url_for('dashboard'))  # Redirect to the dashboard
        else:
            return "Incorrect username or password. Please try again."

    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' in session:
        db = get_db()
        cursor = db.cursor()

        if request.method == 'POST':
            song_name = request.form['song_name']
            cursor.execute("INSERT INTO songs (user_id, song_name) VALUES ((SELECT id FROM users WHERE username = ?), ?)",
                           (session['username'], song_name))
            db.commit()

        cursor.execute("SELECT * FROM users WHERE username = ?", (session['username'],))
        user_data = cursor.fetchone()

        cursor.execute("SELECT * FROM songs WHERE user_id = (SELECT id FROM users WHERE username = ?)",
                       (session['username'],))
        playlist = cursor.fetchall()

        return render_template('dashboard.html', user=user_data, playlist=playlist)
    else:
        return redirect(url_for('login'))

@app.route('/remove_song', methods=['POST'])
def remove_song():
    if 'username' in session:
        db = get_db()
        cursor = db.cursor()

        song_id = request.form.get('song_id')

        cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        db.commit()

        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/top_picks')
def top_picks():
    return render_template('top_picks.html')    

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

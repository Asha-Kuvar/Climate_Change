from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)

def init_db():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='9949237758',
        database='apollo_db'
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS missions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        year VARCHAR(4) NOT NULL,
                        details TEXT NOT NULL)''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('apollo.html')

@app.route('/missions', methods=['GET'])
def get_missions():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='9949237758',
        database='apollo_db'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions")
    missions = cursor.fetchall()
    conn.close()
    return jsonify(missions)

@app.route('/add_mission', methods=['POST'])
def add_mission():
    data = request.get_json()
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='9949237758',
        database='apollo_db'
    )
    cursor = conn.cursor()
    cursor.execute("INSERT INTO missions (name, year, details) VALUES (%s, %s, %s)",
                   (data['name'], data['year'], data['details']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Mission added successfully'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

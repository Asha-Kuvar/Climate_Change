from flask import Flask, request, jsonify, render_template
import mysql.connector
import requests
from netCDF4 import Dataset
from geopy.geocoders import Nominatim
import logging
from flask_mail import Mail, Message
from flask_cors import CORS
import joblib
import numpy as np
from sklearn.preprocessing import LabelEncoder

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

app.config['OPENWEATHER_API_KEY'] = '5746fff655c4e51b21de34dde51d8f20'
app.config['NASA_API_KEY'] = 'ITsTJf0FF74T8xkOsy6Mh5xd2mebXFkCpoUbvJuM'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with your Gmail
app.config['MAIL_PASSWORD'] = 'your-app-specific-password'  # Replace with Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

mail = Mail(app)
geolocator = Nominatim(user_agent="climate_dashboard")

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='9949237758',
        database='climate_db'
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/country_info', methods=['GET'])
def get_country_info():
    country_name = request.args.get('country')
    if not country_name:
        return jsonify({"error": "Country name is required"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT country, co2_emissions, deforestation_rate
        FROM climate_data
        WHERE LOWER(country) = LOWER(%s)
        ORDER BY year DESC
        LIMIT 1
        """
        cursor.execute(query, (country_name,))
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify(data) if data else jsonify({"error": f"No data found for '{country_name}'"}), 404
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/current_temperature', methods=['GET'])
def get_current_temperature():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country name is required"}), 400
    try:
        api_key = app.config['OPENWEATHER_API_KEY']
        url = f"http://api.openweathermap.org/data/2.5/weather?q={country}&appid={api_key}&units=metric"
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch weather data"}), 500
        weather_data = response.json()
        return jsonify({"country": country, "temperature": weather_data['main']['temp']})
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/nasa/co2', methods=['GET'])
def get_nasa_co2():
    country = request.args.get('country', default="India")
    if not country:
        return jsonify({"error": "Country name is required"}), 400
    try:
        location = geolocator.geocode(country, geometry='wkt')
        if not location:
            return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback"})
        bbox = location.raw['boundingbox']
        south, north, west, east = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
        bounding_box = f"{south},{west},{north},{east}"
        
        cmr_url = (
            "https://cmr.earthdata.nasa.gov/search/granules.json?"
            "concept_id=C1906303052-LARC&bounding_box=" + bounding_box +
            "&sort_key=-start_date&page_size=1"
        )
        headers = {"Authorization": f"Bearer {app.config['NASA_API_KEY']}"}
        cmr_response = requests.get(cmr_url, headers=headers)
        if cmr_response.status_code != 200 or not cmr_response.json()['feed']['entry']:
            return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback"})
        
        granule = cmr_response.json()['feed']['entry'][0]
        opendap_url = next((link['href'] for link in granule['links'] if 'opendap' in link['href']), None)
        if not opendap_url:
            return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback"})
        
        dataset = Dataset(opendap_url + '.nc4', 'r')
        xco2 = dataset.variables['xco2'][:]
        lat = dataset.variables['latitude'][:]
        lon = dataset.variables['longitude'][:]
        mask = (lat >= south) & (lat <= north) & (lon >= west) & (lon <= east)
        co2_level = float(xco2[mask].mean()) if mask.any() else float(xco2.mean())
        dataset.close()
        
        return jsonify({"country": country, "co2_level": round(co2_level, 2), "source": "NASA OCO-2 Lite"})
    except Exception as e:
        app.logger.error(f"Error fetching CO2 data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/temperature', methods=['GET'])
def get_temperature_data():
    country = request.args.get('country', default="India")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT year, avg_temperature FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(data)

@app.route('/api/co2-emissions', methods=['GET'])
def get_co2_emissions():
    country = request.args.get('country', default="India")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT year, co2_emissions FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(data)

@app.route('/api/deforestation', methods=['GET'])
def get_deforestation_data():
    country = request.args.get('country', default="India")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT year, deforestation_rate, avg_temperature FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(data)

@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()
    if not all([data.get('name'), data.get('email'), data.get('mobile'), data.get('message')]):
        return jsonify({"error": "All fields are required"}), 400
    name, email, mobile, message = data['name'], data['email'], data['mobile'], data['message']
    try:
        msg = Message(subject=f"New Contact Form Submission from {name}", recipients=['your-email@gmail.com'], body=f"Name: {name}\nEmail: {email}\nMobile: {mobile}\nMessage: {message}")
        mail.send(msg)
        confirmation_msg = Message(subject="Climate Change Dashboard - Contact Confirmation", recipients=[email], body="Thank you for contacting us. We have received your message and will get back to you shortly.")
        mail.send(confirmation_msg)
        return jsonify({"success": "Email sent successfully"}), 200
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")
        return jsonify({"error": "Failed to send email"}), 500

temp_model = joblib.load("temperature_model.pkl")
co2_model = joblib.load("co2_model.pkl")
deforestation_model = joblib.load("deforestation_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

@app.route('/api/predict', methods=['GET'])
def predict():
    country = request.args.get('country')
    year = request.args.get('year')
    if not country or not year:
        return jsonify({"error": "Both 'country' and 'year' parameters are required"}), 400
    try:
        year = int(year)
        country_encoded = label_encoder.transform([country])[0]
        input_data = np.array([[country_encoded, year]])
        predicted_temp = temp_model.predict(input_data)[0]
        predicted_co2 = co2_model.predict(input_data)[0]
        predicted_deforestation = deforestation_model.predict(input_data)[0]
        return jsonify({
            "country": country,
            "year": year,
            "predicted_temperature_c": round(predicted_temp, 2),
            "predicted_co2_emissions_mmt": round(predicted_co2, 2),
            "predicted_deforestation_rate_percent": round(predicted_deforestation, 2)
        })
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/api/predicts', methods=['POST'])
def predicts():
    try:
        data = request.get_json()
        temperature_change = float(data.get('temperatureChange'))
        co2_level = float(data.get('co2Level'))
        predicted_temperature = temperature_change + 0.5
        predicted_co2 = co2_level + 50
        return jsonify({
            "predicted_temperature_c": round(predicted_temperature, 2),
            "predicted_co2_emissions_mmt": round(predicted_co2, 2)
        })
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
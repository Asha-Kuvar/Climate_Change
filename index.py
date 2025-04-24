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
from geopy.exc import GeocoderTimedOut
import time

from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile
import datetime

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

# Add the token here (replace 'YOUR_NEW_TOKEN_HERE' with the actual token)
# app.config['NASA_API_KEY'] = 'eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImFzaGExMjMiLCJleHAiOjE3NDgyNTkwNTcsImlhdCI6MTc0MzA3NTA1NywiaXNzIjoiaHR0cHM6Ly91cnMuZWFydGhkYXRhLm5hc2EuZ292IiwiaWRlbnRpdHlfcHJvdmlkZXIiOiJlZGxfb3BzIiwiYWNyIjoiZWRsIiwiYXNzdXJhbmNlX2xldmVsIjozfQ.CSCexI9IeYLu5uIw3rZwHUrx5t67pACiu8SxpVkxjuSLQDXbiTK_wEJmKaeBmpwnyovRRe_FIP1KBSXZP-aR6N2sKXWEa2ROtHSpv7YToGn9rD6OZTbbWXUYhwaPN_Df_gH0YkllA8m4qtx0AG34febCByiD7PCX9MLKa2WSkCrB8R1qJ4AWhPsz8PTN_6NQUz7YlmjQbUavfZf9JEDGiJme8dHtN2gSC1DGQ1r36AN61RQPd7SUOxbCV6RULNF78cv13P8LYmhjVrWAVLk7m1i3-58_5vyDDZok4XXSHKfYCXqEEScUL0jdVmWEUquYhhHbwrC_eTPpEAEDVZl1_w'

app.config['OPENWEATHER_API_KEY'] = '5746fff655c4e51b21de34dde51d8f20'
app.config['NASA_API_KEY'] = '7gjMCvSavwY9XQfZwUUK5TyQnCWTmAWyfDzNtoMf'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '21svdc2079@svdegreecollege.ac.in'  # Replace with your Gmail
app.config['MAIL_PASSWORD'] = 'bcjcejkokwxbjkpl'  # Replace with Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

mail = Mail(app)
# Initialize geolocator
geolocator = Nominatim(user_agent="climate_dashboard", timeout=10)

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

# @app.route('/api/current_temperature', methods=['GET'])
# def get_current_temperature():
#     country = request.args.get('country')
#     app.logger.debug(f"Fetching temperature for country: {country}")
    
#     try:
#         api_key = app.config['OPENWEATHER_API_KEY']
#         url = f"http://api.openweathermap.org/data/2.5/weather?q={country}&appid={api_key}&units=metric"
#         app.logger.debug(f"OpenWeatherMap URL: {url}")
        
#         response = requests.get(url)
#         app.logger.debug(f"API response status: {response.status_code}")
#         app.logger.debug(f"API response content: {response.text}")
        
#         if response.status_code != 200:
#             app.logger.error(f"API error: {response.text}")
#             return jsonify({"error": "Failed to fetch weather data"}), 500
            
#         weather_data = response.json()
#         temp = weather_data['main']['temp']
#         app.logger.debug(f"Raw temperature value: {temp}")
        
#         if temp < -50 or temp > 60:  # Physical bounds check
#             app.logger.warning(f"Implausible temperature {temp}°C for {country}")
#             temp = 25 if country.lower() == 'india' else 15
            
#         return jsonify({
#             "country": country,
#             "temperature": temp,
#             "details": weather_data
#         })
        
#     except Exception as e:
#         app.logger.error(f"Exception in get_current_temperature: {str(e)}")
#         return jsonify({"error": str(e)}), 500

@app.route('/api/nasa/co2', methods=['GET'])
def get_nasa_co2():
    country = request.args.get('country', default="India")
    if not country:
        return jsonify({"error": "Country name is required"}), 400
    
    # Check if NASA_API_KEY is set
    if 'NASA_API_KEY' not in app.config or not app.config['NASA_API_KEY']:
        app.logger.error("NASA_API_KEY is not configured")
        return jsonify({"error": "Server configuration error: NASA API key missing"}), 500
    
    try:
        # Geocoding with retry logic
        for attempt in range(3):
            try:
                location = geolocator.geocode(country, geometry='wkt')
                if not location:
                    app.logger.warning(f"Geocoding returned no result for {country}")
                    return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback"})
                break
            except GeocoderTimedOut as e:
                app.logger.warning(f"Geocoding timeout on attempt {attempt + 1} for {country}: {e}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                raise
        
        bbox = location.raw['boundingbox']
        south_lat = float(bbox[0])  # Minimum latitude
        north_lat = float(bbox[1])  # Maximum latitude
        west_lon = float(bbox[2])   # Minimum longitude
        east_lon = float(bbox[3])   # Maximum longitude
        app.logger.debug(f"Raw coordinates for {country}: south_lat={south_lat}, west_lon={west_lon}, north_lat={north_lat}, east_lon={east_lon}")
        
        # # Validate ranges
        # if not (-100 <= south_lat <= 100 and -100 <= north_lat <= 100):
        #     app.logger.error(f"Invalid latitude range: south_lat={south_lat}, north_lat={north_lat}")
        #     return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback"})
        # if not (-180 <= west_lon <= 180 and -180 <= east_lon <= 180):
        #     app.logger.error(f"Invalid longitude range: west_lon={west_lon}, east_lon={east_lon}")
        #     return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback"})
        
        # Correct bounding box order: south,west,north,east
        bounding_box = f"{south_lat},{west_lon},{north_lat},{east_lon}"
        print(bounding_box)
        print("=-------------=============------------------==============------------")
        app.logger.debug(f"Constructed bounding box for {country}: {bounding_box}")

        # CMR API request
        base_url = "https://cmr.earthdata.nasa.gov/search/granules.json"
        params = {
            "concept_id": "C1906303052-LARC",
            "bounding_box": bounding_box,
            "sort_key": "-start_date",
            "page_size": "1",
            "temporal": "2023-03-01T00:00:00Z,2023-03-27T23:59:59Z"
        }
        headers = {"Authorization": f"Bearer {app.config['NASA_API_KEY']}"}
        app.logger.debug(f"CMR Base URL: {base_url}")
        app.logger.debug(f"CMR Params: {params}")
        
        cmr_response = requests.get(base_url, headers=headers, params=params)
        app.logger.debug(f"Actual CMR Request URL: {cmr_response.url}")
        app.logger.debug(f"CMR Response Status: {cmr_response.status_code}")
        app.logger.debug(f"CMR Response Content: {cmr_response.text}")
        
        if cmr_response.status_code == 401:
            app.logger.error("Authentication failed: Invalid or missing NASA API token")
            return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - Authentication Error"})
        if cmr_response.status_code != 200:
            app.logger.warning(f"CMR API failed: {cmr_response.text}")
            return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - CMR Error"})
        if not cmr_response.json()['feed']['entry']:
            app.logger.warning("CMR API returned no entries")
            return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - No Data"})

        granule = cmr_response.json()['feed']['entry'][0]
        opendap_url = next((link['href'] for link in granule['links'] if 'opendap' in link['href']), None)
        app.logger.debug(f"OPeNDAP URL: {opendap_url}")
        if not opendap_url:
            app.logger.warning("No OPeNDAP URL found")
            return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - No OPeNDAP"})

        dataset = Dataset(opendap_url + '.nc4', 'r')
        xco2 = dataset.variables['xco2'][:]
        lat = dataset.variables['latitude'][:]
        lon = dataset.variables['longitude'][:]
        mask = (lat >= south_lat) & (lat <= north_lat) & (lon >= west_lon) & (lon <= east_lon)
        app.logger.debug(f"Mask size: {mask.sum()}, Total points: {len(lat)}")
        co2_level = float(xco2[mask].mean()) if mask.any() else float(xco2.mean())
        app.logger.debug(f"CO2 Level: {co2_level}")
        dataset.close()

        return jsonify({"country": country, "co2_level": round(co2_level, 2), "source": "NASA OCO-2 Lite"})
    except Exception as e:
        app.logger.error(f"Error fetching CO2 data: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/nasa/deforestation', methods=['GET'])
def get_nasa_deforestation():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country name is required"}), 400
    
    if 'NASA_API_KEY' not in app.config or not app.config['NASA_API_KEY']:
        app.logger.error("NASA_API_KEY is not configured")
        return jsonify({"error": "Server configuration error: NASA API key missing"}), 500

    try:
        for attempt in range(3):
            try:
                location = geolocator.geocode(country, geometry='wkt')
                if not location:
                    app.logger.warning(f"Geocoding returned no result for {country}")
                    return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback"})
                break
            except GeocoderTimedOut as e:
                app.logger.warning(f"Geocoding timeout on attempt {attempt + 1} for {country}: {e}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                raise
        
        bbox = location.raw['boundingbox']
        south_lat = float(bbox[0])
        north_lat = float(bbox[1])
        west_lon = float(bbox[2])
        east_lon = float(bbox[3])
        app.logger.debug(f"Raw coordinates for {country}: south_lat={south_lat}, west_lon={west_lon}, north_lat={north_lat}, east_lon={east_lon}")

        bounding_box = f"{south_lat},{west_lon},{north_lat},{east_lon}"
        app.logger.debug(f"Constructed bounding box for {country}: {bounding_box}")

        base_url = "https://cmr.earthdata.nasa.gov/search/granules.json"
        params = {
            "provider": "UMD",
            "short_name": "HLF_TCC",  # Hansen Global Forest Change dataset
            "version": "1.9",
            "bounding_box": bounding_box,
            "temporal": "2020-01-01T00:00:00Z,2023-12-31T23:59:59Z",
            "page_size": 1
        }
        headers = {"Authorization": f"Bearer {app.config['NASA_API_KEY']}"}
        
        cmr_response = requests.get(base_url, headers=headers, params=params)
        app.logger.debug(f"CMR Response Status for Deforestation: {cmr_response.status_code}")
        app.logger.debug(f"CMR Response Content for Deforestation: {cmr_response.text}")

        if cmr_response.status_code != 200:
            app.logger.warning(f"CMR API failed for deforestation: {cmr_response.text}")
            return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - CMR Error"})
        if not cmr_response.json()['feed']['entry']:
            app.logger.warning(f"No deforestation data found for {country}")
            return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - No Data"})

        granule = cmr_response.json()['feed']['entry'][0]
        opendap_url = next((link['href'] for link in granule['links'] if 'opendap' in link['href']), None)
        if not opendap_url:
            app.logger.warning(f"No OPeNDAP URL found for {country}")
            return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - No OPeNDAP"})

        dataset = Dataset(opendap_url + '.nc', 'r')
        treecover_2000 = dataset.variables['treecover2000'][:]  # Initial tree cover in 2000 (%)
        loss = dataset.variables['loss'][:]  # Cumulative loss up to latest year
        lat = dataset.variables['lat'][:]
        lon = dataset.variables['lon'][:]

        mask = (lat >= south_lat) & (lat <= north_lat) & (lon >= west_lon) & (lon <= east_lon)
        initial_cover = treecover_2000[mask].mean()  # Mean tree cover in 2000
        total_loss = loss[mask].mean()  # Mean loss over the period

        dataset.close()

        if initial_cover > 0:
            deforestation_rate = (total_loss / initial_cover) * 100  # Percentage of original cover lost
            app.logger.debug(f"Calculated deforestation rate for {country}: {deforestation_rate:.2f}%")
            return jsonify({"country": country, "deforestation_rate": round(deforestation_rate, 2), "source": "NASA GFC"})
        else:
            app.logger.warning(f"No initial tree cover data for {country}")
            return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - No Tree Cover"})

    except Exception as e:
        app.logger.error(f"Error fetching deforestation data: {e}")
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

# @app.route('/api/predicts', methods=['POST'])
# def predicts():
#     try:
#         data = request.get_json()
#         temperature_change = float(data.get('temperatureChange'))
#         co2_level = float(data.get('co2Level'))
#         predicted_temperature = temperature_change + 0.5
#         predicted_co2 = co2_level + 50
#         return jsonify({
#             "predicted_temperature_c": round(predicted_temperature, 2),
#             "predicted_co2_emissions_mmt": round(predicted_co2, 2)
#         })
#     except Exception as e:
#         app.logger.error(f"Error: {e}")
#         return jsonify({"error": str(e)}), 500

@app.route('/api/predicts', methods=['POST'])
def predicts():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract inputs with defaults
        temperature_change = float(data.get('temperatureChange', 0))
        co2_level = float(data.get('co2Level', 400))
        deforestation_change = float(data.get('deforestationChange', 0))

        # Simple simulation logic (replace with real model if available)
        predicted_temp = temperature_change + (co2_level / 1000)  # Temp increases slightly with CO2
        predicted_co2 = co2_level + (deforestation_change * 5)     # CO2 increases with deforestation
        predicted_def = deforestation_change + (temperature_change * 0.2)  # Deforestation impacted by temp

        # Return all three predicted values
        return jsonify({
            "predicted_temperature_c": round(predicted_temp, 2),
            "predicted_co2_emissions_mmt": round(predicted_co2, 2),
            "predicted_deforestation_rate_percent": round(predicted_def, 2)
        })
    except ValueError as e:
        app.logger.error(f"Input Error: {e}")
        return jsonify({"error": "Invalid input values"}), 400
    except Exception as e:
        app.logger.error(f"Simulation Error: {e}")
        return jsonify({"error": str(e)}), 500
    
# Add these new routes to your Flask app
@app.route('/api/compare', methods=['POST'])
def compare_countries():
    data = request.get_json()
    if not data or 'countries' not in data:
        return jsonify({"error": "Countries list is required"}), 400
    
    try:
        results = []
        for country in data['countries']:
            # Get current data
            temp_response = requests.get(f"http://{request.host}/api/current_temperature?country={country}")
            country_response = requests.get(f"http://{request.host}/api/country_info?country={country}")
            
            temp_data = temp_response.json()
            country_data = country_response.json()
            
            results.append({
                "country": country,
                "temperature": temp_data.get('temperature', 0),
                "co2": country_data.get('co2_emissions', 0),
                "deforestation": country_data.get('deforestation_rate', 0)
            })
        
        return jsonify(results)
    
    except Exception as e:
        app.logger.error(f"Comparison error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country is required"}), 400
    
    try:
        # Get all data for the country
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert to CSV
        if not data:
            return jsonify({"error": "No data found"}), 404
            
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename={country}_climate_data.csv"
        response.headers["Content-type"] = "text/csv"
        return response
        
    except Exception as e:
        app.logger.error(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
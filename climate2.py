from flask import Flask, request, jsonify, render_template
import mysql.connector
import requests
import os
from datetime import datetime
import logging
import smtplib
from email.message import EmailMessage
from flask_mail import Mail, Message  # Import Mail and Message
from flask_cors import CORS


import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder


# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['OPENWEATHER_API_KEY'] = '5746fff655c4e51b21de34dde51d8f20'  # Replace with your OpenWeather API key
app.config['CO2_API_KEY'] = 'your_co2_api_key'  # Replace with your CO2 API key
app.config['GFW_API_KEY'] = 'your_gfw_api_key'  # Replace with your GFW API key

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@example.com'

# OpenWeather API Key (Replace with your actual API Key)
OPENWEATHER_API_KEY = "5746fff655c4e51b21de34dde51d8f20"

mail = Mail(app)  # Initialize Mail

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='9949237758',
        database='climate_db'
    )

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Fetch historical CO2 emissions data from an external API
@app.route('/api/external/co2', methods=['GET'])
def get_external_co2():
    country = request.args.get('country', default="India", type=str)
    url = f"https://api.co2data.com/v1/countries/{country}/emissions"  # Replace with actual API endpoint
    headers = {"Authorization": f"Bearer {app.config['CO2_API_KEY']}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch CO2 data"}), 500
    
# Fetch deforestation data from Global Forest Watch API
@app.route('/api/external/deforestation', methods=['GET'])
def get_external_deforestation():
    country = request.args.get('country', default="India", type=str)
    url = f"https://api.globalforestwatch.org/v1/countries/{country}/deforestation"  # Replace with actual API endpoint
    headers = {"Authorization": f"Bearer {app.config['GFW_API_KEY']}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch deforestation data"}), 500

# Replace this with your actual API key
API_KEY = "STVDWmU1TW5jNlpuRnByUG1abDREbTRRYVR0bmxPbDMxQzRYb1pwUw=="
BASE_URL = "https://api.countrystatecity.in/v1"

# API Endpoint to Get Climate Data by Country
@app.route("/get_climate_data", methods=["GET"])
def fetch_climate_data_by_country():  # Renamed function
    country = request.args.get("country")

    if not country:
        return jsonify({"error": "Country name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT temperature, co2_emissions, deforestation_rate
    FROM climate_data
    WHERE country = %s
    """
    cursor.execute(query, (country,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "Data not found"}), 404

@app.route('/api/country_info', methods=['GET'])
def get_country_info():
    country_name = request.args.get('country')
    app.logger.debug(f"Received request for country info: {country_name}")

    if not country_name:
        app.logger.error("Country name is required")
        return jsonify({"error": "Country name is required"}), 400

    try:
        # Fetch current temperature from OpenWeatherMap API
        api_key = app.config['OPENWEATHER_API_KEY']
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={country_name}&appid={api_key}&units=metric"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()
        # print(weather_data)

        if weather_response.status_code != 200:
            app.logger.error(f"Failed to fetch weather data: {weather_data}")
            return jsonify({"error": "Failed to fetch weather data"}), 500

        current_temperature = weather_data['main']['temp']

        # Fetch other data from the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT country, co2_emissions, deforestation_rate
        FROM climate_data
        WHERE LOWER(country) = LOWER(%s)
        ORDER BY year DESC
        LIMIT 1
        """
        app.logger.debug(f"Executing query: {query} with country: {country_name}")
        cursor.execute(query, (country_name,))
        data = cursor.fetchone()

        cursor.close()
        conn.close()

        if data:
            # Add current temperature to the response
            data['avg_temperature'] = current_temperature
            # data['co2_emissions'] = current_co2_emissions
            app.logger.debug(f"Query result: {data}")
            return jsonify(data)
        else:
            app.logger.error(f"No data found for '{country_name}'")
            return jsonify({"error": f"No data found for '{country_name}'"}), 404

    except mysql.connector.Error as err:
        app.logger.error(f"MySQL error: {err}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        app.logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/current_temperature', methods=['GET'])
def get_current_temperature():
    country = request.args.get('country')  # Get the country name from the query parameters

    if not country:
        return jsonify({"error": "Country name is required"}), 400

    try:
        # Fetch current temperature from OpenWeatherMap API
        api_key = app.config['OPENWEATHER_API_KEY']
        url = f"http://api.openweathermap.org/data/2.5/weather?q={country}&appid={api_key}&units=metric"
        response = requests.get(url)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch weather data"}), 500

        weather_data = response.json()
        current_temperature = weather_data['main']['temp']  # Extract temperature in Celsius

        return jsonify({
            "country": country,
            "temperature": current_temperature,
            "weather": weather_data['weather'][0]['description']  # Optional: Include weather description
        })

    except Exception as e:
        app.logger.error(f"Error fetching current temperature: {e}")
        return jsonify({"error": "Internal server error"}), 500
       
@app.route('/api/temperature', methods=['GET'])
def get_temperature_data():
    country = request.args.get('country', default="India", type=str)  # Get country from request

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch temperature data for the selected country
    cursor.execute("SELECT year, avg_temperature FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    print(f"API Temperature Data for {country}:", data)  # Debugging print to check API response
    return jsonify(data)  # Return filtered data as JSON

# Configuration
app.config['NASA_API_KEY'] = 'ITsTJf0FF74T8xkOsy6Mh5xd2mebXFkCpoUbvJuM'  # Replace with your NASA Earthdata API key

# Fetch CO₂ emissions from NASA Earthdata API
@app.route('/api/nasa/co2', methods=['GET'])
def get_nasa_co2():
    """
    Fetch CO₂ emissions data from NASA's Earthdata API.
    """
    try:
        # NASA Earthdata API endpoint (replace with the correct endpoint)
        url = "https://oco2.gesdisc.eosdis.nasa.gov/opendap/OCO2_L2_Lite_FP.10r/contents.html"
        
        # Add your NASA Earthdata API key or token
        headers = {
            "Authorization": f"Bearer {app.config['NASA_API_KEY']}"
        }

        # Make the request to NASA's API
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch CO₂ data from NASA API"}), 500

        # Parse the response (adjust based on NASA API response structure)
        data = response.json()
        co2_level = data.get("co2_level", None)  # Replace with the actual key for CO₂ data

        if not co2_level:
            return jsonify({"error": "CO₂ data not found in NASA API response"}), 404

        return jsonify({"co2_level": co2_level})

    except Exception as e:
        app.logger.error(f"Error fetching CO₂ data from NASA API: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Fetch CO₂ emissions data from the database
@app.route('/api/co2-emissions', methods=['GET'])
def get_co2_emissions():
    country = request.args.get('country', default="India", type=str)  # Get country from request

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch CO₂ emissions for the selected country
    cursor.execute("SELECT year, co2_emissions FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    print(f"API CO₂ Data for {country}:", data)  # Debugging print to check API response
    return jsonify(data)  # Return filtered data as JSON

# Fetch deforestation data from the database
@app.route('/api/deforestation', methods=['GET'])
def get_deforestation_data():
    country = request.args.get('country', default="India", type=str)  # Get country from request

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Fetch deforestation data for the selected country
    cursor.execute("SELECT year, deforestation_rate, avg_temperature FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    print(f"API Deforestation Data for {country}:", data)  # Debugging print
    return jsonify(data)  # Return filtered data as JSON

# Default admin email
ADMIN_EMAIL = "21svdc2079@svdegreecollege.ac.in"  # Replace with your admin email
ADMIN_PASSWORD = "bcjcejkokwxbjkpl"  # Replace with your email password

@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()  # Get JSON data correctly
    if not data:
        return jsonify({"error": "Invalid request, no data received"}), 400

    name = data.get('name')
    email = data.get('email')
    mobile = data.get('mobile')
    message = data.get('message')

    if not all([name, email, mobile, message]):
        return jsonify({"error": "All fields are required"}), 400

    # Email to admin
    email_message = EmailMessage()
    email_message.set_content(f"Name: {name}\nEmail: {email}\nMobile: {mobile}\nMessage: {message}")
    email_message["Subject"] = f"New Contact Form Submission from {name}"
    email_message["From"] = ADMIN_EMAIL
    email_message["To"] = ADMIN_EMAIL

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(ADMIN_EMAIL, ADMIN_PASSWORD)
            server.send_message(email_message)

        # Confirmation email to the user
        confirmation_message = EmailMessage()
        confirmation_message.set_content(
            "Thank you for contacting us. We have received your message and will get back to you shortly."
        )
        confirmation_message["Subject"] = "Climate Change Dashboard - Contact Confirmation"
        confirmation_message["From"] = ADMIN_EMAIL
        confirmation_message["To"] = email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(ADMIN_EMAIL, ADMIN_PASSWORD)
            server.send_message(confirmation_message)

        return jsonify({"success": "Email sent successfully"}), 200
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")
        return jsonify({"error": "Failed to send email"}), 500

# Load models and encoder
temp_model = joblib.load("temperature_model.pkl")
co2_model = joblib.load("co2_model.pkl")
deforestation_model = joblib.load("deforestation_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# Prediction Endpoint
@app.route('/api/predict', methods=['GET'])
def predict():
    # Get query parameters
    country = request.args.get('country')
    year = request.args.get('year')

    if not country or not year:
        return jsonify({"error": "Both 'country' and 'year' parameters are required."}), 400

    try:
        year = int(year)
    except ValueError:
        return jsonify({"error": "Year must be a valid integer."}), 400

    # Convert Country to Encoded Value
    try:
        country_encoded = label_encoder.transform([country])[0]
    except ValueError:
        return jsonify({"error": f"Country '{country}' not found in the dataset."}), 400

    # Prepare Input
    input_data = np.array([[country_encoded, year]])

    # Make Predictions
    predicted_temp = temp_model.predict(input_data)[0]
    predicted_co2 = co2_model.predict(input_data)[0]
    predicted_deforestation = deforestation_model.predict(input_data)[0]

    print("Predicted Temperature:", predicted_temp)
    print("Predicted CO2 Emissions:", predicted_co2)
    print("Predicted Deforestation Rate:", predicted_deforestation)
   
    # Return Results
    return jsonify({
        "country": country,
        "year": year,
        "predicted_temperature_c": round(predicted_temp, 2),
        "predicted_co2_emissions_mmt": round(predicted_co2, 2),
        "predicted_deforestation_rate_percent": round(predicted_deforestation, 2),
    })

@app.route('/api/predicts', methods=['POST'])
def predicts():
    try:
        # Get input data from the frontend
        data = request.get_json()
        print("Received data:", data)  # Debugging: Log received data

        # Convert values to floats (even if they are sent as strings)
        temperature_change = float(data.get('temperatureChange'))
        co2_level = float(data.get('co2Level'))
        # deforestation_rate = float(data.get('deforestationRate'))

        # Perform simulation (replace with actual logic or ML model predictions)
        predicted_temperature = temperature_change + 0.5  # Example calculation
        predicted_co2 = co2_level + 50  # Example calculation
        # predicted_deforestation = deforestation_rate + 5  # Example calculation

        # Prepare response
        response = {
            "predicted_temperature_c": round(predicted_temperature, 2),
            "predicted_co2_emissions_mmt": round(predicted_co2, 2),
            # "predicted_deforestation_rate_percent": round(predicted_deforestation, 2),
        }
        print("Sending response:", response)  # Debugging: Log response

        # Return results
        return jsonify(response)
    except Exception as e:
        print("Error:", str(e))  # Debugging: Log errors
        return jsonify({"error": str(e)}), 500
    
# Run the app
if __name__ == '__main__':
    app.run(debug=True)
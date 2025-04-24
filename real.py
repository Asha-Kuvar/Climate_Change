# from flask import Flask, request, jsonify, render_template
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from flask_mail import Mail, Message
import logging
import smtplib
import mysql.connector
import requests
from netCDF4 import Dataset
from geopy.geocoders import Nominatim
from flask_cors import CORS
import joblib
import numpy as np
from sklearn.preprocessing import LabelEncoder
from geopy.exc import GeocoderTimedOut
import time
import io
import csv
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile
import datetime
import re



# Logging configuration
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app)

# Configuration
app.config['OPENWEATHER_API_KEY'] = '5746fff655c4e51b21de34dde51d8f20'
app.config['NASA_API_KEY'] = '7gjMCvSavwY9XQfZwUUK5TyQnCWTmAWyfDzNtoMf'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '21svdc2079@svdegreecollege.ac.in'  # Replace with your Gmail
app.config['MAIL_PASSWORD'] = 'bcjcejkokwxbjkpl'  # Replace with Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

mail = Mail(app)
geolocator = Nominatim(user_agent="climate_dashboard", timeout=10)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='9949237758',
        database='climate_db'
    )

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"  # Replace with your actual API key

@app.route("/")
def index():
    return render_template("index.html")

# Routes for pages
# @app.route('/')
# def home():
#     return render_template('home.html')

# @app.route('/charts')
# def charts():
#     return render_template('charts.html')

# @app.route('/simulation')
# def simulation():
#     return render_template('simulation.html')

# @app.route('/contact')
# def contact():
#     return render_template('contact.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400

        user_message = data["message"].strip()
        app.logger.debug(f"Received message: {user_message}")

        # Simple response logic - replace this with your actual AI integration
        if "temperature" in user_message.lower():
            response = "Temperature data shows historical trends and current readings. You can view these on the dashboard."
        elif "co2" in user_message.lower() or "carbon" in user_message.lower():
            response = "CO2 emissions data is collected from various sources including satellite measurements and ground stations."
        elif "deforestation" in user_message.lower():
            response = "Deforestation rates are calculated based on satellite imagery and forest cover analysis."
        elif "help" in user_message.lower():
            response = "I can help with questions about: temperature, CO2 emissions, deforestation, and general climate data."
        else:
            response = "I'm ClimateBot, here to help with climate data questions. Try asking about temperature, CO2 emissions, or deforestation."

        return jsonify({"response": response})

    except Exception as e:
        app.logger.error(f"Chat endpoint error: {type(e).__name__}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
# Route for serving the HTML
# @app.route('/')
# def index():
#     return render_template('index.html')

# API: Country Information
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

# API: Current Temperature
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
        temp = weather_data['main']['temp']
        if temp < -50 or temp > 60:  # Physical bounds check
            app.logger.warning(f"Implausible temperature {temp}°C for {country}")
            temp = 25 if country.lower() == 'india' else 15
        return jsonify({
            "country": country,
            "temperature": temp,
            "details": weather_data
        })
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# API: NASA CO2 Data
# @app.route('/api/nasa/co2', methods=['GET'])
# def get_nasa_co2():
#     country = request.args.get('country', default="India")
#     if not country or 'NASA_API_KEY' not in app.config or not app.config['NASA_API_KEY']:
#         app.logger.error("NASA_API_KEY is not configured or country missing")
#         return jsonify({"error": "Server configuration error: NASA API key missing or invalid country"}), 500

#     try:
#         for attempt in range(3):
#             try:
#                 location = geolocator.geocode(country, geometry='wkt')
#                 if not location:
#                     app.logger.warning(f"Geocoding returned no result for {country}")
#                     return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback"})
#                 break
#             except GeocoderTimedOut as e:
#                 app.logger.warning(f"Geocoding timeout on attempt {attempt + 1} for {country}: {e}")
#                 if attempt < 2:
#                     time.sleep(2)
#                     continue
#                 raise

#         bbox = location.raw['boundingbox']
#         south_lat, north_lat, west_lon, east_lon = map(float, bbox)
#         bounding_box = f"{south_lat},{west_lon},{north_lat},{east_lon}"
#         app.logger.debug(f"Bounding box for {country}: {bounding_box}")

#         base_url = "https://cmr.earthdata.nasa.gov/search/granules.json"
#         params = {
#             "concept_id": "C1906303052-LARC",
#             "bounding_box": bounding_box,
#             "sort_key": "-start_date",
#             "page_size": "1",
#             "temporal": "2023-03-01T00:00:00Z,2023-03-27T23:59:59Z"
#         }
#         headers = {"Authorization": f"Bearer {app.config['NASA_API_KEY']}"}
#         cmr_response = requests.get(base_url, headers=headers, params=params)
#         app.logger.debug(f"CMR Response Status: {cmr_response.status_code}")

#         if cmr_response.status_code != 200:
#             app.logger.warning(f"CMR API failed: {cmr_response.text}")
#             return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - CMR Error"})
#         if not cmr_response.json()['feed']['entry']:
#             app.logger.warning("No CMR entries found")
#             return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - No Data"})

#         granule = cmr_response.json()['feed']['entry'][0]
#         opendap_url = next((link['href'] for link in granule['links'] if 'opendap' in link['href']), None)
#         if not opendap_url:
#             app.logger.warning("No OPeNDAP URL found")
#             return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - No OPeNDAP"})

#         dataset = Dataset(opendap_url + '.nc4', 'r')
#         xco2 = dataset.variables['xco2'][:]
#         lat = dataset.variables['latitude'][:]
#         lon = dataset.variables['longitude'][:]
#         mask = (lat >= south_lat) & (lat <= north_lat) & (lon >= west_lon) & (lon <= east_lon)
#         co2_level = float(xco2[mask].mean()) if mask.any() else float(xco2.mean())
#         dataset.close()

#         return jsonify({"country": country, "co2_level": round(co2_level, 2), "source": "NASA OCO-2 Lite"})
#     except Exception as e:
#         app.logger.error(f"Error fetching CO2 data: {e}")
#         return jsonify({"error": str(e)}), 500

@app.route('/api/co2', methods=['GET'])
def get_co2():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country name is required"}), 400

    try:
        # Geocode country with retries
        for attempt in range(3):
            try:
                location = geolocator.geocode(country, timeout=10)
                if not location:
                    app.logger.warning(f"Geocoding failed for {country}")
                    return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - Geocode Failed", "unit": "ppm"}), 404
                break
            except GeocoderTimedOut as e:
                app.logger.warning(f"Geocoding timeout attempt {attempt + 1}: {e}")
                if attempt == 2:
                    return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - Geocode Timeout", "unit": "ppm"}), 500
                time.sleep(2)

        lat, lon = location.latitude, location.longitude
        app.logger.debug(f"Geocoded {country} to lat={lat}, lon={lon}")

        # Try Open-Meteo Air Quality API
        try:
            url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=carbon_monoxide"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                co_data = data.get('hourly', {}).get('carbon_monoxide', [])
                # Find the latest non-None CO value
                co_level = None
                for value in co_data[::-1]:  # Iterate backwards to get latest
                    if value is not None:
                        co_level = value
                        break
                if co_level is not None and co_level >= 0:
                    co2_level = 415.0 + (co_level / 1000.0)  # Simplified scaling
                    if 300 <= co2_level <= 500:  # Bounds check
                        app.logger.debug(f"Open-Meteo CO level for {country}: {co_level} µg/m³, CO2: {co2_level} ppm")
                        return jsonify({
                            "country": country,
                            "co2_level": round(co2_level, 2),
                            "unit": "ppm",
                            "source": "Open-Meteo Air Quality (CO-based)"
                        })
                    else:
                        app.logger.warning(f"Implausible CO2 level {co2_level} ppm from Open-Meteo for {country}")
                else:
                    app.logger.warning(f"No valid CO data from Open-Meteo for {country}: {co_data[-5:]}")
            else:
                app.logger.warning(f"Open-Meteo API failed: {response.status_code} - {response.text}")
        except Exception as e:
            app.logger.warning(f"Open-Meteo error: {str(e)}")

        # Fallback to database
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT co2_emissions
            FROM climate_data
            WHERE LOWER(country) = LOWER(%s)
            ORDER BY year DESC
            LIMIT 1
            """
            cursor.execute(query, (country,))
            data = cursor.fetchone()
            cursor.close()
            conn.close()
            if data and data['co2_emissions'] is not None:
                co2_level = float(data['co2_emissions'])
                if 300 <= co2_level <= 500:  # Bounds check
                    app.logger.debug(f"Database CO2 level for {country}: {co2_level} ppm")
                    return jsonify({
                        "country": country,
                        "co2_level": round(co2_level, 2),
                        "unit": "ppm",
                        "source": "Climate Database"
                    })
                else:
                    app.logger.warning(f"Implausible database CO2 level {co2_level} ppm for {country}")
        except Exception as e:
            app.logger.warning(f"Database error: {str(e)}")

        # Final static fallback
        app.logger.debug(f"Using static fallback for {country}: 415.0 ppm")
        return jsonify({
            "country": country,
            "co2_level": 415.0,
            "unit": "ppm",
            "source": "Fallback - All Sources Failed"
        })

    except Exception as e:
        app.logger.error(f"Error fetching CO2 data for {country}: {type(e).__name__}: {str(e)}")
        return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - Exception", "unit": "ppm"}), 500

# API: Deforestation (Global Forest Watch)
# @app.route('/api/deforestation', methods=['GET'])
# def get_deforestation():
#     country = request.args.get('country', default="India")
#     if not country:
#         return jsonify({"error": "Country name is required"}), 400

#     try:
#         # Map country name to GFW country code (ISO3)
#         country_code_map = {
#             "India": "IND",
#             "Brazil": "BRA",
#             "United States": "USA",
#             # Add more mappings as needed or fetch dynamically
#         }
#         country_code = country_code_map.get(country, None)
#         if not country_code:
#             # Try geocoding to get ISO code
#             for attempt in range(3):
#                 try:
#                     location = geolocator.geocode(country, timeout=10)
#                     if location and 'country_code' in location.raw['address']:
#                         country_code = location.raw['address']['country_code'].upper()
#                         break
#                     app.logger.warning(f"Geocoding failed for {country}")
#                     return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - Geocode Failed", "unit": "%"}), 404
#                 except GeocoderTimedOut as e:
#                     app.logger.warning(f"Geocoding timeout attempt {attempt + 1}: {e}")
#                     if attempt == 2:
#                         return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - Geocode Timeout", "unit": "%"}), 500
#                     time.sleep(2)

#         # Fetch from Global Forest Watch API
#         try:
#             url = f"https://data-api.globalforestwatch.org/v1/query/forest-loss?iso={country_code}&start_year=2020&end_year=2023"
#             response = requests.get(url, timeout=10)
#             if response.status_code == 200:
#                 data = response.json()
#                 if data.get('data') and len(data['data']) > 0:
#                     total_loss = sum(year['tree_cover_loss'] for year in data['data'])  # km²
#                     # Approximate % loss (assuming total forest area; adjust if known)
#                     forest_area = 1000000  # Placeholder (km²); replace with actual data if available
#                     deforestation_rate = (total_loss / forest_area) * 100
#                     app.logger.debug(f"GFW deforestation for {country}: {total_loss} km², rate: {deforestation_rate}%")
#                     return jsonify({
#                         "country": country,
#                         "deforestation_rate": round(deforestation_rate, 2),
#                         "unit": "%",
#                         "source": "Global Forest Watch"
#                     })
#                 app.logger.warning(f"No deforestation data found for {country}")
#             app.logger.warning(f"GFW API failed: {response.status_code} - {response.text}")
#         except Exception as e:
#             app.logger.warning(f"GFW error: {str(e)}")

#         # Fallback to database
#         try:
#             conn = get_db_connection()
#             cursor = conn.cursor(dictionary=True)
#             query = """
#             SELECT deforestation_rate
#             FROM climate_data
#             WHERE LOWER(country) = LOWER(%s)
#             ORDER BY year DESC
#             LIMIT 1
#             """
#             cursor.execute(query, (country,))
#             data = cursor.fetchone()
#             cursor.close()
#             conn.close()
#             if data and data['deforestation_rate'] is not None:
#                 deforestation_rate = float(data['deforestation_rate'])
#                 app.logger.debug(f"Database deforestation rate for {country}: {deforestation_rate}%")
#                 return jsonify({
#                     "country": country,
#                     "deforestation_rate": round(deforestation_rate, 2),
#                     "unit": "%",
#                     "source": "Climate Database"
#                 })
#         except Exception as e:
#             app.logger.warning(f"Database error: {str(e)}")

#         # Final static fallback
#         app.logger.debug(f"Using static fallback for {country}: 10.0%")
#         return jsonify({
#             "country": country,
#             "deforestation_rate": 10.0,
#             "unit": "%",
#             "source": "Fallback - All Sources Failed"
#         })

#     except Exception as e:
#         app.logger.error(f"Error fetching deforestation data for {country}: {type(e).__name__}: {str(e)}")
#         return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - Exception", "unit": "%"}), 500

@app.route('/api/deforestations', methods=['GET'])
def get_deforestation():
    country = request.args.get('country', default="India")
    if not country:
        return jsonify({"error": "Country name is required"}), 400

    try:
        # Step 1: Resolve country name to ISO3 code using REST Countries API
        iso3_code = None
        for attempt in range(3):
            try:
                url = f"https://restcountries.com/v3.1/name/{country}?fullText=true"
                response = requests.get(url, timeout=10)
                app.logger.debug(f"REST Countries API response status for {country}: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        iso3_code = data[0]["cca3"]
                        app.logger.debug(f"Resolved {country} to ISO3: {iso3_code}")
                        break
                    else:
                        app.logger.warning(f"No country data found for {country}")
                        break
                elif response.status_code == 502:
                    app.logger.warning(f"502 Bad Gateway on attempt {attempt + 1} for {country}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
                        continue
                    app.logger.error(f"Failed after 3 attempts for {country}: 502 Bad Gateway")
                    break
                else:
                    app.logger.warning(f"REST Countries API failed for {country}: {response.status_code} - {response.text}")
                    break
            except Exception as e:
                app.logger.warning(f"REST Countries API error for {country} on attempt {attempt + 1}: {type(e).__name__}: {str(e)}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                app.logger.error(f"Failed after 3 attempts for {country}: {str(e)}")
                break

        if not iso3_code:
            app.logger.error(f"Unable to resolve ISO3 code for {country}")
            return jsonify({"error": f"Unable to resolve ISO3 code for {country}"}), 404

        # Step 2: Fetch forest area (% of land) from World Bank API for 2020 and 2022
        years = [2020, 2022]
        forest_areas = {}
        for year in years:
            url = f"https://api.worldbank.org/v2/country/{iso3_code}/indicator/AG.LND.FRST.ZS?date={year}&format=json"
            try:
                response = requests.get(url, timeout=10)
                app.logger.debug(f"World Bank API response status for {country} in {year}: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if len(data) > 1 and data[1] and isinstance(data[1], list) and data[1][0].get("value") is not None:
                        forest_area_percent = float(data[1][0]["value"])
                        if forest_area_percent > 0:
                            forest_areas[year] = forest_area_percent
                            app.logger.debug(f"Forest area for {country} in {year}: {forest_area_percent}% of land")
                        else:
                            app.logger.warning(f"Zero or invalid forest area for {country} in {year}")
                    else:
                        app.logger.warning(f"No valid forest area data for {country} in {year}: {data}")
                else:
                    app.logger.warning(f"World Bank API failed for {country} in {year}: {response.status_code} - {response.text}")
            except Exception as e:
                app.logger.warning(f"World Bank API error for {country} in {year}: {str(e)}")

        # Step 3: Calculate deforestation rate
        if len(forest_areas) == 2:
            area_start = forest_areas[2020]
            area_end = forest_areas[2022]
            deforestation_rate = ((area_start - area_end) / area_start) * 100
            deforestation_rate = min(max(deforestation_rate, 0), 100)
            app.logger.debug(f"World Bank deforestation rate for {country}: {deforestation_rate}%")
            return jsonify({
                "country": country,
                "deforestation_rate": round(deforestation_rate, 2),
                "unit": "%",
                "source": "World Bank (Forest Area % of Land)",
                "data_period": "2020-2022"
            })
        else:
            app.logger.error(f"Insufficient forest area data for {country}: {forest_areas}")
            return jsonify({"error": f"No forest area data available for {country} in 2020-2022"}), 404

    except Exception as e:
        app.logger.error(f"Error fetching deforestation data for {country}: {type(e).__name__}: {str(e)}")
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500
    
# API: Deforestation (GFW API First, Database Fallback)
# @app.route('/api/deforestations', methods=['GET'])
# def get_deforestation():
#     country = request.args.get('country', default="India")
#     if not country:
#         return jsonify({"error": "Country name is required"}), 400

#     try:
#         # Try Global Forest Watch API first
#         try:
#             # Note: GFW API may require an API key or specific region formatting
#             # Using a simplified endpoint; you may need to register for a key at https://www.globalforestwatch.org/
#             url = f"https://data-api.globalforestwatch.org/v1/query/treecoverloss?region={country}&start_year=2023&end_year=2025"
#             response = requests.get(url, timeout=10)
#             app.logger.debug(f"GFW API response status: {response.status_code}, content: {response.text}")
#             if response.status_code == 200:
#                 data = response.json()
#                 if data and 'data' in data and data['data']:
#                     # Extract total tree cover loss (hectares) and estimate rate
#                     total_loss = sum(row.get('area_ha', 0) for row in data['data'])
#                     # Simplified scaling: assume baseline forest area (hectares) for the country
#                     baseline_area = 100_000_000  # 100 million hectares (adjust per country if known)
#                     deforestation_rate = (total_loss / baseline_area) * 100 if baseline_area > 0 else 10.0
#                     deforestation_rate = min(max(deforestation_rate, 0), 100)  # Bound between 0-100%
#                     app.logger.debug(f"GFW tree cover loss for {country}: {total_loss} ha, rate: {deforestation_rate}%")
#                     return jsonify({
#                         "country": country,
#                         "deforestation_rate": round(deforestation_rate, 2),
#                         "unit": "%",
#                         "source": "Global Forest Watch (Tree Cover Loss)"
#                     })
#                 app.logger.warning(f"No valid GFW data found for {country}: {data}")
#             app.logger.warning(f"GFW API failed: {response.status_code} - {response.text}")
#         except Exception as e:
#             app.logger.warning(f"GFW API error for {country}: {str(e)}")

#         # Fallback to database
#         try:
#             conn = get_db_connection()
#             cursor = conn.cursor(dictionary=True)
#             query = """
#             SELECT deforestation_rate
#             FROM climate_data
#             WHERE LOWER(country) = LOWER(%s)
#             ORDER BY year DESC
#             LIMIT 1
#             """
#             cursor.execute(query, (country,))
#             data = cursor.fetchone()
#             cursor.close()
#             conn.close()
#             if data and data['deforestation_rate'] is not None:
#                 deforestation_rate = float(data['deforestation_rate'])
#                 app.logger.debug(f"Database deforestation rate for {country}: {deforestation_rate}%")
#                 return jsonify({
#                     "country": country,
#                     "deforestation_rate": round(deforestation_rate, 2),
#                     "unit": "%",
#                     "source": "Climate Database"
#                 })
#             app.logger.warning(f"No deforestation data found in database for {country}")
#         except Exception as e:
#             app.logger.warning(f"Database error for {country}: {str(e)}")

#         # Final static fallback
#         app.logger.debug(f"Using static fallback for {country}: 10.0%")
#         return jsonify({
#             "country": country,
#             "deforestation_rate": 10.0,
#             "unit": "%",
#             "source": "Fallback - No Data Available",
#             "error": "No data available from API or database"
#         }), 404

#     except Exception as e:
#         app.logger.error(f"Error fetching deforestation data for {country}: {type(e).__name__}: {str(e)}")
#         return jsonify({
#             "country": country,
#             "deforestation_rate": 10.0,
#             "unit": "%",
#             "source": "Fallback - Exception",
#             "error": str(e)
#         }), 500
    
# # API: NASA Deforestation Data
# @app.route('/api/nasa/deforestation', methods=['GET'])
# def get_nasa_deforestation():
#     country = request.args.get('country')
#     if not country or 'NASA_API_KEY' not in app.config or not app.config['NASA_API_KEY']:
#         app.logger.error("NASA_API_KEY is not configured or country missing")
#         return jsonify({"error": "Server configuration error: NASA API key missing or invalid country"}), 500

#     try:
#         for attempt in range(3):
#             try:
#                 location = geolocator.geocode(country, geometry='wkt')
#                 if not location:
#                     app.logger.warning(f"Geocoding returned no result for {country}")
#                     return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback"})
#                 break
#             except GeocoderTimedOut as e:
#                 app.logger.warning(f"Geocoding timeout on attempt {attempt + 1} for {country}: {e}")
#                 if attempt < 2:
#                     time.sleep(2)
#                     continue
#                 raise

#         bbox = location.raw['boundingbox']
#         south_lat, north_lat, west_lon, east_lon = map(float, bbox)
#         bounding_box = f"{south_lat},{west_lon},{north_lat},{east_lon}"
#         app.logger.debug(f"Bounding box for {country}: {bounding_box}")

#         base_url = "https://cmr.earthdata.nasa.gov/search/granules.json"
#         params = {
#             "provider": "UMD",
#             "short_name": "HLF_TCC",
#             "version": "1.9",
#             "bounding_box": bounding_box,
#             "temporal": "2020-01-01T00:00:00Z,2023-12-31T23:59:59Z",
#             "page_size": 1
#         }
#         headers = {"Authorization": f"Bearer {app.config['NASA_API_KEY']}"}
#         cmr_response = requests.get(base_url, headers=headers, params=params)

#         if cmr_response.status_code != 200:
#             app.logger.warning(f"CMR API failed for deforestation: {cmr_response.text}")
#             return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - CMR Error"})
#         if not cmr_response.json()['feed']['entry']:
#             app.logger.warning(f"No deforestation data found for {country}")
#             return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - No Data"})

#         granule = cmr_response.json()['feed']['entry'][0]
#         opendap_url = next((link['href'] for link in granule['links'] if 'opendap' in link['href']), None)
#         if not opendap_url:
#             app.logger.warning(f"No OPeNDAP URL found for {country}")
#             return jsonify({"country": country, "deforestation_rate": 10.0, "source": "Fallback - No OPeNDAP"})

#         dataset = Dataset(opendap_url + '.nc', 'r')
#         treecover_2000 = dataset.variables['treecover2000'][:]
#         loss = dataset.variables['loss'][:]
#         lat = dataset.variables['lat'][:]
#         lon = dataset.variables['lon'][:]
#         mask = (lat >= south_lat) & (lat <= north_lat) & (lon >= west_lon) & (lon <= east_lon)
#         initial_cover = treecover_2000[mask].mean() if mask.any() else treecover_2000.mean()
#         total_loss = loss[mask].mean() if mask.any() else loss.mean()
#         dataset.close()

#         deforestation_rate = (total_loss / initial_cover) * 100 if initial_cover > 0 else 10.0
#         return jsonify({"country": country, "deforestation_rate": round(deforestation_rate, 2), "source": "NASA GFC"})
#     except Exception as e:
#         app.logger.error(f"Error fetching deforestation data: {e}")
#         return jsonify({"error": str(e)}), 500

# API: Temperature Trends
# @app.route('/api/temperature', methods=['GET'])
# def get_temperature_data():
#     country = request.args.get('country', default="India")
#     connection = get_db_connection()
#     cursor = connection.cursor(dictionary=True)
#     cursor.execute("SELECT year, avg_temperature FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
#     data = cursor.fetchall()
#     cursor.close()
#     connection.close()
#     return jsonify(data)

# # API: CO2 Emissions
# @app.route('/api/co2-emissions', methods=['GET'])
# def get_co2_emissions():
#     country = request.args.get('country', default="India")
#     connection = get_db_connection()
#     cursor = connection.cursor(dictionary=True)
#     cursor.execute("SELECT year, co2_emissions FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
#     data = cursor.fetchall()
#     cursor.close()
#     connection.close()
#     return jsonify(data)

@app.route('/api/temperature', methods=['GET'])
def get_temperature_data():
    country = request.args.get('country', default="India")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT year, CAST(avg_temperature AS DECIMAL(10,2)) AS avg_temperature FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(data)

@app.route('/api/co2-emissions', methods=['GET'])
def get_co2_emissions():
    country = request.args.get('country', default="India")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT year, CAST(co2_emissions AS DECIMAL(10,2)) AS co2_emissions FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
    data = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(data)

# API: Deforestation Data
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

# API: Contact Form
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
    
    return render_template('contact.html')


# Combined GET and POST route for /contact
# @app.route('/contact', methods=['GET', 'POST'])
# def contact():
#     if request.method == 'POST':
#         try:
#             # Get form data (assuming traditional form submission)
#             name = request.form.get('name', '').strip()
#             email = request.form.get('email', '').strip()
#             mobile = request.form.get('mobile', '').strip()
#             message = request.form.get('message', '').strip()

#             # Validate inputs
#             if not all([name, email, mobile, message]):
#                 flash('All fields are required and must not be empty.', 'error')
#                 return render_template('contact.html')

#             # Send email to admin
#             admin_msg = Message(
#                 subject=f"New Contact Form Submission from {name}",
#                 recipients=[app.config['MAIL_DEFAULT_SENDER']],
#                 html=f"""
#                 <h3>New Contact Form Submission</h3>
#                 <p><strong>Name:</strong> {name}</p>
#                 <p><strong>Email:</strong> {email}</p>
#                 <p><strong>Mobile:</strong> {mobile}</p>
#                 <p><strong>Message:</strong> {message}</p>
#                 """
#             )
#             mail.send(admin_msg)

#             # Send confirmation email to user
#             confirmation_msg = Message(
#                 subject="Climate Change Dashboard - Contact Confirmation",
#                 recipients=[email],
#                 html="""
#                 <h3>Thank You for Contacting Us</h3>
#                 <p>We have received your message and will get back to you shortly.</p>
#                 """
#             )
#             mail.send(confirmation_msg)

#             flash('Your message has been sent successfully!', 'success')
#             return render_template('contact.html')

#         except smtplib.SMTPAuthenticationError as e:
#             app.logger.error(f"SMTP Authentication Error: {e}")
#             flash('Failed to authenticate with email server.', 'error')
#             return render_template('contact.html')
#         except smtplib.SMTPRecipientsRefused as e:
#             app.logger.error(f"Invalid recipient email: {e}")
#             flash('Invalid email address provided.', 'error')
#             return render_template('contact.html')
#         except smtplib.SMTPException as e:
#             app.logger.error(f"SMTP Error: {e}")
#             flash('Failed to send email due to server issue.', 'error')
#             return render_template('contact.html')
#         except Exception as e:
#             app.logger.error(f"Unexpected error: {e}")
#             flash('An unexpected error occurred.', 'error')
#             return render_template('contact.html')

#     # GET request: Render contact page
#     return render_template('contact.html')

# Load ML Models
temp_model = joblib.load("temperature_model.pkl")
co2_model = joblib.load("co2_model.pkl")
deforestation_model = joblib.load("deforestation_model.pkl")
label_encoder = joblib.load("label_encoder.pkl")

# API: Climate Prediction
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
        return jsonify({"error": str(e)}), 500

# API: Climate Simulation
@app.route('/api/predicts', methods=['POST'])
def predicts():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        temperature_change = float(data.get('temperatureChange', 0))
        co2_level = float(data.get('co2Level', 400))
        deforestation_change = float(data.get('deforestationChange', 0))

        # Simple simulation logic (enhance with real models if available)
        predict_temp = temperature_change + (co2_level / 1000)  # Temp increases with CO2
        predict_co2 = co2_level + (deforestation_change * 5)    # CO2 increases with deforestation
        predict_def = deforestation_change + (temperature_change * 0.2)  # Deforestation impacted by temp

        return jsonify({
            "predict_temperature_c": round(predict_temp, 2),
            "predict_co2_emissions_mmt": round(predict_co2, 2),
            "predict_deforestation_rate_percent": round(predict_def, 2)
        })

        
    
    except ValueError as e:
        app.logger.error(f"Input Error: {e}")
        return jsonify({"error": "Invalid input values"}), 400
    except Exception as e:
        app.logger.error(f"Simulation Error: {e}")
        return jsonify({"error": str(e)}), 500

# API: Compare Countries
@app.route('/api/compare', methods=['POST'])
def compare_countries():
    data = request.get_json()
    if not data or 'countries' not in data:
        return jsonify({"error": "Countries list is required"}), 400
    
    try:
        results = []
        for country in data['countries']:
            temp_response = requests.get(f"http://{request.host}/api/current_temperature?country={country}")
            # country_response = requests.get(f"http://{request.host}/api/country_info?country={country}")
            co2_response = requests.get(f"http://{request.host}/api/co2?country={country}")
            deforestation_response = requests.get(f"http://{request.host}/api/deforestations?country={country}")
            
            temp_data = temp_response.json()
            # country_data = country_response.json()
            co2_data = co2_response.json()
            deforestation_data = deforestation_response.json()
            
            results.append({
                "country": country,
                "temperature": temp_data.get('temperature', 0),
                "co2": co2_data.get('co2_level', 0),
                "deforestation": deforestation_data.get('deforestation_rate', 0)
            })
        
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Comparison error: {e}")
        return jsonify({"error": str(e)}), 500

# API: Export Data as CSV
@app.route('/api/export', methods=['GET'])
def export_data():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country is required"}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM climate_data WHERE country = %s ORDER BY year ASC", (country,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
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

# API: Generate Printable Report (PDF)
# @app.route('/api/generate-report', methods=['GET'])
# def generate_report():
#     country = request.args.get('country')
#     if not country:
#         return jsonify({"error": "Country is required"}), 400
    
#     try:
#         # Fetch data
#         temp_response = requests.get(f"http://{request.host}/api/current_temperature?country={country}")
#         info_response = requests.get(f"http://{request.host}/api/country_info?country={country}")
#         temp_data = temp_response.json()
#         info_data = info_response.json()

#         if temp_data.get('error') or info_data.get('error'):
#             return jsonify({"error": "Failed to fetch data"}), 500

#         # Create PDF
#         buffer = io.BytesIO()
#         doc = SimpleDocTemplate(buffer, pagesize=letter)
#         styles = getSampleStyleSheet()
#         elements = []

#         # Title
#         title = f"Climate Data Report for {country}"
#         elements.append(Paragraph(title, styles['Title']))
#         elements.append(Spacer(1, 12))

#         # Date
#         date = datetime.datetime.now().strftime("%B %d, %Y")
#         elements.append(Paragraph(f"Generated on: {date}", styles['Normal']))
#         elements.append(Spacer(1, 12))

#         # Data Table
#         data = [
#             ["Parameter", "Value"],
#             ["Temperature (°C)", str(temp_data['temperature'])],
#             ["CO2 Emissions (ppm)", str(info_data.get('co2_emissions', 'N/A'))],
#             ["Deforestation Rate (%)", str(info_data.get('deforestation_rate', 'N/A'))]
#         ]
#         table = Table(data)
#         table.setStyle(TableStyle([
#             ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#             ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#             ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#             ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#             ('FONTSIZE', (0, 0), (-1, 0), 14),
#             ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#             ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#             ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
#             ('FONTSIZE', (0, 1), (-1, -1), 12),
#             ('GRID', (0, 0), (-1, -1), 1, colors.black)
#         ]))
#         elements.append(table)
#         elements.append(Spacer(1, 12))

#         # Build PDF
#         doc.build(elements)
#         buffer.seek(0)

#         # Return PDF as response
#         response = make_response(buffer.getvalue())
#         response.headers['Content-Type'] = 'application/pdf'
#         response.headers['Content-Disposition'] = f'attachment; filename={country}_climate_report.pdf'
#         return response
#     except Exception as e:
#         app.logger.error(f"Report generation error: {e}")
#         return jsonify({"error": str(e)}), 500

@app.route('/api/generate-report', methods=['GET'])
def generate_report():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country is required"}), 400
    
    try:
        # Fetch data with fallback values
        temp_response = requests.get(f"http://{request.host}/api/current_temperature?country={country}", timeout=5)
        co2_response = requests.get(f"http://{request.host}/api/co2?country={country}", timeout=5)
        deforestation_response = requests.get(f"http://{request.host}/api/deforestations?country={country}", timeout=5)
        # info_response = requests.get(f"http://{request.host}/api/country_info?country={country}", timeout=5)
        
        temp_data = temp_response.json()
        # info_data = info_response.json()
        co2_data = co2_response.json()
        deforestation_data = deforestation_response.json()

        # Use fallback data if API calls fail
        temperature = float(temp_data.get('temperature', 25)) if not temp_data.get('error') else 25.0
        co2_emissions = float(co2_data.get('co2_level', 415)) if not co2_data.get('error') else 415.0
        deforestation_rate = float(deforestation_data .get('deforestation_rate', 10)) if not deforestation_data .get('error') else 10.0

        # Fetch trends for additional context
        temp_trends = requests.get(f"http://{request.host}/api/temperature?country={country}", timeout=5).json()
        co2_trends = requests.get(f"http://{request.host}/api/co2-emissions?country={country}", timeout=5).json()

        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title and header
        title_style = styles['Title']
        title_style.textColor = colors.HexColor('#2c3e50')
        elements.append(Paragraph(f"<b>Climate Change Report: {country}</b>", title_style))
        elements.append(Spacer(1, 12))
        
        # Report metadata
        date_str = datetime.datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"Generated: {date_str}", styles['Normal']))
        elements.append(Spacer(1, 24))

        # Current Data Section
        elements.append(Paragraph("<b>Current Climate Data</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))

        current_data = [
            ["Parameter", "Value"],
            ["Temperature", f"{temperature} °C"],
            ["CO₂ Emissions", f"{co2_emissions} ppm"],
            ["Deforestation Rate", f"{deforestation_rate}%"]
        ]
        
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
        ])
        
        data_table = Table(current_data)
        data_table.setStyle(table_style)
        elements.append(data_table)
        elements.append(Spacer(1, 24))

        # Trends Section (with type conversion)
        elements.append(Paragraph("<b>Historical Trends</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))

        if temp_trends and len(temp_trends) > 0:
            latest_temp = float(temp_trends[-1].get('avg_temperature', temperature))
            oldest_temp = float(temp_trends[0].get('avg_temperature', temperature))
            temp_change = latest_temp - oldest_temp
            elements.append(Paragraph(f"Temperature change: {temp_change:.2f}°C ({oldest_temp}°C → {latest_temp}°C)", styles['Normal']))

        if co2_trends and len(co2_trends) > 0:
            latest_co2 = float(co2_trends[-1].get('co2_emissions', co2_emissions))
            oldest_co2 = float(co2_trends[0].get('co2_emissions', co2_emissions))
            co2_change = latest_co2 - oldest_co2
            elements.append(Paragraph(f"CO₂ change: {co2_change:.2f} ppm ({oldest_co2} ppm → {latest_co2} ppm)", styles['Normal']))

        elements.append(Spacer(1, 24))

        # Footer
        elements.append(Paragraph("<i>Generated by Climate Change Dashboard - Data may include fallbacks if unavailable</i>", styles['Italic']))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Return PDF as response
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={country}_climate_report.pdf'
        return response
        
    except Exception as e:
        app.logger.error(f"Report generation error: {e}")
        return jsonify({"error": str(e)}), 500
        

if __name__ == '__main__':
    app.run(debug=True)
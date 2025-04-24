from flask import Flask, request, jsonify, render_template, make_response
from flask_mail import Mail, Message
import logging
import smtplib
import mysql.connector
import requests
from geopy.geocoders import Nominatim
from flask_cors import CORS
import joblib
import numpy as np
from sklearn.preprocessing import LabelEncoder
from geopy.exc import GeocoderTimedOut
import time
import io
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import datetime
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import t
import json
import geopandas as gpd
import earthaccess
import rasterio
from rasterio.mask import mask
import os
from groq import Groq
import re
import pandas as pd


# Logging configuration
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app)

# Configuration
app.config['OPENWEATHER_API_KEY'] = '5746fff655c4e51b21de34dde51d8f20'
app.config['NASA_API_KEY'] = '7gjMCvSavwY9XQfZwUUK5TyQnCWTmAWyfDzNtoMf'
app.config['EARTHDATA_TOKEN'] = 'eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImFzaGExMjMiLCJleHAiOjE3NDgyNTkwNTcsImlhdCI6MTc0MzA3NTA1NywiaXNzIjoiaHR0cHM6Ly91cnMuZWFydGhkYXRhLm5hc2EuZ292IiwiaWRlbnRpdHlfcHJvdmlkZXIiOiJlZGxfb3BzIiwiYWNyIjoiZWRsIiwiYXNzdXJhbmNlX2xldmVsIjozfQ.CSCexI9IeYLu5uIw3rZwHUrx5t67pACiu8SxpVkxjuSLQDXbiTK_wEJmKaeBmpwnyovRRe_FIP1KBSXZP-aR6N2sKXWEa2ROtHSpv7YToGn9rD6OZTbbWXUYhwaPN_Df_gH0YkllA8m4qtx0AG34febCByiD7PCX9MLKa2WSkCrB8R1qJ4AWhPsz8PTN_6NQUz7YlmjQbUavfZf9JEDGiJme8dHtN2gSC1DGQ1r36AN61RQPd7SUOxbCV6RULNF78cv13P8LYmhjVrWAVLk7m1i3-58_5vyDDZok4XXSHKfYCXqEEScUL0jdVmWEUquYhhHbwrC_eTPpEAEDVZl1_w'  # Replace with the copied token
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '21svdc2079@svdegreecollege.ac.in'
app.config['MAIL_PASSWORD'] = 'bcjcejkokwxbjkpl'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
app.config['GFW_API_TOKEN'] = 'your-gfw-api-token'  # Replace with actual Global Forest Watch API token
app.config['GROQ_API_KEY'] = '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'

# Initialize Groq client
client = Groq(api_key=app.config['GROQ_API_KEY'])

mail = Mail(app)
geolocator = Nominatim(user_agent="climate_dashboard", timeout=10)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
app.logger = logging.getLogger('climate')

# Load models (ensure these are loaded at app startup)
try:
    temp_model = joblib.load("temperature_model.pkl")
    co2_model = joblib.load("co2_model.pkl")
    deforestation_model = joblib.load("deforestation_model.pkl")
    label_encoder = joblib.load("label_encoder.pkl")
except FileNotFoundError as e:
    app.logger.error(f"Model file missing: {e}")
    raise Exception("Machine learning models not found.")

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='9949237758',
        database='climate_db'
    )

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Validate Groq API key
        if not app.config['GROQ_API_KEY']:
            app.logger.error("Groq API Key is not configured")
            return jsonify({'error': "Groq API Key is not configured. Set GROQ_API_KEY environment variable."}), 500

        # Send message to Groq
        completion = client.chat.completions.create(
            model="llama3-8b-8192",  # Correct model name
            messages=[
                {"role": "system", "content": "You are a helpful climate assistant specializing in deforestation and environmental data."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.6,
            max_tokens=4096,
            top_p=0.95,
            stream=False
        )

        # Get and clean reply
        raw_reply = completion.choices[0].message.content
        clean_reply = re.sub(r'<think>.*?</think>', '', raw_reply, flags=re.DOTALL).strip()

        return jsonify({'reply': clean_reply})
    except Exception as e:
        app.logger.error(f"Groq Error: {str(e)}")
        return jsonify({'error': f"Chat failed: {str(e)}"}), 500
    
@app.route("/")
def index():
    return render_template("index.html")

# Existing /api/chat endpoint unchanged

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
# Configure logging
app.logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
app.logger.addHandler(handler)

@app.route('/api/current_temperature', methods=['GET'])
def get_current_temperature():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country name is required"}), 400

    try:
        # Step 1: Get capital city using REST Countries API
        capital = None
        for attempt in range(3):
            try:
                url = f"https://restcountries.com/v3.1/name/{country}?fullText=true"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        capital = data[0].get("capital", [None])[0]  # Capital is a list in API response
                        break
                    else:
                        break
                elif response.status_code == 502:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    break
                else:
                    break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                break

        if not capital:
            app.logger.error(f"Unable to resolve capital city for {country}")
            return jsonify({"error": f"Unable to resolve capital city for {country}"}), 404

        # Step 2: Fetch temperature for capital city using OpenWeatherMap API
        api_key = app.config['OPENWEATHER_API_KEY']
        url = f"http://api.openweathermap.org/data/2.5/weather?q={capital}&appid={api_key}&units=metric"
        response = requests.get(url)
        if response.status_code != 200:
            app.logger.warning(f"OpenWeatherMap API failed for {capital}: {response.status_code}")
            return jsonify({"error": f"Failed to fetch weather data for {capital}"}), 500

        weather_data = response.json()
        temp = weather_data['main']['temp']
        if temp < -50 or temp > 60:
            app.logger.warning(f"Implausible temperature {temp}°C for {capital}, country: {country}")
            temp = 25 if country.lower() == 'india' else 15

        return jsonify({
            "country": country,
            "capital": capital,
            "temperature": temp,
            "details": weather_data
        })

    except Exception as e:
        app.logger.error(f"Error fetching temperature for {country}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/co2', methods=['GET'])
def get_co2():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country name is required"}), 400

    try:
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
        try:
            url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&hourly=carbon_monoxide"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                co_data = data.get('hourly', {}).get('carbon_monoxide', [])
                co_level = None
                for value in co_data[::-1]:
                    if value is not None:
                        co_level = value
                        break
                if co_level is not None and co_level >= 0:
                    co2_level = 415.0 + (co_level / 1000.0)
                    if 300 <= co2_level <= 500:
                        return jsonify({
                            "country": country,
                            "co2_level": round(co2_level, 2),
                            "unit": "ppm",
                            "source": "Open-Meteo Air Quality (CO-based)"
                        })
                else:
                    app.logger.warning(f"No valid CO data from Open-Meteo for {country}")
            else:
                app.logger.warning(f"Open-Meteo API failed: {response.status_code}")
        except Exception as e:
            app.logger.warning(f"Open-Meteo error: {str(e)}")

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
                if 300 <= co2_level <= 500:
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

        return jsonify({
            "country": country,
            "co2_level": 415.0,
            "unit": "ppm",
            "source": "Fallback - All Sources Failed"
        })
    except Exception as e:
        app.logger.error(f"Error fetching CO2 data for {country}: {type(e).__name__}: {str(e)}")
        return jsonify({"country": country, "co2_level": 415.0, "source": "Fallback - Exception", "unit": "ppm"}), 500

@app.route('/api/deforestations', methods=['GET'])
def get_deforestation():
    country = request.args.get('country', default="India")
    if not country:
        return jsonify({"error": "Country name is required"}), 400

    try:
        iso3_code = None
        for attempt in range(3):
            try:
                url = f"https://restcountries.com/v3.1/name/{country}?fullText=true"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        iso3_code = data[0]["cca3"]
                        break
                    else:
                        break
                elif response.status_code == 502:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    break
                else:
                    break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                break

        if not iso3_code:
            app.logger.error(f"Unable to resolve ISO3 code for {country}")
            return jsonify({"error": f"Unable to resolve ISO3 code for {country}"}), 404

        years = [2020, 2022]
        forest_areas = {}
        for year in years:
            url = f"https://api.worldbank.org/v2/country/{iso3_code}/indicator/AG.LND.FRST.ZS?date={year}&format=json"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if len(data) > 1 and data[1] and isinstance(data[1], list) and data[1][0].get("value") is not None:
                        forest_area_percent = float(data[1][0]["value"])
                        if forest_area_percent > 0:
                            forest_areas[year] = forest_area_percent
                    else:
                        app.logger.warning(f"No valid forest area data for {country} in {year}")
                else:
                    app.logger.warning(f"World Bank API failed for {country} in {year}: {response.status_code}")
            except Exception as e:
                app.logger.warning(f"World Bank API error for {country} in {year}: {str(e)}")

        if len(forest_areas) == 2:
            area_start = forest_areas[2020]
            area_end = forest_areas[2022]
            deforestation_rate = ((area_start - area_end) / area_start) * 100
            deforestation_rate = min(max(deforestation_rate, 0), 100)
            return jsonify({
                "country": country,
                "deforestation_rate": round(deforestation_rate, 2),
                "unit": "%",
                "source": "World Bank (Forest Area % of Land)",
                "data_period": "2020-2022"
            })
        else:
            return jsonify({"error": f"No forest area data available for {country} in 2020-2022"}), 404
    except Exception as e:
        app.logger.error(f"Error fetching deforestation data for {country}: {type(e).__name__}: {str(e)}")
        return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500

# Configure logging
app.logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
app.logger.addHandler(handler)

# @app.route('/api/deforestations', methods=['GET'])
# def get_deforestation():
#     country = request.args.get('country', default="India")
#     if not country:
#         return jsonify({"error": "Country name is required"}), 400

#     try:
#         # Validate Earthdata token
#         if not app.config['EARTHDATA_TOKEN']:
#             app.logger.error("Earthdata Bearer Token is not configured")
#             return jsonify({"error": "Earthdata Bearer Token is not configured. Set EARTHDATA_TOKEN environment variable."}), 500

#         app.logger.debug(f"Earthdata Token: {app.config['EARTHDATA_TOKEN'][:10]}...")

#         # Step 1: Resolve ISO3 code and bounding box
#         iso3_code = None
#         bbox = None
#         for attempt in range(3):
#             try:
#                 url = f"https://restcountries.com/v3.1/name/{country}?fullText=true"
#                 response = requests.get(url, timeout=10)
#                 if response.status_code == 200:
#                     data = response.json()
#                     if data and isinstance(data, list) and len(data) > 0:
#                         iso3_code = data[0]["cca3"]
#                         latlng = data[0].get("latlng", [0, 0])
#                         # Use broader bbox for India
#                         if country.lower() == "india":
#                             bbox = [66.0, 6.0, 89.0, 36.0]  # India's approximate extent
#                         else:
#                             bbox = [
#                                 latlng[1] - 5,
#                                 latlng[0] - 5,
#                                 latlng[1] + 5,
#                                 latlng[0] + 5
#                             ]
#                         break
#                     else:
#                         break
#                 elif response.status_code == 502:
#                     if attempt < 2:
#                         time.sleep(2 ** attempt)
#                         continue
#                     break
#                 else:
#                     break
#             except Exception as e:
#                 if attempt < 2:
#                     time.sleep(2 ** attempt)
#                     continue
#                 break

#         if not iso3_code or not bbox:
#             app.logger.error(f"Unable to resolve ISO3 code or bounding box for {country}")
#             return jsonify({"error": f"Unable to resolve ISO3 code or bounding box for {country}"}), 404

#         # Step 2: Query CMR API for Hansen GFC granules
#         years = [2020, 2022]
#         forest_loss = {2020: 0, 2022: 0}
#         try:
#             cmr_url = "https://cmr.earthdata.nasa.gov/search/granules.json"
#             params = {
#                 "short_name": "HANSEN_GFC",
#                 "temporal": "2020-01-01T00:00:00Z,2022-12-31T23:59:59Z",
#                 "bounding_box": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
#                 "page_size": 50  # Increased for better coverage
#             }
#             headers = {
#                 "Authorization": f"Bearer {app.config['EARTHDATA_TOKEN'].strip()}",
#                 "Accept": "application/json"
#             }
#             app.logger.debug(f"CMR Request: {cmr_url}, Params: {params}, Headers: Authorization: Bearer {app.config['EARTHDATA_TOKEN'][:10]}...")
#             response = requests.get(cmr_url, params=params, headers=headers, timeout=60)
#             if response.status_code == 401:
#                 app.logger.error(f"CMR Authentication failed for {country}: {response.status_code} - {response.text}")
#                 return jsonify({"error": "Invalid or unauthorized Earthdata Bearer Token. Please verify your token and account permissions."}), 500
#             if response.status_code != 200:
#                 app.logger.warning(f"CMR API failed for {country}: {response.status_code} - {response.text}")
#                 return jsonify({"error": f"Failed to query NASA Earthdata CMR: {response.status_code} - {response.text}"}), 500

#             cmr_data = response.json()
#             granules = cmr_data.get("feed", {}).get("entry", [])
#             if not granules:
#                 app.logger.warning(f"No Hansen GFC granules found for {country} in 2020-2022")
#                 return jsonify({"error": f"No forest loss data available for {country} in 2020-2022"}), 404

#             # Step 3: Download and process granules
#             data_dir = os.path.join(os.path.dirname(__file__), "data")
#             os.makedirs(data_dir, exist_ok=True)
#             for granule in granules:  # Process all granules for complete coverage
#                 try:
#                     download_url = None
#                     for link in granule.get("links", []):
#                         if link.get("rel") == "http://esipfed.org/ns/fedsearch/1.1/data#" and link.get("href") and "lossyear" in link["href"].lower():
#                             download_url = link["href"]
#                             break
#                     if not download_url:
#                         app.logger.warning(f"No valid lossyear download URL for granule {granule['id']}")
#                         continue

#                     app.logger.debug(f"Downloading granule: {download_url}")
#                     response = requests.get(download_url, headers=headers, stream=True, timeout=15)
#                     if response.status_code != 200:
#                         app.logger.warning(f"Failed to download granule {granule['id']}: {response.status_code} - {response.text}")
#                         continue

#                     data_file = os.path.join(data_dir, f"{granule['id']}.tif")
#                     with open(data_file, "wb") as f:
#                         for chunk in response.iter_content(chunk_size=8192):
#                             f.write(chunk)

#                     # Step 4: Process raster data
#                     with rasterio.open(data_file) as src:
#                         country_shape = {
#                             "type": "Polygon",
#                             "coordinates": [[
#                                 [bbox[0], bbox[1]],
#                                 [bbox[0], bbox[3]],
#                                 [bbox[2], bbox[3]],
#                                 [bbox[2], bbox[1]],
#                                 [bbox[0], bbox[1]]
#                             ]]
#                         }
#                         out_image, out_transform = mask(src, [country_shape], crop=True)
#                         out_image = out_image[0]

#                         pixel_area_ha = (30 * 30) / 10000  # 30m resolution to hectares
#                         for year in years:
#                             loss_year_value = year - 2000
#                             loss_pixels = np.sum(out_image == loss_year_value)
#                             forest_loss[year] += loss_pixels * pixel_area_ha  # Aggregate across granules

#                     os.remove(data_file)

#                 except Exception as e:
#                     app.logger.warning(f"Error processing granule {granule.get('id', 'unknown')} for {country}: {str(e)}")
#                     continue

#         except Exception as e:
#             app.logger.error(f"Error querying NASA Earthdata for {country}: {str(e)}")
#             return jsonify({"error": f"Failed to query NASA Earthdata: {str(e)}"}), 500

#         # Step 5: Calculate deforestation rate
#         if forest_loss[2020] > 0 or forest_loss[2022] > 0:
#             # Simplified initial cover estimate (ideally use treecover2000)
#             initial_cover = max(forest_loss[2020] + forest_loss[2022], 1000)
#             total_loss = forest_loss[2022] - forest_loss[2020]
#             deforestation_rate = (total_loss / initial_cover) * 100
#             deforestation_rate = min(max(deforestation_rate, 0), 100)
#             return jsonify({
#                 "country": country,
#                 "deforestation_rate": round(deforestation_rate, 2),
#                 "unit": "%",
#                 "source": "NASA Earthdata (Hansen Global Forest Change)",
#                 "data_period": "2020-2022"
#             })
#         else:
#             app.logger.warning(f"No valid forest loss data for {country} in 2020-2022")
#             return jsonify({"error": f"No forest loss data available for {country} in 2020-2022"}), 404

#     except Exception as e:
#         app.logger.error(f"Error fetching deforestation data for {country}: {type(e).__name__}: {str(e)}")
#         return jsonify({"error": f"Failed to fetch data: {str(e)}"}), 500
    
# @app.route('/api/deforestation-hotspots', methods=['GET'])
# def get_deforestation_hotspots():
#     country = request.args.get('country', default="India")
#     if not country:
#         return jsonify({"error": "Country name is required"}), 400

#     try:
#         # Step 1: Resolve ISO3 code
#         iso3_code = None
#         for attempt in range(3):
#             try:
#                 url = f"https://restcountries.com/v3.1/name/{country}?fullText=true"
#                 response = requests.get(url, timeout=10)
#                 if response.status_code == 200:
#                     data = response.json()
#                     if data and isinstance(data, list) and len(data) > 0:
#                         iso3_code = data[0]["cca3"]
#                         break
#                     else:
#                         break
#                 elif response.status_code == 502:
#                     if attempt < 2:
#                         time.sleep(2 ** attempt)
#                         continue
#                     break
#                 else:
#                     break
#             except Exception as e:
#                 if attempt < 2:
#                     time.sleep(2 ** attempt)
#                     continue
#                 break

#         if not iso3_code:
#             app.logger.error(f"Unable to resolve ISO3 code for {country}")
#             return jsonify({"error": f"Unable to resolve ISO3 code for {country}"}), 404

#         # Step 2: Load and filter tree cover loss data from local file
#         try:
#             # Assume GeoJSON file is named after the country or ISO3 code
#             data_file = f"data/{iso3_code.lower()}_treecover_loss.geojson"
#             gdf = gpd.read_file(data_file)

#             # Filter data for 2020–2023 and required fields
#             gdf = gdf[(gdf['year'] >= 2020) & (gdf['year'] <= 2023)]
#             if gdf.empty:
#                 app.logger.warning(f"No deforestation data for {country} in 2020–2023")

#             # Convert to GeoJSON FeatureCollection
#             hotspots = {
#                 "type": "FeatureCollection",
#                 "features": []
#             }

#             for _, row in gdf.iterrows():
#                 # Extract coordinates from geometry (assume point data)
#                 if row.geometry.geom_type == "Point":
#                     coords = [row.geometry.x, row.geometry.y]
#                     geometry = {"type": "Point", "coordinates": coords}
#                 else:
#                     # For polygons, use centroid as point for scatter plot
#                     centroid = row.geometry.centroid
#                     coords = [centroid.x, centroid.y]
#                     geometry = {"type": "Point", "coordinates": coords}

#                 feature = {
#                     "type": "Feature",
#                     "geometry": geometry,
#                     "properties": {
#                         "area_ha": row.get("area_ha", 1000),  # Default if missing
#                         "loss_year": int(row["year"])
#                     }
#                 }
#                 hotspots["features"].append(feature)

#             if not hotspots["features"]:
#                 app.logger.warning(f"No valid features for {country}")

#         except FileNotFoundError:
#             app.logger.warning(f"Data file not found for {country}")
#             # Fallback: Mock data
#             hotspots = {
#                 "type": "FeatureCollection",
#                 "features": [
#                     {
#                         "type": "Feature",
#                         "geometry": {
#                             "type": "Point",
#                             "coordinates": [78.9629, 20.5937]  # India centroid
#                         },
#                         "properties": {
#                             "area_ha": 1000,
#                             "loss_year": 2023
#                         }
#                     },
#                     {
#                         "type": "Feature",
#                         "geometry": {
#                             "type": "Point",
#                             "coordinates": [77.9629, 19.5937]
#                         },
#                         "properties": {
#                             "area_ha": 800,
#                             "loss_year": 2022
#                         }
#                     }
#                 ]
#             }
#         except Exception as e:
#             app.logger.error(f"Error processing data: {str(e)}")
#             hotspots = {
#                 "type": "FeatureCollection",
#                 "features": []
#             }

#         return jsonify({"hotspots": hotspots})

#     except Exception as e:
#         app.logger.error(f"Error fetching deforestation hotspots: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# @app.route('/api/deforestation-hotspots', methods=['GET'])
# def get_deforestation_hotspots():
#     country = request.args.get('country', default="India")
#     if not country:
#         return jsonify({"error": "Country name is required"}), 400

#     try:
#         iso3_code = None
#         for attempt in range(3):
#             try:
#                 url = f"https://restcountries.com/v3.1/name/{country}?fullText=true"
#                 response = requests.get(url, timeout=10)
#                 if response.status_code == 200:
#                     data = response.json()
#                     if data and isinstance(data, list) and len(data) > 0:
#                         iso3_code = data[0]["cca3"]
#                         break
#                     else:
#                         break
#                 elif response.status_code == 502:
#                     if attempt < 2:
#                         time.sleep(2 ** attempt)
#                         continue
#                     break
#                 else:
#                     break
#             except Exception as e:
#                 if attempt < 2:
#                     time.sleep(2 ** attempt)
#                     continue
#                 break

#         if not iso3_code:
#             return jsonify({"error": f"Unable to resolve ISO3 code for {country}"}), 404

#         # Simulated Global Forest Watch API call (replace with actual API)
#         # Note: Requires GFW API token and proper endpoint 
#         try:
#             url = f"https://data-api.globalforestwatch.org/v2/datasets/treecover_loss?geostore_id={iso3_code}&start_year=2020&end_year=2023"
#             headers = {"Authorization": f"Bearer {app.config['GFW_API_TOKEN']}"}
#             response = requests.get(url, headers=headers, timeout=10)
#             if response.status_code == 200:
#                 data = response.json()
#                 hotspots = {
#                     "type": "FeatureCollection",
#                     "features": [
#                         {
#                             "type": "Feature",
#                             "geometry": {
#                                 "type": "Polygon",
#                                 "coordinates": [[[d["lon"], d["lat"]] for d in row["geometry"]]]
#                             },
#                             "properties": {
#                                 "area_ha": row["area_ha"],
#                                 "loss_year": row["year"]
#                             }
#                         } for row in data.get("data", [])
#                     ]
#                 }
#                 return jsonify({"hotspots": hotspots})
#             else:
#                 app.logger.warning(f"GFW API failed: {response.status_code}")
#         except Exception as e:
#             app.logger.warning(f"GFW API error: {str(e)}")

#         # Fallback: Mock hotspots data
#         hotspots = {
#             "type": "FeatureCollection",
#             "features": [
#                 {
#                     "type": "Feature",
#                     "geometry": {
#                         "type": "Polygon",
#                         "coordinates": [[[-60, -10], [-59, -10], [-59, -9], [-60, -9], [-60, -10]]]
#                     },
#                     "properties": {
#                         "area_ha": 1000,
#                         "loss_year": 2023
#                     }
#                 }
#             ]
#         }
#         return jsonify({"hotspots": hotspots})
#     except Exception as e:
#         app.logger.error(f"Error fetching deforestation hotspots: {str(e)}")
#         return jsonify({"error": str(e)}), 500

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

# Setup logging
logging.basicConfig(level=logging.DEBUG)
app.logger = logging.getLogger('climate')

# Load models
try:
    temp_model = joblib.load("temperature_model.pkl")
    co2_model = joblib.load("co2_model.pkl")
    deforestation_model = joblib.load("deforestation_model.pkl")
    label_encoder = joblib.load("label_encoder.pkl")
except FileNotFoundError as e:
    app.logger.error(f"Model file missing: {e}")
    raise Exception("Machine learning models not found.")

# Load the pre-trained models and label encoder at startup
try:
    temp_model = joblib.load('temperature_model.pkl')
    co2_model = joblib.load('co2_model.pkl')
    deforestation_model = joblib.load('deforestation_model.pkl')
    label_encoder = joblib.load('label_encoder.pkl')
except Exception as e:
    print(f"Error loading models or encoder: {str(e)}")
    temp_model = co2_model = deforestation_model = label_encoder = None

# @app.route('/api/predicts', methods=['POST'])
# def predicts():
#     try:
#         # Check if models and encoder are loaded
#         if any(model is None for model in [temp_model, co2_model, deforestation_model, label_encoder]):
#             return jsonify({"error": "Machine learning models or encoder not loaded"}), 500

#         # Get JSON data from request
#         data = request.get_json()
#         if not data:
#             return jsonify({"error": "No data provided"}), 400

#         # Extract and validate inputs
#         temperature_change = float(data.get('temperatureChange', 0))
#         co2_level = float(data.get('co2Level', 400))
#         deforestation_change = float(data.get('deforestationChange', 0))
#         country = data.get('country', 'Global')  # Default to Global
#         year = int(data.get('year', 2025))  # Default to 2025

#         # Input validation
#         if temperature_change < -10 or temperature_change > 10:
#             return jsonify({"error": "Temperature change must be between -10 and 10°C"}), 400
#         if co2_level < 300 or co2_level > 600:
#             return jsonify({"error": "CO₂ level must be between 300 and 600 ppm"}), 400
#         if deforestation_change < -50 or deforestation_change > 50:
#             return jsonify({"error": "Deforestation change must be between -50 and 50%"}), 400
#         if year < 2020 or year > 2100:
#             return jsonify({"error": "Year must be between 2020 and 2100"}), 400

#         # Convert country to encoded value
#         try:
#             country_encoded = label_encoder.transform([country])[0]
#         except ValueError:
#             return jsonify({"error": f"Country '{country}' not found in dataset"}), 400

#         # Prepare input for models: [Country_Encoded, Year]
#         input_data = np.array([[country_encoded, year]])

#         # Make baseline predictions
#         try:
#             baseline_temp = temp_model.predict(input_data)[0]
#             baseline_co2 = co2_model.predict(input_data)[0]
#             baseline_deforestation = deforestation_model.predict(input_data)[0]
#         except Exception as e:
#             return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

#         # Apply user adjustments
#         predicted = {
#             "predict_temperature_c": round(baseline_temp + temperature_change, 2),
#             "predict_co2_emissions_mmt": round(baseline_co2 + co2_level, 2),  # Use user-specified CO2 level directly
#             "predict_deforestation_rate_percent": round(baseline_deforestation + deforestation_change, 2)
#         }

#         return jsonify(predicted), 200

#     except (ValueError, TypeError):
#         return jsonify({"error": "Invalid input format"}), 400
#     except Exception as e:
#         return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/countries', methods=['GET'])
def get_countries():
    try:
        if label_encoder is None:
            return jsonify({"error": "Label encoder not loaded"}), 500
        countries = label_encoder.classes_.tolist()
        return jsonify({"countries": countries}), 200
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/compare', methods=['POST'])
def compare_countries():
    data = request.get_json()
    if not data or 'countries' not in data:
        return jsonify({"error": "Countries list is required"}), 400
    
    try:
        results = []
        for country in data['countries']:
            temp_response = requests.get(f"http://{request.host}/api/current_temperature?country={country}")
            co2_response = requests.get(f"http://{request.host}/api/co2?country={country}")
            deforestation_response = requests.get(f"http://{request.host}/api/deforestations?country={country}")
            
            temp_data = temp_response.json()
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

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, NextPageTemplate, PageBreak
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import matplotlib.pyplot as plt
import datetime

@app.route('/api/generate-report', methods=['GET'])
def generate_report():
    country = request.args.get('country')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not country and not (lat and lon):
        return jsonify({"error": "Country or coordinates are required"}), 400
    
    try:
        if lat and lon:
            location = geolocator.reverse((float(lat), float(lon)), timeout=10)
            country = location.raw['address']['country'] if location else country or "Unknown"

        # Initialize styles
        styles = getSampleStyleSheet()

        # Register custom fonts
        font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        regular_font_path = os.path.join(font_dir, 'Roboto-Regular.ttf')
        bold_font_path = os.path.join(font_dir, 'Roboto-Bold.ttf')

        if os.path.exists(regular_font_path) and os.path.exists(bold_font_path):
            pdfmetrics.registerFont(TTFont('Roboto', regular_font_path))
            pdfmetrics.registerFont(TTFont('Roboto-Bold', bold_font_path))
            styles['Title'].fontName = 'Roboto-Bold'
            styles['Title'].fontSize = 20
            styles['Title'].textColor = colors.HexColor('#2ecc71')
            styles['Heading2'].fontName = 'Roboto-Bold'
            styles['Heading2'].fontSize = 14
            styles['Normal'].fontName = 'Roboto'
            styles['Normal'].fontSize = 10
            styles['Italic'].fontName = 'Roboto'
            styles['Italic'].fontSize = 9
        else:
            # Fallback to default fonts
            styles['Title'].fontName = 'Helvetica-Bold'
            styles['Title'].fontSize = 20
            styles['Title'].textColor = colors.HexColor('#2ecc71')
            styles['Heading2'].fontName = 'Helvetica-Bold'
            styles['Heading2'].fontSize = 14
            styles['Normal'].fontName = 'Helvetica'
            styles['Normal'].fontSize = 10
            styles['Italic'].fontName = 'Helvetica-Oblique'
            styles['Italic'].fontSize = 9
            app.logger.warning("Roboto fonts not found; using Helvetica fallback")

        # Helper function for robust HTTP requests
        def make_request(url):
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
            session.mount('http://', HTTPAdapter(max_retries=retries))
            return session.get(url, timeout=10)

        # Fetch data
        temp_response = make_request(f"http://localhost:5000/api/current_temperature?country={country}")
        co2_response = make_request(f"http://localhost:5000/api/co2?country={country}")
        deforestation_response = make_request(f"http://localhost:5000/api/deforestations?country={country}")
        
        temp_data = temp_response.json()
        co2_data = co2_response.json()
        deforestation_data = deforestation_response.json()

        # Validate and convert data
        temperature = float(temp_data.get('temperature', 25)) if not temp_data.get('error') else 25.0
        co2_emissions = float(co2_data.get('co2_level', 415)) if not co2_data.get('error') else 415.0
        deforestation_rate = float(deforestation_data.get('deforestation_rate', 10)) if not deforestation_data.get('error') else 10.0

        temp_trends = make_request(f"http://localhost:5000/api/temperature?country={country}").json()
        co2_trends = make_request(f"http://localhost:5000/api/co2-emissions?country={country}").json()
        temp_trends = temp_trends if isinstance(temp_trends, list) else []
        co2_trends = co2_trends if isinstance(co2_trends, list) else []

        # Generate trend plots
        def create_trend_plot(data, x_key, y_key, title, ylabel):
            if not data or len(data) < 2:
                return None
            years = [int(item[x_key]) for item in data]
            values = [float(item[y_key]) for item in data]
            
            plt.figure(figsize=(4, 2))
            plt.plot(years, values, marker='o', color='#3498db', linewidth=2)
            plt.title(title, fontsize=10, pad=10)
            plt.xlabel('Year', fontsize=8)
            plt.ylabel(ylabel, fontsize=8)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150)
            plt.close()
            buffer.seek(0)
            return buffer

        temp_plot = create_trend_plot(temp_trends, 'year', 'avg_temperature', 'Temperature Trend', 'Temperature (°C)')
        co2_plot = create_trend_plot(co2_trends, 'year', 'co2_emissions', 'CO₂ Emissions Trend', 'CO₂ (ppm)')

        # Generate PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Cover page
        logo_path = os.path.join('static', 'logo.png')
        def build_cover_page():
            cover_elements = []
            cover_elements.append(Spacer(1, 100))
            cover_elements.append(Paragraph("Climate Change Dashboard", styles['Title']))
            cover_elements.append(Spacer(1, 24))
            cover_elements.append(Paragraph(f"Environmental Report for {country}", styles['Heading2']))
            cover_elements.append(Spacer(1, 12))
            cover_elements.append(Paragraph(f"Generated on {datetime.datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            cover_elements.append(Spacer(1, 24))
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=150, height=75)
                logo.hAlign = 'CENTER'
                cover_elements.append(logo)
            return cover_elements

        elements.extend(build_cover_page())
        elements.append(PageBreak())

        # Main content
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=100, height=50)
            logo.hAlign = 'LEFT'
            elements.append(logo)
            elements.append(Spacer(1, 12))

        elements.append(Paragraph(f"<b>Climate Change Report: {country}</b>", styles['Title']))
        elements.append(Spacer(1, 12))
        
        date_str = datetime.datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"Generated: {date_str}", styles['Normal']))
        elements.append(Spacer(1, 24))

        if lat and lon:
            elements.append(Paragraph(f"Location: Lat {lat}, Lon {lon}", styles['Normal']))
            elements.append(Spacer(1, 12))

        elements.append(Paragraph("<b>Current Climate Data</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))

        current_data = [
            ["Parameter", "Value"],
            ["Temperature", f"{temperature} °C"],
            ["CO₂ Emissions", f"{co2_emissions} ppm"],
            ["Deforestation Rate", f"{deforestation_rate} %"]
        ]
        
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold' if os.path.exists(bold_font_path) else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f6fa')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#dfe4ea')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('FONTNAME', (0, 1), (-1, -1), 'Roboto' if os.path.exists(regular_font_path) else 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])
        
        data_table = Table(current_data)
        data_table.setStyle(table_style)
        elements.append(data_table)
        elements.append(Spacer(1, 24))

        elements.append(Paragraph("<b>Historical Trends</b>", styles['Heading2']))
        elements.append(Spacer(1, 12))

        if temp_plot:
            elements.append(Image(temp_plot, width=300, height=150))
            elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("Temperature trend data unavailable", styles['Italic']))
            elements.append(Spacer(1, 12))

        if co2_plot:
            elements.append(Image(co2_plot, width=300, height=150))
            elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("CO₂ trend data unavailable", styles['Italic']))
            elements.append(Spacer(1, 12))

        prediction_response = make_request(f"http://localhost:5000/api/predict?country={country}&year=2030")
        prediction_data = prediction_response.json()
        if not prediction_data.get('error'):
            elements.append(Paragraph("<b>2030 Climate Prediction</b>", styles['Heading2']))
            elements.append(Spacer(1, 12))
            prediction_table = Table([
                ["Parameter", "Prediction"],
                ["Temperature", f"{prediction_data['predicted_temperature_c']} °C"],
                ["CO₂ Emissions", f"{prediction_data['predicted_co2_emissions_mmt']} ppm"],
                ["Deforestation", f"{prediction_data['predicted_deforestation_rate_percent']} %"]
            ])
            prediction_table.setStyle(table_style)
            elements.append(prediction_table)
            elements.append(Spacer(1, 24))

        elements.append(Paragraph("<i>Generated by Climate Change Dashboard - Data may include fallbacks if unavailable</i>", styles['Italic']))

        doc.build(elements)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={country}_climate_report.pdf'
        return response
    except Exception as e:
        app.logger.error(f"Report generation error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
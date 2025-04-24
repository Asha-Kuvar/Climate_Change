from flask import Flask, jsonify, request,render_template
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend requests

# Mock country list
COUNTRIES = [
    "India", "USA", "China", "Brazil", "Australia", "Canada", "Germany", "Japan", "South Africa", "Russia"
]

# Placeholder for API keys
# To use real climate data, sign up at https://openweathermap.org/api and get an API key
OPENWEATHERMAP_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY_HERE"  # Replace with your key

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/api/countries', methods=['GET'])
def get_countries():
    return jsonify(COUNTRIES)

@app.route('/api/current_temperature', methods=['GET'])
def get_current_temperature():
    country = request.args.get('country')
    if not country or country not in COUNTRIES:
        return jsonify({"error": "Invalid or missing country"}), 400
    
    # Mock data (replace with real API call if you have a key)
    # Example using OpenWeatherMap (uncomment and add your API key):
    """
    import requests
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={country}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            return jsonify({
                "temperature": data['main']['temp'],
                "co2": random.uniform(350, 450),  # Mock CO2
                "deforestation": random.uniform(0, 10)  # Mock deforestation
            })
        else:
            return jsonify({"error": "Failed to fetch weather data"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    """
    
    # Mock response
    return jsonify({
        "temperature": random.uniform(15, 35),
        "co2": random.uniform(350, 450),
        "deforestation": random.uniform(0, 10)
    })

@app.route('/api/predicts', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        temp_change = float(data.get('temperatureChange', 0))
        co2_level = float(data.get('co2Level', 400))
        def_change = float(data.get('deforestationChange', 0))
        
        # Mock prediction logic (replace with real model if available)
        predict_temp = 25 + temp_change * 0.5
        predict_co2 = co2_level + (co2_level * def_change / 100)
        predict_def = 5 + def_change * 0.8
        
        return jsonify({
            "predict_temperature_c": round(predict_temp, 2),
            "predict_co2_emissions_mmt": round(predict_co2, 2),
            "predict_deforestation_rate_percent": round(predict_def, 2)
        })
    except (ValueError, TypeError) as e:
        return jsonify({"error": "Invalid input data"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
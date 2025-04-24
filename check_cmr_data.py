import requests
import time
import pycountry
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# NASA API token
NASA_API_KEY = 'eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGEgTG9naW4iLCJzaWciOiJlZGxqd3RwdWJrZXlfb3BzIiwiYWxnIjoiUlMyNTYifQ.eyJ0eXBlIjoiVXNlciIsInVpZCI6ImFzaGExMjMiLCJleHAiOjE3NDgyNTkwNTcsImlhdCI6MTc0MzA3NTA1NywiaXNzIjoiaHR0cHM6Ly91cnMuZWFydGhkYXRhLm5hc2EuZ292IiwiaWRlbnRpdHlfcHJvdmlkZXIiOiJlZGxfb3BzIiwiYWNyIjoiZWRsIiwiYXNzdXJhbmNlX2xldmVsIjozfQ.CSCexI9IeYLu5uIw3rZwHUrx5t67pACiu8SxpVkxjuSLQDXbiTK_wEJmKaeBmpwnyovRRe_FIP1KBSXZP-aR6N2sKXWEa2ROtHSpv7YToGn9rD6OZTbbWXUYhwaPN_Df_gH0YkllA8m4qtx0AG34febCByiD7PCX9MLKa2WSkCrB8R1qJ4AWhPsz8PTN_6NQUz7YlmjQbUavfZf9JEDGiJme8dHtN2gSC1DGQ1r36AN61RQPd7SUOxbCV6RULNF78cv13P8LYmhjVrWAVLk7m1i3-58_5vyDDZok4XXSHKfYCXqEEScUL0jdVmWEUquYhhHbwrC_eTPpEAEDVZl1_w'

# Initialize geolocator
geolocator = Nominatim(user_agent="climate_check", timeout=10)

def get_bounding_box(country):
    """Get bounding box for a country using Nominatim."""
    for attempt in range(3):
        try:
            location = geolocator.geocode(country, geometry='wkt')
            if not location:
                print(f"Geocoding failed for {country}")
                return None
            bbox = location.raw['boundingbox']
            south_lat, north_lat, west_lon, east_lon = map(float, bbox)
            # Adjust for United States
            if country.lower() == "united states":
                south_lat, west_lon, north_lat, east_lon = 24.396308, -124.848974, 49.384358, -66.885444
            return south_lat, west_lon, north_lat, east_lon
        except GeocoderTimedOut:
            print(f"Geocoding timeout for {country}, attempt {attempt + 1}")
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"Geocoding failed for {country} after retries")
            return None
        except Exception as e:
            print(f"Error geocoding {country}: {e}")
            return None

def check_cmr_data(country, bounding_box):
    """Check CMR API for data availability."""
    if not bounding_box:
        return None
    
    south_lat, west_lon, north_lat, east_lon = bounding_box
    # Validate coordinates
    if not (-90 <= south_lat <= 90 and -90 <= north_lat <= 90 and -180 <= west_lon <= 180 and -180 <= east_lon <= 180):
        print(f"Invalid coordinates for {country}: {bounding_box}")
        return None
    
    base_url = "https://cmr.earthdata.nasa.gov/search/granules.json"
    params = {
        "concept_id": "C1906303052-LARC",
        "bounding_box": f"{south_lat},{west_lon},{north_lat},{east_lon}",
        "sort_key": "-start_date",
        "page_size": "1",
        "temporal": "2025-01-01T00:00:00Z,2025-12-31T23:59:59Z"
    }
    headers = {"Authorization": f"Bearer {NASA_API_KEY}"}
    
    try:
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code == 200:
            json_data = response.json()
            has_data = bool(json_data['feed']['entry'])
            print(f"{country}: {'Has data' if has_data else 'No data'} - Entries: {len(json_data['feed']['entry'])}")
            return has_data
        else:
            print(f"{country}: CMR error - Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"{country}: Request failed - {e}")
        return None

def main():
    # Get list of countries
    countries = [country.name for country in pycountry.countries]
    # For testing, limit to a few: countries = ["India", "Brazil", "United States", "Australia"]
    
    print("Checking CMR API for country data availability...")
    print("===========================================")
    
    for country in countries:
        print(f"\nProcessing {country}...")
        bbox = get_bounding_box(country)
        if bbox:
            check_cmr_data(country, bbox)
        time.sleep(1)  # Rate limiting to avoid overwhelming APIs

if __name__ == "__main__":
    main()
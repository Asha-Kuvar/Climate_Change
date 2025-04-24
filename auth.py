import requests

url = "https://data-api.globalforestwatch.org/auth/login"
payload = {
    "email": "21svdc2079@svdegreecollege.ac.in",  # Use the same email as in sign-up
    "password": "Asha@123"  # Use the password you created during sign-up
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    data = response.json()
    token = data['data']['token']  # Assuming the token is in 'data' -> 'token'
    print("Authentication successful! Token:", token)
else:
    print(f"Authentication failed: {response.status_code}")
    print(response.json())

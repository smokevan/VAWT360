from flask import Flask, render_template, request
import requests

app = Flask(__name__)
api_key = "d7e8ca1b68fd9204c9f64e7d0c338484"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    location = request.form['location']
    print("Location:", location)  # Debug print to check the input

    wind_speed = fetch_current_wind_speed(location)
    print("Wind Speed:", wind_speed)  # Debug print to check the API response

    return render_template('result.html', location=location, wind_speed=wind_speed)

def fetch_current_wind_speed(location):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        wind_speed = data['wind']['speed']  # meters/sec
        return f"{wind_speed} m/s"
    else:
        return "Failed to retrieve data"


if __name__ == '__main__':
    app.run(debug=True)

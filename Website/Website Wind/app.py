from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    location = request.form['location']  # Although not used in the API call yet
    mean_wind_speed = fetch_wind_data()
    return render_template('result.html', location=location, speed=mean_wind_speed)

def fetch_wind_data():
    api_url = "https://globalwindatlas.info/api/gis/country/USA/wind-speed/10"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        # Assuming the structure contains a key for mean wind speed; you'll need to adjust this
        return data.get('mean_wind_speed', 'No data available')
    else:
        return "Failed to retrieve data"

if __name__ == '__main__':
    app.run(debug=True)

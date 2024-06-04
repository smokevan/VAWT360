import requests
import datetime
from flask import Flask, render_template, request
import wexpect
import os
import re 


# Ensure the API key is correctly copied and placed here
api_key = '0ada37d5339bccddde9ea598c7ac93b9'
print("Starting Flask application...")


def fetch_monthly_average_wind_speed(lat, lon, month, year):
    start_date = datetime.datetime(year, month, 1)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1)
    else:
        end_date = datetime.datetime(year, month + 1, 1)
    
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    monthly_url = f"http://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start_timestamp}&end={end_timestamp}&appid={api_key}"
    response = requests.get(monthly_url)
    
    if response.status_code == 200:
        data = response.json()
        wind_speeds = [entry['wind']['speed'] for entry in data['list'] if 'wind' in entry and 'speed' in entry['wind']]
        if wind_speeds:
            average_wind_speed = sum(wind_speeds) / len(wind_speeds)
            return average_wind_speed
        else:
            return None
    else:
        print(f"Failed to fetch historical data for month: {month}, year: {year} - {response.status_code} - {response.text}")
        return None

def fetch_monthly_average_temp_pressure(lat, lon, month, year):
    start_date = datetime.datetime(year, month, 1)
    if month == 12:
        end_date = datetime.datetime(year + 1, 1, 1)
    else:
        end_date = datetime.datetime(year, month + 1, 1)
    
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    monthly_url = f"http://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start_timestamp}&end={end_timestamp}&appid={api_key}"
    response = requests.get(monthly_url)
    
    if response.status_code == 200:
        data = response.json()
        temps = [entry['main']['temp'] for entry in data['list'] if 'main' in entry and 'temp' in entry['main']]
        pressures = [entry['main']['pressure'] for entry in data['list'] if 'main' in entry and 'pressure' in entry['main']]
        if temps and pressures:
            average_temp = sum(temps) / len(temps)
            average_pressure = sum(pressures) / len(pressures)
            return average_temp, average_pressure
        else:
            return None, None
    else:
        print(f"Failed to fetch historical data for month: {month}, year: {year} - {response.status_code} - {response.text}")
        return None, None

def calculate_air_density(temp, pressure):
    R_specific = 287.05  # Specific gas constant for dry air in J/(kg·K)
    temp_kelvin = temp - 273.15  # Convert temperature from Kelvin to Celsius
    air_density = pressure / (R_specific * temp_kelvin)
    return air_density

def fetch_yearly_average_data(location):
    print(f"Fetching geographical coordinates for location: {location}")
    geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&appid={api_key}"
    geocode_response = requests.get(geocode_url)
    if geocode_response.status_code == 200:
        geocode_data = geocode_response.json()
        if not geocode_data:
            print("Geocode data not found")
            return None, None
        lat = geocode_data[0]['lat']
        lon = geocode_data[0]['lon']
        print(f"Coordinates found: lat={lat}, lon={lon}")
    else:
        print(f"Failed to fetch geocode data: {geocode_response.status_code} - {geocode_response.text}")
        return None, None
    
    current_date = datetime.datetime.now()
    monthly_wind_speeds = []
    monthly_air_densities = []

    for i in range(12):
        month = (current_date.month - i - 1) % 12 + 1
        year = current_date.year - (1 if current_date.month - i - 1 < 0 else 0)
        if year == current_date.year and month > current_date.month:
            continue
        
        monthly_average_wind_speed = fetch_monthly_average_wind_speed(lat, lon, month, year)
        if monthly_average_wind_speed is not None:
            monthly_wind_speeds.append(monthly_average_wind_speed)
            print(f"Month {month}, Year {year}: Average wind speed = {monthly_average_wind_speed} m/s")

        monthly_average_temp, monthly_average_pressure = fetch_monthly_average_temp_pressure(lat, lon, month, year)
        if monthly_average_temp is not None and monthly_average_pressure is not None:
            monthly_average_air_density = calculate_air_density(monthly_average_temp, monthly_average_pressure)
            monthly_air_densities.append(monthly_average_air_density)
            print(f"Month {month}, Year {year}: Average air density = {monthly_average_air_density} kg/m^3")

    if monthly_wind_speeds and monthly_air_densities:
        yearly_average_wind_speed = sum(monthly_wind_speeds) / len(monthly_wind_speeds)
        yearly_average_air_density = sum(monthly_air_densities) / len(monthly_air_densities)
        print(f"Yearly average wind speed: {yearly_average_wind_speed} m/s")
        print(f"Yearly average air density: {yearly_average_air_density} kg/m^3")
        return yearly_average_wind_speed, yearly_average_air_density
    else:
        print("No monthly averages collected")
        return None, None


def calculate_reynolds_number(wind_speed, characteristic_length, air_density):
    air_viscosity = 1.8e-5  # Pa.s
    reynolds_number = (air_density * wind_speed * characteristic_length) / air_viscosity
    return reynolds_number




def run_xfoil_simulation(reynolds_number):
    xfoil_path = r"C:\Users\tgoldberg\Documents\GitHub\VAWT360\Website Wind\XFOIL6.99\xfoil.exe"  # Adjust this path to your XFOIL installation
    print(f"XFOIL path: {xfoil_path}")
    if not os.path.exists(xfoil_path):
        raise FileNotFoundError(f"XFOIL executable not found at: {xfoil_path}")
    try:
        child = wexpect.spawn(xfoil_path)
    except Exception as e:
        raise RuntimeError(f"Failed to start XFOIL: {e}")
    
    commands = [
        "naca 0015",
        "OPER",
        "iter 200"
        f"VISC {reynolds_number}",
        "autoPolarSave.txt",
        "autoPolarDump.txt",
        "ASEQ -5 15 1",
        "QUIT"
    ]

    try:
        for command in commands:
            print(f"Sending command: {command}")
            child.sendline(command)
            child.expect('>')

        child.close()

        if not os.path.exists("results.txt"):
            raise FileNotFoundError("XFOIL did not create the results file.")

        with open("results.txt", "r") as file:
            return file.read()
    except Exception as e:
        raise RuntimeError(f"XFOIL command execution failed: {e}")

app = Flask(__name__)
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    location = request.form['location']
    try:
        characteristic_length = float(request.form['characteristic_length'])
    except ValueError:
        return render_template('result.html', location=location, wind_speed="Invalid input for characteristic length", air_density="N/A", reynolds_number="N/A", xfoil_results="N/A")
    
    average_wind_speed, average_air_density = fetch_yearly_average_data(location)
    if average_wind_speed is not None and average_air_density is not None:
        reynolds_number = calculate_reynolds_number(average_wind_speed, characteristic_length, average_air_density)
    try:
        xfoil_results = run_xfoil_simulation(reynolds_number)
        return render_template('result.html', wind_speed=wind_speed, reynolds_number=reynolds_number, xfoil_results=xfoil_results)
    except Exception as e:
        return str(e), 500
    else:
        return render_template('result.html', location=location, wind_speed="Data not available", air_density="N/A", reynolds_number="N/A", xfoil_results="N/A")

if __name__ == '__main__':
    app.run(debug=True)
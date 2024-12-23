from flask import Flask, render_template
import requests

app = Flask(__name__)

# ESP8266 IP address
ESP8266_IP = "169.254.10.60"

# Ensure proper HTTP format for the requests
def format_ip(ip):
    if not ip.startswith("http://"):
        return f"http://{ip}"
    return ip

@app.route('/')
def index():
    esp_url = format_ip(ESP8266_IP)  # Ensure 'http://' is added
    try:
        # Fetch sensor data from ESP8266
        response = requests.get(f"{esp_url}")
        sensor_data = response.text
    except Exception as e:
        sensor_data = f"Error fetching data: {str(e)}"

    return render_template('index.html', sensor_data=sensor_data)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def get_weather_forecast(city):
    api_key = "92cd6be29821152b87d8c2ec5e3cccb6"
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # 檢查 HTTP 狀態碼
        data = response.json()
        
        forecast = []
        for entry in data["list"]:
            forecast.append({
                "datetime": entry["dt_txt"],
                "temperature": entry["main"]["temp"],
                "description": entry["weather"][0]["description"]
            })
        
        return forecast
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# 天氣查詢函數
def get_weather(city):
    api_key = "92cd6be29821152b87d8c2ec5e3cccb6"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # 檢查 HTTP 狀態碼
        data = response.json()
        
        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        pressure = data["main"]["pressure"]
        sunrise = data["sys"]["sunrise"]
        sunset = data["sys"]["sunset"]
        
        return {
            "description": weather_description,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "pressure": pressure,
            "sunrise": sunrise,
            "sunset": sunset
        }
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# 新增天氣預報端點
@app.route('/get_weather_forecast', methods=['POST'])
def handle_weather_forecast_request():
    data = request.json
    city = data.get("city")
    
    if not city:
        return jsonify({"error": "City not provided"}), 400
    
    # 調用天氣預報函數
    forecast_info = get_weather_forecast(city)
    
    # 返回天氣預報信息
    return jsonify(forecast_info)

# 定義即時天氣查詢API端點
@app.route('/get_weather', methods=['POST'])
def handle_weather_request():
    data = request.json
    city = data.get("city")
    
    if not city:
        return jsonify({"error": "City not provided"}), 400
    
    # 調用天氣查詢函數
    weather_info = get_weather(city)
    
    # 返回天氣信息
    return jsonify(weather_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
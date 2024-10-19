import requests
API_key = '92cd6be29821152b87d8c2ec5e3cccb6'

class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def get_weather(self, city):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return f"城市: {data['name']}, 溫度: {data['main']['temp']}°C, 天氣: {data['weather'][0]['description']}"
        else:
            return f"無法取得 {city} 的天氣資訊"
    
    def get_weather_forecast(self, city):
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            forecast = data['list'][:5]  # 只取得未來5天的預報
            return "\n".join([f"日期: {item['dt_txt']}, 溫度: {item['main']['temp']}°C, 天氣: {item['weather'][0]['description']}" for item in forecast])
        else:
            return f"無法取得 {city} 的天氣預報"

# 初始化 WeatherService 實例
weather_service = WeatherService(API_key)
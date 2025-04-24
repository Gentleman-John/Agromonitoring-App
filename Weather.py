import requests
import json
from datetime import datetime, timedelta

class NyanzaWeatherForecaster:
    def __init__(self, api_key):
        self.base_url = "http://api.openweathermap.org/data/2.5/forecast"
        self.api_key = api_key
        self.nyanza_coords = {'lat': -0.5143, 'lon': 34.4618}  # Approximate coordinates for Nyanza region
        self.crop_data = {
            'maize': {'optimal_temp': (20, 30), 'water_needs': 500, 'risk_temp': 35},
            'tea': {'optimal_temp': (15, 25), 'water_needs': 1200, 'risk_temp': 30},
            'beans': {'optimal_temp': (18, 27), 'water_needs': 400, 'risk_temp': 32}
        }
    
    def get_weather_forecast(self):
        """Fetch 5-day weather forecast from OpenWeatherMap API"""
        params = {
            'lat': self.nyanza_coords['lat'],
            'lon': self.nyanza_coords['lon'],
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None
    
    def analyze_forecast(self, forecast_data, crop_type='maize'):
        """Analyze weather forecast for agricultural impact"""
        if not forecast_data:
            return None
            
        crop_info = self.crop_data.get(crop_type, self.crop_data['maize'])
        daily_data = {}
        
        # Process 3-hour interval data into daily summaries
        for item in forecast_data['list']:
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            if date not in daily_data:
                daily_data[date] = {
                    'temp_sum': 0,
                    'temp_count': 0,
                    'rain_sum': 0,
                    'humidity_sum': 0,
                    'max_temp': -float('inf'),
                    'min_temp': float('inf'),
                    'weather_conditions': set()
                }
            
            # Process temperature data
            temp = item['main']['temp']
            daily_data[date]['temp_sum'] += temp
            daily_data[date]['temp_count'] += 1
            daily_data[date]['max_temp'] = max(daily_data[date]['max_temp'], temp)
            daily_data[date]['min_temp'] = min(daily_data[date]['min_temp'], temp)
            
            # Process rain data
            if 'rain' in item:
                daily_data[date]['rain_sum'] += item['rain'].get('3h', 0)
            
            # Process humidity
            daily_data[date]['humidity_sum'] += item['main']['humidity']
            
            # Track weather conditions
            daily_data[date]['weather_conditions'].update(
                w['main'] for w in item['weather']
            )
        
        # Generate daily insights
        insights = []
        for date, data in daily_data.items():
            avg_temp = data['temp_sum'] / data['temp_count']
            avg_humidity = data['humidity_sum'] / data['temp_count']
            total_rain = data['rain_sum']
            
            # Generate farming recommendations
            recommendations = []
            
            # Temperature checks
            if data['max_temp'] > crop_info['risk_temp']:
                recommendations.append("⚠️ High temperature warning! Consider shading crops.")
            elif avg_temp < crop_info['optimal_temp'][0]:
                recommendations.append("❄️ Low temperatures may slow growth.")
            
            # Rainfall analysis (convert mm to approximate water availability)
            if total_rain < 5:
                recommendations.append("🌧️ Little rain expected. Consider irrigation.")
            elif total_rain > 20:
                recommendations.append("🌊 Heavy rain expected. Ensure proper drainage.")
            
            # Special conditions
            if 'Thunderstorm' in data['weather_conditions']:
                recommendations.append("⚡ Thunderstorm expected. Secure equipment and harvest if possible.")
            
            insights.append({
                'date': date,
                'avg_temp': round(avg_temp, 1),
                'max_temp': round(data['max_temp'], 1),
                'min_temp': round(data['min_temp'], 1),
                'total_rain': round(total_rain, 1),
                'avg_humidity': round(avg_humidity, 1),
                'conditions': ', '.join(data['weather_conditions']),
                'recommendations': recommendations
            })
        
        return insights
    
    def format_insights_for_farmers(self, insights, crop_type='maize'):
        """Convert data insights into farmer-friendly messages"""
        if not insights:
            return "No weather data available. Please try again later."
            
        messages = []
        messages.append(f"🌱 Weather Forecast for {crop_type.capitalize()} Farmers in Nyanza 🌱\n")
        
        for day in insights:
            msg = f"\n📅 {day['date']}\n"
            msg += f"🌡️ Temp: {day['min_temp']}°C - {day['max_temp']}°C (Avg: {day['avg_temp']}°C)\n"
            msg += f"💧 Rain: {day['total_rain']}mm | Humidity: {day['avg_humidity']}%\n"
            msg += f"⛅ Conditions: {day['conditions']}\n"
            
            if day['recommendations']:
                msg += "\n🔍 Recommendations:\n"
                for rec in day['recommendations']:
                    msg += f"- {rec}\n"
            else:
                msg += "\n✅ Conditions look favorable for your crops!\n"
            
            messages.append(msg)
        
        return "\n".join(messages)

# Example Usage
if __name__ == "__main__":
    # Replace with your actual OpenWeatherMap API key
    API_KEY = " e41e288aa9606f904fbf90f0ffb41e67"
    
    forecaster = NyanzaWeatherForecaster(API_KEY)
    weather_data = forecaster.get_weather_forecast()
    
    if weather_data:
        # Analyze for maize farming (default) - can change to 'tea' or 'beans'
        insights = forecaster.analyze_forecast(weather_data, crop_type='maize')
        farmer_message = forecaster.format_insights_for_farmers(insights, crop_type='maize')
        print(farmer_message)
        
        # Optional: Save to file for SMS/WhatsApp integration
        with open('weather_alert.txt', 'w') as f:
            f.write(farmer_message)
    else:
        print("Failed to retrieve weather data")
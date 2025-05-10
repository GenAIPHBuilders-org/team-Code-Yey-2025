import os
from dotenv import load_dotenv
import pandas as pd
from weather import get_weather_forecast

load_dotenv()

class CropsPricePredictor:

        
    def load_mock_prices(self):#ur data
        return pd.DataFrame({
            'date': pd.date_range(start='2025-05-09', periods=7),
            'base_price': [40, 41, 42, 43, 44, 45, 42],
            'market': ['Co-Op', 'Distributor', 'Local Market'] * 2 + ['Co-Op']
        })
    
    def analyze_weather_impact(self, weather_data):
        if weather_data["status"] == "error":
            return "Unable to analyze weather impact due to weather data error"
            
        current = weather_data["current"]
        hourly = weather_data["hourly"]
        daily = weather_data["daily"]
        
        # Calculate average precipitation for next 24 hours
        avg_precipitation = sum(hourly["precipitation"]) / len(hourly["precipitation"])
        max_wind_speed = max(hourly["wind_speed"])
        
        # Simple weather impact analysis
        if avg_precipitation > 10 or max_wind_speed > 30:
            return "Severe weather conditions detected - possible typhoon threat"
        elif avg_precipitation > 5:
            return "Moderate rain expected - minor market impact"
        else:
            return "Normal weather conditions"
    
    def predict_prices(self):
        # Get weather forecast
        weather_data = get_weather_forecast()
        
        # Get base prices
        prices_df = self.load_mock_prices()
        
        # Add adjusted_price column with base prices
        prices_df['adjusted_price'] = prices_df['base_price']
        
        # Analyze weather impact
        weather_impact = self.analyze_weather_impact(weather_data)
        
        # Adjust prices based on weather impact
        if "typhoon" in weather_impact.lower():
            prices_df['adjusted_price'] = prices_df['adjusted_price'] * 1.15  # 15% increase
        elif "rain" in weather_impact.lower():
            prices_df['adjusted_price'] = prices_df['adjusted_price'] * 1.05  # 5% increase
            
        return {
            'weather_data': weather_data,
            'weather_analysis': weather_impact,
            'price_predictions': prices_df.to_dict('records'),
        }
    

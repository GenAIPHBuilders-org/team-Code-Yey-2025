import pandas as pd
from catboost import CatBoostRegressor, Pool
from weather import get_weather_forecast

class CropsPricePredictor:
    def __init__(self):
        self.model = CatBoostRegressor()
        self.model.load_model("price_predictor.cbm")

    def generate_input_features(self, date, crop, region, weather_data):
        date = pd.to_datetime(date)
        month = date.month
        year = date.year
        quarter = date.quarter
        day_of_year = date.dayofyear

        pest_outbreak = 1 if weather_data['current']['precipitation'] > 5 else 0
        rainfall = weather_data['current']['precipitation']
        temp = weather_data['current']['temperature']
        rainfall_temp = rainfall * temp

        # placeholder values for fertilizer cost and fuel price
        fertilizer_cost = 30
        fuel_price = 60
        fert_fuel_ratio = fertilizer_cost / fuel_price

        features = pd.DataFrame([{
            "Region": region,
            "Crop": crop,
            "Rainfall (mm)": rainfall,
            "Temperature (°C)": temp,
            "Fertilizer Cost (PHP/kg)": fertilizer_cost,  
            "Fuel Price (PHP/liter)": fuel_price,
            "Pest Outbreak": pest_outbreak,
            "Market Demand (1-10)": 5, 
            "Month": month,
            "Year": year,
            "Quarter": quarter,
            "DayOfYear": day_of_year,
            "Rainfall_Temperature": rainfall_temp,
            "Fertilizer_Fuel_Ratio": fert_fuel_ratio
        }])

        return features
    
    def analyze_weather_impact(self, weather_data):
        if weather_data["status"] == "error":
            return "Unable to analyze weather impact due to weather data error"
        
        hourly = weather_data["hourly"]
        avg_precipitation = sum(hourly["precipitation"]) / len(hourly["precipitation"])
        max_wind_speed = max(hourly["wind_speed"])

        if avg_precipitation > 10 or max_wind_speed > 30:
            return "Severe weather conditions detected - possible typhoon threat"
        elif avg_precipitation > 5:
            return "Moderate rain expected - minor market impact"
        else:
            return "Normal weather conditions"

    def predict_single_price(self, date, crop, region):
        weather_data = get_weather_forecast()
        if weather_data['status'] == 'error':
            return {
                "status": "error",
                "message": "Weather data not available."
            }

        features = self.generate_input_features(date, crop, region, weather_data)
        prediction_pool = Pool(features, cat_features=["Crop", "Region"])
        
        base_price = self.model.predict(prediction_pool)[0]
        adjusted_price = base_price
    
        weather_impact = self.analyze_weather_impact(weather_data)
        if "typhoon" in weather_impact.lower():
            adjusted_price *= 1.15  
        elif "rain" in weather_impact.lower():
            adjusted_price *= 1.05 

        return {
            "status": "success",
            "weather_data": weather_data,
            "weather_analysis": weather_impact,
            "prediction": {
                "crop": crop,
                "region": region,
                "date": date,
                "base_price": round(base_price, 2),
                "adjusted_price": round(adjusted_price, 2)
            }
        }

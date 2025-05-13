import openmeteo_requests 
import requests_cache
from retry_requests import retry 

def get_weather_forecast():
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 13.4088,
	    "longitude": 122.5615,
        "hourly": ["temperature_2m", "precipitation", "wind_speed_10m"],
        "daily": ["precipitation_sum", "precipitation_probability_max"],
        "current": ["temperature_2m", "precipitation", "wind_speed_10m"],
        "timezone": "Asia/Manila",
        "forecast_days": 7
    }
    
    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        # Process current weather data
        current = response.Current()
        current_weather = {
            "temperature": current.Variables(0).Value(),
            "precipitation": current.Variables(1).Value(),
            "wind_speed": current.Variables(2).Value()
        }

        # Process hourly data for the next 24 hours
        hourly = response.Hourly()
        hourly_data = {
            "temperature": hourly.Variables(0).ValuesAsNumpy()[:24].tolist(),
            "precipitation": hourly.Variables(1).ValuesAsNumpy()[:24].tolist(),
            "wind_speed": hourly.Variables(2).ValuesAsNumpy()[:24].tolist()
        }

        # Process daily data
        daily = response.Daily()
        daily_data = {
            "precipitation_sum": daily.Variables(0).ValuesAsNumpy().tolist(),
            "precipitation_probability": daily.Variables(1).ValuesAsNumpy().tolist()
        }

        return {
            "status": "success",
            "current": current_weather,
            "hourly": hourly_data,
            "daily": daily_data
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
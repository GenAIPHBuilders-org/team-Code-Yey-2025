from fastapi import FastAPI, HTTPException
from price_predict import CropsPricePredictor
from weather import get_weather_forecast
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
app = FastAPI()
predictor = CropsPricePredictor()

# Configure the OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
    timeout=60.0,
    max_retries=3,
    default_headers={
        "HTTP-Referer": "https://farm-assist.example.com",
        "X-Title": "Farm Assistant API"
    }
)

@app.post("/predict-prices")
async def predict_prices():
    try:
        predictions = predictor.predict_prices()
        weather_data = predictions['weather_data']
        price_data = predictions['price_predictions']

        if price_data:
            avg_price = sum(p['adjusted_price'] for p in price_data) / len(price_data)
            max_price = max(p['adjusted_price'] for p in price_data)
            markets = ', '.join(set(p['market'] for p in price_data))
        else:
            logger.warning("No price data available")
            avg_price = "N/A"
            max_price = "N/A"
            markets = "N/A"

        # Build context (pass all info here)
        context = f"""
        WEATHER CONDITIONS:
        Temperature: {weather_data['current']['temperature']}°C
        Precipitation: {weather_data['current']['precipitation']}mm
        Wind Speed: {weather_data['current']['wind_speed']}km/h

        CROPS PRICE DATA:
        Highest Price: ₱{max_price}/kg
        Average Price: ₱{avg_price}/kg
        Markets: {markets}

        WEATHER IMPACT:
        {predictions['weather_analysis']}
        """

        logger.info("Sending AI request with contextual data...")

        try:
            completion = client.chat.completions.create(
                model="deepseek/deepseek-r1-zero:free",
                messages=[
                    {
                        "role": "system",
                        "content": """Using the data provided, give a short 3-5 sentence selling recommendation in Filipino/Taglish.
    
                            Rules:
                            - Explain the weather impact except the wind speed on crops, and why you should sell  or not
                            - Use the weather data and price data to give a recommendation
                            - Be conversational and clear
                            - Don't use "average price", just say "high" or "low price"
                            - Focus on harvest and selling tips
                            - Use a friendly SMS-style tone
                            - Do NOT repeat the raw data
                            - Include a closing Yes-or-No question in this format:
                            'Gusto mo bang mabenta ang 'product name' ngayon? Sagot lang ng "OO" para kumpirmahin.'
                            """
                    },
                    {
                        "role": "user",
                        "content": context.strip()
                    }
                ],
                temperature=0.7,
                stream=False
            )

            choices = getattr(completion, "choices", [])
            content = None
            if choices:
                choice = choices[0]
                if isinstance(choice, dict):
                    message = choice.get("message", {})
                    content = message.get("content") or message.get("reasoning")
                elif hasattr(choice, "message"):
                    message = getattr(choice, "message", None)
                    if message:
                        content = getattr(message, "content", None) or getattr(message, "reasoning", None)

            return {
                "recommendation": content.strip() if content else "Walang available na rekomendasyon ngayon."
            }

        except Exception as api_error:
            logger.error(f"AI error: {str(api_error)}")
            return {
                "recommendation": (
                    "Base sa lagay ng panahon at presyo ngayon, magandang magbenta ng kamatis sa umaga. "
                    "Subukang i-check ang pinakamalapit na palengke. Gusto mo bang mabenta ang kamatis ngayon? "
                    "Sagot lang ng 'OO' para kumpirmahin."
                )
            }

    except Exception as e:
        logger.error(f"Error in predict_prices: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Prediction processing failed.")




@app.get("/weather-alert")
async def get_weather_alert():
    try:
        # Get weather forecast
        weather_data = get_weather_forecast()
        weather_context = json.dumps(weather_data, indent=2)
        logger.info("Weather data retrieved successfully")

        
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1-zero:free",
            messages=[
                {
                    "role": "system",
                    "content": f"""Magbigay ng weather alert para sa mga magsasaka base sa weather na ito: {weather_context}

                    IMPORTANT RULES:
                    - USE TAGALOG ONLY
                    - DON'T USE ENGLISH
                    - DON'T REPORT THE DATA OF THE WEATHER. JUST GIVE A SUMMARY.
                    - Maximum 1-2 sentences only
                    - Focus on practical farming impact
                    - Be direct and clear
                    - Don't mention specific numbers
                    """
                },
                {
                    "role": "user",
                    "content": ""
                }
            ],
            temperature=0.7,
            stream=False
        )

        # Extract content safely with multiple fallbacks
        choices = getattr(completion, "choices", [])
        content = None
        if choices:
            choice = choices[0]
            if isinstance(choice, dict):
                message = choice.get("message", {})
                content = message.get("content") or message.get("reasoning")
            elif hasattr(choice, "message"):
                message = getattr(choice, "message", None)
                if message:
                    content = getattr(message, "content", None) or getattr(message, "reasoning", None)

        return {
            "explanation": content.strip() if content else "Walang available na weather alert"
        }
        
    except Exception as e:
        logger.error(f"Error in weather alert: {str(e)}")
        return {
            "status": "error",
            "explanation": "May error sa weather alert system"
        }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Farm Assistant API"}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Farm Assistant API server")
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException, Query
from openai import OpenAI
import os
import logging
import pandas as pd
import json
from dotenv import load_dotenv
from price_predict import CropsPricePredictor 
from weather import get_weather_forecast

# Setup
load_dotenv()
app = FastAPI()
predictor = CropsPricePredictor() 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
    
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
    default_headers={
        "HTTP-Referer": "https://farm-assist.example.com",
        "X-Title": "Farm Assistant API"
    }
)

@app.post("/live-model-test")
async def test_model_with_live_weather(
    crop: str = Query(...),
    region: str = Query(...)
    #placeholder for now, use actual user input when avail
):
    try:
        date = pd.Timestamp.now().strftime("%Y-%m-%d")
        price_prediction = predictor.predict_single_price(date, crop, region)

        if price_prediction["status"] != "success":
            raise HTTPException(status_code=400, detail=price_prediction.get("message", "Prediction failed"))

        weather_json = json.dumps(price_prediction["weather_data"], indent=2)
        weather_analysis = price_prediction["weather_analysis"]

        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1-zero:free",
            messages=[
                {
                    "role": "system",
                    "content": f"""Magbigay ng *maikling* weather alert para sa mga magsasaka base sa weather na ito: {weather_json}
                        IMPORTANT RULES:
                        - TAGALOG LANG.
                        - HUWAG BANGGITIN ANG MGA NUMERO o DETALYENG TEKNIKAL.
                        - HUWAG IULIT ANG WEATHER DATA.
                        - Isang pangungusap lang (maximum 2 kung talagang kailangan).
                        - Tumuon sa epekto sa pagsasaka.
                        - Simple, malinaw, direkta.
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

                # Extract response content safely
        choices = getattr(completion, "choices", [])
        tagalog_summary = None
        if choices:
            choice = choices[0]
            if hasattr(choice, "message"):
                tagalog_summary = getattr(choice.message, "content", None)

        if tagalog_summary:
            tagalog_summary = tagalog_summary.strip()
            if tagalog_summary.startswith("\\boxed{") and tagalog_summary.endswith("}"):
                tagalog_summary = tagalog_summary[8:-1]
            tagalog_summary = tagalog_summary.replace("\\boxed", "").replace("{", "").replace("}", "")


        # Clean and build a one-paragraph summary
        price = price_prediction["prediction"]["base_price"]
        adjusted = price_prediction["prediction"]["adjusted_price"]
        analysis = weather_analysis
        summary = tagalog_summary.strip() if tagalog_summary else "Walang alert ngayon."

        combined_summary = (
            f"Sa {region} ngayong {date}, ang inaasahang presyo ng {crop} ay ₱{price:.2f}."
            f" {analysis}. {summary}"
        )

        return {
            "status": "success",
            "summary": combined_summary
        }

    except Exception as e:
        logger.error(f"Live model test failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Live model test failed.")


@app.get("/weather-alert")
async def get_weather_alert():
    try:
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
                        - TAGALOG LANG.
                        - HUWAG BANGGITIN ANG MGA NUMERO o DETALYENG TEKNIKAL.
                        - HUWAG IULIT ANG WEATHER DATA.
                        - Isang pangungusap lang (maximum 2 kung talagang kailangan).
                        - Tumuon sa epekto sa pagsasaka.
                        - Simple, malinaw, direkta.
                        - Wag magsabi ng specific na mga numero.
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

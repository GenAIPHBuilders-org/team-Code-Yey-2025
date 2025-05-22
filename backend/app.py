from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from openai import OpenAI
import os
import logging
import pandas as pd
import json
import asyncio
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv
from price_predict import CropsPricePredictor 
from weather import get_weather_forecast
from task_manager import FarmTaskManager
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware


# Setup
load_dotenv()
app = FastAPI(title="Farm Assistant API")
predictor = CropsPricePredictor()
task_manager = FarmTaskManager()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client for endpoints that use it directly
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
    default_headers={
        "HTTP-Referer": "https://farm-assist.example.com",
        "X-Title": "Farm Assistant API"
    }
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "status": "running",
        "api_version": "1.0.0",
        "service": "Farm Assistant API"
    }

@app.post("/live-model-test")
async def test_model_with_live_weather(
    crop: str = Query(...), 
    region: str = Query(...),
):
    """Test the price prediction model with live weather data"""
    try:
        date_obj = pd.Timestamp.now()
        date = date_obj.strftime("%B %d, %Y")   
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
                    "content": f"""Gamit ang datos ng presyo at lagay ng panahon, magbigay ng *maikling buod* para sa mga magsasaka tungkol sa inaasahang bentahan ng {crop} sa {region} ngayong araw.

                    IMPORTANT RULES:
                    - TAGALOG LANG.
                    - HUWAG BANGGITIN ANG MGA NUMERO o DETALYENG TEKNIKAL.
                    - HUWAG IULIT ANG WEATHER DATA.
                    - TUON SA PRESYO at BENTA ng ANI, hindi sa weather.
                    - WEATHER ay banggitin lang kung ito ay may malinaw na epekto sa ani o presyo.
                    - ISANG pangungusap lang (dalawa kung talagang kailangan).
                    - SIMPLE, MALIWANAG, at DIREKTA ang tono.
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
            "summary": combined_summary,
            "follow_up": f"Gusto mo ba ibenta {crop} sa {region}? Mag type ng 'OO' upang ituloy.",
            "next_action": {
                "endpoint": "/confirm-sell",
                "method": "POST",
                "params_needed": ["user_crops", "buyers_file", "prices_file"]
            }
        }


    except Exception as e:
        logger.error(f"Live model test failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Live model test failed.")

@app.get("/weather-alert")
async def get_weather_alert():
    """Generate weather alerts in Tagalog for farmers"""
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
            "status": "success",
            "explanation": content.strip() if content else "Walang available na weather alert"
        }
        
    except Exception as e:
        logger.error(f"Error in weather alert: {str(e)}")
        return {
            "status": "error",
            "explanation": "May error sa weather alert system"
        }




@app.get("/selling-initiatives/list")
async def list_selling_initiatives():
    """List all generated selling initiatives"""
    try:
        initiatives = task_manager.initiatives
        
        return {
            "status": "success",
            "count": len(initiatives),
            "initiatives": initiatives
        }
    except Exception as e:
        logger.error(f"Failed to list selling initiatives: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/confirm-sell")
async def confirm_selling_decision(
    background_tasks: BackgroundTasks,
    response: str = Query(...),
    crop: str = Query(...),
    region: str = Query(...)
):
    """Handles user confirmation to sell crops"""
    if response.strip().upper() == "OO":
        try:
            background_tasks.add_task(
                task_manager.generate_selling_initiatives,
                user_crops=[crop],
                buyers_file_path="fictional_buyers_dataset.csv",
                crop_prices_file_path="philippines_crop_prices_mock_data.csv"
            )
            return {
                "status": "success",
                "message": f"Okay! Sinimulan na ang paghahanap ng buyer para sa {crop} sa {region}.",
                "next_check": "/selling-initiatives/list"
            }
        except Exception as e:
            logger.error(f"Failed to start selling initiative: {str(e)}")
            raise HTTPException(status_code=500, detail="Selling process failed.")
    else:
        return {
            "status": "cancelled",
            "message": "Hindi itinuloy ang pagbenta."
        }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Farm Assistant API server")
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.warning("OPENROUTER_API_KEY is not set. AI features will not function correctly.")
    uvicorn.run(app, host="0.0.0.0", port=8000)

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
    region: str = Query(...)
):
    """Test the price prediction model with live weather data"""
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

@app.post("/tasks/generate")
async def generate_tasks(background_tasks: BackgroundTasks):
    """Generate AI-recommended farm tasks based on current conditions"""
    try:
        # Get current weather conditions
        weather_data = get_weather_forecast()
        if not weather_data or (isinstance(weather_data, dict) and weather_data.get("status") == "error"):
            raise HTTPException(status_code=500, detail="Failed to fetch weather data")
            
        # Get crop predictions for common crops
        predictor = CropsPricePredictor()
        date_str = datetime.now().strftime("%Y-%m-%d")
        region = "Region IV-A"  # Default region
        crop_info = {}
        
        for crop in ["Rice", "Corn", "Cassava"]:
            try:
                prediction = predictor.predict_single_price(date_str, crop, region)
                crop_info[crop] = prediction
            except Exception as e:
                logger.warning(f"Failed to get prediction for {crop}: {str(e)}")
                crop_info[crop] = {"status": "error", "message": f"Prediction failed for {crop}"}
        
        # Generate tasks asynchronously
        # We'll start the task generation but return immediately for better UX
        background_tasks.add_task(task_manager.generate_tasks, weather_data, crop_info)
        
        return {
            "status": "success",
            "message": "Task generation started. Check /tasks/list to view tasks once generated."
        }
        
    except Exception as e:
        logger.error(f"Task generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/list")
async def list_tasks():
    """List all generated tasks"""
    try:
        tasks = list(task_manager.tasks.values())
        
        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_tasks = sorted(tasks, key=lambda x: priority_order.get(x.get("priority", "Medium"), 1))
        
        return {
            "status": "success",
            "count": len(sorted_tasks),
            "tasks": sorted_tasks
        }
    except Exception as e:
        logger.error(f"Failed to list tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tasks/{task_id}/feedback")
async def submit_task_feedback(task_id: str, feedback: Dict):
    """Submit feedback for task recommendations"""
    try:
        if not feedback or "rating" not in feedback:
            raise HTTPException(status_code=400, detail="Feedback must include a rating")
            
        success = task_manager.process_feedback(task_id, feedback)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Task ID {task_id} not found")
            
        return {"status": "success", "message": "Feedback processed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/selling-initiatives/generate")
async def generate_selling_initiatives(
    background_tasks: BackgroundTasks,
    user_crops: List[str] = Query(..., description="List of crops the user has"),
    buyers_file: str = Query("fictional_buyers_dataset.csv", description="Path to CSV file with buyer data"),
    prices_file: str = Query("philippines_crop_prices_mock_data.csv", description="Path to CSV file with crop price data")
):
    """Generate AI-recommended selling initiatives based on buyer and crop price data"""
    try:
        # Start initiative generation in the background for better UX
        background_tasks.add_task(
            task_manager.generate_selling_initiatives, 
            user_crops=user_crops,  # Pass the new parameter
            buyers_file_path=buyers_file,
            crop_prices_file_path=prices_file
        )
        
        return {
            "status": "success",
            "message": "Selling initiative generation started. Check /selling-initiatives/list to view results once generated."
        }
    except Exception as e:
        logger.error(f"Selling initiative generation failed to start: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Farm Assistant API server")
    # Check if API key is set
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.warning("OPENROUTER_API_KEY is not set. AI features will not function correctly.")
    uvicorn.run(app, host="0.0.0.0", port=8000)

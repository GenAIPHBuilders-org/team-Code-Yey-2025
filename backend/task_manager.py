from typing import Dict, List, Any
import logging
import json
import csv
from datetime import datetime
from openai import OpenAI
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FarmTaskManager:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("OPENROUTER_API_KEY environment variable not set. AI functionality will be limited.")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://farm-assist.example.com",
                "X-Title": "Farm Assistant API"
            }
        )
        self.initiatives = []  # Store generated initiatives
        self.tasks = {}  # Store generated tasks with IDs

    def _load_csv_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Loads data from a CSV file into a list of dictionaries."""
        data = []
        try:
            with open(file_path, mode="r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append(row)
            logger.info(f"Successfully loaded data from {file_path}")
        except FileNotFoundError:
            logger.error(f"Error: The file {file_path} was not found.")
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
        return data

    def _get_crop_price_info(self, crop_name: str, crop_prices_data: List[Dict[str, Any]], region: str = None) -> Dict[str, Any]:
        """Retrieves average price for a specific crop, optionally filtered by region."""
        relevant_prices = []
        for record in crop_prices_data:
            if record.get("Crop", "").lower() == crop_name.lower():
                if region and record.get("Region", "").lower() == region.lower():
                    try:
                        relevant_prices.append(float(record.get("Price per kg", 0)))
                    except ValueError:
                        pass  # Ignore if price is not a valid float
                elif not region:
                    try:
                        relevant_prices.append(float(record.get("Price per kg", 0)))
                    except ValueError:
                        pass
        
        if relevant_prices:
            avg_price = sum(relevant_prices) / len(relevant_prices)
            return {"crop": crop_name, "average_price_per_kg": round(avg_price, 2)}
        return {"crop": crop_name, "average_price_per_kg": "N/A"}

    async def generate_selling_initiatives(
        self,
        user_crops: List[str],
        buyers_file_path: str = "fictional_buyers_dataset.csv",
        crop_prices_file_path: str = "philippines_crop_prices_mock_data.csv"
    ) -> List[str]:
        """Generate one best selling initiative based on buyer and crop price data."""
        logger.info("Starting selling initiative generation.")

        buyers_data = self._load_csv_data(buyers_file_path)
        crop_prices_data = self._load_csv_data(crop_prices_file_path)

        if not buyers_data:
            logger.warning("No buyer data loaded. Cannot generate initiatives.")
            return []

        self.initiatives = []
        current_date_str = datetime.now().strftime("%Y-%m-%d")

        # Filter buyers who are interested in user crops and sort by price (if available)
        filtered_buyers = []
        for buyer in buyers_data:
            crop_interest = buyer.get("Crop Interest", "").lower()
            if crop_interest in [crop.lower() for crop in user_crops]:
                price_info = self._get_crop_price_info(crop_interest, crop_prices_data, buyer.get("Region"))
                avg_price = price_info["average_price_per_kg"]
                if avg_price == "N/A":
                    price_info = self._get_crop_price_info(crop_interest, crop_prices_data)
                    avg_price = price_info["average_price_per_kg"]
                if isinstance(avg_price, (int, float)):
                    buyer["price_info"] = avg_price
                    filtered_buyers.append(buyer)

        if not filtered_buyers:
            logger.warning("No suitable buyer with price info found.")
            return []

        # Sort buyers by price (descending)
        best_buyer = sorted(filtered_buyers, key=lambda b: b["price_info"], reverse=True)[0]

        context_for_ai = {
            "buyer_profile": best_buyer,
            "product_market_context": {
                "crop": best_buyer.get("Crop Interest"),
                "average_price_per_kg": best_buyer["price_info"]
            },
            "current_date": current_date_str
        }

        system_prompt = (
            """Ikaw ay isang expert na sales strategist sa agrikultura. 
            Ang goal mo ay gumawa ng personalized na selling initiative na magkokonekta sa ani ng magsasaka sa pinaka-best na buyer base sa presyo, 
            klase ng buyer, at regional na data. Dapat isang maikling talata lang ang initiative na nagpapaliwanag kung bakit swak ang buyer na ito at
            paano siya dapat lapitan o kausapin.

            IMPORTANT RULES:
            1. TAGLISH LANG
            2. Huwag magsalita ng english.
            2. 2 hanggang 3 pangungusap lang.
            3. Iwasan ang jargon at masyadong teknikal na salita.

            """ 
        )

        user_prompt_content = json.dumps(context_for_ai, indent=2)

        try:
            if not self.client.api_key:
                logger.error("API key not configured. Skipping API call.")
                return ["Could not generate initiative due to API key missing."]

            logger.info(f"Sending request to AI for best buyer: {best_buyer.get('Buyer Name')}")
            completion = self.client.chat.completions.create(
                model="deepseek/deepseek-r1-zero:free",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt_content}
                ],
                temperature=0.7
            )

            ai_response = completion.choices[0].message.content.strip()
            logger.info(f"Received AI response: {ai_response}")
            self.initiatives.append(ai_response)
            return self.initiatives

        except Exception as e:
            logger.error(f"AI initiative generation failed: {str(e)}", exc_info=True)
            return [f"Failed to generate initiative. Error: {str(e)}"]


    

# For direct script testing
async def main_test():
    task_manager = FarmTaskManager()
    
    # Ensure OPENROUTER_API_KEY is set in your environment before running
    if not os.getenv("OPENROUTER_API_KEY"):
        print("Please set the OPENROUTER_API_KEY environment variable to test.")
        print("Example: export OPENROUTER_API_KEY='your_key_here'")
        return

    print("Generating selling initiatives (this may take a moment and requires an API key)...")
    # Using default file paths as defined in the method signature
    initiatives = await task_manager.generate_selling_initiatives()
    
    if initiatives:
        print("\n--- Generated Selling Initiatives ---")
        for i, initiative_paragraph in enumerate(initiatives):
            print(f"\nInitiative {i+1}:\n{initiative_paragraph}")
    else:
        print("No initiatives were generated. Check logs for details.")

if __name__ == "__main__":
    # For direct script execution testing
    import asyncio
    # asyncio.run(main_test())  # Uncomment to run the test
    print("FarmTaskManager class defined. To test, uncomment the asyncio.run(main_test()) line.")
    print("The script is intended to be used as a module. The main_test function is for demonstration.")

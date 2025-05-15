from typing import Dict, List
import logging
import json
from datetime import datetime
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

class FarmTaskManager:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv('OPENROUTER_API_KEY'),
            default_headers={
                "HTTP-Referer": "https://farm-assist.example.com",
                "X-Title": "Farm Assistant API"
            }
        )
        self.tasks = []

    def _parse_task_response(self, response: str) -> List[Dict]:
        """Parse AI response into structured tasks"""
        import json
        try:
            # Remove LaTeX box if present
            if response.strip().startswith("\\boxed{") and response.strip().endswith("}"):
                response = response.strip()[7:-1].strip()
            response = response.replace("\\boxed", "")

            # Try to parse as JSON
            try:
                data = json.loads(response)
                # If it's a dict of "Task N": {...}
                if isinstance(data, dict):
                    tasks = []
                    for key, value in data.items():
                        if isinstance(value, dict):
                            tasks.append({
                                "description": value.get("description") or value.get("task"),
                                "priority": value.get("priority"),
                                "schedule": value.get("schedule")
                            })
                    if tasks:
                        return tasks
                # If it's a dict with "tasks" key (old format)
                if isinstance(data, dict) and "tasks" in data:
                    return [
                        {
                            "description": t.get("task") or t.get("description"),
                            "priority": t.get("priority"),
                            "schedule": t.get("schedule")
                        }
                        for t in data["tasks"]
                    ]
            except Exception:
                pass  # Fallback to line-by-line parsing below

            # Fallback: line-by-line parsing (old behavior)
            tasks = []
            current_task = {}
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('Task'):
                    if current_task:
                        tasks.append(current_task)
                    current_task = {'description': line.split(':', 1)[1].strip()}
                elif line.startswith('Priority'):
                    current_task['priority'] = line.split(':', 1)[1].strip()
                elif line.startswith('Schedule'):
                    current_task['schedule'] = line.split(':', 1)[1].strip()
            if current_task:
                tasks.append(current_task)
            return tasks

        except Exception as e:
            logger.error(f"Task parsing failed: {str(e)}")
            return []

    def _parse_priority_response(self, response: str) -> List[Dict]:
        """Parse AI priority response"""
        try:
            tasks = []
            for task in self.tasks:
                priority_level = 3  # Default medium priority
                if 'High' in task.get('priority', ''):
                    priority_level = 5
                elif 'Low' in task.get('priority', ''):
                    priority_level = 1
                    
                tasks.append({
                    **task,
                    'priority_level': priority_level
                })
            return tasks
            
        except Exception as e:
            logger.error(f"Priority parsing failed: {str(e)}")
            return self.tasks

    async def generate_tasks(self, weather_data: Dict, crop_info: Dict) -> List[Dict]:
        """Generate AI-recommended tasks based on conditions"""
        try:
            logger.info("Starting task generation with weather and crop data")

            # Summarize weather info
            weather_summary = {
                "temperature": weather_data.get("current", {}).get("temperature"),
                "precipitation": weather_data.get("current", {}).get("precipitation"),
                "wind_speed": weather_data.get("current", {}).get("wind_speed"),
                "weather_analysis": weather_data.get("weather_analysis", "")
            }

            # Summarize crop info (just crop names and predicted prices)
            crop_summary = []
            for crop, info in crop_info.items():
                crop_summary.append({
                    "crop": crop,
                    "predicted_price": info.get("prediction", {}).get("adjusted_price"),
                    "weather_impact": info.get("weather_analysis", "")
                })

            context = {
                "weather": weather_summary,
                "crops": crop_summary,
                "current_date": datetime.now().strftime("%Y-%m-%d")
            }

            logger.info(f"Preparing AI request with summarized context: {json.dumps(context)}")

            completion = self.client.chat.completions.create(
                model="deepseek/deepseek-r1-zero:free",
                messages=[
                    {
                        "role": "system",
                        "content": """Magbigay ng listahan ng mga gawain sa bukid base sa weather 
                    at crop data. 
                    
                    IMPORTANT RULES:
                    - TAGALOG LANG
                    - Maximum 5 tasks
                    - Practical at specific na mga gawain
                    - Include priority level (High/Medium/Low)
                    - Include recommended schedule
                    
                    FORMAT:
                    Task 1: (description)
                    Priority: (level)
                    Schedule: (recommended time)
                    """
                    },
                    {
                        "role": "user", 
                        "content": json.dumps(context, indent=2)
                    }
                ],
                temperature=0.7
            )

            logger.info("Successfully received AI response")
            logger.info(f"AI raw response: {completion.choices[0].message.content}")

            self.tasks = self._parse_task_response(completion.choices[0].message.content)

            if not self.tasks:
                logger.warning("No tasks were generated from AI response")

            return self.tasks

        except Exception as e:
            logger.error(f"Task generation failed: {str(e)}", exc_info=True)
            return []

    async def prioritize_tasks(self, tasks: List[Dict], context: Dict) -> List[Dict]:
        """Prioritize the given tasks based on context"""
        try:
            self.tasks = tasks
            return self._parse_priority_response("")
            
        except Exception as e:
            logger.error(f"Task prioritization failed: {str(e)}")
            return tasks

    def process_feedback(self, task_id: str, feedback: Dict):
        """Process user feedback about task recommendations"""
        try:
            # Implementation for feedback processing
            # Store feedback for future model improvements
            logger.info(f"Processing feedback for task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to process feedback: {str(e)}")
            return False
# 🌱 BukidMate 🌱

Your partner in every Planting.

---

## 📦 Features

- 🌾 **Farmer-Centric SMS Interface**  
  Works with basic phones — enables farmers to receive and respond to market offers via SMS.
  Farmers confirm deals using simple responses like `OO`, with agent follow-up instructions.

- 📉 **Price Trend Analysis**  
  Predicts short-term price changes using mock data and simulated events like typhoons or harvest floods.
  AI sends personalized messages with the best current prices from multiple buyers.

- 🤖 **Agentic Decision-Making**  
  Proactively identifies and recommends optimal deals — not just static price listings.
  Adapts advice based on contextual mock events (e.g., incoming typhoon in Batangas affecting price trends).

- 🧠 **Simulated Buyer Offers**  
  Responds with mock offers from Co-Ops, Distributors, and Wet Markets with time-sensitive deals.



---

## 🛠️ Requirements

- Python 3.8+
- `venv` or virtualenv (recommended)
- pip

---

## 🧪 Installation

```bash
# Clone the repository
git clone https://github.com/GenAIPHBuilders-org/team-Code-Yey-2025.git
cd team-Code-Yey-2025

#Go to the Backend
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   
# On Windows use: venv\Scripts\activate
# On Gitbash use: venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Initialize FAST-API
uvicorn app:app --reload

#Open a separete terminal and run:

#Change crops or region depending on what you'd like to check
curl -X POST "http://localhost:8000/live-model-test?crop=Tomato&region=Region%20IV-A" 

#Selling Initiatives
curl -X POST "http://localhost:8000/selling-initiatives/list"


#Use "OO" for Selling
curl -X POST "http://localhost:8000/confirm-sell?response=OO&crop=Tomato&region=Region%20IV-A"

#or "HINDI" to cancel
curl -X POST "http://localhost:8000/confirm-sell?response=HINDI&crop=Tomato&region=Region%20IV-A"



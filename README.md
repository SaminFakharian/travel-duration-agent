# Travel Duration AI Agent

This is an AI agent who answers questions about current travel duration between two locations for a user-specified model of transport.

## Setup:

1. Clone this repository
2. Create a virtual enviroment and activate it:
```
python -m venv venv
venv\Scripts\activate
```
3. Install the required packages
```
pip install -r requirements.txt
```
4. Create a `.env` file in the project directory with your API keys:
```
OPEN_API_KEY=your_openai_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```
## Usage:

Run the application:
```
streamlit run main.py
```
Enter your travel duration query and click on `Get Answer` button.

Example queries:
- What is the current travel duration by car between Filoli Historic House & Garden, Woodside, CA to Pulgas Water Temple, Redwood City, CA?
- I want to bike from Shoreline Amphitheatre in Mountain View to the Computer History Museum. How long will it take?
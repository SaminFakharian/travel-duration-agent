# Travel Duration AI Agent

This is an AI agent that answers questions about current travel duration between two locations for a user-specified mode of transport. It leverages the Google Maps API and OpenAI API to provide accurate and intelligent responses.

## Setup:

1. Clone this repository.
2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
4. Create a `.env` file in the project directory with your API keys:
    ```plaintext
    OPEN_API_KEY=your_openai_api_key
    GOOGLE_MAPS_API_KEY=your_google_maps_api_key
    ```

## Usage:

Run the application:
```bash
streamlit run main.py
```

Enter your travel duration query and click on the `Get Answer` button.

Example queries:
- What is the current travel duration by car between Filoli Historic House & Garden, Woodside, CA to Pulgas Water Temple, Redwood City, CA?
- I want to bike from Shoreline Amphitheatre in Mountain View to the Computer History Museum. How long will it take?


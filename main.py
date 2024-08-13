import json
import os
from dotenv import load_dotenv
import openai
import googlemaps
import streamlit as st

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))


def process_query(query):
    extraction_prompt = f"""
    Extract the following information from the query:
    1. Origin location
    2. Destination location
    3. Model of transport (default to 'driving' if not specified.)
    Important: Map the mode of transportation to one of these five options: driving, walking, bicycling, vtol or transit. Use the following guidelines: 
    - Map car, automobile, drive, vehicle, motor to "driving" 
    - Map walk, on foot, pedestrian, stroll, hike to "walking" 
    - Map bike, bicycle, cycle, cycling, pedal, biking to "bicycling" 
    - Map bus, train, subway, metro, public transport, tram, rail to "transit" 
    - If no mode is specified, default to "driving"

    If the query is not about travel duration between two locations, or if it asks for information you can't provide (like specific traffic conditions, weather, or travel costs), classify it as "out_of_scope".

    Query: "{query}"

    Respond in JSON format:
    {{
        "query_type": "travel_duration" or "out_of_scope"
        "origin":"extracted origin",
        "destination":"extracted destination",
        "original_mode":"original mode of transport mentioned by the user (if any)",
        "mode": "mapped mode of transport (driving, walking, bicycling, vtol or transit)",
        "out_of_scope_reason": "Brief explanation if query is out of scope",
    }}

    Ensure your response contains only the JSON object, with no additional text before or after.
    """
    extraction_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts travel information from queries."},
            {"role": "user", "content": extraction_prompt}
        ]
    )
    try:
        extracted_info = json.loads(extraction_response.choices[0].message['content'])
    except json.JSONDecodeError:
        return "I'm sorry, I couldn't understand the query. Please try rephrasing it."
    # Handle out-of-scope queries
    if extracted_info['query_type'] == 'out_of_scope':
        out_of_scope_prompt = f"""
        Generate a polite and informative response for an out-of-scope query. The user asked: "{query}" 

        Explain that you can only provide travel durations between two locations using driving, walking, bicycling, or transit modes. 
        Briefly mention why their query is out of scope: {extracted_info['out_of_scope_reason']} 
        Provide an example of a query you can answer. 

        Keep the response concise and friendly.
        """
        out_of_scope_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system",
                       "content": "You are a helpful assistant that explains the limitations of a travel duration service."},
                      {"role": "user",
                       "content": out_of_scope_prompt}])
        return out_of_scope_response.choices[0].message['content'].strip()

    origin = get_coordinates(extracted_info['origin'])
    destination = get_coordinates(extracted_info['destination'])

    if not origin or not destination:
        error_prompt = f"""
        Generate a helpful response for a user whose query couldn't be processed due to location issues.
        Origin: {extracted_info['origin']} {'(Not found)' if not origin else '(Found)'}
        Destination: {extracted_info['destination']} {'(Not found)' if not destination else '(Found)'}

        Explain that one or both locations couldn't be found. If it's a generic location like 'Walmart', suggest adding more details like city, state, or a specific address. Provide an example of a more specific query that would work better.

        Keep the response friendly and helpful.
        """
        error_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system",
                       "content": "You are a helpful assistant that guides users in formulating clear travel queries."},
                      {"role": "user",
                       "content": error_prompt}])
        response = error_response.choices[0].message['content'].strip()

        if not origin:
            if destination:
                nearby_origins = get_nearby_places(destination, extracted_info['origin'])
                if nearby_origins:
                    response += "\n\nHere are three suggestions for your origin location:\n"
                    for i, place in enumerate(nearby_origins, 1):
                        response += f"{i}. {place['name']} - {place['vicinity']}\n"
                    updated_query = query.replace(extracted_info['origin'],
                                                  nearby_origins[0]['name'] + nearby_origins[0]['vicinity'])
                    response += f"\nIf you pick the first origin location:\n{process_query(updated_query)}"
            else:
                return "I'm sorry I couldn't find one or both of the locations you specified."

        if not destination:
            if origin:
                nearby_destinations = get_nearby_places(origin, extracted_info['destination'])
                if nearby_destinations:
                    response += "\n\nHere are three suggestions for your destination location:\n"
                    for i, place in enumerate(nearby_destinations, 1):
                        response += f"{i}. {place['name']} - {place['vicinity']}\n"
                    updated_query = query.replace(extracted_info['destination'],
                                                  nearby_destinations[0]['name'] + nearby_destinations[0]['vicinity'])
                    response += f"\nIf you pick the first destination location:\n{process_query(updated_query)}"
            else:
                return "I'm sorry I couldn't find one or both of the locations you specified."

        return response

    if extracted_info['mode'] not in ["driving", "walking", "bicycling", "transit", "vtol"]:
        return "I'm sorry, but the mode of transportation you selected is not supported. Please choose from one of the following options: driving, walking, bicycling, vtol or transit."

    duration = get_travel_duration(origin, destination, extracted_info['mode'])
    if not duration:
        return f"I'm sorry I couldn't calculate the travel duration for specified route and mode of transport. Your specified mode of transport is {extracted_info['mode']}"
    # uber_response=""

    response_prompt = f"""
    Generate a natural language response for the following travel query:
    Origin: {extracted_info['origin']}
    Destination: {extracted_info['destination']}
    Mode of Transport: {extracted_info['mode']}
    Original Model Mentioned: {extracted_info.get('original_mode', 'Not specified')}
    Travel Duration: {duration}

    The response should be concise and informative. Ask the user if they want an Uber from their origin to destination.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides travel duration information."},
            {"role": "user", "content": response_prompt}
        ]
    )
    return response.choices[0].message.content.strip(), origin, destination, extracted_info['origin'], extracted_info[
        'destination']


def process_uber_query(origin, destination, actual_origin, actual_destination):
    if not origin or not destination:
        return "I'm sorry, I couldn't find one or both of the locations you specified for the Uber request."

    return get_uber(origin, destination, actual_origin, actual_destination)


def get_coordinates(location):
    try:
        geocode_result = gmaps.geocode(location)
        if geocode_result:
            return geocode_result[0]['geometry']['location']
        else:
            return None
    except Exception as e:
        print(f"Error geocoding {location}: {e}")
        return None


def get_travel_duration(origin, destination, mode):
    try:
        direction_result = gmaps.directions(origin, destination, mode=mode)
        if direction_result:
            duration = direction_result[0]['legs'][0]['duration']['text']
            return duration
        else:
            return None
    except Exception as e:
        print("Error getting directions: {e}")
        return None


def get_nearby_places(location, query):
    try:
        result = gmaps.places_nearby(location=location, radius=5000, keyword=query)
        return result['results'][:3]  # Return top 3 results
    except Exception as e:
        print(f"Error finding nearby places: {e}")
        return []


def get_uber(origin, destination, actual_origin, actual_destination):
    return f"Your Uber has been requested for {actual_origin} to {actual_destination}"


def main():
    st.title("Travel Duration Query Assistant")
    examples = [
        "What is the current travel duration by car between Filoli Historic House & Garden, Woodside, CA to Pulgas Water Temple, Redwood City, CA?",
        "I want to bike from Shoreline Amphitheatre in Mountain View to the Computer History Museum. How long will it take?",
        "time to travel from Chez Panisse to Mezzo in Berkeley",
        "How long will it take me to bike from the Ferry Building in San Francisco to Walgreens?"
    ]

    selected_example = st.selectbox("Choose a predefined example:", [""] + examples)
    query = st.text_input("Or enter your travel duration query:", value=selected_example)
    # to be able to show the Uber result after answer given for this query we need to have session
    if 'answer_given' not in st.session_state:
        st.session_state.answer_given = False
    if st.button("Get Answer"):
        if query:
            response, origin, destination, actual_origin, actual_destination = process_query(query)
            st.write(response)
            st.session_state.query_results = {
                "origin": origin,
                "destination": destination,
                "actual_origin": actual_origin,
                "actual_destination": actual_destination
            }
            st.session_state.answer_given = True
        else:
            st.write("Please enter a query.")

    if st.session_state.answer_given:
        if st.button("Get Uber"):
            if hasattr(st.session_state, 'query_results'):
                uber_response = process_uber_query(
                    st.session_state.query_results["origin"],
                    st.session_state.query_results["destination"],
                    st.session_state.query_results["actual_origin"],
                    st.session_state.query_results["actual_destination"]
                )
                st.write(uber_response)


if __name__ == "__main__":
    main()

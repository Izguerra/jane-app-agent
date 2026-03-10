import os
import aiohttp
import json
from datetime import datetime

from backend.services.integration_service import IntegrationService

class ExternalTools:
    def __init__(self, workspace_id: str = None):
        self.workspace_id = workspace_id
        
    def __init__(self, workspace_id: str = None):
        self.workspace_id = workspace_id
        self.weather_api_key = None
        self.aviation_api_key = None
        self.google_maps_api_key = None

    async def get_current_weather(self, location: str, date: str = None, units: str = "metric", **kwargs):
        """
        Get weather for a location. 
        Supports future dates (approximate).
        """
        details = kwargs.get("details", [])
        if not self.weather_api_key:
            self.weather_api_key = await IntegrationService.async_get_provider_key(
                workspace_id=self.workspace_id, 
                provider="openweathermap", 
                env_fallback="OPENWEATHERMAP_API_KEY"
            )

        print(f"DEBUG: get_current_weather called for {location}, Date: {date}, Unit: {units}, Details: {details}. Key found: {bool(self.weather_api_key)}")
        if not self.weather_api_key:
            return "Weather API key is not configured."

        # Convert simple units
        unit_sys = "metric" if units.lower() == "celsius" or units.lower() == "metric" else "imperial"
        unit_symbol = "°C" if unit_sys == "metric" else "°F"

        try:
            async with aiohttp.ClientSession() as session:
                # Determine Endpoint: Forecast (Future) vs Weather (Current)
                is_future = bool(date and "today" not in date.lower() and "now" not in date.lower())
                endpoint = "forecast" if is_future else "weather"
                
                url = f"http://api.openweathermap.org/data/2.5/{endpoint}?q={location}&appid={self.weather_api_key}&units={unit_sys}"
                
                async with session.get(url) as response:
                    if response.status != 200:
                        return f"Could not get weather for {location}. Status: {response.status}"
                    
                    data = await response.json()
                    
                    # --- Data Extraction Helper ---
                    def extract_metrics(raw_data):
                        main = raw_data.get('main', {})
                        weather_desc = raw_data.get('weather', [{}])[0].get('description', 'unknown')
                        temp = main.get('temp', 'N/A')
                        feels_like = main.get('feels_like', 'N/A')
                        humidity = main.get('humidity', 'N/A')
                        wind = raw_data.get('wind', {}).get('speed', 'N/A')
                        sys = raw_data.get('sys', {})
                        sunrise = datetime.fromtimestamp(sys.get('sunrise', 0)).strftime('%H:%M') if sys.get('sunrise') else "N/A"
                        sunset = datetime.fromtimestamp(sys.get('sunset', 0)).strftime('%H:%M') if sys.get('sunset') else "N/A"
                        
                        report = f"Conditions: {weather_desc}. Temp: {temp}{unit_symbol}."
                        return report

                    # --- Forecast Logic ---
                    if is_future:
                        # Find closest entry in 3-hour list
                        # Naive: just take the one around noon tomorrow
                        # Better: OpenWeather Free provides 5 day / 3 hour. We look for first match of date.
                        target_dt_txt = date.split('T')[0] # Rough string match if ISO, else rely on Agent's parsing
                        
                        # If agent passes "2024-05-20", we look for it
                        found_cast = None
                        for item in data.get('list', []):
                            if date in item.get('dt_txt', ''):
                                found_cast = item
                                break
                        
                        if not found_cast:
                            # Fallback: Just return tomorrow noon? Or message.
                            return f"Forecast for specific date '{date}' not found in 5-day window."
                            
                        return f"Forecast for {location} on {found_cast.get('dt_txt')}: {extract_metrics(found_cast)}"
                    else:
                        # Current Weather
                        return f"Current Weather in {location}: {extract_metrics(data)}"

        except Exception as e:
            return f"Error fetching weather: {str(e)}"

    async def get_flight_status(self, flight_number: str = None, origin: str = None, destination: str = None, airline: str = None, date: str = None, approx_time: str = None):
        """
        Get status for a specific flight using AviationStack. 
        Supports Route-based schedule lookup with time filtering.
        """
        if not self.aviation_api_key:
            self.aviation_api_key = await IntegrationService.async_get_provider_key(
                workspace_id=self.workspace_id, 
                provider="aviationstack", 
                env_fallback="AVIATIONSTACK_API_KEY"
            )

        print(f"DEBUG: get_flight_status called. F:{flight_number} O:{origin} D:{destination} T:{approx_time}. Key found: {bool(self.aviation_api_key)}")
        if not self.aviation_api_key:
            return "AviationStack API key is not configured."
            
        try:
            query_params = f"access_key={self.aviation_api_key}"
            
            if flight_number:
                clean_flight_num = flight_number.replace(" ", "").upper()
                query_params += f"&flight_iata={clean_flight_num}"
            elif origin and destination:
                query_params += f"&dep_iata={origin}&arr_iata={destination}"
                if airline:
                     query_params += f"&airline_iata={airline}"
            else:
                 return "Please provide either a Flight Number OR an Origin and Destination."
            
            async with aiohttp.ClientSession() as session:
                url = f"http://api.aviationstack.com/v1/flights?{query_params}"
                async with session.get(url) as response:
                    if response.status != 200:
                         return f"Could not get flight info. Status: {response.status}"
                    
                    data = await response.json()
                    results = data.get('data', [])
                    
                    if not results:
                        return "No flights found matching criteria."

                    # --- Time Filtering Logic ---
                    if approx_time and not flight_number:
                        # Simple filter: Filter results where departure time matches approx hour
                        # Parsing "5pm" is hard without nlp, but Agent usually sends structured time if possible.
                        # We'll rely on string matching or simplistic hour checks if approx_time is e.g. "17:00"
                        filtered = []
                        target_hour = None
                        
                        # Very naive parse
                        try:
                            if "pm" in approx_time.lower():
                                target_hour = int(approx_time.lower().replace("pm", "").strip()) + 12
                            elif "am" in approx_time.lower():
                                target_hour = int(approx_time.lower().replace("am", "").strip())
                            elif ":" in approx_time:
                                target_hour = int(approx_time.split(":")[0])
                                
                            if target_hour is not None:
                                for f in results:
                                    dep_str = f.get('departure', {}).get('scheduled', '')
                                    # dep_str format: 2024-05-20T17:20:00+00:00
                                    if 'T' in dep_str:
                                        f_hour = int(dep_str.split('T')[1].split(':')[0])
                                        # Match within 2 hour window
                                        if abs(f_hour - target_hour) <= 2:
                                            filtered.append(f)
                                results = filtered or results # Fallback to all if none match
                        except:
                            pass # Formatting error, return all

                    # Limit and Format
                    def get_dep_time(f):
                        return f.get('departure', {}).get('scheduled', '9999-99-99')
                    results.sort(key=get_dep_time)
                    
                    output = []
                    limit = 1 if flight_number else 5 # Use 5 for schedule
                    
                    for flight in results[:limit]:
                        f_num = flight.get('flight', {}).get('iata', 'Unknown')
                        status = flight.get('flight_status', 'unknown')
                        airline_name = flight.get('airline', {}).get('name', '')
                        dep = flight.get('departure', {})
                        arr = flight.get('arrival', {})
                        
                        dep_txt = f"{dep.get('airport')} ({dep.get('iata')}) at {dep.get('scheduled', '')}"
                        arr_txt = f"{arr.get('airport')} ({arr.get('iata')}) at {arr.get('scheduled', '')}"
                        
                        output.append(f"✈️ {f_num} {airline_name}\n   Status: {status}\n   Departs: {dep_txt}\n   Arrives: {arr_txt}")
                    
                    return "\n\n".join(output)
                    
        except Exception as e:
            return f"Error fetching flight status: {str(e)}"

    async def get_directions(self, origin: str, destination: str, mode: str = "driving"):
        """Get directions and traffic info using Google Maps."""
        if not self.google_maps_api_key:
            self.google_maps_api_key = await IntegrationService.async_get_provider_key(
                workspace_id=self.workspace_id, 
                provider="google_maps", 
                env_fallback="GOOGLE_MAPS_API_KEY"
            )

        print(f"DEBUG: get_directions called: {origin} -> {destination}. Key found: {bool(self.google_maps_api_key)}")
        if not self.google_maps_api_key:
            print("DEBUG: Maps API key missing.")
            return "Google Maps API key is not configured."
            
        try:
            async with aiohttp.ClientSession() as session:
                if mode not in ["driving", "walking", "bicycling", "transit"]:
                    mode = "driving"
                    
                url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={self.google_maps_api_key}&departure_time=now&traffic_model=best_guess&mode={mode}"
                async with session.get(url) as response:
                    print(f"DEBUG: Maps API Status: {response.status}")
                    
                    if response.status != 200:
                        text = await response.text()
                        print(f"DEBUG: Maps API Error: {text}")
                        return f"Could not get directions. Status: {response.status}"
                    
                    data = await response.json()
                    routes = data.get('routes', [])
                    
                    if not routes:
                        return f"No routes found from {origin} to {destination} ({mode})."
                    
                    route = routes[0]
                    leg = route.get('legs', [{}])[0]
                    
                    duration = leg.get('duration', {}).get('text', 'unknown')
                    distance = leg.get('distance', {}).get('text', 'unknown')
                    start_address = leg.get('start_address', origin)
                    end_address = leg.get('end_address', destination)
                    
                    summary = route.get('summary', '')
                    
                    msg = f"The {mode} directions from {start_address} to {end_address} via {summary} is {distance} and takes {duration}."
                    
                    if mode == "driving":
                        duration_in_traffic = leg.get('duration_in_traffic', {}).get('text', 'unknown')
                        msg += f" With current traffic, it is estimated to take {duration_in_traffic}."
                    
                    print(f"DEBUG: Maps Result: {msg}")
                    return msg
        except Exception as e:
            print(f"DEBUG: Maps Exception: {e}")
            return f"Error fetching directions: {str(e)}"

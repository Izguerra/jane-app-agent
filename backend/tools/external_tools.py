import os
import aiohttp
import json
from datetime import datetime
from livekit.agents import llm

from backend.services.integration_service import IntegrationService

class ExternalTools:
    def __init__(self, workspace_id: str = None):
        self.workspace_id = workspace_id
        self.weather_api_key = None
        self.aviation_api_key = None
        self.google_maps_api_key = None
        self.timeout = aiohttp.ClientTimeout(total=10) # 10s default timeout

    @llm.function_tool(description="Get current weather for a city or location.")
    async def get_weather(self, location: str, date: str = None, units: str = "metric"):
        """
        Get weather for a location. 
        Supports future dates (approximate).
        """
        details = []
        if not self.weather_api_key:
            return "Weather API key is not configured."

        # Convert simple units
        unit_sys = "metric" if units.lower() == "celsius" or units.lower() == "metric" else "imperial"
        unit_symbol = "°C" if unit_sys == "metric" else "°F"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Determine Endpoint: Forecast (Future) vs Weather (Current)
                is_future = bool(date and "today" not in date.lower() and "now" not in date.lower())
                endpoint = "forecast" if is_future else "weather"
                
                params = {
                    "q": location,
                    "appid": self.weather_api_key,
                    "units": unit_sys
                }
                
                url = f"http://api.openweathermap.org/data/2.5/{endpoint}"
                print(f"DEBUG: Weather API Request: {url} with params { {k: '***' if k=='appid' else v for k,v in params.items()} }")
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"ERROR: Weather API failed for {location}: {response.status} - {error_text}")
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

    @llm.function_tool(description="Get real-time status and schedule information for a specific flight.")
    async def get_flight_status(self, flight_number: str = None, origin: str = None, destination: str = None, airline: str = None, date: str = None, approx_time: str = None):
        """
        Get status for a specific flight using FlightAware AeroAPI. 
        Supports Route-based schedule lookup with time filtering.
        """
        if not self.aviation_api_key:
            self.aviation_api_key = await IntegrationService.async_get_provider_key(
                workspace_id=self.workspace_id, 
                provider="aeroapi", 
                env_fallback="AEROAPI_KEY"
            )

        print(f"DEBUG: get_flight_status called. F:{flight_number} O:{origin} D:{destination} T:{approx_time}. Key found: {bool(self.aviation_api_key)}")
        if not self.aviation_api_key:
            return "FlightAware AeroAPI key is not configured."
            
        try:
            import aiohttp
            headers = {"x-apikey": self.aviation_api_key}
            base_url = "https://aeroapi.flightaware.com/aeroapi"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if flight_number:
                    # Flight number search (e.g., UAL100 or AC100)
                    clean_flight_num = flight_number.replace(" ", "").upper()
                    url = f"{base_url}/flights/{clean_flight_num}"
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                             return f"Could not get flight info. Status: {response.status}"
                        
                        data = await response.json()
                        results = data.get('flights', [])
                        
                elif origin and destination:
                    # Route search
                    from datetime import datetime, timedelta, timezone
                    now = datetime.now(timezone.utc)
                    end = now + timedelta(days=2) # 48 hour window
                    start_str = now.strftime("%Y-%m-%d")
                    end_str = end.strftime("%Y-%m-%d")
                    
                    url = f"{base_url}/schedules/{start_str}/{end_str}?origin={origin}&destination={destination}"
                    async with session.get(url, headers=headers) as response:
                        if response.status != 200:
                             return f"Could not get flight schedules. Status: {response.status}"
                        
                        data = await response.json()
                        results = data.get('scheduled', [])
                else:
                     return "Please provide either a Flight Number OR an Origin and Destination."
                
                if not results:
                    return "No flights found matching criteria."

                # AeroAPI specific output formatting
                output = []
                limit = 1 if flight_number else 5
                
                for flight in results[:limit]:
                    f_num = flight.get('ident', 'Unknown')
                    status = "scheduled" if 'scheduled_out' in flight else "unknown"  
                    if flight.get('actual_on'): status = "landed"
                    elif flight.get('actual_off'): status = "in_air"
                    elif flight.get('cancelled'): status = "cancelled"
                    elif flight.get('delayed'): status = "delayed"
                    
                    # Handle both dictionary forms and straight string forms of origin/dest
                    dep_obj = flight.get('origin', {})
                    arr_obj = flight.get('destination', {})
                    
                    dep_code = dep_obj.get('code_iata') if isinstance(dep_obj, dict) else dep_obj
                    arr_code = arr_obj.get('code_iata') if isinstance(arr_obj, dict) else arr_obj
                    
                    dep_time = flight.get('scheduled_out', 'Unknown Time')
                    arr_time = flight.get('scheduled_in', 'Unknown Time')
                    
                    dep_txt = f"{dep_code} at {dep_time}"
                    arr_txt = f"{arr_code} at {arr_time}"
                    
                    output.append(f"✈️ {f_num}\n   Status: {status}\n   Departs: {dep_txt}\n   Arrives: {arr_txt}")
                
                return "\n\n".join(output)
                
        except Exception as e:
            return f"Error fetching flight status: {str(e)}"

    @llm.function_tool(description="Get the current local date and time for a specific city or timezone. Use this for 100% accuracy when a user asks 'What time is it in [City]?'")
    async def get_current_time(self, location: str):
        """
        Get exact current time for a location.
        Args:
            location: City name (e.g. 'London', 'Tokyo', 'Toronto') or Timezone (e.g. 'EST').
        """
        import pytz
        from datetime import datetime
        
        # Simple mapping for common cities to ensure high-speed accuracy without web search
        CITY_TZ_MAP = {
            "toronto": "America/Toronto", "new york": "America/New_York", "nyc": "America/New_York",
            "london": "Europe/London", "paris": "Europe/Paris", "berlin": "Europe/Berlin",
            "tokyo": "Asia/Tokyo", "dubai": "Asia/Dubai", "sydney": "Australia/Sydney",
            "los angeles": "America/Los_Angeles", "la": "America/Los_Angeles", "san francisco": "America/Los_Angeles",
            "chicago": "America/Chicago", "miami": "America/New_York", "vancouver": "America/Vancouver",
            "mexico city": "America/Mexico_City", "sao paulo": "America/Sao_Paulo", "cairo": "Africa/Cairo",
            "johannesburg": "Africa/Johannesburg", "mumbai": "Asia/Kolkata", "delhi": "Asia/Kolkata",
            "singapore": "Asia/Singapore", "hong kong": "Asia/Hong_Kong", "seoul": "Asia/Seoul"
        }
        
        normalized_location = location.lower().strip()
        tz_name = CITY_TZ_MAP.get(normalized_location)
        
        # If not in our common list, try to find it in pytz's full list (case-insensitive)
        if not tz_name:
            for tz in pytz.all_timezones:
                if normalized_location in tz.lower():
                    tz_name = tz
                    break
        
        if not tz_name:
            # Last fallback: Agent should use web_search if this fails
            return f"I couldn't find a specific timezone for '{location}'. You might want to use web_search to find it."
            
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            return f"The current time in {location} ({tz_name}) is {now.strftime('%A, %B %d, %Y at %I:%M %p')}."
        except Exception as e:
            return f"Error getting time for {location}: {str(e)}"

    @llm.function_tool(description="Get directions, distance, and travel time between two locations.")
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
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if mode not in ["driving", "walking", "bicycling", "transit"]:
                    mode = "driving"
                    
                import urllib.parse
                
                # Cleanup addresses (remove extra spaces and hyphens from postal codes)
                def clean_address(addr: str) -> str:
                    # 1. Handle Canadian Postal codes with spaces (L 9 T 0 E 2 -> L9T0E2)
                    import re
                    # Find patterns like "L 9 T 0 E 2" and collapse them
                    # Look for 6 individual characters separated by optional spaces
                    addr = re.sub(r'([A-Z])\s*(\d)\s*([A-Z])\s*(\d)\s*([A-Z])\s*(\d)', r'\1\2\3\4\5\6', addr, flags=re.IGNORECASE)
                    
                    # 2. Handle hyphens (L9T-0E2 -> L9T0E2)
                    addr = addr.replace("-", "")
                    
                    # 3. Clean up extra internal spaces
                    addr = " ".join(addr.split())
                    return addr

                clean_origin = clean_address(origin)
                clean_dest = clean_address(destination)
                
                safe_origin = urllib.parse.quote(clean_origin)
                safe_dest = urllib.parse.quote(clean_dest)
                
                url = f"https://maps.googleapis.com/maps/api/directions/json?origin={safe_origin}&destination={safe_dest}&key={self.google_maps_api_key}&departure_time=now&traffic_model=best_guess&mode={mode}"
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

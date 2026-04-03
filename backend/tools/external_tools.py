import os
import aiohttp
import json
import time
from datetime import datetime, timezone
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
    async def get_current_weather(self, location: str, date: str = None, units: str = "metric"):
        """
        Get weather for a location. 
        Supports future dates (approximate).
        """
        details = []
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
            
            # --- Smart Parameter Merging & Strict Checks (Layer 1) ---
            if flight_number:
                flight_number = str(flight_number).strip().upper()
                
                # Rule: Refuse broad search on digits only (e.g. "190") without airline
                if flight_number.isdigit() and not airline:
                    return "To provide an accurate status for such a common flight number, I need the Airline Name or its IATA code (e.g., 'Air Canada' or 'AC'). Could you please provide that?"
                
                # Rule: Smart Merging (e.g. "Air Canada" + "190" -> "AC190")
                if flight_number.isdigit() and airline:
                    airline_iata_map = {
                        "air canada": "AC", "westjet": "WS", "united": "UA", 
                        "delta": "DL", "american": "AA", "emirates": "EK",
                        "british airways": "BA", "lufthansa": "LH", "porter": "PD"
                    }
                    carrier = airline_iata_map.get(airline.lower())
                    if not carrier and len(airline) == 2: carrier = airline.upper()
                    
                    if carrier:
                        flight_number = f"{carrier}{flight_number}"
                        print(f"DEBUG: Smart merged flight number: {flight_number}")
                    else:
                        # If we can't map the airline but have a name, AviationStack might prefer route+airline
                        # but we'll try prepending the first 2 letters as a hail-mary if it's not a common one
                        pass 

                clean_flight_num = flight_number.replace(" ", "").upper()
                query_params += f"&flight_iata={clean_flight_num}"
            elif origin and destination:
                query_params += f"&dep_iata={origin}&arr_iata={destination}"
                if airline:
                     # Respect airline IATA if user provided name
                     airline_iata_map = {"air canada": "AC", "westjet": "WS", "united": "UA"}
                     airline_code = airline_iata_map.get(airline.lower(), airline.upper()[:2])
                     query_params += f"&airline_iata={airline_code}"
            else:
                 return "Please provide either a Flight Number OR an Origin and Destination."
            
            # Optional date filter if provided (AviationStack format: YYYY-MM-DD)
            if date:
                # Naive normalization: "today" or "tomorrow" logic could go here
                # For now we pass what the agent extracted or current date
                pass
            
            # 1. Try FlightAware AeroAPI (Highest accuracy)
            aero_key = os.getenv("AEROAPI_KEY") or os.getenv("FLIGHTAWARE_API_KEY")
            if aero_key and flight_number:
                try:
                    ident = flight_number.replace(" ", "").upper()
                    # Ensure Air Canada uses AC or ACA (FlightAware identifies AC190 as ACA190)
                    url = f"https://aeroapi.flightaware.com/aeroapi/flights/{ident}"
                    headers = {"x-apikey": aero_key}
                    
                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.get(url, headers=headers) as aero_resp:
                            if aero_resp.status == 200:
                                aero_data = await aero_resp.json()
                                print(f"DEBUG: AeroAPI RAW Response: {json.dumps(aero_data, indent=2)}")
                                aero_flights = aero_data.get('flights', [])
                                if aero_flights:
                                    # Pick the most relevant instance instead of assuming index 0.
                                    # AeroAPI v4 frequently returns multiple segments, often newest first.
                                    # We want the active flight, OR the flight scheduled closest to NOW.
                                    f = None
                                    now = datetime.now(timezone.utc)
                                    
                                    # 1. Look for a flight that is currently active (Departed but not arrived/cancelled)
                                    for flight in aero_flights:
                                        if flight.get('actual_off') and not flight.get('actual_on') and not flight.get('cancelled'):
                                            f = flight
                                            break
                                            
                                    # 2. Look for the flight scheduled closest to current time
                                    if not f:
                                        def get_time_diff(fl):
                                            ts = fl.get('estimated_out') or fl.get('scheduled_out')
                                            if not ts: return float('inf')
                                            try:
                                                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                                return abs((dt - now).total_seconds())
                                            except:
                                                return float('inf')
                                        valid_flights = [fl for fl in aero_flights if not fl.get('cancelled')]
                                        if valid_flights:
                                            valid_flights.sort(key=get_time_diff)
                                            f = valid_flights[0]
                                        else:
                                            f = aero_flights[0]
                                            
                                    f_num = f.get('ident_iata') or f.get('ident') or ident
                                    status = f.get('status', 'Unknown')
                                    airline = f.get('operator_name', 'Unknown')
                                    foresight = f.get('foresight_predictions_available', False)
                                    
                                    # Time Formatting Helper
                                    def format_aero(t_str):
                                        if not t_str: return "Unknown"
                                        try:
                                            # format: 2024-05-20T17:20:00Z
                                            dt = datetime.fromisoformat(t_str.replace('Z', '+00:00'))
                                            return dt.strftime("%I:%M %p (Local Airport Time)")
                                        except: return t_str

                                    # Delays (AeroAPI v4 provides these in seconds)
                                    d_delay_sec = f.get('departure_delay', 0)
                                    a_delay_sec = f.get('arrival_delay', 0)
                                    d_delay = int(d_delay_sec / 60) if d_delay_sec else 0
                                    a_delay = int(a_delay_sec / 60) if a_delay_sec else 0
                                    
                                    delay_txt = ""
                                    if d_delay > 5: delay_txt += f"\n   ⚠️ Departure Delay: {d_delay} mins"
                                    if a_delay > 5: delay_txt += f"\n   ⚠️ Arrival Delay: {a_delay} mins"
                                    if foresight: delay_txt += "\n   ✨ Accuracy: High (FlightAware Foresight™)"

                                    dep_info = f"{f.get('origin', {}).get('name', 'Unknown')} at {format_aero(f.get('scheduled_out'))}"
                                    arr_info = f"{f.get('destination', {}).get('name', 'Unknown')} at {format_aero(f.get('scheduled_in'))}"
                                    
                                    extra_txt = ""
                                    act_out = f.get('actual_out') or f.get('actual_off')
                                    est_out = f.get('estimated_out')
                                    if act_out: extra_txt += f"\n   Actual departure: {format_aero(act_out)}"
                                    elif est_out and est_out != f.get('scheduled_out'): extra_txt += f"\n   Estimated departure: {format_aero(est_out)}"
                                    
                                    act_in = f.get('actual_in') or f.get('actual_on')
                                    est_in = f.get('estimated_in')
                                    if act_in: extra_txt += f"\n   Actual arrival: {format_aero(act_in)}"
                                    elif est_in and est_in != f.get('scheduled_in'): extra_txt += f"\n   Estimated arrival: {format_aero(est_in)}"
                                    
                                    gate_txt = ""
                                    if f.get('gate_origin'): gate_txt += f"\n   Departure Gate: {f.get('terminal_origin', '')}{f.get('gate_origin')}"
                                    if f.get('gate_destination'): gate_txt += f"\n   Arrival Gate: {f.get('terminal_destination', '')}{f.get('gate_destination')}"

                                    now_t = datetime.now().strftime("%I:%M %p")
                                    ctx = f"\n   (Reference Current Time in Toronto: {now_t})"
                                    
                                    return f"✈️ {f_num} {airline}\n   Status: {status.upper()}{delay_txt}\n   Departs: {dep_info}\n   Arrives: {arr_info}{extra_txt}{gate_txt}{ctx}"
                except Exception as e:
                    print(f"DEBUG: FlightAware Error: {e}")
                    pass # Fallback to AviationStack

            # 2. Fallback to AviationStack (Existing logic)
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                url = f"http://api.aviationstack.com/v1/flights?{query_params}&access_key={os.getenv('AVIATIONSTACK_API_KEY')}"
                async with session.get(url) as response:
                    if response.status != 200:
                         return f"Could not get flight info. Status: {response.status}"
                    
                    data = await response.json()
                    # Log raw data for observability (RM_... traces)
                    print(f"DEBUG: AviationStack RAW Response for {flight_number or (origin+'->'+destination)}: {json.dumps(data)[:500]}...")
                    
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

                    # Filter for today/future flights to avoid stale results from previous days
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    # Many flights for 'today' might have a flight_date of today
                    results = [f for f in results if f.get('flight_date', '0000-00-00') >= today_str]

                    # Limit and Format
                    def get_dep_time(f):
                        return f.get('departure', {}).get('scheduled', '9999-99-99')
                    results.sort(key=get_dep_time)
                    
                    output = []
                    limit = 1 if flight_number else 5 # Use 5 for schedule
                    
                    def clean_time(time_str):
                        if not time_str: return "Unknown"
                        # API returns times with +00:00 despite them representing local airport time.
                        # We must strip the ISO format so the LLM doesn't incorrectly apply timezone math.
                        try:
                            # 2026-03-30T07:00:00+00:00 -> 2026-03-30 07:00:00 (Local Time)
                            raw = time_str.split('+')[0].replace('Z', '')
                            dt = datetime.fromisoformat(raw)
                            return dt.strftime("%I:%M %p (Local Airport Time)")
                        except:
                            return time_str.replace('+00:00', ' (Local Airport Time)')

                    for flight in results[:limit]:
                        f_num = flight.get('flight', {}).get('iata', 'Unknown')
                        status = flight.get('flight_status', 'unknown')
                        airline_name = flight.get('airline', {}).get('name', '')
                        dep = flight.get('departure', {})
                        arr = flight.get('arrival', {})
                        
                        dep_txt = f"{dep.get('airport')} ({dep.get('iata')}) at {clean_time(dep.get('scheduled', ''))}"
                        arr_txt = f"{arr.get('airport')} ({arr.get('iata')}) at {clean_time(arr.get('scheduled', ''))}"
                        
                        # Delay information (Enhanced Detection)
                        dep_delay = dep.get('delay')
                        arr_delay = arr.get('delay')
                        
                        # Fallback: Many airlines report delays in 'estimated' vs 'scheduled' before updating 'delay' flag
                        def detect_delay(sched, est):
                            if not sched or not est: return 0
                            try:
                                s_dt = datetime.fromisoformat(sched.split('+')[0].replace('Z',''))
                                e_dt = datetime.fromisoformat(est.split('+')[0].replace('Z',''))
                                diff = int((e_dt - s_dt).total_seconds() / 60)
                                return diff if diff > 0 else 0
                            except: return 0

                        if not dep_delay: dep_delay = detect_delay(dep.get('scheduled'), dep.get('estimated'))
                        if not arr_delay: arr_delay = detect_delay(arr.get('scheduled'), arr.get('estimated'))

                        delay_txt = ""
                        if dep_delay and int(dep_delay) > 0:
                            delay_txt += f"\n   ⚠️ Departure delayed by {dep_delay} minutes"
                        if arr_delay and int(arr_delay) > 0:
                            delay_txt += f"\n   ⚠️ Arrival delayed by {arr_delay} minutes"
                        
                        # Actual times (ONLY if different from scheduled AND status is Landed/Arrived)
                        actual_dep = dep.get('actual')
                        actual_arr = arr.get('actual')
                        
                        # Estimated times (for future/active flights)
                        est_dep = dep.get('estimated')
                        est_arr = arr.get('estimated')
                        
                        extra_txt = ""
                        if actual_dep:
                            extra_txt += f"\n   Actual departure: {clean_time(actual_dep)}"
                        elif est_dep and est_dep != dep.get('scheduled'):
                            extra_txt += f"\n   Estimated departure: {clean_time(est_dep)}"
                            
                        if actual_arr:
                            extra_txt += f"\n   Actual arrival: {clean_time(actual_arr)}"
                        elif est_arr and est_arr != arr.get('scheduled'):
                            extra_txt += f"\n   Estimated arrival: {clean_time(est_arr)}"
                        
                        # Gate/Terminal info
                        gate_txt = ""
                        if dep.get('gate'):
                            gate_txt += f"\n   Departure Gate: {dep.get('terminal', '')}{dep.get('gate', '')}"
                        if arr.get('gate'):
                            gate_txt += f"\n   Arrival Gate: {arr.get('terminal', '')}{arr.get('gate', '')}"
                        
                        # Current System Time context for the LLM (Enhanced for Toronto)
                        now_dt = datetime.now()
                        current_sys_time = now_dt.strftime("%I:%M %p")
                        
                        # SMART STATUS OVERRIDE
                        # If API says LANDED but the actual/estimated arrival is in the future, it's stale/wrong.
                        is_future_arrival = False
                        check_arr = actual_arr or est_arr or arr.get('scheduled')
                        if check_arr:
                            try:
                                # Parse the arrival time (ignoring target timezone for a rough now check)
                                arr_dt = datetime.fromisoformat(check_arr.split('+')[0].replace('Z',''))
                                # If arrival is more than 5 mins in the future, it's not 'landed'
                                if arr_dt > now_dt:
                                    is_future_arrival = True
                            except: pass

                        display_status = status.upper()
                        if status.lower() == 'landed' and is_future_arrival:
                            # Detect Departure Delay for status
                            if dep_delay and int(dep_delay) > 60:
                                display_status = "DEPARTING LATE"
                            else:
                                display_status = "IN AIR / DELAYED"
                        
                        ctx_txt = f"\n   (Reference Current Time in Toronto: {current_sys_time})"
                        
                        output.append(f"✈️ {f_num} {airline_name}\n   Status: {display_status}{delay_txt}\n   Departs: {dep_txt}\n   Arrives: {arr_txt}{extra_txt}{gate_txt}{ctx_txt}")
                    
                    return "\n\n".join(output)
                    
        except Exception as e:
            return f"Error fetching flight status: {str(e)}"

    @llm.function_tool(description="Get the current local time and date for a specific city or location globally.")
    async def get_current_time(self, location: str):
        """Get the current time and timezone for any location using Google Maps."""
        if not self.google_maps_api_key:
            self.google_maps_api_key = await IntegrationService.async_get_provider_key(
                workspace_id=self.workspace_id, 
                provider="google_maps", 
                env_fallback="GOOGLE_MAPS_API_KEY"
            )

        print(f"DEBUG: get_current_time called for {location}")
        if not self.google_maps_api_key:
            return "Google Maps API key is not configured."
            
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # 1. Geocode to get Lat/Lng
                geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={self.google_maps_api_key}"
                async with session.get(geo_url) as geo_resp:
                    if geo_resp.status != 200:
                        return f"Could not geocode location. Status: {geo_resp.status}"
                    geo_data = await geo_resp.json()
                    if not geo_data.get('results'):
                        return f"Location '{location}' not found."
                    
                    loc = geo_data['results'][0]['geometry']['location']
                    lat, lng = loc['lat'], loc['lng']
                    address = geo_data['results'][0]['formatted_address']

                # 2. Get Timezone for Lat/Lng
                timestamp = int(time.time())
                tz_url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={timestamp}&key={self.google_maps_api_key}"
                async with session.get(tz_url) as tz_resp:
                    if tz_resp.status != 200:
                        return f"Could not get timezone. Status: {tz_resp.status}"
                    tz_data = await tz_resp.json()
                    
                    if tz_data.get('status') != 'OK':
                        return f"Timezone API error: {tz_data.get('status')}"

                    # 3. Calculate Local Time
                    # dstOffset + rawOffset = total offset from UTC in seconds
                    total_offset = tz_data.get('dstOffset', 0) + tz_data.get('rawOffset', 0)
                    tz_name = tz_data.get('timeZoneName', 'Unknown')
                    tz_id = tz_data.get('timeZoneId', 'UTC')
                    
                    # Compute current local time
                    from datetime import timezone, timedelta
                    now_utc = datetime.now(timezone.utc)
                    local_now = now_utc + timedelta(seconds=total_offset)
                    
                    time_str = local_now.strftime("%I:%M %p")
                    date_str = local_now.strftime("%A, %B %d, %Y")
                    
                    return f"The current time in {address} is {time_str} ({tz_name}) on {date_str}."

        except Exception as e:
            print(f"DEBUG: Time tool Exception: {e}")
            return f"Error fetching current time: {str(e)}"

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



    @llm.function_tool(description="Check real-time delays and operational health at a specific airport.")
    async def get_airport_delays(self, airport_code: str):
        """
        Checks for delays at an airport (e.g., YYZ, LAX, YLW). 
        Returns counts of arrival/departure delays and indicates if a ground stop is in effect.
        """
        aero_key = await IntegrationService.async_get_provider_key(
            workspace_id=self.workspace_id,
            provider="flightaware",
            env_fallback="AEROAPI_KEY"
        )
        if not aero_key: return "FlightAware API key not configured for airport delays."

        code = airport_code.upper()
        url = f"https://aeroapi.flightaware.com/aeroapi/airports/{code}/delays"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers={"x-apikey": aero_key}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        arr_d = data.get('arrivals', {}).get('delay_count', 0)
                        dep_d = data.get('departures', {}).get('delay_count', 0)
                        ground_stop = "Yes" if data.get('ground_stop') else "No"
                        
                        report = f"🏢 Airport Health: {code}\n"
                        report += f"   - Arrival Delays: {arr_d}\n"
                        report += f"   - Departure Delays: {dep_d}\n"
                        report += f"   - Ground Stop active: {ground_stop}"
                        return report
                    return f"Could not get delay info for {code} (Status: {resp.status})"
        except Exception as e:
            return f"Error fetching airport delays: {e}"

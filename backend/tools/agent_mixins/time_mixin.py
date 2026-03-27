import pytz
from datetime import datetime
from livekit.agents import llm
import logging
import aiohttp

logger = logging.getLogger("time-mixin")

class TimeMixin:
    def __init__(self, *args, **kwargs):
        pass

    @llm.function_tool(description="Get the current time for a specific location or timezone.")
    async def get_current_time(self, location: str = "local"):
        """
        Get the current time. 
        Pass a city name (e.g., 'Tokyo', 'New York') or 'local'.
        """
        try:
            if not location or location.lower() == "local":
                return f"The current time is {datetime.now().strftime('%I:%M %p %Z')}."

            # Hardcoded common mappings to avoid massive DBs
            common_tz = {
                "tokyo": "Asia/Tokyo",
                "london": "Europe/London",
                "new york": "America/New_York",
                "los angeles": "America/Los_Angeles",
                "san francisco": "America/Los_Angeles",
                "chicago": "America/Chicago",
                "paris": "Europe/Paris",
                "berlin": "Europe/Berlin",
                "dubai": "Asia/Dubai",
                "singapore": "Asia/Singapore",
                "sydney": "Australia/Sydney",
            }
            
            tz_name = common_tz.get(location.lower())
            
            if not tz_name:
                # Last resort: just try to put it in pytz if it looks like one
                if "/" in location:
                    tz_name = location
                else:
                    return f"I can't determine the timezone for {location} yet. Please try specifying 'Asia/Tokyo' or 'America/New_York'."

            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            return f"The current time in {location} ({tz_name}) is {now.strftime('%I:%M %p %Z')}."

        except Exception as e:
            logger.error(f"Error in get_current_time: {e}")
            return f"I had trouble getting the time for {location}. {str(e)}"

    @llm.function_tool(description="Get the current date.")
    def get_current_date(self):
        """Returns the current date in a readable format."""
        return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."

# API Setup Guide

To enable Weather, Flight Tracking, and Maps capabilities, you need to obtain API keys for the respective services.

## 1. Weather API (OpenWeatherMap)
**Used for:** Getting real-time weather information.
1. Go to [OpenWeatherMap](https://openweathermap.org/api).
2. Sign up for a free account.
3. Navigate to "My API Keys".
4. Copy your Main key.
5. Add it to your `.env` file:
   ```env
   OPENWEATHER_API_KEY=your_key_here
   ```

## 2. Flight Tracker API (AviationStack)
**Used for:** Checking flight status and details.
1. Go to [AviationStack](https://aviationstack.com/).
2. Sign up for a "Free" plan (100 requests/month).
3. Copy your API Access Key from the dashboard.
4. Add it to your `.env` file:
   ```env
   AVIATIONSTACK_API_KEY=your_key_here
   ```

## 3. Maps & Traffic (Google Maps Platform)
**Used for:** Directions, travel time, and traffic information.
1. Go to the [Google Cloud Console](https://console.cloud.google.com/google/maps-apis/overview).
2. Create a new project (or select an existing one).
3. Enable the following APIs in the "APIs & Services" > "Library" section:
   - **Directions API**
   - **Places API** (New)
   - **Geocoding API**
4. Go to "Credentials" and create an **API Key**.
5. Add it to your `.env` file:
   ```env
   GOOGLE_MAPS_API_KEY=your_key_here
   ```

### 💰 Cost Information
**Google Maps Platform:**
- **Free Tier:** Google provides a **$200 monthly credit** for free, which covers a significant amount of usage (e.g., thousands of requests).
- **Pay-as-you-go:** You only pay for what you use beyond the free credit.
- **Card Required:** You verified have to provide a credit/debit card to enable the account, but you are not charged unless you exceed the $200 credit.
- **Waze:** Waze data is partially integrated into Google Maps Directions/Traffic. There is no separate public Waze API for general directions that is better than Google Maps for this use case.

**OpenWeatherMap:** Free tier allows 1,000 calls/day.
**AviationStack:** Free tier allows 100 calls/month.

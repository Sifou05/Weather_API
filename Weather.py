import os

import WeatherAPI
import requests
from flask import Flask, request, jsonify
from redis import Redis
from dotenv import load_dotenv

app = flask(WeatherAPI)
load_dotenv()

redis_client = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
CACHE_EXPIRY = int(os.getenv('CACHE_EXPIRY', 43200))
app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City parameter is required.'}), 400

    # Check cache
    cached_data = redis_client.get(city.lower())
    if cached_data:
        return jsonify({'source': 'cache', 'data': eval(cached_data)})

    # Fetch from OpenWeatherMap API
    try:
        response = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={'q': city, 'appid': WEATHER_API_KEY, 'units': 'metric'}
        )
        response.raise_for_status()
        weather_data = response.json()

        # Cache the result
        redis_client.setex(city.lower(), CACHE_EXPIRY, str(weather_data))

        return jsonify({'source': 'api', 'data': weather_data})
    except requests.exceptions.HTTPError as http_err:
        return jsonify({'error': f'HTTP error occurred: {http_err}'}), response.status_code
    except Exception as err:
        return jsonify({'error': f'An error occurred: {err}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
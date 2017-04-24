import requests
import json
import urllib


L_stations = 'L06 L05 L03 L02 L01'.split()


def one_to_nyc(source, departure_time="8:00:00", exclude_stops=None,
               **options):
    exclude_stops = exclude_stops or []
    base_url = "http://transit.sidewalklabs.com/one-to-nyc"
    params = {
        "origin": {
            "lat": source[0],
            "lng": source[1],
        },
        "departureTime": departure_time,
        "options": {
            "departure_time": departure_time,
            "max_walking_distance_km": 4,
            "walking_speed_kph": 4.8,
            "max_waiting_time_secs": 1800,
            "transfer_penalty_secs": 300,
            "max_number_of_transfers": 1,
            "bus_multiplier": -1,
            "rail_multiplier": 1,
            "exclude_routes": [],
            "exclude_stops": exclude_stops,
            "require_wheelchair": False
        }
    }
    params['options'].update(options)
    params_url = urllib.parse.quote(json.dumps(params))
    url = "{}?{}".format(base_url, params_url)
    return requests.get(url).json()

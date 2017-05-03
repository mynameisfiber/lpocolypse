import api
import numpy as np
import geopandas as gp
import shapely
from tqdm import tqdm

import os
from operator import itemgetter


bbox_min = np.array((-74.255591363152206, 40.496115395170378))
bbox_max = np.array((-73.700009063871278, 40.915532776000099))
boroughs_file = ("./data/borough_shape/"
                 "geo_export_258deaa6-18f5-4fed-9165-69cd6eafca74.shp")
boroughs = gp.read_file(boroughs_file)


def _none_to_num(_iter, fill_value=0):
    for item in _iter:
        if item is None:
            yield fill_value
        else:
            yield item


def travel_vector(source, departure_time, exclude_stops):
    result = api.one_to_nyc(source, departure_time, exclude_stops)
    result = list(result.items())
    result.sort()
    keys, data = zip(*result)
    df = gp.GeoDataFrame.from_dict({"to_location": keys, "transit_time": data})
    return df


hour_cdf = [0.027789147825086381, 0.043976948862134616, 0.055854062439159725,
            0.058536046817330656, 0.062322779776828673, 0.065240602912424492,
            0.07129489948941152, 0.097915728050970596, 0.13858388205327415,
            0.201937745057821, 0.26885758163628298, 0.31740826003663597,
            0.39007364789146337, 0.43686196822662793, 0.47114804308477576,
            0.49201014258749082, 0.5501631651579344, 0.61249540075877618,
            0.6926757864077453, 0.76168272240368218, 0.85274374052029467,
            0.92071115277333693, 0.97709911767001889, 1.0]


def time_sampler():
    hour = np.searchsorted(hour_cdf, np.random.random())
    halfhour = 30 * (np.random.random() > 0.5)
    return "{:02d}:{:02d}:00".format(hour, halfhour)


def _location_sampler():
    loc = np.random.random(2)
    return loc * (bbox_max - bbox_min) + bbox_min


def location_sampler():
    while True:
        point = _location_sampler()
        point_gs = shapely.geometry.Point(*point)
        found_borough = boroughs.contains(point_gs)
        if found_borough.sum():
            borough = boroughs[found_borough].boroname.values[0]
            return list(reversed(point)), borough


if __name__ == "__main__":
    pbar = tqdm("Sampling", total=None)
    while True:
        time = time_sampler()
        location, borough = location_sampler()
        for exclude_stops in ([], api.L_stations):
            df = travel_vector(location, time, exclude_stops)
            df['location_x'], df['location_y'] = location
            df['borough'] = borough
            df['time'] = time
            df['exclude_l'] = bool(exclude_stops)

            has_L = "NO_L" if exclude_stops else 'L'
            directory = "./data/samples/{}/{}/{}/".format(has_L, time, borough)
            filename = "{},{}.pkl".format(*location)
            try:
                os.makedirs(directory)
            except IOError:
                pass
            df.to_pickle(os.path.join(directory, filename))
            pbar.update(1)

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


# hour_cdf gotten by looking at turnstile data from the MTA for april 3rd-9th.
hour_cdf = [0.031159591265737956, 0.049744326191976912,
            0.068914506276546231, 0.072767623085696648, 0.078045203229668278,
            0.081690114399689664, 0.08783637958779543, 0.1208384005365527,
            0.15669585761409446, 0.21136422660372567, 0.27236733690341774,
            0.29470539480076419, 0.36218795122116976, 0.40958770181321114,
            0.45478043917290556, 0.48015848041574349, 0.54033666454040274,
            0.60340602334297699, 0.69267813028881231, 0.76368339736116475,
            0.84983014853956684, 0.91438754766651298, 0.97678648730289552, 1.0]

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

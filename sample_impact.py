import geopandas as gp
import pandas as pd
import numpy as np
from tqdm import tqdm
import pyemd
from shapely.geometry import Point
import pylab as py

from sample_api import time_sampler
import plot_utils

from multiprocessing import Pool
import pickle
import os
import sys


def _num_samples(dirname):
    try:
        return len(os.listdir(dirname))
    except IOError:
        return 0


class LocationImpact(gp.GeoDataFrame):
    borough_cdfs = {}
    boroughs = []

    def __init__(self):
        self.borough_cdfs, self.boroughs = self._calc_borough_cdf()
        self.geoid_distances = np.load("./data/geoid_sorted_distances.npy")

    def _calc_borough_cdf(self):
        borough_cdfs = {}
        boroughs = os.listdir("./data/samples/L/00:00:00")
        for time in os.listdir("./data/samples/L"):
            weights = [
                _num_samples(os.path.join(
                    "./data/samples/L/",
                    time,
                    b
                ))
                for b in boroughs
            ]
            weights_cdf = np.cumsum(weights).astype('float32')
            weights_cdf /= weights_cdf[-1]
            borough_cdfs[time] = weights_cdf
        return borough_cdfs, boroughs

    def borough_sampler(self, time):
        idx = np.searchsorted(self.borough_cdfs[time], np.random.random())
        return self.boroughs[idx]

    def sample_transit_vector(self, time=None, borough=None):
        time = time or time_sampler()
        borough = borough or self.borough_sampler(time)
        datadir = os.path.join(
            "./data/samples/L/",
            time,
            borough,
        )
        points_str = os.listdir(datadir)
        location_str = np.random.choice(points_str)

        dfs = []
        for exclude_l in ("L", "NO_L"):
            filename = os.path.join(
                "./data/samples/",
                exclude_l,
                time,
                borough,
                location_str
            )
            try:
                with open(filename, 'rb') as fd:
                    dfs.append(pickle.load(fd))
            except IOError:
                return self.sample_transit_vector(time, borough)
        return pd.concat(dfs)

    def sample_impact(self, time=None, borough=None):
        df = self.sample_transit_vector(time, borough)
        df_loc = df.set_index('to_location').fillna(0)
        df_l = df_loc.query('exclude_l == False')
        df_nol = df_loc.query('exclude_l == True')

        impact = pyemd.emd(
            np.ascontiguousarray(df_nol.transit_time.values),
            np.ascontiguousarray(df_l.transit_time.values),
            self.geoid_distances
        )
        df_new = (df.drop(['transit_time', 'to_location', 'exclude_l'], axis=1)
                  .drop_duplicates())
        df_new['impact'] = impact
        return df_new, df


def _exception_eater(f):
    try:
        return f()
    except Exception as e:
        print('Ate exception while sampling: {}'.format(e))
    except KeyboardInterrupt:
        raise
    return None


def multiprocess_sampler(f, N):
    pool = Pool()
    samples = pool.map(lambda *args, **kwargs: _exception_eater(f),
                       tqdm(range(N)),
                       chunksize=32)
    return list(filter(None, samples))


if __name__ == "__main__":
    sampler = LocationImpact()

    df = pd.concat(multiprocess_sampler(
        lambda *args, **kwargs: sampler.sample_impact(),
        10000
    ))
    points = [Point(xy) for xy in zip(df.location_x, df.location_y)]
    crs = {'init': 'epsg:4326'}
    gdf = gp.GeoDataFrame(df, crs=crs, geometry=points)

    for borough in (None, 'Brooklyn', 'Queens', 'Bronx',
                    'Manhattan', 'Staten Island'):
        print("Plotting for: " + (borough or 'nyc'))
        if borough:
            subset = gdf.query('borough == "{}"'.format(borough))
        else:
            subset = gdf

        py.clf()
        plot_utils.plot_points(subset, 'impact', (1024, 1024))
        py.savefig("figures/impact_{}.png".format(borough or 'nyc'),
                   dpi=600)

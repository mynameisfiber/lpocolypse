import geopandas as gp
import pandas as pd
import numpy as np
from tqdm import tqdm
from scipy.spatial import distance
from scipy.stats import entropy
from shapely.geometry import Point
import pylab as py

from sample_api import time_sampler
import plot_utils

import pickle
import os


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

        impact_cos = 1 - distance.cosine(
            df_nol.transit_time,
            df_l.transit_time
        )
        impact_kl = distance.cosine(
            df_nol.transit_time,
            df_l.transit_time
        )
        df_new = (df.drop(['transit_time', 'to_location', 'exclude_l'], axis=1)
                  .drop_duplicates())
        df_new['impact_cos'] = 1 - impact_cos
        df_new['impact_kl'] = impact_kl
        return df_new


def sampler_exception_eater(f, N):
    with tqdm(total=N, desc='Sampling') as pbar:
        while N > 0:
            try:
                yield f()
                N -= 1
                pbar.update(1)
            except Exception as e:
                print('Ate exception while sampling: {}'.format(e))
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    sampler = LocationImpact()

    df = pd.concat(list(sampler_exception_eater(
        lambda: sampler.sample_impact(),
        10000
    )))
    points = [Point(xy) for xy in zip(df.location_x, df.location_y)]
    crs = {'init': 'epsg:4326'}
    gdf = gp.GeoDataFrame(df, crs=crs, geometry=points)

    py.clf()
    plot_utils.plot_points(gdf, 'figures/impact_kl', (1024, 1024))
    py.savefig("impact_kl.png", dpi=600)

    py.clf()
    plot_utils.plot_points(gdf, 'figures/impact_cos', (1024, 1025))
    py.savefig("impact_cos.png", dpi=600)

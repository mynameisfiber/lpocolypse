import pylab as py
import numpy as np
import geopandas as gp
from sklearn.neighbors import KNeighborsRegressor


def plot_points(data, field, bins=(100, 100), percentile=True):
    knn = KNeighborsRegressor(n_neighbors=12, weights='distance')
    if percentile is False:
        accessor = lambda d: d[field]
    else:
        values = data[field].sort(inplace=False)
        accessor = lambda d: (np.searchsorted(values, d[field],
                                              side='right')[0] *
                              100 / len(values))
    X, y = zip(*[((d.geometry.coords[0][1], d.geometry.coords[0][0]),
                  accessor(d))
                 for i, d in data.iterrows()])
    knn.fit(X, y)

    x0 = min(x[0] for x in X)
    x1 = max(x[0] for x in X)
    y0 = min(x[1] for x in X)
    y1 = max(x[1] for x in X)

    xx, yy = np.meshgrid(np.linspace(x0, x1, bins[0]),
                         np.linspace(y0, y1, bins[1]))
    Z = knn.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    boroughs_file = ("./data/borough_shape/"
                     "geo_export_258deaa6-18f5-4fed-9165-69cd6eafca74.shp")
    boroughs = gp.read_file(boroughs_file)
    subway = gp.read_file("./data/subway_shape/nyctsubwayroutes_100627.shp")

    boroughs.plot(color='white', alpha=0.5, ax=py.gca())
    py.pcolormesh(xx, yy, Z)
    py.xlim(xx.min(), xx.max())
    py.ylim(yy.min(), yy.max())
    py.xticks(())
    py.yticks(())
    py.colorbar()
    py.tight_layout()
    subway.plot(ax=py.gca())

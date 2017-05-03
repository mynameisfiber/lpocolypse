import pandas as pd
import datetime

cdf = []

try:
    turnstiles = pd.read_csv('./data/turnstile_170401.txt')
except IOError:
    cdf = [0.027789147825086381, 0.043976948862134616, 0.055854062439159725,
           0.058536046817330656, 0.062322779776828673, 0.065240602912424492,
           0.07129489948941152, 0.097915728050970596, 0.13858388205327415,
           0.201937745057821, 0.26885758163628298, 0.31740826003663597,
           0.39007364789146337, 0.43686196822662793, 0.47114804308477576,
           0.49201014258749082, 0.5501631651579344, 0.61249540075877618,
           0.6926757864077453, 0.76168272240368218, 0.85274374052029467,
           0.92071115277333693, 0.97709911767001889, 1.0]

if not cdf:
    # fix column name
    col = list(turnstiles.columns)
    col[-1] = 'EXITS'
    turnstiles.columns = col

    # construct datetime column for turnstile counts across midnight
    turnstiles['datetime'] = turnstiles.apply(lambda x: datetime.datetime.strptime(
        x['DATE'] + ' ' + x['TIME'], '%m/%d/%Y %H:%M:%S'), axis=1)

    diffs = turnstiles.groupby(
        ['C/A', 'UNIT', 'SCP', 'STATION', 'LINENAME'])[['ENTRIES', 'EXITS', 'datetime']].diff()
    diffs.columns = ['dEntry', 'dExit', 'dTime']
    turnstiles = turnstiles.join(diffs)

    turnstiles['dEntry'] = abs(turnstiles['dEntry'])
    turnstiles['dExit'] = abs(turnstiles['dExit'])
    turnstiles = turnstiles.dropna()
    turnstiles = turnstiles[~turnstiles['DATE'].isin(
        ['03/25/2017', '03/26/2017'])]  # discard weekend
    turnstiles = turnstiles[turnstiles['dEntry'] < 5000]
    # truncate times at hour
    turnstiles['TIME'] = turnstiles['TIME'].map(lambda x: datetime.datetime.strptime(
        x, '%H:%M:%S').time().replace(minute=0, second=0))
    binned = turnstiles.groupby(['TIME']).agg(
        {'dEntry': 'sum', 'TIME': 'count'})
    normalized = pd.DataFrame(
        {'nEntry': binned['dEntry'] / binned['TIME']}, index=binned.index)

    cdf = list(np.cumsum(normalized['nEntry'] /
                         normalized['nEntry'].sum()))

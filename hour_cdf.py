import pandas as pd
import datetime

# http://web.mta.info/developers/data/nyct/turnstile/turnstile_170401.txt
turnstiles = pd.read_csv('./data/turnstile_170401.txt')

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

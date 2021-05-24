"""Remotely control your Coinbase Pro account via their API"""

import pandas as pd
import re

import requests

from datetime import datetime, timedelta


class AuthAPIBase():
    def _isMarketValid(self, market):
        p = re.compile(r"^[1-9A-Z]{2,5}\-[1-9A-Z]{2,5}$")
        return p.match(market)


class PublicAPI(AuthAPIBase):
    def __init__(self):
        # options
        self.debug = False
        self.die_on_api_error = False

        self.api_url = 'https://api.pro.coinbase.com/'

    def getHistoricalData(self, market='BTC-EUR', granularity=3600, iso8601start='', iso8601end=''):
        # validates the market is syntactically correct
        if not self._isMarketValid(market):
            raise TypeError('Coinbase Pro market required.')

        # validates granularity is an integer
        if not isinstance(granularity, int):
            raise TypeError('Granularity integer required.')

        # validates the granularity is supported by Coinbase Pro
        if not granularity in [60, 300, 900, 3600, 21600, 86400]:
            raise TypeError(
                'Granularity options: 60, 300, 900, 3600, 21600, 86400')

        # validates the ISO 8601 start date is a string (if provided)
        if not isinstance(iso8601start, str):
            raise TypeError('ISO8601 start integer as string required.')

        # validates the ISO 8601 end date is a string (if provided)
        if not isinstance(iso8601end, str):
            raise TypeError('ISO8601 end integer as string required.')

        # if only a start date is provided
        if iso8601start != '' and iso8601end == '':
            multiplier = 1
            if(granularity == 60):
                multiplier = 1
            elif(granularity == 300):
                multiplier = 5
            elif(granularity == 900):
                multiplier = 10
            elif(granularity == 3600):
                multiplier = 60
            elif(granularity == 21600):
                multiplier = 360
            elif(granularity == 86400):
                multiplier = 1440

            # calculate the end date using the granularity
            iso8601end = str((datetime.strptime(iso8601start, '%Y-%m-%dT%H:%M:%S.%f') +
                              timedelta(minutes=granularity * multiplier)).isoformat())

        resp = self.authAPI('GET', 'products/' + market + '/candles?granularity=' +
                            str(granularity) + '&start=' + iso8601start + '&end=' + iso8601end)

        # convert the API response into a Pandas DataFrame
        df = pd.DataFrame(
            resp, columns=['epoch', 'low', 'high', 'open', 'close', 'volume'])
        # reverse the order of the response with earliest last
        df = df.iloc[::-1].reset_index()

        if(granularity == 60):
            freq = 'T'
        elif(granularity == 300):
            freq = '5T'
        elif(granularity == 900):
            freq = '15T'
        elif(granularity == 3600):
            freq = 'H'
        elif(granularity == 21600):
            freq = '6H'
        else:
            freq = 'D'

        # convert the DataFrame into a time series with the date as the index/key
        try:
            tsidx = pd.DatetimeIndex(pd.to_datetime(
                df['epoch'], unit='s'), dtype='datetime64[ns]', freq=freq)
            df.set_index(tsidx, inplace=True)
            df = df.drop(columns=['epoch', 'index'])
            df.index.names = ['ts']
            df['date'] = tsidx
        except ValueError:
            tsidx = pd.DatetimeIndex(pd.to_datetime(
                df['epoch'], unit='s'), dtype='datetime64[ns]')
            df.set_index(tsidx, inplace=True)
            df = df.drop(columns=['epoch', 'index'])
            df.index.names = ['ts']
            df['date'] = tsidx

        df['market'] = market
        df['granularity'] = granularity

        # re-order columns
        df = df[['date', 'market', 'granularity',
                 'low', 'high', 'open', 'close', 'volume']]

        return df

    def getTicker(self, market='BTC-GBP'):
       # validates the market is syntactically correct
        if not self._isMarketValid(market):
            raise TypeError('Coinbase Pro market required.')

        resp = self.authAPI('GET', 'products/' + market + '/ticker')
        if 'price' in resp:
            return float(resp['price'])

        return 0.0

    def getTime(self):
        """Retrieves the exchange time"""

        try:
            resp = self.authAPI('GET', 'time')
            epoch = int(resp['epoch'])
            return datetime.fromtimestamp(epoch)
        except:
            return None

    def authAPI(self, method, uri, payload=''):
        if not isinstance(method, str):
            raise TypeError('Method is not a string.')

        if not method in ['GET', 'POST']:
            raise TypeError('Method not GET or POST.')

        if not isinstance(uri, str):
            raise TypeError('Method is not a string.')

        try:
            if method == 'GET':
                resp = requests.get(self.api_url + uri)
            elif method == 'POST':
                resp = requests.post(self.api_url + uri, json=payload)

            if resp.status_code != 200:
                if self.die_on_api_error:
                    raise Exception(method.upper() + 'GET (' + '{}'.format(resp.status_code) + ') ' +
                                    self.api_url + uri + ' - ' + '{}'.format(resp.json()['message']))
                else:
                    print('error:', method.upper() + ' (' + '{}'.format(resp.status_code) +
                          ') ' + self.api_url + uri + ' - ' + '{}'.format(resp.json()['message']))
                    return pd.DataFrame()

            resp.raise_for_status()
            json = resp.json()
            return json

        except requests.ConnectionError as err:
            if self.debug:
                if self.die_on_api_error:
                    raise SystemExit(err)
                else:
                    print(err)
                    return pd.DataFrame()
            else:
                if self.die_on_api_error:
                    raise SystemExit('ConnectionError: ' + self.api_url)
                else:
                    print('ConnectionError: ' + self.api_url)
                    return pd.DataFrame()

        except requests.exceptions.HTTPError as err:
            if self.debug:
                if self.die_on_api_error:
                    raise SystemExit(err)
                else:
                    print(err)
                    return pd.DataFrame()
            else:
                if self.die_on_api_error:
                    raise SystemExit('HTTPError: ' + self.api_url)
                else:
                    print('HTTPError: ' + self.api_url)
                    return pd.DataFrame()

        except requests.Timeout as err:
            if self.debug:
                if self.die_on_api_error:
                    raise SystemExit(err)
                else:
                    print(err)
                    return pd.DataFrame()
            else:
                if self.die_on_api_error:
                    raise SystemExit('Timeout: ' + self.api_url)
                else:
                    print('Timeout: ' + self.api_url)
                    return pd.DataFrame()

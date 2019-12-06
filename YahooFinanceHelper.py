# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 09:16:30 2019

@author: nhoang

modified from: https://stackoverflow.com/questions/39218742/using-beautifulsoup-to-search-through-yahoo-finance
"""
import re
#import json
from datetime import datetime, timedelta

import requests
import pandas as pd


class YahooHistoricalData:
    timeout = 2
    crumb_link = 'https://finance.yahoo.com/quote/{0}/history?p={0}'
    crumble_regex = r'CrumbStore":{"crumb":"(.*?)"}'
    quote_link = 'https://query2.finance.yahoo.com/v8/finance/chart/{quote}?formatted=true&crumb={crumb}\
                &lang=en-US&region=US&period1={dfrom}&period2={dto}&interval=1d&events=div%7Csplit\
                &corsDomain=finance.yahoo.com'
    
    def __init__(self, symbol, days_back=7):
        self.symbol = symbol
        self.session = requests.Session()
        self.dt = timedelta(days=days_back)
        
    def get_crumb(self):
        response = self.session.get(self.crumb_link.format(self.symbol), timeout=self.timeout)
        response.raise_for_status()
        match = re.search(self.crumble_regex, response.text)
        if not match:
            raise ValueError('Could not get crumb from Yahoo Finance')
        else:
            self.crumb = match.group(1)
    
    def get_quote(self):
        if not hasattr(self, 'crumb') or len(self.session.cookies) == 0:
            self.get_crumb()
        now = datetime.utcnow()
        dateto = int(now.timestamp())
        datefrom = int((now - self.dt).timestamp())
        
        url = self.quote_link.format(quote=self.symbol, dfrom=datefrom, dto=dateto, crumb=self.crumb)
        #print(url)
        response = self.session.get(url)
        response.raise_for_status()
        data = response.json()
        #json_string = json.loads(response.text)
        
        dates = data['chart']['result'][0]['timestamp']
        highs = data['chart']['result'][0]['indicators']['quote'][0]['high']
        lows = data['chart']['result'][0]['indicators']['quote'][0]['low']
        opens = data['chart']['result'][0]['indicators']['quote'][0]['open']
        closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
        volumes = data['chart']['result'][0]['indicators']['quote'][0]['volume']
        adjcloses = data['chart']['result'][0]['indicators']['adjclose'][0]['adjclose']
        
        quote_dict = {'Date':dates, 'Open':opens, 'High':highs, 'Low':lows, 'Close':closes, 'Adj Close':adjcloses,
                     'Volume':volumes}
        df = pd.DataFrame(quote_dict)
        df['Date'] = pd.to_datetime(df['Date'],unit='s').dt.date
        df.dropna(inplace=True)
        df.set_index('Date', inplace=True)
        return df
    
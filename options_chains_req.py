#%%
# Import the client
from td.client import TDClient
import datetime
import time
from yahoo_earnings_calendar import YahooEarningsCalendar
import csv
from datetime import date
import pickle
from config import client_id, redirect_uri

import json 
import os 
import re

def get_front_date(date_delta):
    dates_list = []
    for i in range(0, date_delta):
        d = datetime.date.today()
        d += datetime.timedelta(i)
        if d.weekday() == 4:
            dates_list.append(str(d))
    #print(dates_list[-2])
    return dates_list[-2]

def get_back_date(date_delta):
    dates_list = []
    for i in range(0, date_delta):
        d = datetime.date.today()
        d += datetime.timedelta(i)
        if d.weekday() == 4:
            dates_list.append(str(d))
    #print(dates_list[-1])
    return dates_list[-1]

# Create a new session, credentials path is optional.
TDSession = TDClient(
    client_id= client_id,
    redirect_uri= redirect_uri,
    credentials_path=''
)

# Login to the session
TDSession.login()

# ========= scanner parameters ==========
option_price_threshold = 0.25     # front expiration mark price
calendar_ratio_threshold = 0.65    # front expiration mark price / back mark price (higher is better)
spread_ratio_threshold = 0.7      # front expiration ask-bid / mark  (should be low)
OTM_amount = 1.06                   # how far OTM do we scan?

symbol = "MSFT"
date_delta = 20 
front_date = get_front_date(date_delta)
back_date = get_back_date(date_delta) 

# ========= check earnings calendar ==========
date_from = datetime.datetime.strptime(date.today().strftime('%Y-%m-%d') + " 05:00:00",  '%Y-%m-%d %X')
date_to = datetime.datetime.strptime(front_date + " " + "18:00:00", '%Y-%m-%d %X')
#print(date_from, date_to)


symbols = []
watchlist_filename = "./2020-11-04-watchlist.csv"
with open(watchlist_filename, newline="") as watchlist_file:
    fr = csv.reader(watchlist_file, delimiter=',', quotechar='|')
    for row in fr:
        if len(row) > 1 and row[0] != "Symbol":
            symbols.append(row[0])


options_chains_list = [

]

for symbol in symbols:
    #options_chains_dict = {
    #}
    opt_chain = {
        'symbol': symbol,
        'contractType': 'CALL',
        'optionType': 'S',
        'fromDate': front_date,
        'toDate': back_date,
        #'strikeCount': 15,
        'includeQuotes': True,
        'range': 'OTM',
        'strategy': 'SINGLE',
    }
    option_chains = TDSession.get_options_chain(option_chain=opt_chain)
    try:
        quote = option_chains['underlying']['mark']
        strikes_otm = OTM_amount * quote
    except:
        print("error getting stock quote for", symbol)
    front_chain = {};
    back_chain = {};
    for x in (option_chains['callExpDateMap']):
        if front_date in x:
            front_chain = option_chains['callExpDateMap'].get(x)
        if back_date in x:
            back_chain= option_chains['callExpDateMap'].get(x)
    options_chains_list.append(option_chains)
    print('slep')
    time.sleep(.5)
    print('resume')
with open('options_chains_list.json', 'w') as f:
    json.dump(options_chains_list, f)
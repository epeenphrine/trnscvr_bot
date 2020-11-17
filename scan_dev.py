
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

# get s and p 500 symbols
symbols = []
watchlist_filename = "./2020-11-04-watchlist.csv"
with open(watchlist_filename, newline="") as watchlist_file:
    fr = csv.reader(watchlist_file, delimiter=',', quotechar='|')
    for row in fr:
        if len(row) > 1 and row[0] != "Symbol":
            symbols.append(row[0])

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
golden_ratio = 0.85                # mark options that have really good ratios
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

yec = YahooEarningsCalendar()

date_range = [
    front_date, back_date
]
# cache the earnings calendar so we don't need to scrape it every time we scan
#def date_check():
    #date_range = [
        #front_date, back_date
    #]
    #if os.path.isfile('date_range.json'):
        #with open('date_range.json', 'r') as f:
            #config_json = json.load(f)
        #if config_json == date_range:
            #return
        #else:
            #return yec.earnings_between(date_from, date_to)
    #else:
        #with open('date_range.json', 'w') as f:
            #json.dump(date_range, f)
        #return yec.earnings_between(date_from, date_to)

def get_earnings_dates_from_yahoo():
    '''
        get earnings date and ticker from yahoo calendar library
        save as format:
        [
            {
            ticker: 'string',
            date: 'string',
            },
            ...
        ]


    '''
    #print('getting earnings dates from yahoo')
    earnings_list= []
    #print(yec.earnings_on(date_from))
    #earnings_calendar = yec.earnings_between(date_from, date_to) # <-- get request for yahoo calendar ehre
    earnings_calendar =yec.earnings_between(date_from, date_to)
    #print(earnings_calendar)
    if earnings_calendar:
        for company in earnings_calendar:
            earnings_dict = {}
            earnings_dict['ticker'] = company['ticker']
            earnings_dict['date'] = re.findall('\d\d\d\d-\d\d-\d\d',company['startdatetime'])[0]
            earnings_list.append(earnings_dict)
            print(earnings_dict)
            #print(earnings_list)
        with open('companies_earnings.json', 'w') as f:
            json.dump(earnings_list, f)
        with open('date_range.json', 'w') as f:
            json.dump(date_range, f)
        return earnings_list
    #print('finished getting earnings date from yahoo')

    # ========= load watchlist (saved as csv from TOS) ==========
#print(symbols)

## file check
if os.path.isfile('companies_earnings.json') and os.path.isfile('date_range.json'):
    with open('date_range.json', 'r') as f:
        date_range_json = json.load(f)
    if date_range_json == date_range:
        with open('companies_earnings.json', 'r') as f:
            earnings_calendar = json.load(f)
    else:
        #print('getting new dates')
        earnings_calendar = get_earnings_dates_from_yahoo()
else:
    #print("files don't exist creating new ones")
    earnings_calendar = get_earnings_dates_from_yahoo()
#print('finished checking')

# ========= main scanner function ==========
# oneline: print out full ratio information or only the strikes
#%%
def scan_calendar_ratio(filename, oneline = False):
    with open(filename) as f:
        options_chains_list = json.load(f)
        output_list = []

        for option_chains in options_chains_list:
            output_string = ""
            symbol = option_chains['symbol']

            try:
                quote = option_chains['underlying']['mark']
                strikes_otm = OTM_amount * quote
            except:
                print("error getting stock quote for", symbol)
                continue

            front_chain = {};
            back_chain = {};
            for x in (option_chains['callExpDateMap']):
                if front_date in x:
                    front_chain = option_chains['callExpDateMap'].get(x)
                if back_date in x:
                    back_chain= option_chains['callExpDateMap'].get(x)
            #print(option_chains)
            #print(front_chain)
            #print(back_chain)


            symbol_printed = False

            bad_spread_count = 0
            for strike in front_chain:
                #print(strike)
                if float(strike) < strikes_otm:
                    continue
                is_bad_spread = False
                if strike in back_chain:
                    front_mark = front_chain.get(strike)[0]['mark']
                    if front_mark < option_price_threshold:
                        break
                    if (front_chain.get(strike)[0]['ask'] - front_chain.get(strike)[0]['bid']) / front_mark > spread_ratio_threshold:
                        bad_spread_count = bad_spread_count + 1
                        is_bad_spread = True
                    if bad_spread_count >= 3:
                        break
                    if back_chain.get(strike)[0]['mark'] <= 0:
                        continue
                    ratio = front_mark / back_chain.get(strike)[0]['mark']
                    if ratio > calendar_ratio_threshold:
                        if not is_bad_spread:
                            if oneline:
                                # print all the strikes for each symbol in one line
                                if not symbol_printed:
                                    output_string += (symbol + " ")
                                    filtered = next((sub for sub in earnings_calendar if sub['ticker'] == symbol), None)
                                    if filtered:
                                        re_filter = re.findall('\d\d\d\d\-\d\d-\d\d', filtered['date'])[0]
                                        output_string += (f"/ (ER: {re_filter}) /" + " ")
                                    symbol_printed = True
                                output_string += strike
                                if ratio > golden_ratio:
                                    output_string += ("*")
                                output_string += (" ")
                            else:
                                # print a separte line for each option strike
                                output_string += (symbol, strike, front_chain.get(strike)[0]['mark'], back_chain.get(strike)[0]['mark'], ratio, "badspread" if is_bad_spread else "")
                                output_list.append(output_string)
                                output_string = ""
            if oneline and symbol_printed:
                output_list.append(output_string)
    return output_list


print(date_range)
scan_calendar_ratio('options_chains_list.json', oneline=True)

#%%  should be in separate file
def get_option_chains():
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

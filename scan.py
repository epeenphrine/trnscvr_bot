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

def get_front_date(date_delta):
    dates_list = []
    for i in range(0, date_delta):
        d = datetime.date.today()
        d += datetime.timedelta(i)
        if d.weekday() == 4:
            dates_list.append(str(d))
    print(dates_list[-2])
    return dates_list[-2]

def get_back_date(date_delta):
    dates_list = []
    for i in range(0, date_delta):
        d = datetime.date.today()
        d += datetime.timedelta(i)
        if d.weekday() == 4:
            dates_list.append(str(d))
    print(dates_list[-1])
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
watchlist_filename = "./2020-11-04-watchlist.csv"

# ========= check earnings calendar ==========
date_from = datetime.datetime.strptime(date.today().strftime('%Y-%m-%d') + " 05:00:00",  '%Y-%m-%d %X')
date_to = datetime.datetime.strptime(front_date + " " + "18:00:00", '%Y-%m-%d %X')
#print(date_from, date_to)

yec = YahooEarningsCalendar()
# cache the earnings calendar so we don't need to scrape it every time we scan
try:
    f = open("earnings_calendar.txt", 'rb')
    x = pickle.load(f)
    date_read = x[0]
    if date_read != date_to:
        raise ValueError("earnings calendar update required")
    else:
        earnings_tickers = x[1]
except:
    print("updating earnings calendar")
    #print(yec.earnings_on(date_from))
    earnings_calendar = yec.earnings_between(date_from, date_to)
    #print(earnings_calendar)

    earnings_tickers = [x['ticker'] for x in earnings_calendar]
    earnings_date= [x['startdatetime'] for x in earnings_calendar]

    f = open("earnings_calendar.txt", 'wb')
    pickle.dump([date_to, earnings_tickers], f)

#print(earnings_date)

# ========= load watchlist (saved as csv from TOS) ==========
symbols = []
with open(watchlist_filename, newline="") as watchlist_file:
    fr = csv.reader(watchlist_file, delimiter=',', quotechar='|')
    for row in fr:
        if len(row) > 1 and row[0] != "Symbol":
            symbols.append(row[0])

#print(symbols)

# ========= main scanner function ==========
# oneline: print out full ratio information or only the strikes
#%%
def scan_calendar_ratio(symbol, oneline = False):
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

    # Get Option Chains
    option_chains = TDSession.get_options_chain(option_chain=opt_chain)
    try:
        quote = option_chains['underlying']['mark']
        strikes_otm = OTM_amount * quote
    except:
        print("error getting stock quote for", symbol)
        return
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
            ratio = front_mark/ back_chain.get(strike)[0]['mark']
            if ratio > calendar_ratio_threshold:
                if not is_bad_spread:
                    if oneline:
                        if not symbol_printed:
                            print(symbol,  end=" ")
                            if symbol in earnings_tickers:
                                print("(ER)", end=" ")
                                print("")
                            symbol_printed = True
                        print(strike, end=" ")
                    else:
                        print(symbol, strike, front_chain.get(strike)[0]['mark'], back_chain.get(strike)[0]['mark'], ratio, "badspread" if is_bad_spread else "")
    if oneline and symbol_printed: print(" ")
for symbol in symbols:
    scan_calendar_ratio(symbol, oneline=True)
    time.sleep(.6)
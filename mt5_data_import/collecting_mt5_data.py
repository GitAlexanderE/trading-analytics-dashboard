from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import mysql.connector
import os.path
import MetaTrader5 as mt5


def get_session(dt):
    hour = dt.hour
    if 2 <= hour < 6:
        return 'Asia'
    elif 8 <= hour < 11:
        return 'London'
    elif 11 <= hour < 13:
        return 'Lunch'
    elif 13 <= hour < 16:
        return 'New York'
    elif 16 <= hour < 18:
        return 'London Close'
    else:
        return 'Out of Session'

def upload_df_with_update(df, table_name, primary_key):
    # columns to insert
    cols = df.columns.tolist()

    # %s is a placeholder for a value in a SQL query
    placeholders = ",".join(["%s"] * len(cols))

    # Update columns (without the primary key as this gives uniqueness - avoids duplicates)
    # List comprehension [EXPRESSION for ITEM in LIST if CONDITION] and expression = what I want to include in the new list
    update_cols = [col for col in cols if col not in primary_key]
    update_stmt = ",".join([f"{col}=VALUES({col})" for col in update_cols])
    # -> ["symbol=VALUES(symbol)", "volume=VALUES(volume)", "profit=VALUES(profit)", "time=VALUES(time)"]

    # Complete query:
    sql = f"INSERT INTO {table_name} ({','.join(cols)})VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_stmt}"

    # Converts DataFrame rows to list of tuples
    data = [tuple(x) for x in df.to_numpy()]

    mycursor.executemany(sql, data)
    mydb.commit()
    print(f"{mycursor.rowcount} rows inserted/updated in {table_name}.")


register_matplotlib_converters()

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

account = 5044355516
password = os.getenv("METAQUOTESDEMO_PASSWORD")
server = "MetaQuotes-Demo"

# Login
authorized = mt5.login(account, password=password, server=server, timeout=60)

if authorized:
    print(f"Connected to account #{account} ")
else:
    error_code, error_msg = mt5.last_error()
    print(f"Failed to connect to account #{account}, error code: {error_code}, error message: {error_msg}")

# Account info
time_last_update = datetime.now(tz=timezone.utc)

if authorized:
    account_info = mt5.account_info()
    if account_info != None:  # Returns None in case of an error
        print(f"Account balance: €{account_info.balance}")
        print(f"Current account equity: €{account_info.equity}")
        print(f"Current profit: €{account_info.profit}")
        print(f"Account mode (0 - Demo, 1 - Live, 2 - Strategy Tester, 3 - Contest Mode): {account_info.trade_mode}")

        accountinfo = [[
            account_info.login,
            account_info.trade_mode,
            account_info.balance,
            account_info.equity,
            account_info.profit,
            account_info.company,
            account_info.currency,
            time_last_update
        ]]

columns_accountinfo = [
    "account_login_number",
    "trade_mode",
    "balance",
    "equity",
    "profit",
    "company",
    "currency",
    "time_last_update"
]

df_account = pd.DataFrame(accountinfo, columns=columns_accountinfo)
df_account['time_last_update'] = pd.to_datetime(df_account['time_last_update'])

# Data about open positions
active_positions = mt5.positions_get()

activepositions = [
    [
        position.identifier,
        position.symbol,
        position.volume,
        position.price_open,
        position.sl,
        position.tp,
        position.swap,
        position.profit,
        datetime.fromtimestamp(position.time, tz=timezone.utc),
        time_last_update
    ] for position in active_positions
] if active_positions else []

columns_active = [
    "position_id",
    "symbol",
    "volume",
    "price_open",
    "sl",
    "tp",
    "swap",
    "profit",
    "time_open",
    "time_last_update"
]

df_active = pd.DataFrame(activepositions, columns=columns_active)
df_active['time_open'] = pd.to_datetime(df_active['time_open'])
df_active['time_last_update'] = pd.to_datetime(df_active['time_last_update'])


# Data about already closed positions
utc_to = datetime.now()
utc_from = utc_to - timedelta(days=5474)  # 15 years
closed_positions = mt5.history_deals_get(utc_from, utc_to)

closedpositions = [
    [position.position_id,
     position.symbol,
     position.volume,
     position.price,
     position.swap,
     position.profit,
     position.fee,
     datetime.fromtimestamp(position.time, tz=timezone.utc),
     ]
    for position in closed_positions
] if closed_positions else []

columns_closed = [
    "position_id",
    "symbol",
    "volume",
    "price",
    "swap",
    "profit",
    "fee",
    "time_close"
]

df_closed = pd.DataFrame(closedpositions, columns=columns_closed)
df_closed['time_close'] = pd.to_datetime(df_closed['time_close'])

# Store all deals in a list where entry = 0 (-> Opening)
open_deals = [d for d in closed_positions if d.entry == 0]  # 0 = Opening
#Earliest opening time and opening price per positions
open_info = {}
for deal in open_deals:
    pid = deal.position_id
    if pid not in open_info or deal.time < open_info[pid]['time_open']:
        open_info[pid] = {
            'time_open': datetime.fromtimestamp(deal.time, tz=timezone.utc),
            'open_price': deal.price
        }

# One trade can have multiple deals when closing partials -> aggregated positions
df_closed_agg = df_closed.groupby('position_id').agg(
    symbol=('symbol','first'),
    volume=('volume','sum'),
    close_price=('price','last'),
    profit=('profit','sum'),
    swap=('swap','sum'),
    fee=('fee','sum'),
    time_close=('time_close','max')
).reset_index()

# Map Open-Time und Open-Price
df_closed_agg['time_open'] = df_closed_agg['position_id'].map(lambda pid: open_info.get(pid, {}).get('time_open', None))
df_closed_agg['open_price'] = df_closed_agg['position_id'].map(lambda pid: open_info.get(pid, {}).get('open_price', None))

# Daily Stats (for closed positions)
# Weekday
df_closed_agg['weekday_num'] = df_closed_agg['time_open'].dt.weekday

weekday_map = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
}
df_closed_agg['weekday'] = df_closed_agg['weekday_num'].map(weekday_map)
df_closed_agg.drop(columns=['weekday_num'], inplace=True)

# Sessions
# Add session to each open_info entry
for pid, info in open_info.items():
    info['session'] = get_session(info['time_open'])

# Add session column to aggregated df
df_closed_agg['session'] = df_closed_agg['position_id'].map(lambda pid: open_info.get(pid, {}).get('session', 'Unknown'))


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="trades"
)

mycursor = mydb.cursor()

# Clear open positions from MySQL first
mycursor.execute("TRUNCATE TABLE open_positions")
mydb.commit()
df_active = df_active.where(pd.notnull(df_active), None)

df_closed_agg = df_closed_agg.where(pd.notnull(df_closed_agg), None)
df_account = df_account.where(pd.notnull(df_account), None)


upload_df_with_update(df_active, 'open_positions', primary_key='position_id')
upload_df_with_update(df_closed_agg, 'closed_positions', primary_key='position_id')
upload_df_with_update(df_account, 'account', primary_key=['account_login_number', 'time_last_update'])

mycursor.close()
mydb.close()

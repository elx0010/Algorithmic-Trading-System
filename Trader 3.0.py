import time, mysql.connector, os, requests, uuid, json, pandas as pd, numpy as np
from coinbase import jwt_generator
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()


pd.options.mode.copy_on_write = True
database_password = os.getenv("DB_Password")
host = os.getenv("host")
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
create_order_url = 'https://api.coinbase.com/api/v3/brokerage/orders'
create_order_path = '/api/v3/brokerage/orders'
request_post = "POST"
request_get = "GET"
candle_url = "https://api.coinbase.com/api/v3/brokerage/products/ETH-USD/candles"
candle_path = "/api/v3/brokerage/products/ETH-USD/candles"
accounts_url = "https://api.coinbase.com/api/v3/brokerage/accounts"
accounts_path = "/api/v3/brokerage/accounts"
period = 14
granularity = "FOUR_HOUR"



# MYSQL database connection
db = mysql.connector.connect(
    host=host,
    user="root",
    password=database_password,
    database="trader"
)
cursor = db.cursor()




# JWT generation Functions
def jwt_account_gen():
        jwt_uri = jwt_generator.format_jwt_uri(request_get, accounts_path)
        jwt_token = jwt_generator.build_rest_jwt(jwt_uri, api_key, api_secret)
        return jwt_token

def jwt_order_gen():
        jwt_uri = jwt_generator.format_jwt_uri(request_post, create_order_path)
        jwt_token = jwt_generator.build_rest_jwt(jwt_uri, api_key, api_secret)
        return jwt_token

def jwt_candle_gen():
        jwt_uri = jwt_generator.format_jwt_uri(request_get, candle_path)
        jwt_token = jwt_generator.build_rest_jwt(jwt_uri, api_key, api_secret)
        return jwt_token



# Initial values
buy_price = None
macd_sell_triggered = False
last_candle_time = None


# Trading loop
while True:


    # Timeframe setup
    end_unix_timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    start_unix_timestamp = str(int(datetime.now(timezone.utc).timestamp()) - (1814400))
    params = {
        "start": start_unix_timestamp,
        "end": end_unix_timestamp,
        "granularity": granularity
    }




    # Headers setup for requests

    candle_header = {
        "Authorization": f"Bearer {jwt_candle_gen()}"
    }

    accounts_header = {
        "Authorization": f"Bearer {jwt_account_gen()}" 
    }

    order_header = {
        "Authorization": f"Bearer {jwt_order_gen()}"
    }




    # Get account data
    try:
        accounts_response = requests.get(accounts_url, headers=accounts_header, timeout=10)
        accounts_data = accounts_response.json()
    except requests.RequestException as e:
        print("Error getting account data:", e)
        time.sleep(10)
        continue




    # Account balance functions
    def account_USD_balance():
        for account in accounts_data.get("accounts", []):
            if account["currency"] == "USD":
                return float(account["available_balance"]["value"])
            
    def eth_balance():
        for account in accounts_data.get("accounts", []):
            if account["currency"] == "ETH":
                return float(account["available_balance"]["value"])
        return 0.0

    eth_available = eth_balance()
    
    if eth_available <= 0.00001:
        buy_price = None



    # Get candle data
    try:
        candle_response = requests.get(candle_url, headers=candle_header, params=params, timeout=10)
        print("\nCandle status Code:", candle_response.status_code)
    except requests.RequestException as e:
        print("Error fetching candles:", e)
        time.sleep(10)
        continue

    if candle_response.status_code != 200:
        print("Error fetching candles. Status code:", candle_response.status_code)
        print("Error response:", candle_response.text)
        time.sleep(10)
        continue

    try:
        candle_json_data = candle_response.json()
    except Exception as e:
        print("Error converting JSON:", e)
        time.sleep(10)
        continue




    # Parse candle data into Pandas Dataframe
    if isinstance(candle_json_data, dict) and 'candles' in candle_json_data:
        candle_df = pd.DataFrame(candle_json_data['candles'])
    else:
        candle_df = pd.DataFrame(candle_json_data)
    


    # process candle data
    candle_df = candle_df.iloc[::-1].reset_index(drop=True)
    candle_df["high"] = candle_df["high"].astype(float)
    candle_df["low"] = candle_df["low"].astype(float)
    candle_df["close"] = candle_df["close"].astype(float)
    candle_df["open"] = candle_df["open"].astype(float)
    equity = account_USD_balance()
    risk_amt = equity




    # Calculate EMA'S
    ema_fast = candle_df["close"].ewm(span=12, adjust=False).mean()
    ema_slow = candle_df["close"].ewm(span=26, adjust=False).mean()


    # Calculate MACD and Signal Line
    candle_df["macd"] = ema_fast - ema_slow
    candle_df["signal"] = candle_df["macd"].ewm(span=9, adjust=False).mean()
    


    # Get current and previous candle data
    cur = candle_df.iloc[-1]
    prev = candle_df.iloc[-2]
    prev_prev = candle_df.iloc[-3]
    

    # Trading Logic
    macd_direction = "UP" if cur['macd'] > prev['macd'] else "DOWN"
    signal_direction = "UP" if cur['signal'] > prev['signal'] else "DOWN"
    macd_upward = (cur["macd"] > prev["macd"])
    macd_downward = (cur["macd"] < prev["macd"])
    signal_downward = (cur["signal"] < prev["signal"])
    signal_upward = (cur["signal"] > prev["signal"])
    macd_above_signal = (cur["macd"] > cur["signal"])
    macd_below_signal = (cur["macd"] < cur["signal"])
    if buy_price is not None:
        take_profit = buy_price * 1.03
    else:
        take_profit = None

    current_candle_time = cur['start']
    is_new_candle = (last_candle_time is None or current_candle_time != last_candle_time)

    if macd_below_signal:
        macd_sell_triggered = False





    # Log market data on the new candle
    if is_new_candle:
        cursor.execute("""
            INSERT INTO market_data (MACD_Value, Signal_Value, ETH_Price, MACD_Trend, Signal_Trend, Position, Time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (cur['macd'], cur['signal'], float(cur['close']), macd_direction, signal_direction,
                'MACD above signal' if cur['macd'] > cur['signal'] else 'MACD below signal', datetime.now()))
        db.commit()
        last_candle_time = current_candle_time


    


    # Buy trigger if MACD increases by at least 10 units
    if is_new_candle and cur['macd'] - prev['macd'] >= 10 and macd_upward:
        if eth_balance() <= .00001:
            client_order_id = str(uuid.uuid4())
            print(f"\n--- BUY SIGNAL TRIGGERED ---")
            print(f"Goin long, price: {cur['close']}")

            quote_size = str(round(risk_amt, 2))

            print(f"quote_size: ${quote_size}")

            order_data = {
            "client_order_id": client_order_id,
            "product_id": 'ETH-USD',
            "side": "BUY",
            "order_configuration": {
                "market_market_ioc": {
                    "quote_size": quote_size,
                },
            },
            "leverage": "3.0",
        }
            # Place Buy Order and Log Trade
            order_response = requests.post(create_order_url, headers=order_header, json=order_data)
            print("Order Buy Code:", order_response.status_code)
            print("Order Response:", order_response.text)
            if order_response.status_code == 200:
                buy_price = float(cur['close'])

                cursor.execute("""
                    INSERT INTO trades (Trade_Type, Time, Price, ETH_Quantity,
                                       MACD_Value, Signal_Value, Reason, Order_ID, Order_Status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, ("BUY", datetime.now(), buy_price, eth_balance(),
                        cur['macd'], cur['signal'], "MACD_BUY_SIGNAL", client_order_id, "Success"))
                db.commit()
                time.sleep(2)
                cursor.execute("""
                    INSERT INTO account_balance (ETH_Balance, USD_Balance, Time)
                     VALUES (%s, %s, %s)
                """, (eth_balance(), equity, datetime.now()))
                db.commit()
                cursor.execute("""
                    INSERT INTO positions (Entry_Time, Entry_Price, ETH_Quantity)
                        VALUES (%s, %s, %s)
                """, (datetime.now(), buy_price, eth_balance()))
                db.commit()

            if order_response.status_code != 200:
                try:
                    print("Response JSON:", order_response.json())
                except Exception as e:
                    print("Error converting JSON response:", e)
            else:
                print("Buy order placed successfully.")
        else:
            print(f"Already holding ETH: {eth_balance():.6f}")



    # Take Profit Sell trigger
    if take_profit is not None and cur['high'] >= take_profit and macd_above_signal and eth_balance() > 0.00001:
        client_order_id = str(uuid.uuid4())
        print(f"\n---TAKE PROFIT TRIGGERED ---")
        print(f"We sellin this shit")
        
        base_size = str(eth_balance())
        order_data = {
        "client_order_id": client_order_id,
        "product_id": 'ETH-USD',
        "side": "SELL",
        "order_configuration": {
            "market_market_ioc": {
                    "base_size": base_size,
            },
        },
    }
        # Sell request and log info
        order_response = requests.post(create_order_url, headers=order_header, json=order_data)
        print("TP Order Response Code:", order_response.status_code)
        print("TP Order Response:", order_response.text)
        if order_response.status_code == 200:
            sell_price = float(cur['close'])
            profit_loss_USD = (sell_price - buy_price) * eth_balance()
            profit_loss_percent = round(((sell_price - buy_price) / buy_price) * 100, 2)
            cursor.execute("""
                INSERT INTO trades (Trade_Type, Time, Price, ETH_Quantity,
                                    MACD_Value, Signal_Value, Reason, Order_ID, Order_Status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("SELL", datetime.now(), sell_price, eth_balance(),
                    cur['macd'], cur['signal'], "TAKE_PROFIT", client_order_id, "Success"))
            db.commit()
            time.sleep(2)
            cursor.execute("""
                INSERT INTO account_balance (ETH_Balance, USD_Balance, Time)
                VALUES (%s, %s, %s)
            """, (eth_balance(), equity, datetime.now()))
            db.commit()
            cursor.execute("""
                INSERT INTO positions (Exit_Time, Exit_Price, Take_Profit, Profit_Loss_USD, Profit_Loss_Percent)
                VALUES (%s, %s, %s, %s, %s)
            """, (datetime.now(), sell_price, take_profit, profit_loss_USD, profit_loss_percent))
            db.commit()
            buy_price = None



        # Error logging for failed TP sell
        if order_response.status_code != 200:
            cursor.execute("""
                INSERT INTO trades (Trade_Type, Time, Price, ETH_Quantity,
                                    MACD_Value, Signal_Value, Reason, Order_ID, Order_Status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("SELL", datetime.now(), float(cur['close']), eth_balance(),
                    cur['macd'], cur['signal'], "TAKE_PROFIT", client_order_id, "Failed"))
            db.commit()
            try:
                print("Response JSON:", order_response.json())
            except Exception as e:
                print("Error converting JSON response:", e)
        else:
            print("TP sell order successful.")
            buy_price = None




    # MACD decreases by more than 2.5 sell trigger
    if macd_above_signal and (cur['macd'] - prev['macd']) <= 2.5 and eth_available > 0.00001:
        macd_sell_triggered = True

        client_order_id = str(uuid.uuid4())
        print(f"We sellin this shit")
        print("Macd is going down bitch!!")
        base_size = str(eth_balance())
        order_data = {
        "client_order_id": client_order_id,
        "product_id": 'ETH-USD',
        "side": "SELL",
        "order_configuration": {
            "market_market_ioc": {
                    "base_size": base_size,
            },
        },
    }


        # MACD sell request and log info
        order_response = requests.post(create_order_url, headers=order_header, json=order_data)
        print("Order Response Code:", order_response.status_code)
        print("Order Response:", order_response.text)
        if order_response.status_code == 200:
            sell_price = float(cur['close'])
            profit_loss_USD = (sell_price - buy_price) * eth_balance()
            profit_loss_percent = round(((sell_price - buy_price) / buy_price) * 100, 2)
            cursor.execute("""
                INSERT INTO trades (Trade_Type, Time, Price, ETH_Quantity,
                                    MACD_Value, Signal_Value, Reason, Order_ID, Order_Status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("SELL", datetime.now(), sell_price, eth_balance(),
                    cur['macd'], cur['signal'], "MACD Momentum Loss", client_order_id, "Success"))
            db.commit()
            time.sleep(2)
            cursor.execute("""
                INSERT INTO account_balance (ETH_Balance, USD_Balance, Time)
                VALUES (%s, %s, %s)
            """, (eth_balance(), equity, datetime.now()))
            db.commit()
            cursor.execute("""
                INSERT INTO positions (Exit_Time, Exit_Price, Take_Profit, Profit_Loss_USD, Profit_Loss_Percent)
                VALUES (%s, %s, %s, %s, %s)
            """, (datetime.now(), sell_price, take_profit, profit_loss_USD, profit_loss_percent))
            db.commit()
            buy_price = None


        # Error logging for failed MACD sell
        if order_response.status_code != 200:
            cursor.execute("""
                INSERT INTO trades (Trade_Type, Time, Price, ETH_Quantity,
                                    MACD_Value, Signal_Value, Reason, Order_ID, Order_Status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("SELL", datetime.now(), float(cur['close']), eth_balance(),
                    cur['macd'], cur['signal'], "MACD Momentum Loss", client_order_id, "Failed"))
            db.commit()
            try:
                print("Response JSON:", order_response.json())
            except Exception as e:
                print("Error converting JSON response:", e)
        else:
            print("Order successful.")



    # MACD bearish crossover sell
    if macd_below_signal and macd_downward:
        if eth_available > 0.00001:
            client_order_id = str(uuid.uuid4())
            print(f"\n--- SELL SIGNAL TRIGGERED ---")
            print(f"We sellin this shit")
            
            base_size = str(eth_available)
            order_data = {
            "client_order_id": client_order_id,
            "product_id": 'ETH-USD',
            "side": "SELL",
            "order_configuration": {
                "market_market_ioc": {
                     "base_size": base_size,
                },
            },
        }
            # Sell request and log info
            order_response = requests.post(create_order_url, headers=order_header, json=order_data)
            print("Order Response Code:", order_response.status_code)
            print("Order Response:", order_response.text)
            if order_response.status_code == 200:
                sell_price = float(cur['close'])
                profit_loss_USD = (sell_price - buy_price) * eth_balance()
                profit_loss_percent = round(((sell_price - buy_price) / buy_price) * 100, 2)
                cursor.execute("""
                    INSERT INTO trades (Trade_Type, Time, Price, ETH_Quantity,
                                        MACD_Value, Signal_Value, Reason, Order_ID, Order_Status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, ("SELL", datetime.now(), sell_price, eth_balance(),
                        cur['macd'], cur['signal'], "Bearish Crossover", client_order_id, "Success"))
                db.commit()
                time.sleep(2)
                cursor.execute("""
                    INSERT INTO account_balance (ETH_Balance, USD_Balance, Time)
                    VALUES (%s, %s, %s)
                """, (eth_balance(), equity, datetime.now()))
                db.commit()
                cursor.execute("""
                INSERT INTO positions (Exit_Time, Exit_Price, Take_Profit, Profit_Loss_USD, Profit_Loss_Percent)
                VALUES (%s, %s, %s, %s, %s)
                """, (datetime.now(), sell_price, take_profit, profit_loss_USD, profit_loss_percent))
                db.commit()
                buy_price = None


            # Error logging for failed MACD sell
            if order_response.status_code != 200:
                cursor.execute("""
                    INSERT INTO trades (Trade_Type, Time, Price, ETH_Quantity,
                                        MACD_Value, Signal_Value, Reason, Order_ID, Order_Status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, ("SELL", datetime.now(), float(cur['close']), eth_balance(),
                        cur['macd'], cur['signal'], "Bearish Crossover", client_order_id, "Failed"))
                db.commit()
                try:
                    print("Response JSON:", order_response.json())
                except Exception as e:
                    print("Error converting JSON response:", e)
            else:
                print("Sell order placed successfully.")
                buy_price = None
        else:
            print(f"No ETH to sell. Balance: {eth_available:.6f}")




    # Print Status info
    print(f"\nETH Price: ${cur['close']:,.2f}")
    print(f"Fast EMA: {ema_fast.iloc[-1]:.6f}")
    print(f"Slow EMA: {ema_slow.iloc[-1]:.6f}")
    print(f"MACD: {cur['macd']:.6f}")
    print(f"Signal: {cur['signal']:.6f}")
    print(f"\nMACD Trend: {macd_direction}")
    print(f"Signal Trend: {signal_direction}")
    print(f"Position: {'MACD above signal' if cur['macd'] > cur['signal'] else 'MACD below signal'}")
    print(f"\nAccount Balance: ${account_USD_balance():.2f}")
    print(f"ETH Balance: {eth_balance():.6f}")
    print('macd sell trigger value:', macd_sell_triggered)
    if buy_price is not None:
        print(f"  Buy Price: ${buy_price}")
        potential_profit_loss_USD = round((float(cur['close']) - buy_price) * eth_balance(), 2)
        potential_profit_loss_percent = round(((float(cur['close']) - buy_price) / buy_price) * 100, 2)
        print(f"  Potential Profit/Loss: ${potential_profit_loss_USD} {potential_profit_loss_percent}%")

    time.sleep(15)
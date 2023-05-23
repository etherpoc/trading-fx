# import packages
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import tensorflow as tf
import numpy as np
# envファイル読み込み
load_dotenv()
login_server = os.environ.get("LOGIN_SERVER")
login_id = int(os.environ.get("LOGIN_ID"))
login_password = os.environ.get("LOGIN_PASSWORD")

# login mt5
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()
print(f'MetaTrader5 version : {mt5.version()}')

authorized=mt5.login(login = login_id, password = login_password, server = login_server)
if authorized:
    account_info=mt5.account_info()
    if account_info!=None:
        print(account_info)
        account_info_dict = mt5.account_info()._asdict()
        for prop in account_info_dict:
            print("  {}={}".format(prop, account_info_dict[prop]))
        print()
else:
    print("failed to connect to trade account 25115284 with password=gqz0343lbdm, error code =",mt5.last_error())
    quit()
 
# 各種設定
symbol = "USDJPY"   # 取引対象
magic_number = 10001 # bot識別番号
per     = 0.1       # 1回の投資金額
losscut = 0.995     # ロスカットする比率
per_lot = 100000     # 1ロット当たりの通貨数
leverage = 100        # レバレッジ(整数)
maxlen = 60         # modelの入力データの長さ

# 最小lot数取得
point=mt5.symbol_info(symbol).point


# 現在時刻取得
recent = datetime.now()

# 指定した学習済みモデルを読み込み
mlmodel = tf.keras.models.load_model("src\models\model60_20230523_010554.h5")

while True:
    #記録
    now = datetime.now()
    if recent.date() < now.date() or recent.hour < now.hour:
        print("処理")
        recent = now
        # 1時間たったら予測
        # 直近60時間のデータを取得（時間足）
        # 1時間足のチャート取得
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 1, 60+maxlen-1)
        rates_frame = pd.DataFrame(rates)
        # 乖離率算出
        deviation_rate = [rates_frame.iloc[i+59, 4]/rates_frame.iloc[i:i+60, 4].mean()  for i in range(0, maxlen)]
        deviation_rate = np.array(deviation_rate).reshape(-1, maxlen, 1)
        # モデルで予測上昇度算出
        predicted = mlmodel.predict(deviation_rate)[0][0]
        print(f"予測 {predicted}")
        # 残高
        balance = mt5.account_info()._asdict()["balance"]
        symbol_tick=mt5.symbol_info_tick(symbol) # symbolのtick情報を取得
        # ポジション情報取得
        positions = mt5.positions_get(symbol = symbol)
        if predicted >= 0.5:
            print("買い")
            if len(positions) == 0:
                result = mt5.order_send({
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": round((balance * per * leverage / rates_frame["close"].values[-1]) / per_lot, 2),
                    "type": mt5.ORDER_TYPE_BUY,
                    "price": symbol_tick.ask,
                    "sl": rates_frame["close"].values[-1] * losscut,
                    "tp": rates_frame["close"].values[-1] * 1.01,
                    "deviation": 20,
                    "magic": 234000,
                    "comment": "python script open",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                    })
                print(result)
            else:
                position = positions[0]._asdict()
                if position["type"] == 1:
                    print("Close")
                    result = mt5.order_send({
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": position["symbol"],
                        "volume": position["volume"],
                        "type": mt5.ORDER_TYPE_BUY,
                        "position": position["ticket"],
                        "price": symbol_tick.ask,
                    })
                    print(result)
                    result = mt5.order_send({
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": round((balance * per * leverage / rates_frame["close"].values[-1]) / per_lot, 2),
                        "type": mt5.ORDER_TYPE_BUY,
                        "price": symbol_tick.ask,
                        "sl": rates_frame["close"].values[-1] * losscut,
                        "tp": rates_frame["close"].values[-1] * 1.01,
                        "deviation": 20,
                        "magic": 234000,
                        "comment": "python script open",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_RETURN,
                    })
                    print(result)
        else:
            if len(positions) == 0:
                print("売り")
                result = mt5.order_send({
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": round((balance * per * leverage / rates_frame["close"].values[-1]) / per_lot, 2),
                    "type": mt5.ORDER_TYPE_SELL,
                    "price": symbol_tick.bid,
                    "sl": rates_frame["close"].values[-1] * (2-losscut),
                    "tp": rates_frame["close"].values[-1] * 0.99,
                    "deviation": 20,
                    "magic": 234000,
                    "comment": "python script open",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                })
                print(result)
            else:
                print("売り")
                position = positions[0]._asdict()
                if position["type"] == 0:
                    print("Close")
                    result = mt5.order_send({
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": position["symbol"],
                        "volume": position["volume"],
                        "type": mt5.ORDER_TYPE_SELL,
                        "position": position["ticket"],
                        "price": symbol_tick.bid,
                    })
                    print(result)
                    result = mt5.order_send({
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": round((balance * per * leverage / rates_frame["close"].values[-1]) / per_lot, 2),
                        "type": mt5.ORDER_TYPE_SELL,
                        "price": symbol_tick.bid,
                        "sl": rates_frame["close"].values[-1] * (2-losscut),
                        "tp": rates_frame["close"].values[-1] * 0.99,
                        "deviation": 20,
                        "magic": 234000,
                        "comment": "python script open",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_RETURN,
                    })
                    print(result)


mt5.shutdown()
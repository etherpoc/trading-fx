# import packages
import os
from dotenv import load_dotenv
from datetime import datetime
import shutil
import numpy as np
import pandas as pd
import tensorflow as tf
import MetaTrader5 as mt5
from modules import MT5Client

# 現在時刻取得
recent = datetime.now()

# envファイル読み込み
load_dotenv()
login_server = os.environ.get("LOGIN_SERVER")
login_id = int(os.environ.get("LOGIN_ID"))
login_password = os.environ.get("LOGIN_PASSWORD")

# 各種設定
symbol = "USDJPY"   # 取引対象
magic_number = 10001 # bot識別番号
per     = 0.1       # 1回の投資金額
stop_loss = 0.997     # ロスカットする比率
take_profit = 1.01  # 利確
per_lot = 100000     # 1ロット当たりの通貨数
leverage = 100        # レバレッジ(整数)
maxlen = 90         # modelの入力データの長さ


# login mt5
mt5client = MT5Client(id = login_id, 
                      password = login_password, 
                      server = login_server,
                      symbol = symbol,
                      magic_number=magic_number,
                      per=per,
                      stop_loss=stop_loss,
                      take_profit=take_profit,
                      per_lot=per_lot,
                      leverage=leverage,
                      maxlen = maxlen)

# 最小lot数取得
point=mt5.symbol_info(symbol).point

# 指定した学習済みモデルを読み込み
mlmodel = tf.keras.models.load_model("src\models\model90_20230524_220904.h5")

while True:
    #記録
    now = datetime.now()
    # 1時間たったら処理実行
    if recent.date() < now.date() or recent.hour < now.hour:
        recent = now
        terminal_size = shutil.get_terminal_size()
        print()
        print("="*terminal_size.columns)
        print(now)
        print("="*terminal_size.columns)
        print()
        
        # 直近60時間のデータを取得（時間足）
        # 1時間足のチャート取得
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 1, 60+maxlen-1)
        rates_frame = pd.DataFrame(rates)
        
        # 乖離率算出
        deviation_rate = [rates_frame.iloc[i+59, 4]/rates_frame.iloc[i:i+60, 4].mean()  for i in range(0, maxlen)]
        deviation_rate = np.array(deviation_rate).reshape(-1, maxlen, 1)
        
        # モデルで予測上昇度算出
        predicted = mlmodel.predict(deviation_rate)[0][0]
        print(f"Close    : {rates_frame['close'].values[-1]}")
        print(f"Predicted: {predicted}")
        
        # 残高
        balance = mt5.account_info()._asdict()["balance"]
        
        # ポジション情報取得
        positions = mt5client.positions_get(symbol)
        if predicted >= 0.5:
            print("Buy")
            if len(positions) == 0:
                print("\nOrder Buy")
                result = mt5client.order_buy()
                print(f"Result", result)
                
            else:
                position = positions[0]._asdict()
                if position["type"] == mt5.ORDER_TYPE_SELL:
                    print("\nAll Position Close")
                    results = mt5client.order_close_all()
                    for i, v in enumerate(results):
                        print(f"[{i+1}]:", v)
                    
                    print("\nOrder Buy")
                    result = mt5client.order_buy()
                    print(f"Result", result)
                else:
                    print("Continue Now Positions")
        else:
            print("Sell")
            if len(positions) == 0:
                print("\nOrder Sell")
                result = mt5client.order_sell()
                print(f"Result", result)
            else:
                position = positions[0]._asdict()
                if position["type"] == mt5.ORDER_TYPE_BUY:
                    print("\nAll Position Close")
                    results = mt5client.order_close_all()
                    for i, v in enumerate(results):
                        print(f"[{i+1}]:", v)
                    
                    print("\nOrder Sell")
                    result = mt5client.order_sell()
                    print(f"Result", result)
                else:
                    print("Continue Now Positions")
        break

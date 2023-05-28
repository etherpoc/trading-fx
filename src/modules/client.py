import MetaTrader5 as mt5
import textwrap

class MT5Client:
    
    def __init__(self, id: str, password: str, server: str, symbol:str, 
                 magic_number:int = 10001, 
                 per:float = 0.1, 
                 stop_loss:float = 0.997, 
                 take_profit:float = 1.01, 
                 per_lot:int = 100000, 
                 leverage:int = 100, 
                 maxlen:int = 60):
        """
        id(str)             口座番号\n
        password(str)       パスワード\n
        server(str)         サーバー名\n
        symbol(str)         銘柄\n
        magic_number(int)   bot識別番号\n
        per(float)          1回の投資金額\n
        stop_loss(float)    ロスカットする比率\n
        take_profit(float)  利確\n
        per_lot(int)        1ロット当たりの通貨数\n
        leverage(int)       レバレッジ(整数)\n
        maxlen(int)         modelの入力データの長さ\n
        """
        if not mt5.initialize():
            print("MetaTrader5.initialize() failed, error code =", mt5.last_error())
            exit()
        print(f'MetaTrader5 version : {mt5.version()}')
        self.authorized = mt5.login(
            login = id,
            password = password,
            server = server
        )
        if self.authorized:
            account_info=mt5.account_info()
            if account_info!=None:
                account_info_dict = mt5.account_info()._asdict()
                print(textwrap.dedent(f"""
                      Account : {account_info_dict["login"]}
                      Name : {account_info_dict["name"]}
                      Server : {account_info_dict["server"]}
                      TradeMode : {account_info_dict["trade_mode"]} (demo: 0, contest: 1, real: 2)
                      Balance : {account_info_dict["balance"]}({account_info_dict["currency"]})
                      Leverage : {account_info_dict["leverage"]}
                      LimitOrders : {account_info_dict["limit_orders"]}
                      """))
                print("Authentication Success!")
            else:
                print(f"failed to connect to trade account {id} with password={password}, error code =",mt5.last_error())
                quit()
        
        self.symbol = symbol
        self.magic_number = magic_number
        self.per = per
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.per_lot = per_lot
        self.leverage = leverage
        self.maxlen = maxlen
    
    def symbol_info(self, symbol):
        """銘柄の情報取得"""
        return mt5.symbol_info(symbol)
    
    def order_send(self, action, symbol, volume, order_type, price, 
                   stop_loss, take_profit, 
                   deviation=20, 
                   magic=234000,
                   comment="Send Order",
                   type_time=mt5.ORDER_TIME_GTC,
                   type_filling=mt5.ORDER_FILLING_RETURN):
        """注文送信"""
        result = mt5.order_send({
            "action": action,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": deviation,
            "magic": magic,
            "comment": comment,
            "type_time": type_time,
            "type_filling": type_filling,
        })
        return result
    
    def order_buy(self, symbol = None, volume = None, stop_loss = None, take_profit = None, 
                   deviation=20, 
                   magic=234000,
                   comment="Send Buy Order",
                   type_time=mt5.ORDER_TIME_GTC,
                   type_filling=mt5.ORDER_FILLING_RETURN):
        """成り行き注文(買い)"""
        
        if symbol is None:
            symbol = self.symbol
        symbol_tick=mt5.symbol_info_tick(symbol)
        point = mt5.symbol_info(symbol).point
        if volume is None:
            balance = mt5.account_info()._asdict()["balance"]
            volume = round((balance * self.per * self.leverage / symbol_tick.ask) / self.per_lot, 2)
            if volume < point:
                volume = point
                
        
        if stop_loss is None:
            stop_loss = symbol_tick.bid * self.stop_loss
        
        if take_profit is None:
            take_profit = symbol_tick.bid * self.take_profit
            
        return self.order_send(mt5.TRADE_ACTION_DEAL, symbol, volume, mt5.ORDER_TYPE_BUY, symbol_tick.ask, stop_loss, take_profit, 
                   deviation, magic, comment, type_time, type_filling)
        
    def order_sell(self, symbol = None, volume = None, stop_loss = None, take_profit = None, 
                   deviation=20, 
                   magic=234000,
                   comment="Send Sell Order",
                   type_time=mt5.ORDER_TIME_GTC,
                   type_filling=mt5.ORDER_FILLING_RETURN):
        """成り行き注文(売り)"""
        if symbol is None:
            symbol = self.symbol
        symbol_tick=mt5.symbol_info_tick(symbol)
        point = mt5.symbol_info(symbol).point
        
        if volume is None:
            balance = mt5.account_info()._asdict()["balance"]
            volume = round((balance * self.per * self.leverage / symbol_tick.bid) / self.per_lot, 2)
            if volume < point:
                volume = point
        
        if stop_loss is None:
            stop_loss = symbol_tick.ask * (2-self.stop_loss)
        
        if take_profit is None:
            take_profit = symbol_tick.ask * (2-self.take_profit)
            
        return self.order_send(mt5.TRADE_ACTION_DEAL, symbol, volume, mt5.ORDER_TYPE_SELL, symbol_tick.bid, stop_loss, take_profit, 
                   deviation, magic, comment, type_time, type_filling)
    
    def order_close(self, position):
        """ポジション決済"""
        position_dict = position._asdict()
        symbol_tick = mt5.symbol_info_tick(position_dict["symbol"])
        order_type = None
        if position_dict["type"] == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
        elif position_dict["type"] == mt5.ORDER_TYPE_SELL:
            order_type = mt5.ORDER_TYPE_BUY
        else:
            print(f"OrderTypeError:{position_dict}")
        
        result = mt5.order_send({
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position_dict["symbol"],
                "volume": position_dict["volume"],
                "type": order_type,
                "position": position_dict["ticket"],
                "price": symbol_tick.ask,
            })
        return result
    
    def order_close_all(self, symbol = None):
        """すべてのポジション決済"""
        if symbol is None:
            symbol = self.symbol
        result = []
        positions = self.positions_get(symbol)
        for position in positions:
            result.append(self.order_clear(position))
        return result
    
    def positions_get(self, symbol = None):
        """ポジション情報取得"""
        if symbol is None:
            symbol = self.symbol
        return mt5.positions_get(symbol = symbol)
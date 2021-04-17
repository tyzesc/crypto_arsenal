class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {'Binance': {'pairs': ['BTC-USDT'], }, }
        self.period = 5 * 60
        self.options = {}

        # user defined class attribute
        self.phase = -1
        self.amt = [0.8, 0.5, 0.2]
        self.sw = float(-1)
        self.sl = float(-1)
        self.close_price_trace = np.array([])
        self.low_price_trace = np.array([])
        self.open_price_trace = np.array([])
        self.high_price_trace = np.array([])

        # enum
        self.UP = 1
        self.DOWN = 2

        self.last_cur = self.DOWN

    def on_order_state_change(self, order):
        Log("order price: " + str(order["price"]) + " " + str(order['amount']))

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, int(self['ma_short']))[-1]
        l_ma = talib.SMA(self.close_price_trace, int(self['ma_long']))[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN


    def update_price(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        self.close_price_trace = self.close_price_trace[-1 * int(self['window']):]
        low_price = information['candles'][exchange][pair][0]['low']
        self.low_price_trace = np.append(self.low_price_trace, [float(low_price)])
        self.low_price_trace = self.low_price_trace[-1 * int(self['window']):]
        open_price = information['candles'][exchange][pair][0]['open']
        self.open_price_trace = np.append(self.open_price_trace, [float(open_price)])
        self.open_price_trace = self.open_price_trace[-1 * int(self['window']):]
        high_price = information['candles'][exchange][pair][0]['high']
        self.high_price_trace = np.append(self.high_price_trace, [float(high_price)])
        self.high_price_trace = self.high_price_trace[-1 * int(self['window']):]
        
        return close_price

    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        base_currency_amount = self['assets'][exchange]['BTC']
        target_currency_amount = self['assets'][exchange]['USDT']

        close_price = self.update_price(information)

        cur_cross = self.get_current_ma_cross()
        if cur_cross is None:
            return []


        if base_currency_amount == 0.0:
            if cur_cross == self.UP:
                Log("long...")
                self.sl = np.min(self.low_price_trace) * (1 - float(self['ratio']))
                self.sw = close_price + (close_price - self.sl)
                return [{'exchange': exchange, 'amount': 1, 'price': -1, 'type': 'MARKET', 'pair': pair}]
            elif self['is_shorting']:
                Log("short...")
                self.sw = np.max(self.high_price_trace) * (1 + float(self['ratio']))
                self.sl = close_price - (self.sl - close_price)
                return [{'exchange': exchange, 'amount': -1, 'price': -1, 'type': 'MARKET', 'pair': pair}]


        else:
            if close_price <= self.sl or close_price >= self.sw:
                Log("close...")
                return [{'exchange': exchange, 'amount': -base_currency_amount, 'price': -1, 'type': 'MARKET', 'pair': pair}]
        return []

class Strategy():
    def __setitem__(self, key, value):
        self.options[key] = value

    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        self.exchange = "Binance"
        self.pair = "ETH-USDT"
        self.base =  self.pair.split("-")[0]
        self.target = self.pair.split("-")[1]
        self.subscribedBooks = {'Binance': {'pairs': [self.pair], }, }
        self.period = 60 # 5 * 60
        self.options = {}

        self.status = "start"

        self.orders = []
        self.startprice = 2500
        self.border = 0.1
        self.grid_num = 20
        self.grid_trade_protection =  0.05

        self.track_amt = None
        self.track_price = None

        self.pendding = []
        self.check_clear = []

        

    def floor(self, f):
        s = str(f)
        if '.' in s:
            arr = s.split(".")
            arr[1] = arr[1][:2]
            s = ".".join(arr)
        return float(s)
    def abs(self, a):
        if a < 0:
            return a * -1
        return a

    def on_order_state_change(self, order):
        # Log(order['status'] + " " + str(order))
        if self.status == "start":
            Log(order['status'] + " " + str(order))
            if order['status'] == "FILLED":
                if self.track_amt == order['amount']:
                    self.track_price = order['price']
                    self.status = "build"
            pass
        elif self.status == "build":
            Log("xxxxx")
            pass
        elif self.status == "running":
            Log("網格單被吃 " + str(order['amount']) + " @ " + str(order['price']))
            Log("天地單點為 " + str(self.top_price) + " " + str(self.bot_price))
            r = self.floor(self.track_price * self.border / self.grid_num)
            if order['amount'] > 0:
                self.pendding.append([order['price']+r, 'sell'])
            else:
                self.pendding.append([order['price']-r, 'buy'])
            if order['price'] >= self.top_price or order['price'] <= self.bot_price:
                self.status = "clear"
                self.check_clear = []
            pass
        elif self.status == "clear":
            pass
        elif self.status == "close":
            Log("=====================================")
            if order['status'] == "FILLED":
                self.status = "start"
                self.orders = []
            pass


    def print_order(self, orders):
        Log("=============================")
        for o in orders:
            Log(o['status'] + str(o))
        Log("=============================")

    def trade(self, information):
        # self.print_order(information['orders'])
        if self.status == "start":
            if len(self.orders) == 0:
                price = self.floor(self.startprice)
                amt =  self.floor(self['assets'][self.exchange][self.target] / 2 / price)
                order = {'exchange': self.exchange, 'amount': amt, 'price': price, 'type': 'LIMIT', 'pair': self.pair}
                self.orders.append(order)
                self.track_amt = amt
                self.track_price = price
                Log("設置收購訂單" + str(self.track_amt) + " @ " + str(self.track_price))
                return [order]
            else:
                # Log("等待收購")
                return []
        elif self.status == "build":
            Log("完成收購 建立網格訂單")
            self.orders = []
            # sell
            p = self.floor(self.track_price)
            r = self.floor(p * self.border / self.grid_num)
            for i in range(self.grid_num):
                p += r
                amt = self.floor(self.track_amt / (self.grid_num + self.grid_trade_protection))
                self.orders.append({'exchange': self.exchange, 'amount': amt * -1, 'price': p, 'type': 'LIMIT', 'pair': self.pair})
            self.top_price = p + r
            
            # buy
            p = self.floor(self.track_price)
            for i in range(self.grid_num):
                p -= r
                amt = self.floor(self.track_amt / (self.grid_num + self.grid_trade_protection))
                self.orders.append({'exchange': self.exchange, 'amount': amt, 'price': p, 'type': 'LIMIT', 'pair': self.pair})
            self.bot_price = p - r
            self.status = "running"
            return self.orders
        elif self.status == "running":
            # Log(str(self['assets']))
            # s = ""
            # for o in information['orders'][:5]:
            #     s += (o['status'] + " " + str(o['price']) + " " + str(o['amount'])) + " "
            # Log(s)
            arr = []
            r = self.floor(self.track_price * self.border / self.grid_num)

            for p in self.pendding:
                price = self.floor(p[0])
                amt = self.floor(self.track_amt / (self.grid_num + self.grid_trade_protection))
                if p[1] == 'sell':
                    arr.append({'exchange': self.exchange, 'amount': amt * -1, 'price': price, 'type': 'LIMIT', 'pair': self.pair})
                if p[1] == 'buy':
                    arr.append({'exchange': self.exchange, 'amount': amt, 'price': price, 'type': 'LIMIT', 'pair': self.pair})
            self.orders = self.orders + arr
            self.pendding = []
            return arr
        elif self.status == "clear":
            return []
            # Log("撞到天地單")
            if len(self.check_clear) >= 4:
                self.orders = []
                self.status = "close"
                self.startprice = information['candles'][self.exchange][self.pair][0]['close']

            flag = False
            for order in information['orders']:
                try:
                    if order['status'] == "NEW":
                        CancelOrder(order)
                        flag = True
                        Log("還有訂單")
                except:
                    pass
            if flag:
                self.check_clear = []
            else:
                self.check_clear.append(True)
            return []
        elif self.status == "close":
            Log("清理完訂單不 " + str(self['assets'][self.exchange][self.base]) + ' ' + str(self['assets'][self.exchange][self.target]))
            if len(self.orders) == 0:
                order = {'exchange': self.exchange, 'amount': self['assets'][self.exchange][self.base] * -1, 'price': -1, 'type': 'MARKET', 'pair': self.pair}
                self.orders.append(order)
                return [order]
            else:
                # Log("等待吃單")
                return []

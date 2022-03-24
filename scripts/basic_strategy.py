class BasicStrategy:

    def __init__(self, df_product_historic_rates, df_product_future_rates, currency_pair_stat):
        self.df_product_historic_rates = df_product_historic_rates
        self.df_product_future_rates = df_product_future_rates
        self.currency_pair_stat = currency_pair_stat

        self.quote_currency_volume = 50
        self.base_currency_volume = 0
        self.placed_buying_orders = []         #[{price_wanted, volume}]
        self.placed_selling_orders = []        # [{price_wanted, volume}]
        self.buying_volume = 10
        self.max_buying_orders = 2
        self.fees_rate = 0.006                  #Coinbase fees rate (so high)

        self.Q1 = df_product_historic_rates.describe().loc['25%', 'close']
        self.median = df_product_historic_rates.describe().loc['50%', 'close']
        self.Q3 = df_product_historic_rates.describe().loc['75%', 'close']

        self.under_Q1 = False
        self.btwn_median_Q1 = False
        self.btwn_Q3_median = False
        self.over_Q3 = False

    def strategy(self):
        loop_idx = 0
        for index, row in self.df_product_historic_rates:

            #case init
            if(loop_idx == 0):
                self.update_pos_state(row)
                self.init_buying_order(row)
            else:
                #update selling
                #update buying
                #update_risk_management
                pass

            loop_idx += 1

        #close selling, by selling with the last price

    def init_buying_order(self, row_historic_rate):
        price = row_historic_rate['close']
        if(price < self.Q1):
            self.placed_buying_orders.append({'price_wanted' : self.Q1, 'volume' : self.buying_volume*2})
        elif(price < self.median):
            diff_price_median = abs(price - self.median)
            self.placed_buying_orders.append({'price_wanted': self.median - (diff_price_median / 2), 'volume': self.buying_volume * 2})

    def update_pos_state(self, row_historic_rate):
        price = row_historic_rate['close']
        if(price < self.Q1):
            self.under_Q1 = True
        elif(price < self.median):
            self.btwn_median_Q1 = True
        elif (price < self.Q3):
            self.btwn_Q3_median = True
        else:
            self.over_Q3 = True
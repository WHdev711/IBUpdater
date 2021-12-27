from ib.opt import ibConnection
from ib.opt import Connection
import datetime as dt
import time
from threading import Timer
import pandas as pd
import requests
import configparser

class PerpetualTimer():

   def __init__(self,t,hFunction):
      self.t=t
      self.hFunction = hFunction
      self.thread = Timer(self.t,self.handle_function)

   def handle_function(self):
      self.hFunction()
      self.thread = Timer(self.t,self.handle_function)
      self.thread.start()

   def start(self):
      self.thread.start()

   def cancel(self):
      self.thread.cancel()


class AccountUpdater:
    """ This class connects to IB, receives the account information and posts it
    to the web server """
    def __init__(
                 self, 
                 host                  = 'localhost', 
                 port                  = 4001,
                 client_id             = 101, 
                 is_use_gateway        = False, 
                 req_interval_secs     = 20,
                 ib_field_list         = None,
                 server_name_list      = None,
                 h                     = None,
                 url                   = None,
                 restricted_accounts   = None
                 ):
        
        self.host = host
        self.port = port
        self.client_id = client_id
        self.restricted_accounts = restricted_accounts
        self.h = h
        self.url = url
        self.ib_field_list = ib_field_list
        self.server_name_list = server_name_list
        self.account_history = pd.DataFrame(columns=['date', 'account', 'key', 'value'])
        self.req_interval_secs = req_interval_secs
        self.accounts = ""

        # Use ibConnection() for TWS, or create connection for API Gateway
        self.conn = ibConnection() if is_use_gateway else \
            Connection.create(host=self.host, port=self.port, clientId=self.client_id)
        self.__register_data_handlers(self.__event_handler)
        self.updater = PerpetualTimer(self.req_interval_secs, self.req_account_update)


    def __register_data_handlers(self, universal_event_handler):
        """Register data handlers with IB"""
        print("\nRegistering data handlers ...")
        self.conn.registerAll(universal_event_handler)


    def req_account_update(self):
        """Request account updates"""
        # Stream account updates
        for i in range(len(self.accounts)):
            time.sleep(3)
            self.conn.reqAccountUpdates(True, self.accounts[i])

    def update_history(self, msg):
        """ Update the history in pandas dataframe"""
        l = len(self.account_history)
        self.account_history.loc[l, 'date'] = dt.datetime.now()
        self.account_history.loc[l,'account'] = msg.accountName
        self.account_history.loc[l, 'key'] = msg.key
        self.account_history.loc[l, 'value'] = msg.value


    def post_to_server(self, msg):
        """ Post selected data to the web server"""
        idx = self.ib_field_list.index(msg.key)
        post_data = {
                     'ibaccount': msg.accountName, 
                     'h': self.h, 
                     self.server_name_list[idx]: msg.value
                     }

        post_response = requests.post(url='https://ibbuckets.com/1/ibapi.cfm', data=post_data)
        #print(post_data)
          #print(dir(post_response))
        #print(post_response.status_code)
        #print(post_response.reason)
        return post_response


    def __event_handler(self, msg):
        """ Handle all events sent from IB"""
        if msg.typeName == "managedAccounts":
            self.accounts = [x.strip() for x in msg.accountsList.split(',')]
            self.accounts = list(filter(None, self.accounts))
            for i in range(len(self.restricted_accounts)):
                if self.restricted_accounts[i] in self.accounts: 
                    self.accounts.remove(self.restricted_accounts[i])
            
            print('---------------------------------------------------------')
            print('Accounts = ', self.accounts)

        elif msg.typeName == "updateAccountValue":
            
            if msg.value == 0.0 and msg.key == 'NetLiquidation':
                self.accounts.remove(msg.accountName)
            elif msg.key in self.ib_field_list:

                self.update_history(msg)
                self.post_to_server(msg)

                print('---------------------------------------------')
                print(dt.datetime.now(), '\n' + msg.key + ' = ', 
                      float(msg.value), msg.accountName)

        elif msg.typeName == "error":
            print(msg)


    def start(self):
        """ Start the updater """
        print("\n Account Updater Started. \n")

        self.conn.connect()  # Get IB connection object
        self.conn.reqManagedAccts()
        time.sleep(3)
        self.req_account_update()
        self.updater.start()


if __name__ == "__main__":

    # read the config file
    config = configparser.ConfigParser()
    config.read('Config.ini')

    # parse query params
    host = config['QueryParams']['host']
    port = int(config['QueryParams']['port'])
    client_id = int(config['QueryParams']['client_id'])
    is_use_gateway = eval(config['QueryParams']['is_use_gateway'])
    req_interval_secs = float(config['QueryParams']['req_interval_secs'])
    ib_field_list = eval(config['QueryParams']['ib_field_list'])

    # parse post params
    server_name_list = eval(config['PostParams']['server_name_list'])
    h = config['PostParams']['h']
    url = config['PostParams']['url']
    restricted_accounts = eval(config['PostParams']['restricted_accounts'])

    # Initiate the connection
    updater = AccountUpdater(
                             host                  = host, 
                             port                  = port,
                             client_id             = client_id, 
                             is_use_gateway        = is_use_gateway, 
                             req_interval_secs     = req_interval_secs,
                             ib_field_list         = ib_field_list,
                             server_name_list      = server_name_list,
                             h                     = h,
                             url                   = url,
                             restricted_accounts   = restricted_accounts
                             )

    # start updating
    updater.start()

        
        


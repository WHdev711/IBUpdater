from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import time
import configparser
import requests

accountdata = {}
class TestApp(EWrapper, EClient):
    global  accountdata
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)
    
    def nextValidId(self, orderId:int):
        print("setting nextValidOrderId: %d", orderId)
        # here is where you start using api
        self.reqAccountSummary(9002, "All", "NetLiquidation,FullInitMarginReq,FullAvailableFunds")    
    def accountSummary(self, reqId:int, account:str, tag:str, value:str, currency:str):
        if tag == "FullAvailableFunds":
            accountdata[account] = ',' + str(value)
        else:
            accountdata[account] = accountdata[account]  + "," + str(value)
        print("account: %s, tag: %s, value: %s, currency:%s\n" % (account, tag, value, currency))

    def accountSummaryEnd(self, reqId:int):
        
        self.disconnect()

def main():
    config = configparser.ConfigParser()
    config.read('Config.ini')
    h = config['PostParams']['h']
    app = TestApp()

    app.connect("127.0.0.1", 7496, 55)
    time.sleep(5)

    app.run()
    print(accountdata)
    for key, value in accountdata.items():
        post_data = {
                'h': h, 
                'cashinfo': key + value
                }
        post_response = requests.post(url='https://my.aeromir.com/1/ibapi.cfm', data=post_data)
        print("Sent Data")
        print(key+value)
        print("Done",post_response)

if __name__ == "__main__":
    main()
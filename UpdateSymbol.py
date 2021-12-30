from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import time
import configparser
import requests


updatedata = ''
class TestApp(EWrapper, EClient):
    
    def __init__(self):
        EClient.__init__(self, self)
    def customdefinition(self, postdata):
        global updatedata
        updatedata = postdata
        
    def error(self, reqId, errorCode, errorString):
        print("Error: ", reqId, " ", errorCode, " ", errorString)

    def historicalData(self, reqId, bar):
        tmp =  str(bar.open)+ ","+ str(bar.high)+ ","+ str(bar.low)+ ","+ str(bar.close)
        self.customdefinition(tmp)
        print("HistoricalData. ", reqId, " Date:", bar.date, "Open:", bar.open, "High:", bar.high, "Low:", bar.low, "Close:", bar.close, "Volume:", bar.volume, "Count:", bar.barCount, "WAP:", bar.average)
        self.done = True

    def historicalDataUpdate(self, reqId, bar):
        print("HistoricalData_update. ", reqId, " Date:", bar.date, "Open:", bar.open, "High:", bar.high, "Low:", bar.low, "Close:", bar.close, "Volume:", bar.volume, "Count:", bar.barCount, "WAP:", bar.average)

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        self.disconnect()

def main():
    global updatedata
    config = configparser.ConfigParser()
    config.read('Config.ini')

    # parse query params
    host = config['QueryParams']['host']
    port = int(config['QueryParams']['port'])
    client_id = int(config['QueryParams']['client_id'])
    is_use_gateway = eval(config['QueryParams']['is_use_gateway'])
    req_interval_secs = float(config['QueryParams']['req_interval_secs'])
    ib_field_list = eval(config['QueryParams']['ib_field_list'])

    symbol = config['Symbol']['symbol']
    sectype = config['Symbol']['sectype']
    exchange = config['Symbol']['exchange']
    currency = config['Symbol']['currency']

    # parse post params
    h = config['PostParams']['h']
    url = config['PostParams']['url']
    app = TestApp()

    app.connect("127.0.0.1", 7496, 55)
    time.sleep(5)
    # define contract for EUR.USD forex pair
    contract = Contract() 
    contract.symbol = symbol
    contract.secType = sectype
    contract.exchange = exchange
    contract.currency = currency
    endtime = time.strftime('%Y%m%d %H:%M:%S')
    print(endtime)

    app.reqHistoricalData(1, contract, '', "1 D", "1 min", "MIDPOINT", 0, 1, False, [])

    app.run()
    updatedata = symbol + "," + updatedata
    post_data = {
                'h': h, 
                'symbol': updatedata
                }
    post_response = requests.post(url='https://my.aeromir.com/1/ibapi.cfm', data=post_data)
    print("Sent Data")
    print(updatedata)
    print("Done",post_response)


if __name__ == "__main__":
    main()
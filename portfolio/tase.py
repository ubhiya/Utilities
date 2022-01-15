import http.client
import json
import sys
import time
from datetime import datetime, timedelta
import requests


class Tase:

    # Initializing
    def __init__(self):
        self.last_bday = self.last_business_day()
        self.authorization_token = self.get_new_token()
        self.conn = http.client.HTTPSConnection("openapigw.tase.co.il")
        print('Tase created.')

    # Deleting (Calling destructor)
    def __del__(self):
        print('Destructor called, Employee deleted.')
        self.conn.close()

    def last_business_day(self):
        # https://www.geeksforgeeks.org/python-get-most-recent-previous-business-day/
        today = datetime.today()
        diff = max(1, (today.weekday() + 6) % 7 - 2)
        res = today - timedelta(days=diff)
        return res


    def get_new_token(self):
        auth_server_url = "https://openapigw.tase.co.il/tase/prod/oauth/oauth2/token"
        client_id = '74fb9e32ec8d6e975f3e93c98087f749'
        client_secret = 'c635993099dfc4880c7f1083926f5774'

        token_req_payload = {'grant_type': 'client_credentials', 'scope': 'tase'}

        token_response = requests.post(auth_server_url,
                                       data=token_req_payload, verify=False, allow_redirects=False,
                                       auth=(client_id, client_secret))

        if token_response.status_code != 200:
            print("Failed to obtain token from the OAuth 2.0 server", file=sys.stderr)
            sys.exit(1)

        print("Successfuly obtained a new token")
        tokens = json.loads(token_response.text)
        return tokens['access_token']


    def get_quote_last_business_day(self, symbol):
        business_day = self.last_bday
        request = "/tase/prod/api/v1/securities/end-of-day-trading-data"
        request = request + "/" + str(business_day.year)
        request = request + "/" + str(business_day.month)
        request = request + "/" + str(business_day.day)
        request = request + "?securityId=" + str(symbol)

        headers = {
            'authorization': "Bearer " + self.authorization_token,
            'accept-language': "he-IL",
            'accept': "application/json"
        }

        self.conn.request("GET", request, headers=headers)

        res = self.conn.getresponse()
        resp = json.loads(res.read())
        price = resp['securitiesEndOfDayTradingData']['result'][0]['closingPrice']

        return price,self.last_bday

    def get_quote_latest(self, symbol):
        # returns latest known quotation for symbol
        # date = datetime.now()
        # return 2130, date

        request = "/tase/prod/api/v1/securities-trading-data/last-updated?securityId="
        request = request + str(symbol)

        headers = {
            'authorization': "Bearer " + self.authorization_token,
            'accept-language': "he-IL",
            'accept': "application/json"
        }

        self.conn.request("GET", request, headers=headers)

        res = self.conn.getresponse()
        resp = json.loads(res.read())
        # Interface is burst-limited to one call per second
        time.sleep(1)

        price = resp['getSecuritiesLastUpdate']['result'][0]['securityLastPrice']
        date_string = resp['getSecuritiesLastUpdate']['result'][0]['date']
        date_obj = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f')

        return price, date_obj

if __name__ == "__main__":
    # execute only if run as a script

    tase_quoter = Tase()
    quote, date = tase_quoter.get_quote_latest("01143718")
    print(quote)
    print(date)

    #token = get_new_token()
    #conn = http.client.HTTPSConnection("openapigw.tase.co.il")
    #quote = get_quote_last_business_day(conn, "01143718", token)
    #conn.close()



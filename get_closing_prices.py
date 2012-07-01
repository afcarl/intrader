import sys
import pymongo
import intrade_api
import dateutil.parser

def main():

    conn = pymongo.Connection()
    data = conn.intrade

    intrade = intrade_api.Intrade()

    for contract in [743474, 743475]:
        prices = intrade.closing_price(contract)
        for rec in prices['cp']:
            rec['contract_id'] = str(contract)
            rec['@date'] = dateutil.parser.parse(rec['@date']).astimezone(dateutil.tz.tzutc())
            data.closing.update(rec, rec, upsert = True)

if __name__ == '__main__':
    main()

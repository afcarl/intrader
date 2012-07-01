import pymongo
from unicodewriter import UnicodeWriter

def main():
    
    conn = pymongo.Connection()
    data = conn.intrade

    file = open('dow_export.csv', 'w')
    writer = UnicodeWriter(file)
    headers = ['time', 'dow']
    writer.writerow(headers)

    for rec in data.dow.find():
        writer.writerow([rec['_id'], rec['l']])
    
    file = open('intrade_export.csv', 'w')
    writer = UnicodeWriter(file)
    headers = ['time', 'contract', 'bid_ask', 'volume', 'price']
    writer.writerow(headers)

    uniques = set()

    for rec in data.price.find():
        try:
            check = ''.join([rec['@lastUpdateTime'], rec['symbol']])
        except:
            continue
        if check in uniques:
            continue
        uniques.add(check)
        if rec['orderBook']['bids']:
            writer.writerow([rec['@lastUpdateTime'],
                             rec['symbol'],
                             'BID',
                             rec['orderBook']['bids']['bid'][0]['@quantity'] if isinstance(rec['orderBook']['bids']['bid'], list) else rec['orderBook']['bids']['bid']['@quantity'],
                             rec['orderBook']['bids']['bid'][0]['@price'] if isinstance(rec['orderBook']['bids']['bid'], list) else rec['orderBook']['bids']['bid']['@price']])
        if rec['orderBook']['offers']:
            writer.writerow([rec['@lastUpdateTime'],
                             rec['symbol'],
                             'ASK',
                             rec['orderBook']['offers']['offer'][0]['@quantity'] if isinstance(rec['orderBook']['offers']['offer'], list) else rec['orderBook']['offers']['offer']['@quantity'],
                             rec['orderBook']['offers']['offer'][0]['@price'] if isinstance(rec['orderBook']['offers']['offer'], list) else rec['orderBook']['offers']['offer']['@price']])

if __name__ == '__main__':
    main()

""" Formats XML -> JSON returns from Intrade to be more useful. All prices
are stored in cents as integers. """
from datetime import datetime
from decimal import Decimal
import time

def format_prices(input_rec):
    """ Generator of formatted individual contract records from price return """
    if 'contractInfo' not in input_rec or (not input_rec['contractInfo']):
        yield None
        raise StopIteration()

    if not isinstance(input_rec['contractInfo'], list):
        for_iter = [input_rec['contractInfo']]
    else:
        for_iter = input_rec['contractInfo']

    for contract in for_iter:
        result = {}
        result['contract'] = contract['symbol'] if 'symbol' in contract else 'unknown'
        result['contract_id'] = int(contract['@conID']) if '@conID' in contract else None
        result['volume'] = int(contract['@vol']) if '@vol' in contract else 0
        result['last_trade_ts'] = (int(contract['@lstTrdTme']) if
                                   '@lstTrdTme' in contract and
                                   contract['@lstTrdTme'] != '-'
                                   else None)
        result['last_trade'] = (dt_from_ms_ts(int(contract['@lstTrdTme'])) if
                                '@lstTrdTme' in contract and
                                contract['@lstTrdTme'] != '-'
                                else None)
        result['last_update_ts'] = (int(input_rec['@lastUpdateTime']) if
                                    '@lastUpdateTime' in input_rec and
                                    input_rec['@lastUpdateTime']
                                    else int(time.time() * 1000))
        result['last_update'] = (dt_from_ms_ts(int(input_rec['@lastUpdateTime'])) if
                                 '@lastUpdateTime' in input_rec and
                                 input_rec['@lastUpdateTime']
                                 else None)

        result['last_price'] = (int(Decimal((contract['@lstTrdPrc'])) * 10)
                                if '@lstTrdPrc' in contract
                                and contract['@lstTrdPrc'] != '-'
                                else None)
    
        if 'orderBook' in contract:
    
            if ('offers' in contract['orderBook'] 
                and 'offer' in contract['orderBook']['offers'] 
                and contract['orderBook']['offers']['offer']):

                if not isinstance(contract['orderBook']['offers']['offer'],
                                  list):
                    contract['orderBook']['offers']['offer'] = [
                        contract['orderBook']['offers']['offer']]
    
                orders = []
                for offer in contract['orderBook']['offers']['offer']:
                    orders.append({'price': offer['@price'],
                                   'quantity': offer['@quantity']})
                result['offers'] = orders
            else:
                result['offers'] = None
    
            if ('bids' in contract['orderBook']
                and 'bid' in contract['orderBook']['bids']
                and contract['orderBook']['bids']['bid']):

                if not isinstance(contract['orderBook']['bids']['bid'],
                                  list):
                    contract['orderBook']['bids']['bid'] = [
                        contract['orderBook']['bids']['bid']]
    
                bids = []
                for bid in contract['orderBook']['bids']['bid']:
                    bids.append({'price': bid['@price'],
                                 'quantity': bid['@quantity']})
                result['bids'] = bids
            else:
                result['bids'] = None
    
        yield result
    
def dt_from_ms_ts(timestamp):
    """ Returns datetime object from timestamp with milliseconds """
    return datetime.fromtimestamp(timestamp / 1000)

from requests import get
from simplejson import loads

def get_dow():
    r = get('http://www.google.com/finance/info?infotype=infoquoteall&q=.DJI')
    return loads(r.content[6:-3])

if __name__ == '__main__':
    get_dow()

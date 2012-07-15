from flask import Flask, render_template, jsonify, redirect, url_for, request
import pymongo
from bson import ObjectId as oid
from itertools import product

app = Flask(__name__)

def clean_return(clean, key_exception_list = []):
    """ Cleans dict return from jQuery """
    if '' in clean:
        del clean['']

    for k, v in clean.iteritems():
        if k[-2:] == '[]':
            clean[k[:-2]] = v
            del clean[k]

    for k, v in clean.iteritems():
        if k not in key_exception_list:
            if isinstance(v, list) and len(v) == 1:
                clean[k] = v[0]

@app.route('/get_chart_data')
def get_chart_data():

    args = dict(request.args)
    clean_return(args, ['contract-select'])

    group_rec = data.contract_groups.find_one({'_id': oid(args['contract-group'])})

    chart_data = []
    if args['options-order'] == 'both':
        order_types = ['bids', 'offers']
    else:
        order_types = ['bids'] if args['options-order'] == 'bid' else ['offers']

    if args['options-chart'] == 'indiv':

        for contract, order in product(args['contract-select'], order_types):

            this_contract = {'name': ' '.join([[x['name']
                                                for x in group_rec['contracts']
                                                if int(x['id']) == int(contract)][0],
                                               order.title()]),
                             'order': order,
                             'data': []}

            for rec in data.price.find({'contract_id': int(contract)}):

                if rec[order]:
                    this_contract['data'].append([rec['last_update_ts'],
                                                  float(rec[order][0]['price'])])
                else:
                    this_contract['data'].append([rec['last_update_ts'], None])

            chart_data.append(this_contract)
            
    elif args['options-chart'] == 'agg':

        for order in order_types:

            this_agg = {'name': order.title(),
                        'order': order,
                        'data': []}
            latest_prices = {}

            q = {'contract_id': {'$in': [int(x) for x in args['contract-select']]}}
        
            for rec in data.price.find(q,
                                       sort = [['last_update_ts', pymongo.ASCENDING]]):
                
                latest_prices[rec['contract_id']] = float(rec[order][0]['price'])
                
                # add to plot if we have price data for every contract
                if len(latest_prices) == len(args['contract-select']):

                    this_agg['data'].append([rec['last_update_ts'],
                                             sum([x for x
                                                  in latest_prices.itervalues()])])

            chart_data.append(this_agg)

    chart_title = ': '.join([group_rec['name'],
                             'Individual Contracts' if args['options-chart'] == 'indiv'
                             else 'Aggregated Contracts'])

    return jsonify(chart_type = 'stock_default',
                   title = chart_title,
                   data = chart_data)

@app.route('/get_contract_names/<group_id>')
def get_contract_names(group_id):
    if group_id == 'no-selection':
        return jsonify(data = [{'id': '', 'name': 'No Group Selected'}])
    rec = data.contract_groups.find_one({'_id': oid(group_id)})
    results = [{'id': x['id'], 'name': x['name']} for x in rec['contracts']]
    return jsonify(data = results)

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/charts')
def charts():

    # initialize charts page, does not handle the chart update

    groups = []
    for rec in data.contract_groups.find():
        groups.append({'id': str(rec['_id']), 'name': rec['name']})

    return render_template('charts.html', groups = groups)

@app.route('/logs')
def logs():
    log_data = []
    for i, rec in enumerate(logs.intrader.find({},
                                               limit = 100,
                                               sort = [('$natural', pymongo.DESCENDING)])):
        log_data.append({'rownum': i + 1,
                         '_id': rec['_id'],
                         'level': rec['levelname'],
                         'time': rec['time'].strftime("%Y-%m-%d %H:%m:%S"),
                         'process': rec['processName'],
                         'message': rec['message']})
    return render_template('logs.html', log_data = log_data)

@app.route('/')
def index():
    return redirect(url_for('charts'), 301)

if __name__ == '__main__':
    conn = pymongo.Connection()
    data = conn.intrade
    logs = conn.logs
    app.debug = True
    app.run()

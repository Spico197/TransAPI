import json

import requests
from flask import Flask, request, jsonify, render_template

from config import configger
from storage import RAMMapStorager, ProxyInstance

import threading

class APIMiddleware(object):
    def __init__(self):
        self.api_url = 'http://{}:{}'.format(configger.API_IP, configger.API_PORT)
    
    def get_len(self, name):
        if name == 'non':
            response = requests.get(self.api_url + '/proxy/get_len?name=non')
            response.raise_for_status()
            return json.loads(response.text).get('length', 0)
        elif name == 'ggl':
            response = requests.get(self.api_url + '/proxy/get_len?name=ggl')
            response.raise_for_status()
            return json.loads(response.text).get('length', 0)
        else:
            response = requests.get(self.api_url + '/proxy/get_len?name=tot')
            response.raise_for_status()
            return json.loads(response.text).get('length', 0)
    
    def save(self, obj):
        data = obj.to_dict()
        response = requests.post(self.api_url + '/proxy/save', data=data)
        response.raise_for_status()

    def delete(self, ip, port, protocol):
        params = {
            'ip': ip,
            'port': port,
            'protocol': protocol
        }
        response = requests.get(self.api_url + '/proxy/delete', params=params)
        response.raise_for_status()
    
    def find(self, **kwargs):
        response = requests.get(self.api_url + '/proxy/find', params=kwargs)
        response.raise_for_status()
        return json.loads(response.text)

    def get_proxies(self, num=1, google_passed=0):
        params = {
            'num': num,
            'google_passed': google_passed
        }
        response = requests.get(self.api_url + '/proxy/get_proxies', params=params)
        response.raise_for_status()
        return json.loads(response.text)


def run():
    storager = RAMMapStorager()
    app = Flask('storage_api')

    @app.route('/proxy/tot_length', methods=['GET'])
    def tot_length():
        return jsonify({'length': len(storager)})

    @app.route('/proxy/get_length', methods=['GET'])
    def get_length():
        google_passed = int(request.args.get('google_passed', False))
        return jsonify({'length': storager.get_length(bool(google_passed))})
    
    @app.route('/proxy/get_len', methods=['GET'])
    def get_len():
        name = request.args.get('name', 'tot')
        if name == 'non':
            return jsonify({'length': storager.get_length(False)})
        elif name == 'ggl':
            return jsonify({'length': storager.get_length(True)})
        else:
            return jsonify({'length': len(storager)})

    @app.route('/proxy/save', methods=['POST'])
    def save():
        data = request.form
        google_passed = data.get('google_passed', False)
        if google_passed == 'True':
            google_passed = True
        else:
            google_passed = False

        verified = data.get('verified', False)
        if verified == 'True':
            verified = True
        else:
            verified = False

        nd = dict(
            ip = data.get('ip'),
            port = str(data.get('port')),
            protocol = data.get('protocol').lower(),
            location = data.get('location', '').lower(),
            anonymity = data.get('anonymity', '').lower(),
            google_passed = google_passed,
            verified = verified,
            speed = data.get('speed', 10.0)
        )
        px = ProxyInstance(**nd)
        storager.save(px)
        return ''

    @app.route('/proxy/delete', methods=['GET'])
    def delete():
        px = ProxyInstance(ip=request.args.get('ip'),
                           port=request.args.get('port'),
                           protocol=request.args.get('protocol'))
        storager.delete(px)
        return '', 204
    
    @app.route('/proxy/find', methods=['GET'])
    def find():
        return jsonify(storager.find(**request.args))
    
    @app.route('/proxy/get_proxies', methods=['GET'])
    def get_proxies():
        print(request.args)
        num = int(request.args.get('num', 1))
        google_passed = int(request.args.get('google_passed', 0))
        return jsonify(storager.get_proxies(num=num, google_passed=google_passed))
    
    @app.route('/proxy/report', methods=['GET'])
    def report():
        r = {
            'tot_proxies': len(storager),
            'google_num': storager.get_length(True),
            'non_google_num': storager.get_length(False)
        }
        return render_template('report.html', data=r)

    app.run(host=configger.API_IP,
            port=configger.API_PORT,
            debug=False)


if __name__ == "__main__":
    run()

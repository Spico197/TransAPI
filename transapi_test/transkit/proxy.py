import json
import time
import random
import telnetlib

import requests

from lxml import etree


class ProxyPool(object):
    def __init__(self):
        self.proxies_pool = dict()
        self.UA_headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Mobile Safari/537.36'}
        
    def verify_proxy(self, ip, port, proto, timeout=1.5):
        try:
            telnetlib.Telnet(ip, port=port, timeout=timeout)
            pxs = {
                'http': "{}://{}:{}".format(proto, ip, port),
                'https': "{}://{}:{}".format(proto, ip, port)
            }
            response = requests.get('https://translate.google.cn', headers=self.UA_headers, proxies=pxs, timeout=timeout)
            response.raise_for_status()
            return True
        except:
            return False

    def save_proxy(self, ip, port, proto, filepath='./proxy_file_saved'):
        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write("{}:{}:{}\n".format(proto, ip, port))
        except:
            pass
    
    def clear(self):
        self.proxies_pool.clear()
    
    def load_proxy_file(self, file_path):
        proxies = dict()
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                proto = line.split(':')[0].strip()
                ip = line.split(':')[1].strip()
                port = line.split(':')[2].strip()
                proxies[ip] = {'port': port, 'proto': proto}
        self.proxies_pool.clear()
        self.proxies_pool = proxies

    def crawl_proxies(self, name, *args, **kwargs):
        if name == 'github':
            self._crawl_github_proxies(*args, **kwargs)
        elif name == 'xici':
            self._crawl_xici_proxies(*args, **kwargs)
    
    def _crawl_github_proxies(self, speed=1.5, protocols={'http', 'https'}, early_stopped=None):
        url = 'https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list'
        while True:
            try:
                response = requests.get(url, headers=self.UA_headers, timeout=5.0)
                response.raise_for_status()
                break
            except:
                time.sleep(5)
                continue
        lines = response.text.split('\n')
        lens = len(lines)
        cnt = 1
        for line in lines:
            px = json.loads(line.strip())
            t = px['type']
            h = px['host']
            p = px['port']
            if t.lower().strip() in protocols:
                if self.verify_proxy(h, p, t.strip().lower(), timeout=speed):
                    self.proxies_pool[h] = {'port': p, 'proto': t}
                    self.save_proxy(h, p, t)
            print(' '*100 + '\r', end='')
            print('Github Proxies - Process: {}/{} - lens: {}\r'.format(cnt, lens, len(self.proxies_pool)), end='')
            cnt += 1
            if early_stopped:
                if len(self.proxies_pool) >= early_stopped:
                    break

    def _crawl_xici_proxies(self, speed=0.50, connecting_time=0.50, protocols={'http', 'https'}, early_stopped=None):
        base_url = 'https://www.xicidaili.com/wn/'
        response = requests.get(base_url, headers=self.UA_headers, timeout=1.0)
        response.raise_for_status()
        response.encoding = 'UTF-8'
        html = etree.HTML(response.text)
        pages = html.xpath('//a[@class="next_page"]/preceding-sibling::a/@href')[-1].split('/')[-1]
        for page in range(1, int(pages) + 1):
            time.sleep(1)
            while True:
                try:
                    url = base_url + str(page)
                    response = requests.get(url, headers=self.UA_headers)
                    response.encoding = 'UTF-8'
                    html = etree.HTML(response.text)
                    tds = html.xpath('//td/text()')
                    if tds:
                        break
                except AttributeError:
                    print('.', end='')
                    pass
            ips = tds[0::12]
            ports = tds[1::12]
            protos = tds[5::12]
            # seconds = html.xpath('//td[@class="country"]/div[contains(@title, "秒")]/@title')
            # spds = seconds[0::2]
            # cons = seconds[1::2]

            for ip, port, proto in zip(ips, ports, protos):
                if proto.strip().lower() in protocols:
                    if self.verify_proxy(ip, port, proto.strip().lower()):
                        self.proxies_pool[ip] = {'port': port, 'proto': proto.lower().strip()}
                        self.save_proxy(ip, port, proto)
                        if early_stopped:
                            if len(self.proxies_pool) >= early_stopped:
                                break
            print(' '*100 + '\r', end='')
            print('Xici Proxies - Process: {}/{} - proxies: {}\r'.format(page, pages, len(self.proxies_pool)), end='')

    def get_proxies(self):
        proxies = list(self.proxies_pool.items())
        phttp = random.choice(proxies)
        phttps = random.choice(proxies)
        prox = {
            'http': '{}://{}:{}'.format(phttp[1]['proto'], phttp[0], phttp[1]['port']),
            'https': '{}://{}:{}'.format(phttps[1]['proto'], phttps[0], phttps[1]['port'])
        }
        return prox


class APIMiddleware(object):
    def __init__(self):
        self.api_url = 'http://{}:{}'.format('127.0.0.1', '65430')
    
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
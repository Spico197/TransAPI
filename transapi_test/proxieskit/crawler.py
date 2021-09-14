import time
import json
import re
import datetime
import threading

import requests
from lxml import etree

from config import configger
from verification import verify
from storage import ProxyInstance
from webapi import APIMiddleware


class CrawlerMeta(object):
    def __init__(self, *args, **kwargs):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Mobile Safari/537.36',
        }
        self.api_mdw = APIMiddleware()
    
    def check_alive(self):
        # reach the upper bound: the crawler can close, else it has to work
        # basically like Schmidt Trigger
        if self.api_mdw.get_len('ggl') >= configger.STORAGE_NONGOOGLE_UPPER_BOUND \
            and self.api_mdw.get_len('non') >= configger.STORAGE_GOOGLE_UPPER_BOUND:
            return False
        else:
            return True
            
    def download(self, *args, **kwargs):
        pass
    
    def parse(self, *args, **kwargs):
        pass
    
    def save(self, obj):
        self.api_mdw.save(obj)
    
    def run(self):
        pass
    

class hookzof_socks5_list(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(hookzof_socks5_list, self).__init__(*args, **kwargs)
        self.base_url = 'https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt'
        self.protocol = 'socks5'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        return response.text.split('\n')

    def parse(self, lines):
        proxies = []
        for line in lines:
            line = line.strip()
            if len(line.split(':')) == 2:
                px = ProxyInstance(ip=line.split(':')[0],
                                   port=line.split(':')[1],
                                   protocol='socks5')
                proxies.append(px)
        return proxies
    
    def run(self):
        print('hookzof_socks5_list')
        if not self.check_alive():
            return
        texts = self.download()
        objs = self.parse(texts)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class dxxzst_free_proxy_list(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(dxxzst_free_proxy_list, self).__init__(*args, *kwargs)
        self.base_url = 'https://raw.githubusercontent.com/dxxzst/free-proxy-list/master/README.md'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def parse(self, text):
        resultset = []
        rs = re.findall(r'\|\d+\.\d+\.\d+\.\d+\|\d+\|https?\|.*?\|.*?\|', text)
        for r in rs:
            r = r.strip()
            r_ = r.split('|')
            px = ProxyInstance(ip=r_[1],
                               port=r_[2],
                               protocol=r_[3],
                               anonymity=r_[4],
                               location=r_[5])
            resultset.append(px)
        return resultset

    def run(self):
        print('dxxzst_free_proxy_list')
        if not self.check_alive():
            return
        text = self.download()
        objs = self.parse(text)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class TheSpeedX_SOCKS_List(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(TheSpeedX_SOCKS_List, self).__init__(*args, **kwargs)
        self.base_url = 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks.txt'
        self.protocol = 'socks5'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        return response.text

    def parse(self, text):
        resultset = []
        rs = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', text)
        for r in rs:
            r = r.strip()
            r_ = r.split(':')
            px = ProxyInstance(ip=r_[0],
                               port=r_[1],
                               protocol=self.protocol)
            resultset.append(px)
        return resultset
    
    def run(self):
        print('TheSpeedX_SOCKS_List')
        if not self.check_alive():
            return
        texts = self.download()
        objs = self.parse(texts)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class mclvren_proxy_list(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(mclvren_proxy_list, self).__init__(*args, *kwargs)
        self.base_url = 'https://raw.githubusercontent.com/mclvren/proxy-list/master/https.txt'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def parse(self, text):
        resultset = []
        rs = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', text)
        for r in rs:
            r = r.strip()
            r_ = r.split(':')
            px = ProxyInstance(ip=r_[0],
                               port=r_[1],
                               protocol='https')
            resultset.append(px)
        return resultset

    def run(self):
        print('mclvren_proxy_list')
        if not self.check_alive():
            return
        text = self.download()
        objs = self.parse(text)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class a2u_free_proxy_list(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(a2u_free_proxy_list, self).__init__(*args, *kwargs)
        self.base_url = 'https://raw.githubusercontent.com/a2u/free-proxy-list/master/free-proxy-list.txt'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def parse(self, text):
        resultset = []
        rs = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', text)
        for r in rs:
            r = r.strip()
            r_ = r.split(':')
            px = ProxyInstance(ip=r_[0],
                               port=r_[1],
                               protocol='https')
            resultset.append(px)
        return resultset

    def run(self):
        print('a2u_free_proxy_list')
        if not self.check_alive():
            return
        text = self.download()
        objs = self.parse(text)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class clarketm_proxy_list(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(clarketm_proxy_list, self).__init__(*args, *kwargs)
        self.base_url = 'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def parse(self, text):
        resultset = []
        rs = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+\s.*', text)
        for r in rs:
            r = r.strip()
            if '-S' in r:
                proto = 'https'
            else:
                proto = 'http'
            r_ = r.split(' ')[0].split(':')
            px = ProxyInstance(ip=r_[0],
                               port=r_[1],
                               protocol=proto)
            resultset.append(px)
        return resultset

    def run(self):
        print('clarketm_proxy_list')
        if not self.check_alive():
            return
        text = self.download()
        objs = self.parse(text)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class fate0_proxylist(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(fate0_proxylist, self).__init__(*args, **kwargs)
        self.base_url = 'https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def parse(self, text):
        resultset = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) <= 0:
                continue
            p = json.loads(line)
            px = ProxyInstance(ip=p['host'],
                               port=p['port'],
                               protocol=p['type'])
            resultset.append(px)
        return resultset

    def run(self):
        print('fate0_proxylist')
        if not self.check_alive():
            return
        text = self.download()
        objs = self.parse(text)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class ip_jiangxianli_com(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(ip_jiangxianli_com, self).__init__(*args, **kwargs)
        self.base_url = 'http://ip.jiangxianli.com/?page={}'

    def download(self, page):
        response = requests.get(self.base_url.format(page), headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def parse(self, text):
        resultset = []
        html = etree.HTML(text)
        urls = html.xpath('//button[contains(@class, "btn-copy")]/@data-url')
        lines = urls
        for line in lines:
            line = line.strip()
            if len(line) <= 0:
                continue
            px = ProxyInstance(ip=line.replace('//', '').split(':')[1],
                               port=line.split(':')[-1],
                               protocol=line.split(':')[0])
            resultset.append(px)
        return resultset

    def run(self):
        print('ip_jiangxianli_com')
        if not self.check_alive():
            return
        for i in range(10):
            text = self.download(i)
            objs = self.parse(text)
            if len(objs) <= 0:
                break
            for obj in objs:
                if not self.check_alive():
                    break
                obj_ = verify(obj)
                if obj_:
                    self.save(obj_)


class ip3366_net(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(ip3366_net, self).__init__(*args, **kwargs)
        self.base_url = [
            'http://www.ip3366.net/free/?stype=1&page={}',
            'http://www.ip3366.net/free/?stype=2&page={}'
        ]

    def download(self, url, page):
        response = requests.get(url.format(page), headers=self.headers)
        response.raise_for_status()
        response.encoding = 'gb2312'
        return response.text
    
    def parse(self, text):
        resultset = []
        html = etree.HTML(text)
        urls = html.xpath('//tbody//tr/td/text()')
        ips = urls[0::7]
        ports = urls[1::7]
        protocols = urls[3::7]
        for ip, port, proto in zip(ips, ports, protocols):
            px = ProxyInstance(ip=ip,
                               port=port,
                               protocol=proto)
            resultset.append(px)
        return resultset

    def run(self):
        print('ip3366_net')
        if not self.check_alive():
            return
        for url in self.base_url:
            if not self.check_alive():
                break
            response = requests.get(url.format(1), headers=self.headers)
            response.raise_for_status()
            response.encoding = 'gb2312'
            match_obj = re.search(r'page=(\d+)">尾页</a>', response.text)
            if match_obj:
                tot_page = int(match_obj.group(1))
                for i in range(1, tot_page + 1):
                    if not self.check_alive():
                        break
                    text = self.download(url, i)
                    objs = self.parse(text)
                    if len(objs) <= 0:
                        break
                    for obj in objs:
                        if not self.check_alive():
                            break
                        obj_ = verify(obj)
                        if obj_:
                            self.save(obj_)


class www_goubanjia_com(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(www_goubanjia_com, self).__init__(*args, **kwargs)
        self.base_url = 'http://www.goubanjia.com/'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    
    def parse(self, text):
        resultset = []
        html = etree.HTML(text)
        tds = html.xpath('//tbody//tr/td[@class="ip"]')
        ips = []
        ports = []
        for td in tds:
            cs = []
            for c in td.getchildren():
                if c.attrib.get('style') != 'display: none;' and c.attrib.get('style') != 'display:none;':
                    if c.text != None:
                        cs.append(c.text)
            ips.append(''.join(cs[:-1]))
            ports.append(cs[-1])
        protos = html.xpath('//tbody/tr/td/a[contains(@title, "http")]/text()')
        for ip, port, proto in zip(ips, ports, protos):
            px = ProxyInstance(ip=ip,
                               port=port,
                               protocol=proto)
            resultset.append(px)
        return resultset

    def run(self):
        print('www_goubanjia_com')
        if not self.check_alive():
            return
        text = self.download()
        objs = self.parse(text)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class proxy_coderbusy_com(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(proxy_coderbusy_com, self).__init__(*args, **kwargs)
        self.base_url = 'https://proxy.coderbusy.com'

    def download(self):
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    
    def parse(self, text):
        resultset = []
        html = etree.HTML(text)
        tds = html.xpath('//tbody//tr/td')
        rs = []
        for td in tds:
            if td.getchildren():
                for c in td.getchildren():
                    if c.tag == 'span':
                        rs.append(c.text.strip())
            else:
                if td.text != None:
                    rs.append(td.text.strip())
                else:
                    rs.append('None')
        ips = rs[0::9]
        ports = rs[1::9]
        httpses = rs[3::9]
        for ip, port, https in zip(ips, ports, httpses):
            if https == '√':
                proto = 'https'
            else:
                proto = 'http'
            px = ProxyInstance(ip=ip,
                               port=port,
                               protocol=proto)
            resultset.append(px)
        return resultset

    def run(self):
        print('proxy_coderbusy_com')
        if not self.check_alive():
            return
        text = self.download()
        objs = self.parse(text)
        for obj in objs:
            if not self.check_alive():
                break
            obj_ = verify(obj)
            if obj_:
                self.save(obj_)


class www_kuaidaili_com(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(www_kuaidaili_com, self).__init__(*args, **kwargs)
        self.base_url = [
            'https://www.kuaidaili.com/free/inha/{}/',
            'https://www.kuaidaili.com/free/intr/{}/'
        ]

    def download(self, url, page):
        response = requests.get(url.format(page), headers=self.headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    
    def parse(self, text):
        resultset = []
        html = etree.HTML(text)
        ips = html.xpath('//tbody//td[@data-title="IP"]/text()')
        ports = html.xpath('//tbody//td[@data-title="PORT"]/text()')
        protos = html.xpath('//tbody//td[@data-title="类型"]/text()')
        times = html.xpath('//tbody//td[@data-title="最后验证时间"]/text()')
        for ip, port, proto, time in zip(ips, ports, protos, times):
            if datetime.datetime.now().strftime('%Y-%m-%d') in time:
                px = ProxyInstance(ip=ip,
                                   port=port,
                                   protocol=proto)
                resultset.append(px)
        return resultset

    def run(self):
        print('www_kuaidaili_com')
        if not self.check_alive():
            return
        for url in self.base_url:
            if not self.check_alive():
                break
            time.sleep(2)
            response = requests.get(url.format(1), headers=self.headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            match_obj = re.search(r'>(\d+)</a></li><li>页</li>', response.text)
            if match_obj:
                tot_page = int(match_obj.group(1))
                for i in range(1, tot_page + 1):
                    if not self.check_alive():
                        break
                    time.sleep(1)
                    text = self.download(url, i)
                    objs = self.parse(text)
                    if len(objs) <= 0:
                        break
                    for obj in objs:
                        if not self.check_alive():
                            break
                        obj_ = verify(obj)
                        if obj_:
                            self.save(obj_)


class www_66ip_cn(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(www_66ip_cn, self).__init__(*args, **kwargs)
        self.base_url = 'http://www.66ip.cn/areaindex_{}/1.html'

    def download(self, page):
        response = requests.get(self.base_url.format(page), headers=self.headers)
        response.raise_for_status()
        response.encoding = 'gb2312'
        return response.text
    
    def parse(self, text):
        resultset = []
        html = etree.HTML(text)
        nums = html.xpath('//p[@class="style7"]/span/text()')[0]
        if nums == '0':
            return resultset
        tds = html.xpath('//table[@border="2px"]//td/text()')
        ips = tds[0::5][1:]
        ports = tds[1::5][1:]
        for ip, port in zip(ips, ports):
            px = ProxyInstance(ip=ip,
                                port=port,
                                protocol='http')
            resultset.append(px)
        return resultset

    def run(self):
        print('www_66ip_cn')
        if not self.check_alive():
            return
        for num in range(1, 35):
            if not self.check_alive():
                break
            text = self.download(num)
            objs = self.parse(text)
            for obj in objs:
                if not self.check_alive():
                    break
                obj_ = verify(obj)
                if obj_:
                    self.save(obj_)


class www_xicidaili_com(CrawlerMeta):
    def __init__(self, *args, **kwargs):
        super(www_xicidaili_com, self).__init__(*args, **kwargs)
        self.base_url = [
            'https://www.xicidaili.com/nn/{}/',
            'https://www.xicidaili.com/nt/{}/',
            'https://www.xicidaili.com/wn/{}/',
            'https://www.xicidaili.com/wt/{}/',
        ]
    def download(self, url, page):
        response = requests.get(url.format(page), headers=self.headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
    
    def parse(self, text):
        resultset = []
        html = etree.HTML(text)
        tds = html.xpath('//td/text()')
        ips = tds[0::12]
        ports = tds[1::12]
        protos = tds[5::12]
        for ip, port, proto in zip(ips, ports, protos):
            px = ProxyInstance(ip=ip,
                                port=port,
                                protocol=proto)
            resultset.append(px)
        return resultset

    def run(self):
        print('www_xicidaili_com')
        if not self.check_alive():
            return
        for url in self.base_url:
            if not self.check_alive():
                break
            for i in range(1, 3):
                if not self.check_alive():
                    break
                time.sleep(1)
                text = self.download(url, i)
                objs = self.parse(text)
                for obj in objs:
                    if not self.check_alive():
                        break
                    obj_ = verify(obj)
                    if obj_:
                        self.save(obj_)


def run():
    crawlers = [
        # hookzof_socks5_list(),
        dxxzst_free_proxy_list(),
        # TheSpeedX_SOCKS_List(),
        mclvren_proxy_list(),
        a2u_free_proxy_list(),
        clarketm_proxy_list(),
        fate0_proxylist(),
        ip_jiangxianli_com(),
        ip3366_net(),
        www_goubanjia_com(),
        proxy_coderbusy_com(),
        www_kuaidaili_com(),
        www_66ip_cn(),
        www_xicidaili_com()
    ]
    handlers = []
    for c in crawlers:
        handlers.append(threading.Thread(target=c.run))
    
    for h in handlers:
        try:
            h.start()
        except:
            pass

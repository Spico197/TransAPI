import json
import time
import random
import hashlib

import requests

from nltk import word_tokenize
from googletrans import Translator as GglTrans


class Translated(object):
    def __init__(self, text, sentence, src, dest):
        self.text = text
        self.sentence = sentence
        self.src_lang = src
        self.dest_lang = dest


class TransMeta(object):
    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.get('timeout', 3.0)
        self.proxies = kwargs.get('proxies', None)
    
    def translate(self, sentence, src='', dest=''):
        raise NotImplementedError
        # return Translated('', sentence, src, dest)


class NiuTrans(TransMeta):
    def __init__(self, *args, **kwargs):
        super(NiuTrans, self).__init__(*args, **kwargs)
        self.apikey = 'bbe2be82785cfa8100e9f668bbf74b55'
        
        self.api_url = 'http://api.niutrans.vip/NiuTransServer/translation'
        self.request_data = {
            'from': '',
            'to': '',
            'apikey': self.apikey,
            'src_text': '',
            'consumed': "0"
        }
        
    def translate(self, sentence, src='en', dest='zh-cn'):
        if src == 'zh-cn':
            src = 'zh'
        if dest == 'zh-cn':
            dest = 'zh'
        self.request_data['from'] = src
        self.request_data['to'] = dest
        self.request_data['src_text'] = sentence
        if self.proxies:
            response = requests.post(self.api_url, data=self.request_data, timeout=self.timeout, proxies=self.proxies)
        else:
            response = requests.post(self.api_url, data=self.request_data, timeout=self.timeout)
        response.raise_for_status()
        result = json.loads(response.text)
        text = result['tgt_text']
        translated = Translated(text, sentence, src, dest)
        return translated

class BaiduTrans(TransMeta):
    def __init__(self, *args, **kwargs):
        super(BaiduTrans, self).__init__(*args, **kwargs)
        self.appid = '20190814000326481'
#         self.appid = '20190814000326315'
        self.secretKey = 'wDyZnsfaxD4CtzBU2udI'
#         self.secretKey = 'GKsPplUZr_BoZ0Pv0heC'
        self.api_url = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
        self.salt = random.randint(32768, 65536)
        
        self.request_data = {
            'q': '',
            'from': '',
            'to': '',
            'appid': self.appid,
            'salt': self.salt,
            'sign': ''
        }
        
    def translate(self, sentence, src='en', dest='zh-cn'):
        if src == 'zh-cn':
            src = 'zh'
        if dest == 'zh-cn':
            dest = 'zh'
        self.request_data['from'] = src
        self.request_data['to'] = dest
        self.request_data['q'] = sentence
        
        sign = self.appid + sentence + str(self.salt) + self.secretKey
        m1 = hashlib.md5()
        m1.update(sign.encode('utf-8'))
        sign = m1.hexdigest()
        self.request_data['sign'] = sign
        
        if self.proxies:
            response = requests.post(self.api_url, data=self.request_data, timeout=self.timeout, proxies=self.proxies)
        else:
            response = requests.post(self.api_url, data=self.request_data, timeout=self.timeout)
        response.raise_for_status()
        result = json.loads(response.text)
        text = result['trans_result'][0]['dst']
        translated = Translated(text, sentence, src, dest)
        return translated


class Translator(object):
    def __init__(self, *args, **kwargs):
        assert len(args) == 1
        self.utils = kwargs.get('util_obj')
        self.proxies = kwargs.get('proxies')
        
        if 'google' in args:
            self.translator_name = 'google'
            if kwargs.get('proxies'):
                self.translator = GglTrans(service_urls=['translate.google.cn'], 
                                           timeout=kwargs.get('timeout', 3.0),
                                           proxies=kwargs.get('proxies'))
            else:
                self.translator = GglTrans(service_urls=['translate.google.cn'], 
                                           timeout=kwargs.get('timeout', 3.0))
        elif 'xiaoniu' in args:
            self.translator_name = 'xiaoniu'
            if kwargs.get('proxies'):
                self.translator = NiuTrans(timeout=kwargs.get('timeout', 3.0),
                                           proxies=kwargs.get('proxies'))
            else:
                self.translator = NiuTrans(timeout=kwargs.get('timeout', 3.0))
        elif 'baidu' in args:
            self.translator_name = 'baidu'
            if kwargs.get('proxies'):
                self.translator = BaiduTrans(timeout=kwargs.get('timeout', 3.0),
                                             proxies=kwargs.get('proxies'))
            else:
                self.translator = BaiduTrans(timeout=kwargs.get('timeout', 3.0))
    
    def backforth_translate(self, sentence, head, tail, tokens=None, head_pos=None, tail_pos=None, tokenize=True):
        if tokens and head_pos and tail_pos:
            labeled_sent = self.utils.tokens_labeled(tokens, head_pos, tail_pos)
        else:
            labeled_sent = self.utils.sentence_labeled(sentence, head, tail)
        en2zh_sent = self.en2zh(labeled_sent)
        en2zh_sent = self.utils.sentence_delabeled(en2zh_sent, 'A'*15, 'B'*15)
        if self.translator_name == 'xiaoniu':
            time.sleep(0.5)
        elif self.translator_name == 'baidu':
            time.sleep(0.5)
        zh2en_sent = self.zh2en(en2zh_sent)
        delabeled_sent = self.utils.sentence_delabeled(zh2en_sent, head, tail)
#         except:
#             print('sentence: ', sentence)
#             print('head: ', head)
#             print('tail: ', tail)
#             print('labeled_sent: ', labeled_sent)
#             print('en2zh_sent: ', en2zh_sent)
#             print('zh2en_sent: ', zh2en_sent)
#             raise KeyboardInterrupt
        if tokenize:
            delabeled_sent = ' '.join(word_tokenize(delabeled_sent))
        return delabeled_sent.lower()
    
    def en2zh(self, sentence):
        res = self.translator.translate(sentence, src='en', dest='zh-cn')
        return res.text

    def zh2en(self, sentence):
        res = self.translator.translate(sentence, src='zh-cn', dest='en')
        return res.text

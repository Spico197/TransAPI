import re
import json
import time
import random
import hashlib
from typing import Optional

import requests
from nltk import word_tokenize


class Translated(object):
    def __init__(self, text, sentence, src, dest):
        self.text = text
        self.sentence = sentence
        self.src_lang = src
        self.dest_lang = dest


class TransMeta(object):
    def __init__(self):
        pass

    def translate(self, sentence, src='', dest='', proxies=None):
        raise NotImplementedError


class NiuTrans(TransMeta):
    def __init__(self, apikey, api_url):
        super().__init__()
        self.apikey = apikey

        self.api_url = api_url
        self.request_data_template = {
            'from': '',
            'to': '',
            'apikey': self.apikey,
            'src_text': '',
            'consumed': "0"
        }

    def translate(self, sentence, src='en', dest='zh-cn', timeout=3.0, proxies=None):
        if src == 'zh-cn':
            src = 'zh'
        if dest == 'zh-cn':
            dest = 'zh'
        self.request_data_template['from'] = src
        self.request_data_template['to'] = dest
        self.request_data_template['src_text'] = sentence
        response = requests.post(self.api_url, data=self.request_data_template, timeout=timeout, proxies=proxies)
        response.raise_for_status()
        result = json.loads(response.text)
        text = result['tgt_text']
        translated = Translated(text, sentence, src, dest)
        return translated


class BaiduTrans(TransMeta):
    def __init__(self, appid, secret_key, api_url):
        super().__init__()
        self.appid = appid
        self.secret_key = secret_key
        self.api_url = api_url
        self.salt = random.randint(32768, 65536)

        self.request_data_template = {
            'q': '',
            'from': '',
            'to': '',
            'appid': self.appid,
            'salt': self.salt,
            'sign': ''
        }

    def translate(self, sentence, src='en', dest='zh-cn', timeout=3.0, proxies=None):
        if src == 'zh-cn':
            src = 'zh'
        if dest == 'zh-cn':
            dest = 'zh'
        self.request_data_template['from'] = src
        self.request_data_template['to'] = dest
        self.request_data_template['q'] = sentence

        sign = self.appid + sentence + str(self.salt) + self.secret_key
        m1 = hashlib.md5()
        m1.update(sign.encode('utf-8'))
        sign = m1.hexdigest()
        self.request_data_template['sign'] = sign

        response = requests.post(self.api_url, data=self.request_data_template, timeout=timeout, proxies=proxies)
        response.raise_for_status()
        result = json.loads(response.text)
        text = result['trans_result'][0]['dst']
        translated = Translated(text, sentence, src, dest)
        return translated


class TranslatorBase(object):
    def __init__(self, trans_type: str, trans_config: dict, time_interval: Optional[float] = 0.5):
        super().__init__()

        self.trans_type = trans_type
        self.time_interval = time_interval

        self.translator = {
            "BaiduTrans": BaiduTrans,
            "NiuTrans": NiuTrans
        }[self.trans_type](**trans_config)

    def backforth_translate(self, sentence, head, tail, tokens=None, head_pos=None, tail_pos=None, tokenize=True):
        raise NotImplementedError

    def en2zh(self, sentence, timeout=3.0, proxies=None):
        res = self.translator.translate(sentence, src='en', dest='zh-cn', timeout=timeout, proxies=proxies)
        return res.text

    def zh2en(self, sentence, timeout=3.0, proxies=None):
        res = self.translator.translate(sentence, src='zh-cn', dest='en', timeout=timeout, proxies=proxies)
        return res.text


class ReTranslatorViaAB(TranslatorBase):
    """
    relation extraction translator by AAA and BBB substitution, return in lower case
    """
    def __init__(self, trans_type: str, trans_config: dict, time_interval: Optional[float] = 0.5):
        super().__init__(trans_type, trans_config, time_interval=time_interval)

    def tokens_labeled(self, tokens, head_pos, tail_pos, replace=True):
        tokens = [x.lower().strip() for x in tokens]
        for pos in head_pos:
            tokens[pos[0]] = '<e1>' + tokens[pos[0]]
            tokens[pos[-1]] = tokens[pos[-1]] + '<e1e>'
        for pos in tail_pos:
            tokens[pos[0]] = '<e2>' + tokens[pos[0]]
            tokens[pos[-1]] = tokens[pos[-1]] + '<e2e>'
        sent = ' '.join(filter(lambda x: len(x.strip()) > 0, tokens))
        if replace:
            sent = re.sub(r'<\s?[eE]1\s?>.*?<\s?[eE]1[eE]\s?>', 'A' * 15, sent)
            sent = re.sub(r'<\s?[eE]2\s?>.*?<\s?[eE]2[eE]\s?>', 'B' * 15, sent)
        return sent.lower()

    def sentence_labeled(self, sentence, head, tail, replace=True):
        sent = sentence
        if replace:
            sent = sent.replace(head, 'A' * 15)
            sent = sent.replace(tail, 'B' * 15)
        else:
            sent = sent.replace(head, '<e1>' + head + '<e1e>')
            sent = sent.replace(tail, '<e2>' + tail + '<e2e>')
        return sent

    def sentence_delabeled(self, sentence, head, tail, replace=True):
        sent = sentence
        if replace:
            sent = re.sub(r'[Aa]{4,}', head, sent)
            sent = re.sub(r'[Bb]{4,}', tail, sent)
        else:
            sent = re.sub(r'<\s?[eE]1\s?>.*?<\s?[eE]1[eE]\s?>', head, sent)
            sent = re.sub(r'<\s?[eE]2\s?>.*?<\s?[eE]2[eE]\s?>', tail, sent)
        return sent.lower().strip()

    def backforth_translate(self, sentence, head, tail, tokens=None, head_pos=None, tail_pos=None, tokenize=True):
        if tokens and head_pos and tail_pos:
            labeled_sent = self.tokens_labeled(tokens, head_pos, tail_pos)
        else:
            labeled_sent = self.sentence_labeled(sentence, head, tail)
        en2zh_sent = self.en2zh(labeled_sent)
        en2zh_sent = self.sentence_delabeled(en2zh_sent, 'A' * 15, 'B' * 15)

        time.sleep(self.time_interval)

        zh2en_sent = self.zh2en(en2zh_sent)
        delabeled_sent = self.sentence_delabeled(zh2en_sent, head, tail)
        if tokenize:
            delabeled_sent = ' '.join(word_tokenize(delabeled_sent))
        return delabeled_sent


class ReTranslatorViaCodeSwitch(TranslatorBase):
    """
    relation extraction translator by code-switch, return in lower case
    """
    def __init__(self, trans_type: str, trans_config: dict, time_interval: Optional[float] = 0.5):
        super().__init__(trans_type, trans_config, time_interval=time_interval)
        
        self.zh_ent1 = "实体甲"
        self.zh_ent2 = "实体乙"
        self.en_ent1 = "ent1"
        self.en_ent2 = "ent2"

    def tokens_labeled(self, tokens, head_pos, tail_pos, head_str, tail_str, replace=True):
        tokens = [x.lower().strip() for x in tokens]
        for pos in head_pos:
            tokens[pos[0]] = '<e1>' + tokens[pos[0]]
            tokens[pos[-1]] = tokens[pos[-1]] + '<e1e>'
        for pos in tail_pos:
            tokens[pos[0]] = '<e2>' + tokens[pos[0]]
            tokens[pos[-1]] = tokens[pos[-1]] + '<e2e>'
        sent = ' '.join(filter(lambda x: len(x.strip()) > 0, tokens))
        if replace:
            sent = re.sub(r'<\s?[eE]1\s?>.*?<\s?[eE]1[eE]\s?>', head_str, sent)
            sent = re.sub(r'<\s?[eE]2\s?>.*?<\s?[eE]2[eE]\s?>', tail_str, sent)
        return sent.lower()

    def sentence_labeled(self, sentence, head, tail, head_str, tail_str, replace=True):
        sent = sentence
        if replace:
            sent = sent.replace(head, head_str)
            sent = sent.replace(tail, tail_str)
        else:
            sent = sent.replace(head, '<e1>' + head + '<e1e>')
            sent = sent.replace(tail, '<e2>' + tail + '<e2e>')
        return sent

    def sentence_delabeled(self, sentence, head_str, tail_str, head, tail, replace=True):
        sent = sentence
        if replace:
            sent = re.sub(head_str, head, sent)
            sent = re.sub(tail_str, tail, sent)
        else:
            sent = re.sub(r'<\s?[eE]1\s?>.*?<\s?[eE]1[eE]\s?>', head, sent)
            sent = re.sub(r'<\s?[eE]2\s?>.*?<\s?[eE]2[eE]\s?>', tail, sent)
        return sent.lower().strip()

    def backforth_translate(self, sentence, head, tail, tokens=None, head_pos=None, tail_pos=None, tokenize=True):
        if tokens and head_pos and tail_pos:
            labeled_sent = self.tokens_labeled(tokens, head_pos, tail_pos, self.zh_ent1, self.zh_ent2)
        else:
            labeled_sent = self.sentence_labeled(sentence, head, tail, self.zh_ent1, self.zh_ent2)

        en2zh_sent = self.en2zh(labeled_sent)
        en2zh_sent = self.sentence_labeled(en2zh_sent, self.zh_ent1, self.zh_ent2, self.en_ent1, self.en_ent2)

        time.sleep(self.time_interval)

        zh2en_sent = self.zh2en(en2zh_sent)
        delabeled_sent = self.sentence_delabeled(zh2en_sent.lower(), self.en_ent1, self.en_ent2, head, tail)

        if tokenize:
            delabeled_sent = ' '.join(word_tokenize(delabeled_sent))
        return delabeled_sent


class ParaphraseTranslator(TranslatorBase):
    """
    pure backforth translation
    """
    def __init__(self, trans_type: str, trans_config: dict, time_interval: Optional[float] = 0.5):
        super().__init__(trans_type, trans_config, time_interval=time_interval)

    def backforth_translate(self, sentence, *args, tokenize=True, **kwargs):
        en2zh_sent = self.en2zh(sentence)
        time.sleep(self.time_interval)
        delabeled_sent = self.zh2en(en2zh_sent)

        if tokenize:
            delabeled_sent = ' '.join(word_tokenize(delabeled_sent))
        return delabeled_sent

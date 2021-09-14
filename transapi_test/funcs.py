import os
import time
import json
import urllib3
import traceback
import threading
import copy
import logging
import multiprocessing as mp

from flask import Flask, render_template

from transkit.translator import Translator
from transkit.utils import FewRelUtils
from transkit.mpshare import SharedInfo
from transkit.proxy import APIMiddleware


logger = logging.getLogger('trans_logger')
logger.setLevel(logging.INFO)
log_path = 'log.log'
fh = logging.FileHandler(log_path)
fh.setLevel(logging.INFO)
fmt = "[%(asctime)-15s]-%(levelname)s-%(filename)s-%(lineno)d-%(process)d: %(message)s"
datefmt = "%a %d %b %Y %H:%M:%S"
formatter = logging.Formatter(fmt, datefmt)
fh.setFormatter(formatter)
logger.addHandler(fh)


def backforth_trans(name, trans_obj, ins, tokens=None, head_pos=None, tail_pos=None):
    sh = qmsg.get()
    sh.tot_proxies_num = api_mdw.get_len('tot')
    sh.non_proxies_num = api_mdw.get_len('non')
    sh.ggl_proxies_num = api_mdw.get_len('ggl')
    qmsg.put(sh)
    while True:
        try:
            sent = trans_obj.backforth_translate(ins['sentence'], ins['head'], ins['tail'],
                                                 tokens=tokens, head_pos=head_pos, tail_pos=tail_pos)
            if sent:
                break
        except (OSError, json.JSONDecodeError, ConnectionError, \
                urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError):
            err = traceback.format_exc()
            logger.error('{} in backforthtrans function from main.py: {}'.format(name, err.replace('\n', '\t')))
            if trans_obj.proxies:
                ip = trans_obj.proxies['http'].split(':')[1].split('/')[-1]
                port = trans_obj.proxies['http'].split(':')[-1]
                protocol = trans_obj.proxies['http'].split(':')[1].split('/')[-1]
                api_mdw.delete(ip, port, protocol)
            trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=api_mdw.get_proxies())
            
            sh = qmsg.get()
            if name == 'google':
                sh.ggl_obj_changed_cnt += 1
            elif name == 'baidu':
                sh.baidu_obj_changed_cnt += 1
            elif name == 'xiaoniu':
                sh.xiaoniu_obj_changed_cnt += 1
            qmsg.put(sh)
            print('.', end='')
        except KeyError:
            err = traceback.format_exc()
            logger.error('{} in backforthtrans function from main.py: {}'.format(name, err.replace('\n', '\t')))
            if name == 'baidu':
                continue
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            err = traceback.format_exc()
            logger.error('{} in backforthtrans function from main.py: {}'.format(name, err.replace('\n', '\t')))
            if 'sre_constants.error' in str(e.__class__):
                with open('middle/error_process_instances', 'a', encoding='utf-8') as f:
                    f.write('{}\n'.format(json.dumps(ins)))
                sent = ""
            break
    return trans_obj, sent


def multi_trans(param):
    cnt = 0; file_data = param['data']
    sh = qmsg.get()
    if param['name'] == 'google':
        sh.ggl_tot_cnt = len(file_data) - param['start'] + 1
    elif param['name'] == 'baidu':
        sh.baidu_tot_cnt = len(file_data) - param['start'] + 1
    elif param['name'] == 'xiaoniu':
        sh.xiaoniu_tot_cnt = len(file_data) - param['start'] + 1
    qmsg.put(sh)
    
    if not os.path.exists('middle'):
        os.mkdir('middle')
        
    t = Translator(param['name'], util_obj=FewRelUtils())
    for ins in file_data:
        cnt += 1
        if cnt < param['start']:
            continue
        tokens_ = ins['original_info']['tokens']
        head_pos_ = ins['original_info']['h'][-1]
        tail_pos_ = ins['original_info']['t'][-1]
        st = time.time()
        t, ins['translation'][param['name']] = backforth_trans(param['name'], t, ins,
                                                                tokens=tokens_, 
                                                                head_pos=head_pos_, 
                                                                tail_pos=tail_pos_)
        et = time.time() - st
        sh = qmsg.get()
        if param['name'] == 'google':
            sh.ggl_cnt += 1
            sh.ggl_last_time = et
            sh.ggl_tot_time += et
            sh.ggl_avg_time = sh.ggl_tot_time / sh.ggl_cnt
        elif param['name'] == 'baidu':
            sh.baidu_cnt += 1
            sh.baidu_last_time = et
            sh.baidu_tot_time += et
            sh.baidu_avg_time = sh.baidu_tot_time / sh.baidu_cnt
        elif param['name'] == 'xiaoniu':
            sh.xiaoniu_cnt += 1
            sh.xiaoniu_last_time = et
            sh.xiaoniu_tot_time += et
            sh.xiaoniu_avg_time = sh.xiaoniu_tot_time / sh.xiaoniu_cnt
        qmsg.put(sh)
        with open('middle/' + param['file'] + '_' + param['name'], 'a', encoding='utf-8') as f:
            f.write('{}\n'.format(json.dumps(ins)))
            

def ensemble(file, names):
    results = []
    with open('middle/' + file + "_" + names[0], 'r', encoding='utf-8') as f:
        for line in f:
            ins = json.loads(line.strip())
            results.append(ins)
    
    if len(names) == 1:
        return results
    
    datas = dict()
    for name in names[1:]:
        datas[name] = dict()
        with open('middle/' + file + "_" + name, 'r', encoding='utf-8') as f:
            for line in f:
                ins = json.loads(line.strip())
                datas[name][ins['id']] = ins
    
    for name in names[1:]:
        for ins in results:
            ins['translation'][name] = datas[name][ins['id']]['translation'][name]
    
    if not os.path.exists('results'):
        os.mkdir('results')
    for ins in results:
        with open('results/' + file + "_ensemble_results", 'a', encoding='utf-8') as f:
            f.write('{}\n'.format(json.dumps(ins)))

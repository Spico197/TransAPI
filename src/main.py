import os
import time
import json
import urllib3
import traceback
import threading
import copy
import logging

import multiprocessing as mp

from transkit.translator import Translator
from transkit.utils import FewRelUtils
from transkit.proxy import ProxyPool
from transkit.mpshare import SharedInfo
from flask import Flask, render_template


DATA_DIR = '/data/tzhu/FewRel'
DATA_FILES = [
    'fewrel_train.json', 'fewrel_val.json',
]

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


def backforth_trans(name, trans_obj, ins, ppool, tokens=None, head_pos=None, tail_pos=None):
    retries = 0
    while True:
        try:
            sent = trans_obj.backforth_translate(ins['sentence'], ins['head'], ins['tail'],
                                                 tokens=tokens, head_pos=head_pos, tail_pos=tail_pos)
            if sent:
                break
#         except OSError:
#             trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=ppool.get_proxies())
#             retries += 1
#             print('.', end='')
#         except json.JSONDecodeError:
#             trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=ppool.get_proxies())
#             retries += 1
#             print('.', end='')
#         # except ConnectionError:
#         #     trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=ppool.get_proxies())
#         #     retries += 1
#         #     print('.', end='')
#         except urllib3.exceptions.NewConnectionError:
#             trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=ppool.get_proxies())
#             retries += 1
#             print('.', end='')
#         except urllib3.exceptions.MaxRetryError:
#             trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=ppool.get_proxies())
#             retries += 1
#             print('.', end='')
        except:
            err = traceback.format_exc()
            logger.error('{} in backforthtrans function from main.py: {}'.format(name, err.replace('\n', '\t')))
            trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=ppool.get_proxies())
            
            sh = qmsg.get()
            if name == 'google':
                sh.ggl_obj_changed_cnt += 1
            elif name == 'baidu':
                sh.baidu_obj_changed_cnt += 1
            elif name == 'xiaoniu':
                sh.xiaoniu_obj_changed_cnt += 1
            qmsg.put(sh)
            
            retries += 1
            print('.', end='')
        if retries >= 30:
            ppool.clear()
            ppool.crawl_proxies('github', early_stopped=3)
    return trans_obj, sent, ppool


def multi_trans(param):
    cnt = 0; file_data = param['data']
    ppool = param['ppool']
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
        t, ins['translation'][param['name']], ppool = backforth_trans(param['name'], t, ins, ppool,
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
    
            
def main_thread(DATA_FILES):
    utils = FewRelUtils()
    for file in DATA_FILES:
        if qmsg.qsize() > 0:
            qmsg.get()
        sh = SharedInfo()
        sh.name = file.split('.')[0]
        qmsg.put(sh)
        
        path = os.path.join(DATA_DIR, file)
        file_data = utils.load_data(path)
        
        """start multi processing"""

        pool = mp.Pool()
        gppool = ProxyPool()
        gppool.clear()
        gppool.crawl_proxies('github', early_stopped=200)
        nppool = ProxyPool()
        nppool.clear()
        nppool.crawl_proxies('github', early_stopped=5)
        bppool = ProxyPool()
        bppool.clear()
        bppool.crawl_proxies('github', early_stopped=5)
        
        
        if file == 'fewrel_train.json':
            params = [
                {'file': file.split('.')[0], 'name':'google', 'data': file_data.copy(), 'start': 960, 'ppool': gppool},
                {'file': file.split('.')[0], 'name':'xiaoniu', 'data': file_data.copy(), 'start': 17759, 'ppool': nppool},
                {'file': file.split('.')[0], 'name':'baidu', 'data': file_data.copy(), 'start': 17646, 'ppool': bppool}
            ]
        else:
            params = [
                {'file': file.split('.')[0], 'name':'google', 'data': file_data.copy(), 'start': 1, 'ppool': gppool},
                {'file': file.split('.')[0], 'name':'xiaoniu', 'data': file_data.copy(), 'start': 1, 'ppool': nppool},
                {'file': file.split('.')[0], 'name':'baidu', 'data': file_data.copy(), 'start': 1, 'ppool': bppool}
            ]
        
        pool.map(multi_trans, params)
        pool.close()
        pool.join()
        
        ensemble(file.split('.')[0], ['google', 'baidu', 'xiaoniu'])

        
def watch_thread(params):
    ipt = input('>>> ')
    while ipt != 'c':
        if ipt == 'report':
            sh = qmsg.get()
            sh.report()
            qmsg.put(sh)
        ipt = input('>>> ')


def flask_thread(params):
    app = Flask('data_translation')

    @app.route('/')
    def get_status():
        sh = qmsg.get()
        data = copy.deepcopy(sh)
        qmsg.put(sh)
        try:
            setattr(data, 'ggl_process', data.ggl_cnt/data.ggl_tot_cnt*100)
        except:
            setattr(data, 'ggl_process', 0.0)
        setattr(data, 'ggl_remain_time', data.ggl_avg_time*(data.ggl_tot_cnt - data.ggl_cnt))
        try:
            setattr(data, 'baidu_process', data.baidu_cnt/data.baidu_tot_cnt*100)
        except:
            setattr(data, 'baidu_process', 0.0)
        setattr(data, 'baidu_remain_time', data.baidu_avg_time*(data.baidu_tot_cnt - data.baidu_cnt))
        try:
            setattr(data, 'xiaoniu_process', data.xiaoniu_cnt/data.xiaoniu_tot_cnt*100)
        except:
            setattr(data, 'xiaoniu_process', 0.0)
        setattr(data, 'xiaoniu_remain_time', data.xiaoniu_avg_time*(data.xiaoniu_tot_cnt - data.xiaoniu_cnt))
        return render_template('report.html', report=data)
    
    app.run(host="0.0.0.0")
    
        
if __name__ == "__main__":
    qmsg = mp.Queue()

    main_thread_handler = threading.Thread(target=main_thread, args=(DATA_FILES,))
    watch_thread_handler = threading.Thread(target=watch_thread, args=(1,))
    flask_thread_handler = threading.Thread(target=flask_thread, args=(1,))
    
    main_thread_handler.start()
    watch_thread_handler.start()
    flask_thread_handler.start()

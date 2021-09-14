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


DATA_DIR = '/data/tzhu/FewRel'
DATA_FILES = [
    'fewrel_val.json',
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
                print('delete: ', trans_obj.proxies)
                fr = api_mdw.find(ip=ip, port=port, protocol=protocol)
                if fr:
                    print(fr)
                    assert 0
                fr2 = api_mdw.get_proxies()[0]
                if fr2 == trans_obj.proxies:
                    assert 0
            if name == 'google':
                pxes = api_mdw.get_proxies(num=1, google_passed=1)
                px = pxes[0]
            else:
                pxes = api_mdw.get_proxies(num=1, google_passed=0)
                px = pxes[0]
            trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=px)
            
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
            else:
                err = traceback.format_exc()
                logger.error('{} in backforthtrans function from main.py: {}'.format(name, err.replace('\n', '\t')))
                if trans_obj.proxies:
                    ip = trans_obj.proxies['http'].split(':')[1].split('/')[-1]
                    port = trans_obj.proxies['http'].split(':')[-1]
                    protocol = trans_obj.proxies['http'].split(':')[1].split('/')[-1]
                    api_mdw.delete(ip, port, protocol)
                    print('delete: ', trans_obj.proxies)
                    fr = api_mdw.find(ip=ip, port=port, protocol=protocol)
                    if fr:
                        print(fr)
                        assert 0
                    fr2 = api_mdw.get_proxies()[0]
                    if fr2 == trans_obj.proxies:
                        assert 0
                if name == 'google':
                    pxes = api_mdw.get_proxies(num=1, google_passed=1)
                    px = pxes[0]
                else:
                    pxes = api_mdw.get_proxies(num=1, google_passed=0)
                    px = pxes[0]
                trans_obj = Translator(name, util_obj=trans_obj.utils, proxies=px)
                sh = qmsg.get()
                if name == 'google':
                    sh.ggl_obj_changed_cnt += 1
                elif name == 'baidu':
                    sh.baidu_obj_changed_cnt += 1
                elif name == 'xiaoniu':
                    sh.xiaoniu_obj_changed_cnt += 1
                qmsg.put(sh)
                print('.', end='')
    return trans_obj, sent


def multi_trans(param):
    cnt = 0; file_data = param['data']
    sh = qmsg.get()
    if param['name'] == 'google':
        sh.ggl_tot_cnt = len(file_data)
    elif param['name'] == 'baidu':
        sh.baidu_tot_cnt = len(file_data)
    elif param['name'] == 'xiaoniu':
        sh.xiaoniu_tot_cnt = len(file_data)
    qmsg.put(sh)
    
    if not os.path.exists('middle'):
        os.mkdir('middle')

    if param['name'] == 'google':
        pxes = api_mdw.get_proxies(num=1, google_passed=1)
        px = pxes[0]
    else:
        pxes = api_mdw.get_proxies(num=1, google_passed=0)
        px = pxes[0]
    t = Translator(param['name'], util_obj=FewRelUtils(), proxies=px)
    for ins in file_data:
        cnt += 1
        if cnt < param['start']:
            sh = qmsg.get()
            if param['name'] == 'google':
                sh.ggl_cnt += 1
            elif param['name'] == 'baidu':
                sh.baidu_cnt += 1
            elif param['name'] == 'xiaoniu':
                sh.xiaoniu_cnt += 1
            qmsg.put(sh)
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
    id_set = set()
    with open('middle/' + file + "_" + names[0], 'r', encoding='utf-8') as f:
        for line in f:
            ins = json.loads(line.strip())
            if ins['id'] not in id_set:
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
        print(len(file_data))
        params = [
            {'file': file.split('.')[0], 'name':'google', 'data': file_data.copy(), 'start': 1},
            {'file': file.split('.')[0], 'name':'xiaoniu', 'data': file_data.copy(), 'start': 1},
            {'file': file.split('.')[0], 'name':'baidu', 'data': file_data.copy(), 'start': 1}
        ]

        pool.map(multi_trans, params)
        pool.close()
        pool.join()
        
        ensemble(file.split('.')[0], ['google', 'baidu', 'xiaoniu'])

        
# def watch_thread(params):
#     ipt = input('>>> ')
#     while ipt != 'c':
#         if ipt == 'report':
#             sh = qmsg.get()
#             sh.report()
#             qmsg.put(sh)
#         ipt = input('>>> ')


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
    
    app.run(host="0.0.0.0", port='65420')
    
        
if __name__ == "__main__":
    qmsg = mp.Queue()
    api_mdw = APIMiddleware()

    main_thread_handler = threading.Thread(target=main_thread, args=(DATA_FILES,))
    # watch_thread_handler = threading.Thread(target=watch_thread, args=(1,))
    flask_thread_handler = threading.Thread(target=flask_thread, args=(1,))
    
    main_thread_handler.start()
    # watch_thread_handler.start()
    flask_thread_handler.start()
    print(api_mdw.get_proxies())

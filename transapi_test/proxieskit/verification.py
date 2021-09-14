import telnetlib

import requests

from config import configger
from storage import ProxyInstance

header = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Mobile Safari/537.36',
}

def verify(obj, timeout=configger.VERIFICATION_TIMEOUT):
    if not isinstance(obj, ProxyInstance):
        raise ValueError
    ip = obj.ip
    port = obj.port
    proto = obj.protocol
    try:
        telnetlib.Telnet(ip, port=port, timeout=timeout)
        obj.verified = True
        obj.google_passed = False
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        return False
        
    try:
        pxs = {
            'http': "{}://{}:{}".format(proto, ip, port),
            'https': "{}://{}:{}".format(proto, ip, port)
        }
        response = requests.get('https://translate.google.cn', headers=header, proxies=pxs, timeout=timeout)
        response.raise_for_status()
        obj.speed = response.elapsed.total_seconds()
        obj.google_passed = True
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        pass
    finally:
        return obj

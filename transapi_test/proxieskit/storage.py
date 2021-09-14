# import heapq # heap is not good enough for this task
from functools import total_ordering


@total_ordering
class ProxyInstance(object):
    def __init__(self, *args, **kwargs):
        assert kwargs.get('ip', False)
        assert kwargs.get('port', False)
        assert kwargs.get('protocol', False)
        
        self.ip = kwargs.get('ip')
        self.port = str(kwargs.get('port'))
        self.protocol = kwargs.get('protocol').lower()
        self.location = kwargs.get('location', '').lower()
        self.anonymity = kwargs.get('anonymity', '').lower()
        self.google_passed = kwargs.get('google_passed', False)
        self.verified = kwargs.get('verified', False)
        self.speed = kwargs.get('speed', 10.0)
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except:
            return default

    def __int__(self):
        return int(self.speed)
    
    def __float__(self):
        return float(self.speed)

    def __lt__(self, other):
        return self.speed < other.speed

    def __eq__(self, other):
        return (self.speed - other.speed) <= 1e-6
    
    def __str__(self):
        return "{}://{}:{}".format(self.protocol, self.ip, self.port)

    def __type__(self):
        return '<ProxyInstance: {}>'.format(str(self))
    
    def to_dict(self):
        return self.__dict__


class StoragerMeta(object):
    def __init__(self, *args, **kwargs):
        pass

    def save(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError
    
    def get(self):
        raise NotImplementedError


class DictDataBase(object):
    def __init__(self, *args, **kwargs):
        """
        {"ip-port-protocol": ProxyInstance()}
        example:
            {
                "1.2.3.4-3455-http": ProxyInstance(),
                "2.3.4.1-4567-https": ProxyInstance()
            }
        """
        self.db = dict()

    def _match(self, obj, kwargs):
        for k, v in kwargs.items():
            if obj.get(k, None) == v:
                return True
        return False

    def select(self, kwargs):
        resultset = []
        if kwargs.get('limit'):
            limit = kwargs.get('limit')
        else:
            limit = len(self)
        print('limit', limit)
        cnt = 0
        for obj in self.db.values():
            if cnt >= limit:
                break
            if self._match(obj, kwargs):
                resultset.append(obj)
                cnt += 1
        return resultset

    def insert(self, obj):
        self.db['{}-{}-{}'.format(obj.ip, obj.port, obj.protocol)] = obj
    
    def update(self, obj, new_obj):
        self.db['{}-{}-{}'.format(obj.ip, obj.port, obj.protocol)] = new_obj

    def delete(self, obj):
        try:
            del self.db['{}-{}-{}'.format(obj.ip, obj.port, obj.protocol)]
        except:
            pass
    
    def __len__(self):
        return len(self.db)


class RAMMapStorager(StoragerMeta):
    def __init__(self, *args, **kwargs):
        super(RAMMapStorager, self).__init__(*args, **kwargs)
        self.client = DictDataBase()
        self.black_list = set()

    def __len__(self):
        return len(self.client)

    def save(self, obj):
        if isinstance(obj, ProxyInstance):
            if str(obj) not in self.black_list:
                self.client.insert(obj)
    
    def delete(self, obj):
        self.black_list.add(str(obj))
        self.client.delete(obj)
    
    def get_proxies(self, num=1, google_passed=0):
        resultset = []
        if google_passed:
            objs = self.client.select({'google_passed': True, 'limit': num})
            objs = sorted(objs)[:num]
        else:
            objs = self.client.select({'google_passed': False, 'limit': num})
            
        for obj in objs:
            px = {
                'http': str(obj),
                'https': str(obj)
            }
            resultset.append(px)
        return resultset
    
    def get_length(self, google_passed):
        if google_passed:
            return len(self.client.select({'google_passed': True}))
        else:
            return len(self.client.select({'google_passed': False}))
        
    def find(self, **kwargs):
        return self.client.select(kwargs)

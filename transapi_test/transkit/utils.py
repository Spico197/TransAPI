import re
import json


class UtilsMeta(object):
    def tokens2sentence(self, tokens, head, tail):
        sentence = ' '.join(tokens)
        sentence = ' '.join(re.sub(r'\s', ' ', sentence).split())
        return sentence.lower()

    def load_data(self, path):
        raise NotImplementedError
    
    def sentence_labeled(self, sentence, head, tail, replace=True):
        sent = sentence
        if replace:
            sent.replace(head, 'A'*15)
            sent.replace(tail, 'B'*15)
        else:
            sent = sent.replace(head, '<e1>' + head + '<e1e>')
            sent = sent.replace(tail, '<e2>' + tail + '<e2e>')
        return sent
    
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
            sent = re.sub(r'<\s?[eE]1\s?>.*?<\s?[eE]1[eE]\s?>', 'A'*15, sent)
            sent = re.sub(r'<\s?[eE]2\s?>.*?<\s?[eE]2[eE]\s?>', 'B'*15, sent)
        return sent.lower()
    
    def sentence_delabeled(self, sentence, head, tail, replace=True):
        sent = sentence
        if replace:
            sent = re.sub(r'[Aa]{4,}', head, sent)
            sent = re.sub(r'[Bb]{4,}', tail, sent)
        else:
            sent = re.sub(r'<\s?[eE]1\s?>.*?<\s?[eE]1[eE]\s?>', head, sent)
            sent = re.sub(r'<\s?[eE]2\s?>.*?<\s?[eE]2[eE]\s?>', tail, sent)
        return sent.lower().strip()

    
class FewRelUtils(UtilsMeta):
    def __init__(self, *args, **kwargs):
        super(FewRelUtils, self).__init__(*args, **kwargs)
        
    def load_data(self, path):
        return_data = []
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cnt = 1
        for rel, values in data.items():
            for ins in values:
                one_data = {
                    "id": str(cnt),
                    "original_info": {},
                    "sentence": "",
                    "relation": "",
                    "head": "",
                    "tail": "",
                    "translation": {
                        "google": "",
                        "baidu": "",
                        "xiaoniu": ""
                    }
                }
                one_data['original_info'] = ins
                one_data['sentence'] = self.tokens2sentence([x.lower() for x in \
                                                             ins['tokens']], ins['h'][0].lower(), ins['t'][0].lower())
                one_data['relation'] = rel
                one_data['head'] = ins['h'][0].lower()
                one_data['tail'] = ins['t'][0].lower()
                return_data.append(one_data)
                cnt += 1
        return return_data

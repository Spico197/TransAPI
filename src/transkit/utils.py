import re
import json
from nltk import word_tokenize


class UtilsMeta(object):
    def tokens2sentence(self, tokens):
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
                one_data['sentence'] = self.tokens2sentence([x.lower() for x in ins['tokens']])
                one_data['relation'] = rel
                one_data['head'] = ins['h'][0].lower()
                one_data['tail'] = ins['t'][0].lower()
                return_data.append(one_data)
                cnt += 1
        return return_data

    
class TacredUtils(UtilsMeta):
    def __init__(self, *args, **kwargs):
        super(TacredUtils, self).__init__(*args, **kwargs)
    
    def load_data(self, path):
        return_data = []
        with open(path, 'r', encoding='utf-8') as f:
            ori_data = json.load(f)
        cnt = 1
        for ins in ori_data:
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
            one_data['sentence'] = self.tokens2sentence([x.lower() for x in ins['token']])
            one_data['relation'] = ins['relation']
            one_data['head'] = ' '.join(ins['token'][ins['subj_start']: ins['subj_end'] + 1]).lower()
            one_data['tail'] = ' '.join(ins['token'][ins['obj_start']: ins['obj_end'] + 1]).lower()
            return_data.append(one_data)
            cnt += 1
        return return_data

    
class SemEval2010Task8Utils(UtilsMeta):
    def __init__(self, *args, **kwargs):
        super(SemEval2010Task8Utils, self).__init__(*args, **kwargs)
        
    def load_data(self, filepath):
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            texts = f.readlines()

            ori_ids = re.findall(r'(\d+)\t".*?"', '\n'.join(texts))
            sentences = re.findall(r'\d+\t"(.*)"\n', '\n'.join(texts))
            relations = re.findall(r'(.*?(\(e2,e1\)|\(e1,e2\))|\nOther)', '\n'.join(texts))
            relations = [x[0].strip() for x in relations]
            comments = re.findall(r'\nComment:(.*?)\n', '\n'.join(texts))
            comments = [x.strip() for x in comments]
            heads = re.findall(r'<e1>(.*?)</e1>', '\n'.join(texts))
            tails = re.findall(r'<e2>(.*?)</e2>', '\n'.join(texts))
    #         print(len(sentences))
    #         print(sentences)
            cnt = 1
            for ori_id, sentence, relation, comment, head, tail in \
                zip(ori_ids, sentences, relations, comments, heads, tails):
                new_sent = re.sub(r'<e1>.*?</e1>', ' {} '.format(head), sentence)
                new_sent = re.sub(r'<e2>.*?</e2>', ' {} '.format(tail), new_sent)
                new_sent = ' '.join(word_tokenize(new_sent))
                head_pos = [[new_sent.split().index(head.split()[0]), \
                             new_sent.split().index(head.split()[0]) + len(head.split())]]
                tail_pos = [[new_sent.split().index(tail.split()[0]), \
                             new_sent.split().index(tail.split()[0]) + len(tail.split())]]
                one_data = {
                    "id": str(cnt),
                    "original_info": {
                        "id": ori_id,
                        "sentence": sentence,
                        "relation": relation,
                        "comment": comment,
                        "head_pos": head_pos,
                        "tail_pos": tail_pos,
                        "token": new_sent.split(),
                    },
                    "sentence": new_sent,
                    "relation": relation,
                    "head": head,
                    "tail": tail,
                    "translation": {
                        "google": "",
                        "baidu": "",
                        "xiaoniu": ""
                    }
                }
                data.append(one_data)

                cnt += 1
        return data

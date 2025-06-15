import os
import sys
import re
import pandas as pd
from tqdm import tqdm
import nltk
from nltk.corpus import stopwords
from pymorphy3 import MorphAnalyzer

nltk.download('stopwords', quiet=True)
rus_stop = set(stopwords.words('russian'))

morph = MorphAnalyzer()

class InvIndex():
    def __init__(self, df, stop_words=None, morph = None):
        self.stop_words = stop_words
        self.morph = morph
        df = df.dropna(subset=['text']).reset_index(drop=True)
        df['doc_id'] = df.index.astype(str)
        self.df = df
        self.index = self.create_index(self.df)
        
    def tokenizer(self, text):
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        lemmas = []
        for t in tokens:
            if self.stop_words is not None and t in self.stop_words:
                continue
            if self.morph is not None:
                parses = morph.parse(t)
                if not parses:
                    continue
                lemma = parses[0].normal_form
                if self.stop_words is not None:
                    if lemma not in self.stop_words:
                        lemmas.append(lemma)
                else:
                    lemmas.append(lemma)
            else:
                lemmas.append(t)
        return lemmas
    
    def create_index(self, df):
        index = {}
        for q, row in tqdm(df.iterrows(), total=df.shape[0]):
            tokens = self.tokenizer(row['text'])
            doc_id = row['doc_id']
            freqs = {}
            for word in tokens:
                freqs[word] = freqs.get(word, 0) + 1
            for word, cnt in freqs.items():
                if word in index:
                    index[word][doc_id] = cnt
                else:
                    index[word] = {doc_id: cnt}
                    
        return index
    
    def search_word(self, word):
        token = self.tokenizer(word)
        if len(token) == 0:
            return []
        
        w = token[0]
        posting = self.index.get(w, {})
        if len(posting) == 0:
            return []
        results = list(posting.items())
        results.sort(key=lambda x: x[1], reverse=True)
        # return [doc[0] for doc in results]
        return results
    
    def search_multiword(self, text):
        words = self.tokenizer(text)
        if len(words) == 0:
            return []

        postings = []
        for w in words:
            posting = self.index.get(w, {})
            if len(posting) == 0:
                return []
            postings.append(posting)

        common_docs = set(postings[0].keys())
        for posting in postings[1:]:
            common_docs &= set(posting.keys())
        if len(common_docs) == 0:
            return []
        results = []
        for doc_id in common_docs:
            score = sum(posting[doc_id] for posting in postings)
            results.append((doc_id, score))
        results.sort(key=lambda x: x[1], reverse=True)
        # return [doc[0] for doc in results]
        return results
    
    def get_docs(self, doc_id):
        if isinstance(doc_id, str):
            return self.df.loc[self.df['doc_id']==doc_id, 'text'].values[0]
        elif isinstance(doc_id, (list, tuple, set)):
            return self.df.loc[self.df['doc_id'].isin(doc_id), 'text']
        
    def get_corpus_len(self):
        return len(self.index)
    
if __name__ == "__main__":
    path = sys.argv[1]
    df = pd.read_csv(path, sep='\t')
    
    inv_index = InvIndex(df, morph=morph, stop_words=rus_stop)

    test_query = [
        'отопление',
        'перемена',
        'в Московском зоопарке начали',
        'Ранее во Владивостоке'
    ]
    results = []
    for query in test_query:
        print(f'Target word: "{query}"')
        if len(query.split(' ')) > 1:
            output = inv_index.search_multiword(query)
        else:
            output = inv_index.search_word(query)
        print(output)
        output = [doc[0] for doc in output]
        
        tokens_list = inv_index.tokenizer(query)
        
        flag = True
        for doc_id in output:
            doc = inv_index.get_docs(doc_id)
            doc_lemma = inv_index.tokenizer(inv_index.get_docs(doc_id))
            results.append({'query':query, 'lemma':doc_lemma, 'text':doc})
            for token in tokens_list:
                if token not in doc:
                    flag *= False
        print(f'All docs contain token "{tokens_list}": {flag}')
        print()
    
    df_res = pd.DataFrame(results)
    df_res.to_csv('res.csv')
        
    print(f'Num of index with morhp and stop-words: {inv_index.get_corpus_len()}')
    
    inv_index = InvIndex(df, morph=None, stop_words=rus_stop)
    print(f'Num of index with stop-words: {inv_index.get_corpus_len()}')
    
    inv_index = InvIndex(df, morph=None, stop_words=None)
    print(f'Num of index without morph and stop-words: {inv_index.get_corpus_len()}')

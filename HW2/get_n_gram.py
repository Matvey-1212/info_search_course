import os 
import re
import sys
import pandas as pd
import nltk
from nltk.corpus import stopwords
from pandarallel import pandarallel
from collections import Counter
from сustom_map import CastomCounter

nltk.download('stopwords', quiet=True)
rus_stop = set(stopwords.words('russian'))

pandarallel.initialize(progress_bar=True)

def preprocess_text(text):
    if not isinstance(text, str):
        return []
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    return [t for t in tokens if t not in rus_stop]

def get_ngrams(tokens_list, n):
    ngrams = []
    for tokens in tokens_list:
        for i in range(len(tokens) - n + 1):
            gram = tuple(tokens[i:i+n])
            ngrams.append(gram)
    return ngrams

if __name__ == "__main__":
    N = [2, 3, 4]
    top_len = 20
    path = sys.argv[1]
    df = pd.read_csv(path, sep='\t')
    
    tokens = df['text'].parallel_apply(preprocess_text).tolist()
    
    for n in N:
        print(f'top {top_len} N-gamm for n={n}')
        print(f"COUNTER {'_'*100}")
        print(Counter(get_ngrams(tokens, n)).most_common(top_len))
        print(f"CASTOM {'_'*100}")
        print(CastomCounter(get_ngrams(tokens, n)).most_common(top_len))
        print()
    
    
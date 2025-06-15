import os
import re
import numpy as np
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
# from transformers import AutoTokenizer, AutoModel
import torch
import faiss

class InvIndex():
    def __init__(self, df, embeddings=None, model_name='cointegrated/rubert-tiny'):
        df = df.dropna(subset=['text']).reset_index(drop=True)
        df = df[df['text'].apply(self.drop_short)].reset_index(drop=True)
        df['doc_id'] = df.index.astype(str)
        self.df = df
        self.model = SentenceTransformer(model_name)
        
        if embeddings is None:
            self.embeddings = self.get_emb(df['text'].tolist(), show_progress_bar=True)
            np.save('embeddings.npy', self.embeddings)
        elif embeddings.shape[0] == df.shape[0]:
            faiss.normalize_L2(embeddings)
            self.embeddings = embeddings
            
        self.create_index()
        
    def drop_short(self, val):
        if len(val) < 50:
            return False
        return True
    
    def get_emb(self, data_list, show_progress_bar=False):
        embeddings = self.model.encode(data_list, convert_to_numpy=True, show_progress_bar=show_progress_bar)
        faiss.normalize_L2(embeddings)
        return embeddings
        
        
    def create_index(self):
        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(self.embeddings)
    
    def semantic_search(self, word, top_k=10):
        query_emb = self.get_emb([word])
        D, I = self.index.search(query_emb, top_k)
        sims = D[0]
        sims_norm = (sims + 1) / 2
        results = []
        for idx, score in zip(I[0], sims_norm):
            doc_id = self.df.iloc[idx]['doc_id']
            results.append((doc_id, float(score)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    
    def get_docs(self, doc_id):
        if isinstance(doc_id, str):
            return self.df.loc[self.df['doc_id']==doc_id, 'text'].values[0]
        elif isinstance(doc_id, (list, tuple, set)):
            return self.df.loc[self.df['doc_id'].isin(doc_id), 'text']
    
if __name__ == "__main__":
    path = 'data/articles_extracted.tsv'
    df = pd.read_csv(path, sep='\t')
    embeddings = None
    try:
        embeddings = np.load('data/embeddings.npy')
    except:
        pass
    inv_index = InvIndex(df, model_name='distiluse-base-multilingual-cased-v2',embeddings=embeddings)

    test_query = [
        'введение дополнительных пошлин запланировано на октябрь следующего года',
        'обожаю мультики',
        'в Московском зоопарке начали',
        'Ранее во Владивостоке'
    ]

    results = []
    for query in test_query:
        print(f'Target word: "{query}"')
        output = inv_index.semantic_search(query)
        print(output)
        output = [doc[0] for doc in output]
        
        for doc_id in output:
            doc = inv_index.get_docs(doc_id)
            results.append({'query':query, 'text':doc})
        print()

    df_res = pd.DataFrame(results)
    df_res.to_csv('res.csv')
        
# Target word: "введение дополнительных пошлин запланировано на октябрь следующего года"
# [('4518', 0.6549399495124817), ('2476', 0.6511968374252319), ('6192', 0.6510170698165894), ('5535', 0.6382994055747986), ('7396', 0.6338196992874146), ('1655', 0.6328158378601074), ('9677', 0.6294562816619873), ('590', 0.6260074377059937), ('4588', 0.6181036829948425), ('3657', 0.6177862882614136)]

# Target word: "обожаю мультики"
# [('8941', 0.5958610773086548), ('798', 0.5781135559082031), ('4804', 0.5740636587142944), ('824', 0.5689041018486023), ('7347', 0.5626034736633301), ('459', 0.5620265603065491), ('3577', 0.5608938336372375), ('6838', 0.5585743188858032), ('5806', 0.558009147644043), ('9173', 0.5542946457862854)]

# Target word: "в Московском зоопарке начали"
# [('3933', 0.7285987734794617), ('9394', 0.7048007249832153), ('3868', 0.7040282487869263), ('4794', 0.6950809955596924), ('9193', 0.6917909979820251), ('8296', 0.6883907318115234), ('3431', 0.684501051902771), ('1557', 0.6827715635299683), ('8817', 0.6820986270904541), ('2667', 0.6805094480514526)]

# Target word: "Ранее во Владивостоке"
# [('284', 0.6937113404273987), ('7819', 0.693475604057312), ('1972', 0.6908295154571533), ('4070', 0.6889685392379761), ('4087', 0.685509443283081), ('2189', 0.6849928498268127),
    
        
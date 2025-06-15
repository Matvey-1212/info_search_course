import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_and_parse(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        title_el = soup.find('h1', class_='article__heading')
        title = title_el.get_text(separator=' ', strip=True) if title_el else ''
        summary_el = soup.find('div', class_='article__summary')
        summary = summary_el.get_text(separator=' ', strip=True) if summary_el else ''
        body_el = soup.find('div', class_='article__text')
        if body_el:
            paragraphs = [p.get_text(separator=' ', strip=True) for p in body_el.find_all('p')]
            body = ' '.join(paragraphs)
        else:
            body = ''
        meta_theme = soup.find('meta', attrs={'name': 'mediator_theme'})
        category = meta_theme['content'] if meta_theme and meta_theme.has_attr('content') else ''
        title = title.replace('\t', ' ')
        summary = summary.replace('\t', ' ')
        body = body.replace('\t', ' ')
        category = category.replace('\t', ' ')
        return {'url': url, 'title': title, 'summary': summary, 'text': body, 'category': category}
    except:
        return {'url': url, 'title': '', 'summary': '', 'text': '', 'category': ''}

if __name__ == "__main__":
    sitemap_index_url = "https://russian.rt.com/sitemap.xml"
    max_links = 100
    max_workers = 100
    
    save_path = 'articles_extracted2.tsv'

    r = requests.get(sitemap_index_url)
    root = ET.fromstring(r.text)
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemaps = []
    for s in root.findall('sm:sitemap', ns):
        loc = s.find('sm:loc', ns).text
        lm = s.find('sm:lastmod', ns)

        lm_dt = datetime.fromisoformat(lm.text) if lm is not None else datetime.min
        sitemaps.append((loc, lm_dt))
    sitemaps.sort(key=lambda x: x[1], reverse=False)

    entries = []
    for loc, _ in sitemaps[::-1]:
        r2 = requests.get(loc, headers={"User-Agent": "Mozilla/5.0"})
        root2 = ET.fromstring(r2.text)
        for u in root2.findall('sm:url', ns):
            url = u.find('sm:loc', ns).text
            lm2 = u.find('sm:lastmod', ns)
            # last = lm2.text if lm2 is not None else ""
            entries.append(url)
            if max_links and len(entries) >= max_links:
                break
        if max_links and len(entries) >= max_links:
            break
        
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_and_parse, url): url for url in entries}
        for future in tqdm(as_completed(futures), total=len(futures)):
            results.append(future.result())

    out = pd.DataFrame(results)
    out = out.dropna()
    out = out.drop_duplicates(subset=['url'])
    out.to_csv(save_path, sep='\t', index=False)

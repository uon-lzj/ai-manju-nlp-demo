"""可审计的原始领域分词与正负token出现次数规则。"""
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
from research_core import tokenize as original_tokenize, sentiment as original_sentiment, DOMAIN, STOPWORDS

ROOT = Path(__file__).resolve().parent


def load_lexicon():
    return json.loads((ROOT / 'lexicon.json').read_text(encoding='utf-8'))


def tokenize(text, lexicon=None):
    return original_tokenize(text)


def analyze(text, lexicon=None):
    lexicon = lexicon or load_lexicon()
    cleaned = text
    tokens = tokenize(text)
    positive = [w for w in tokens if w in lexicon['positive']]
    negative = [w for w in tokens if w in lexicon['negative']]
    p, n = len(positive), len(negative)
    if p > n:
        label, reason = '正向', '正向词出现次数多于负向词。'
    elif n > p:
        label, reason = '负向', '负向词出现次数多于正向词。'
    elif p:
        label, reason = '中性', '正负词出现次数相等（混合命中）。'
    else:
        label, reason = '中性', '未命中情感词；不代表已经确认客观中性。'
    assert label == original_sentiment(tokens)
    return {'text': text, 'normalized': cleaned, 'tokens': tokens,
            'positive_hits': positive, 'negative_hits': negative, 'label': label,
            'confidence': round(abs(p - n) / (p + n + 2), 6), 'reason': reason,
            'lexicon_version': lexicon['version']}


def highlight(text, lexicon=None):
    lexicon = lexicon or load_lexicon()
    # 保留原始字符位置，仅给实际分词命中的词上色。
    cleaned = re.sub(r'百度联想查询[:：]|百度返回联想词[:：]|百度未返回扩展联想词|查询词[:：]|联想词[:：]', lambda m: ' ' * len(m.group()), text)
    occupied = [False] * len(cleaned)
    spans = []
    for word in sorted(DOMAIN, key=len, reverse=True):
        for match in re.finditer(re.escape(word), cleaned, re.I):
            if not any(occupied[match.start():match.end()]):
                spans.append((match.start(), match.end(), word))
                occupied[match.start():match.end()] = [True] * (match.end() - match.start())
    rest = ''.join(' ' if occupied[i] else c for i, c in enumerate(cleaned))
    for match in re.finditer(r'[A-Za-z]{2,}|[\u4e00-\u9fff]{2,5}', rest):
        word = match.group()
        if word not in STOPWORDS and not word.startswith('百度'):
            spans.append((match.start(), match.end(), word))
    chunks, cursor = [], 0
    for start, end, word in sorted(spans):
        if word not in lexicon['positive'] + lexicon['negative']:
            continue
        chunks.append(html.escape(text[cursor:start]))
        positive = word in lexicon['positive']
        color, badge = ('#d1fae5', '正向') if positive else ('#fee2e2', '负向')
        chunks.append(f'<mark title="{badge}" style="background:{color};color:#111;padding:2px 4px;border-radius:3px">{html.escape(text[start:end])}</mark>')
        cursor = end
    chunks.append(html.escape(text[cursor:]))
    return ''.join(chunks)


def parse_response(raw, callback='nlp_demo'):
    raw = raw.lstrip('\ufeff').strip()
    if raw.startswith('{'):
        data = json.loads(raw)
    else:
        match = re.fullmatch(re.escape(callback) + r'\s*\((.*)\)\s*;?', raw, re.S)
        if not match:
            raise ValueError('回包不是预期的 JSON / JSONP，未执行任何回调代码。')
        data = json.loads(match.group(1))
    if not isinstance(data, dict) or not isinstance(data.get('s'), list) or not all(isinstance(w, str) for w in data['s']):
        raise ValueError('回包结构变化：缺少字符串列表 s。请查看原始回包。')
    if data.get('status', 0) != 0:
        raise ValueError(f"百度返回非零状态：{data['status']}")
    return data


def fetch_suggestions(seed):
    seed = seed.strip()
    if not seed or len(seed) > 100:
        raise ValueError('请输入1—100个字符的种子词。')
    started = datetime.now(timezone.utc).isoformat()
    response = requests.get('https://suggestion.baidu.com/su',
                            params={'wd': seed, 'cb': 'nlp_demo', 'ie': 'utf-8', 'json': 1},
                            headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}, timeout=(5, 15))
    response.raise_for_status()
    response.encoding = response.encoding if response.encoding and response.encoding.lower() != 'iso-8859-1' else 'utf-8'
    raw = response.text
    record = {'seed': seed, 'request_url': response.url, 'fetched_at_utc': started,
              'http_status': response.status_code, 'elapsed_ms': round(response.elapsed.total_seconds() * 1000),
              'raw_response': raw, 'content_type': response.headers.get('Content-Type', ''),
              'parsed_json': None, 'parse_error': None}
    try:
        record['parsed_json'] = parse_response(raw)
    except (ValueError, json.JSONDecodeError) as error:
        record['parse_error'] = str(error)
    return record

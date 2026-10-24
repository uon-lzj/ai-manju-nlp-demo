import json
from collections import Counter
from datetime import datetime

import requests
import streamlit as st

from analyzer import analyze, fetch_suggestions, highlight, load_lexicon

st.set_page_config(page_title='AI漫剧 NLP 现场实验', layout='wide')
st.title('AI漫剧 NLP 现场实验')
st.write('种子词 → 百度实时联想 → 领域词典分词 → 情感词命中 → 规则判定')
lexicon = load_lexicon()
with st.sidebar:
    st.header('判定口径')
    st.write('P>N→正向；N>P→负向；P=N→中性。P/N为分词后正负词的出现次数，含重复。')
    st.caption('这是原报告的词典规则，未处理否定或反讽。“不赚钱”仍会命中“赚钱”；“版权”按原报告计负向，并非法律判断。')
    st.subheader('词典来源')
    st.write(lexicon['provenance'])
    st.json(lexicon)
    st.subheader('置信度说明')
    st.write('展示规则证据分数 C=|P−N|/(P+N+2)，P/N为分词后正/负向词出现次数；不是训练模型概率或准确率。')
    st.caption('此分数为演示新增，无命中或正负数量相等时为0；重复会增加证据次数，不表示独立证据。')

with st.form('query'):
    seed = st.text_input('输入任意种子词', value='AI 漫剧赚钱', max_chars=100,
                         help='例如：AI 漫剧赚钱、AI 漫剧侵权、AI 漫剧教程。输入后回车或点击按钮。')
    submitted = st.form_submit_button('实时请求并分析', type='primary')

if submitted:
    st.session_state.pop('record', None)
    st.session_state.pop('error', None)
    if not seed.strip():
        st.session_state.error = '请输入种子词。'
    else:
        try:
            with st.spinner('正在请求百度联想接口…'):
                st.session_state.record = fetch_suggestions(seed)
        except (requests.RequestException, ValueError) as error:
            st.session_state.error = f'请求失败：{error}。检查网络后重新提交；此处不会用模拟回包替代。'
if 'error' in st.session_state:
    st.error(st.session_state.error)
record = st.session_state.get('record')
if record:
    st.caption(f"真实请求 · HTTP {record['http_status']} · {record['elapsed_ms']} ms · UTC {record['fetched_at_utc']}")
    st.code(record['request_url'], language='text')
    tab1, tab2, tab3 = st.tabs(['分词与判定', '原始回包与 JSON', '导出实验记录'])
    with tab2:
        st.subheader('接口原始 JSONP 文本（未改写）')
        st.code(record['raw_response'], language='javascript')
        if record['parse_error']:
            st.error(record['parse_error'])
        else:
            st.subheader('去除回调包装后的 JSON 对象')
            st.json(record['parsed_json'])
    with tab1:
        if record['parsed_json'] is not None:
            suggestions_text = '、'.join(record['parsed_json']['s'])
            combined = f"百度联想查询：{record['seed']}；百度返回联想词：{suggestions_text}" if suggestions_text else f"百度联想查询：{record['seed']}；百度未返回扩展联想词"
            aggregate = analyze(combined)
            st.subheader('整条记录最终判定（与论文统计单位一致）')
            x, y = st.columns(2)
            x.metric('查询词与联想词合并判定', aggregate['label'])
            y.metric('置信度（规则证据分数）', f"{aggregate['confidence']:.1%}")
            st.markdown(highlight(combined), unsafe_allow_html=True)
            st.write('领域分词：', ' / '.join(aggregate['tokens']))
            st.write('正向命中：', '、'.join(aggregate['positive_hits']) or '无')
            st.write('负向命中：', '、'.join(aggregate['negative_hits']) or '无')
            st.caption(aggregate['reason'])
        st.subheader('输入词本身的判定')
        result = analyze(record['seed'])
        a, b = st.columns(2)
        a.metric('最终情感判定', result['label'])
        b.metric('置信度（规则证据分数）', f"{result['confidence']:.1%}")
        st.markdown(highlight(record['seed']), unsafe_allow_html=True)
        st.write('领域分词：', ' / '.join(result['tokens']))
        st.write('停用词过滤后：', ' / '.join(t for t in result['tokens'] if t not in lexicon['stopwords']))
        st.write('正向命中：', '、'.join(result['positive_hits']) or '无')
        st.write('负向命中：', '、'.join(result['negative_hits']) or '无')
        st.caption(result['reason'])
        st.subheader('百度实际返回的联想词逐条分析')
        suggestions = record['parsed_json']['s'] if record['parsed_json'] else []
        if not suggestions:
            st.info('本次没有可分析的联想词。输入词的判定来自本地规则，不代表接口返回了联想词。')
        results = [analyze(text) for text in suggestions]
        if results:
            counts = Counter(r['label'] for r in results)
            st.write(f"实际返回{len(results)}条：正向{counts['正向']}，负向{counts['负向']}，中性{counts['中性']}。")
            st.dataframe([{'联想词': r['text'], '分词': ' / '.join(r['tokens']),
                           '正向命中': '、'.join(r['positive_hits']), '负向命中': '、'.join(r['negative_hits']),
                           '判定': r['label'], '规则证据分数': f"{r['confidence']:.1%}"} for r in results], hide_index=True)
            for i, r in enumerate(results, 1):
                st.markdown(f"{i}. {highlight(r['text'])} → **{r['label']}** · {r['confidence']:.1%}", unsafe_allow_html=True)
        st.caption('绿色为实际命中的正向词，红色为实际命中的负向词。使用原脚本分词：领域词按长度优先提取，余文提取2—5字汉字段；token顺序是算法提取顺序，不是原文顺序。')
    with tab3:
        payload = {**record, 'lexicon': lexicon, 'seed_analysis': analyze(record['seed']),
                   'combined_analysis': analyze(combined) if record['parsed_json'] is not None else None,
                   'suggestion_analyses': [analyze(t) for t in (record['parsed_json']['s'] if record['parsed_json'] else [])]}
        st.download_button('下载完整 JSON 实验记录', json.dumps(payload, ensure_ascii=False, indent=2),
                           file_name=f"nlp_demo_{datetime.now():%Y%m%d_%H%M%S}.json", mime='application/json')
else:
    st.info('输入种子词并提交，即可展示实时接口回包及完整分析链路。')

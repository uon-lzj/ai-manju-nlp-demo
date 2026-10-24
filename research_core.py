"""原始分析脚本的常量及分词、情感函数，逐字提取，未改算法。"""
import re

STOPWORDS = set("的 了 和 是 在 对 与 及 或 也 为 有 被 将 等 中 从 到 以 把 这 那 一个 以及 进行 可以 相关 通过 百度 联想 查询 返回 扩展 百度联想查 百度返回联 想词 查询词 联想词 未返回".split())

DOMAIN = [
    "AI漫剧", "AIGC短剧", "AI漫画视频", "AI动画短剧", "AI短视频", "生成式AI短剧",
    "剧本生成", "漫画生成", "配音", "分镜", "剪辑", "角色", "剧情", "提示词",
    "文生图", "文生视频", "数字人", "抖音", "快手", "B站", "小红书", "视频号",
    "流量", "推荐", "封面", "播放量", "粉丝", "商业化", "变现", "赚钱", "兼职",
    "创业", "收益", "爆款", "版权", "侵权", "授权", "监管", "审核", "标识",
    "合规", "原创", "素材", "肖像权", "声音权", "用户", "观众", "争议", "同质化",
]

POSITIVE = set("推荐 好看 爆款 免费 好用 赚钱 收益 创业 热点 原创 优质".split())

NEGATIVE = set("侵权 风险 争议 下架 投诉 同质化 吐槽 监管 审核 版权".split())

def tokenize(text):
    text = re.sub(r"百度联想查询[:：]|百度返回联想词[:：]|百度未返回扩展联想词|查询词[:：]|联想词[:：]", " ", text)
    tokens = []
    occupied = [False] * len(text)
    for word in sorted(DOMAIN, key=len, reverse=True):
        for m in re.finditer(re.escape(word), text, flags=re.I):
            if not any(occupied[m.start():m.end()]):
                tokens.append(word)
                for i in range(m.start(), m.end()):
                    occupied[i] = True
    rest = "".join(" " if occupied[i] else ch for i, ch in enumerate(text))
    tokens += re.findall(r"[A-Za-z]{2,}|[\u4e00-\u9fff]{2,5}", rest)
    cleaned = []
    for t in tokens:
        if t.lower() == "ai":
            t = "AI"
        if t not in STOPWORDS and len(t) > 1 and not t.startswith("百度"):
            cleaned.append(t)
    return cleaned

def sentiment(tokens):
    p = sum(t in POSITIVE for t in tokens)
    n = sum(t in NEGATIVE for t in tokens)
    return "正向" if p > n else "负向" if n > p else "中性"

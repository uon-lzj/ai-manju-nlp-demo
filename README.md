# AI漫剧 NLP 实时演示

公开云端部署配置，保留原研究的Python分词、词典和情感判定算法。输入种子词后实时调用百度接口，展示原始JSONP、解析后的JSON、领域分词、命中高亮、最终分类及未校准的规则证据分数。

## Render 部署

将本目录文件放到一个独立GitHub仓库根目录，使用Render Blueprint读取render.yaml，或创建Python Web Service：

- Build Command：`python -m pip install -r requirements.txt`
- Start Command：`python start_cloud.py`
- Health Check Path：`/_stcore/health`
- Instance Type：Free

服务通过平台分配的PORT端口监听0.0.0.0，发布后可由任何持有公开URL的访客访问，不需要访问者安装Python。

免费服务可能因闲置而休眠，答辩前应提前打开。实际可用性还取决于访客网络和云端到百度接口的连通性；部署后需在云端实测“AI 漫剧赚钱”“AI 漫剧侵权”。遇到接口失败会明确显示，不会切换为虚构数据。

## Streamlit Community Cloud 备选

将代码放到GitHub仓库后，在Streamlit Community Cloud选择该仓库、分支和`app.py`部署。此平台使用app.py作为入口，不使用start_cloud.py。

## 发布内容与研究口径

本公开部署目录仅包含工具代码及词典，未包含论文、原始CSV、作者信息或原压缩包。没有需要写入代码的API密钥。运行时只向百度请求用户当次提交的种子词；应用不主动持久保存输入或实验记录，访客可自行下载结果。托管平台仍可能产生正常服务日志。

正向11词、负向10词全部来自原研究脚本。分类比较分词后正负token出现次数，P>N正向、N>P负向、相等中性。工具不处理否定与反讽，不是训练出的情感模型。

置信度栏为新增规则分数C=|P−N|/(P+N+2)，不是准确率或校准概率。历史1200条数据的复核包保留在本地交付版本，公开服务不分发历史数据。

测试：`python -m unittest discover -s tests -v`

部署文档：[Render Web Services](https://render.com/docs/web-services)、[Render 免费服务](https://render.com/docs/free)、[Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)。

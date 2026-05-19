根据自己本地的Java项目构建一个问答智能体，可以问这个本地项目的问题，搜索不到答案会联网访问AI大模型进行搜索。

已实现的功能(目前使用智谱AI回答，可以根据需要进行变更)：

注意：

1、智谱AI的API KEY请自行申请

2、智谱AI的API KEY配置在.env文件中

3、Java和vue路径配置在config文件中

4、初次使用需要下载依赖pip install -r requirements.txt
将config文件中的REBUILD_INDEX_ON_STARTUP = False 改为True，用于创建索引，载入向量库

5、运行main.py即可启动服务

6、前端运行目录是frontend，需要先cd进入，然后执行 python -m http.server 3000命令启动服务

7、语义检索器使用的是：shibing624/text2vec-base-chinese，无法访问该地址所以设置 HuggingFace 镜像，
有魔法的可以使用魔法
设置 HuggingFace 镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

8、启动后端和前端服务之后访问http://localhost:3000/，即可根据自己的项目作为知识库，同时联网搜索答案
初次启动由于网络、配置、项目大小需要创建向量库所以需要久等一会，请耐心等候....


代码检索 - CodeIndexer 类可以索引和检索本地 Java/Vue 代码

检索格式化 - KnowledgeRetriever 能格式化检索结果为上下文

LLM调用 - LLMClient 调用智谱AI生成回答

Web服务 - FastAPI 提供 /query 接口

向量库/索引 - ChromaDB

会话管理 - 支持多轮对话历史

效果如下图：
<img width="1919" height="868" alt="image" src="https://github.com/user-attachments/assets/f9a85399-4c3d-402f-93f5-994377ab50b5" />
<img width="1919" height="857" alt="image" src="https://github.com/user-attachments/assets/56ad71ae-ebc0-4a42-a6e0-0d5971b66d91" />

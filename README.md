## 红楼梦数据可视化大屏

本项目采用前后端分离结构：

- 后端：Python Flask，读取 `txt_data/红楼梦.txt`，完成文本清洗、章节切分、人物频次、词云、情绪、关系图谱等统计，并统一返回 JSON。
- 前端：Vue3 + Vite，负责页面路由、国风布局、ECharts 图表、Three.js 三维书本和交互展示。

所有图表数据均由后端从原始 txt 文本自动解析生成，前端不维护静态假数据。

### 后端启动

```bash
pip install -r requirements.txt
python app.py
```

默认 API 地址：`http://127.0.0.1:5000/api`

Windows 虚拟环境启动示例：

```powershell
cd D:\honglou_data_screen
.\.venv\Scripts\python.exe app.py
```

浏览器直接打开 `http://127.0.0.1:5000` 只会看到后端 JSON 状态信息，这是正常的。

主要接口：

- `GET /api/basic-data`
- `GET /api/characters`
- `GET /api/characters/frequency`
- `GET /api/characters/graph`
- `GET /api/chapters/wordcloud`
- `GET /api/chapters/count`
- `GET /api/chapters/emotion`

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

默认页面地址：`http://127.0.0.1:5173`

如果当前电脑没有全局 npm，可以使用项目内已准备好的 npm：

```powershell
cd D:\honglou_data_screen\frontend
$env:PATH="D:\honglou_data_screen\.tools\npm\bin;C:\Users\武妞妞\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;$env:PATH"
node D:\honglou_data_screen\.tools\npm\bin\npm-cli.js run dev
```

前后端需要同时运行：后端终端保持 `5000`，前端终端保持 `5173`，最终打开 `http://127.0.0.1:5173` 查看页面。

### 页面结构

- 首页：`/`
- 中心数据大屏：`/screen`
- 章节词云详情：`/detail/wordcloud`
- 情绪走势详情：`/detail/emotion`
- 人物关联详情：`/detail/relation`
- 家族关联详情：`/detail/social`
- 字数散点详情：`/detail/scatter`

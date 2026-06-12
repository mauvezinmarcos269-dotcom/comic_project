# 📊 美漫销量智能问数与高级分析平台

《高级 Python 程序设计》课程期末大作业

---

# 1. 项目简介

## 1.1 项目背景

美国漫画产业经过近百年的发展，形成了以 Marvel（漫威）和 DC（DC 漫画）为代表的庞大商业体系。不同系列作品、创作者和出版商之间的销量差异具有较高的研究价值。

本项目以 2010—2019 年美国漫画销量数据为基础，结合 ComicVine 和 Grand Comics Database（GCD）等公开数据源，对漫画销量、创作者、角色、出版商等信息进行自动富化，并利用统计分析与可视化技术进行探索性分析。

---

## 1.2 分析目标

主要研究以下问题：

* Marvel 与 DC 谁在近十年更具市场统治力；
* 哪些漫画系列累计销量最高；
* 哪些编剧和画师对销量贡献最大；
* 销量与价格、评分之间是否存在相关关系；
* 不同出版商的市场份额分布情况；
* 漫画产业整体销量变化趋势。

---

# 2. 数据来源

## 2.1 原始销量数据

来源：

Comichron

数据时间范围：

2010—2019 年

每年销量 Top100

共约 1000 条记录。

---

## 2.2 ComicVine API

用于补充：

* Writer
* Artist
* Main Character
* Franchise

官方网址：

https://comicvine.gamespot.com/api/

---

## 2.3 Grand Comics Database (GCD)

用于交叉验证创作者信息。

官方网址：

https://www.comics.org/

---

# 3. 数据字段说明

| 字段                 | 含义         |
| ------------------ | ---------- |
| Title              | 漫画标题       |
| Issue              | 期号         |
| Studio/Pub         | 出版商        |
| Release Year       | 发行年份       |
| Unit Sales         | 销量         |
| Price              | 定价         |
| Writer             | 编剧         |
| Artist             | 画师         |
| Awards             | 获奖情况       |
| Main_Character     | 主角         |
| Franchise          | 系列         |
| Universe           | 漫威/DC/独立宇宙 |
| Semantic_Tags      | 语义标签       |
| Comic_Type         | 连载类型       |
| Publication_Status | 完结状态       |

---

# 4. 技术栈

## 数据处理

* pandas
* numpy

## 网络请求

* requests

## 数据分析

* scikit-learn
* statsmodels

## 数据可视化

* plotly

## Web 应用

* Streamlit

## 工具库

* tqdm
* python-dotenv
* reportlab

---

# 5. 项目结构


COMIC_PROJECT
│ app.py
│ pipeline.py
│ data_cleaner.py
│ README.md
│ requirements.txt
│
├─core
│ ├─agent
│ ├─collectors
│ ├─features
│ ├─ui
│ ├─utils
│ └─visualization
│
├─data
├─outputs
└─assets


---

# 6. 数据处理流程

```text
原始销量数据
        ↓
数据清洗
        ↓
ComicVine 富化
        ↓
GCD 补偿验证
        ↓
语义标签生成
        ↓
特征工程
        ↓
统计分析
        ↓
可视化展示
        ↓
AI 智能问答
```

---

# 7. 数据清洗

项目进行了以下预处理：

### 缺失值处理

使用：

```python
fillna()
```

填补缺失年份、销量等字段。

### 数据类型转换

利用：

```python
pd.to_numeric()
```

统一数值格式。

### 标题规范化

生成：

```python
Norm_Title
```

去除：

* #编号
* Vol.信息

便于后续聚合统计。

### 富化字段统一

将：

* Unknown
* None
* NaN

统一转换为：

```text
Not Available
```

---

# 8. 探索性分析

项目实现了：

### （1）时间序列分析

研究行业总销量变化趋势。

图表：

折线图

---

### （2）Marvel 与 DC 对比分析

研究两大出版社长期竞争关系。

图表：

双折线图

---

### （3）出版商市场份额分析

图表：

饼图

---

### （4）创作者销量排行

统计销量最高的编剧与画师。

图表：

水平柱状图

---

### （5）特征相关性分析

研究：

* 销量
* 价格
* 评分
* 页数

之间的关系。

图表：

热力图

---

### （6）PCA 聚类分析

采用：

* StandardScaler
* KMeans
* PCA

对漫画进行聚类。

图表：

散点图

---

### （7）线性回归分析

采用 OLS 模型研究价格与销量关系。

---

### （8）标题词频分析

统计高频关键词。

---

# 9. 主要结论

通过分析得到以下结果：

### ① Marvel 与 DC 长期占据市场主导地位。

### ② Star Wars、Detective Comics、Amazing Spider-Man 等系列具有较高累计销量。

### ③ Todd McFarlane、Scott Snyder 等创作者对销量贡献显著。

### ④ 销量与价格之间相关性较弱。

### ⑤ 出版商市场呈现双寡头格局。

---

# 10. 可视化结果

项目包含多种图表：

1. 折线图
2. 饼图
3. 热力图
4. 散点图
5. 柱状图

所有图表均包含：

* 标题
* 坐标轴标签
* 图例说明

满足课程要求。

---

# 11. 运行方法

## 安装依赖

```bash
pip install -r requirements.txt
```

---

## 配置环境变量

复制：

```text
.env.example
```

生成：

```text
.env
```

配置：

```text
COMICVINE_API_KEY=
GCD_EMAIL=
GCD_PASSWORD=
```

---

## 执行数据富化

```bash
python pipeline.py
```

生成：

```text
outputs/comic_sales_complete.xlsx
```

---

## 启动系统

```bash
streamlit run app.py
```

---

# 12. 总结与反思

本项目综合运用了《高级 Python 程序设计》课程所学习的：

* 函数封装；
* 面向对象；
* 文件操作；
* 异常处理；
* 第三方库使用；
* 数据分析；
* 数据可视化；

并通过模块化设计构建了完整的数据分析系统。

在开发过程中，主要难点包括：

* 多源数据融合；
* API 请求稳定性；
* 缺失值处理；
* 数据标准化；
* 可视化交互设计。

通过缓存机制、自动重试机制和特征工程方法，提高了系统稳定性与分析质量。

---

# 13. AI 使用声明

本项目开发过程中合理使用了 ChatGPT、Gemini 等生成式人工智能工具。

代码级别标注如下：

### app.py

AI-assisted：

使用 Gemini 生成 Streamlit 页面基础框架，并手动调整页面布局。

### charts.py

AI-assisted：

使用 ChatGPT 辅助生成 Plotly 图表初版，并修改配色方案与交互细节。

### comicvine_collector.py

AI-assisted：

使用 Gemini 辅助完成 API 请求逻辑，并手动增加缓存、异常处理和降级机制。

### dashboard.py

AI-assisted：

使用 ChatGPT 生成多标签页布局，并根据需求重新设计展示结构。

### pipeline.py

AI-assisted：

使用 Gemini 辅助生成并发任务框架，手动修改数据富化逻辑。

最终提交的所有代码、分析结果和文档均经过本人理解、验证和修改，可以独立解释项目实现过程，并能够现场复现。

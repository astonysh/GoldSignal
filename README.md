# 黄金宏观信号系统

每日自动监测三个宏观条件，判断当前宏观环境是否适合持有黄金。

> 免责声明：本工具仅提供宏观环境数据分析，不构成任何投资建议。

## 这个项目是什么

基于以下三个宏观条件对当前黄金持有环境进行评分：

- 条件一：实际利率（10年期TIPS收益率）— 最核心指标
- 条件二：系统性信用压力（高收益债利差、美联储资产负债表）
- 条件三：央行结构性购金（结构性支撑信号）

每个条件评分 0-100，综合判断输出四种信号：
- HOLD（持有）
- STRUCTURAL_SUPPORT（结构性支撑）
- WATCH（观望）
- AVOID（回避）

## 数据来源

所有数据来自 FRED（美联储圣路易斯分部），免费公开数据。

| 指标 | Series ID | 说明 |
|------|-----------|------|
| 10年期TIPS实际收益率 | DFII10 | 条件一核心数据 |
| 高收益债利差 | BAMLH0A0HYM2 | 条件二核心数据 |
| 美联储资产负债表 | WALCL | 条件二辅助数据 |
| 美元指数 | DTWEXBGS | 条件三调整参数 |

## 如何自己部署

第一步：Fork 这个仓库
点击右上角 Fork 按钮，复制到你自己的 GitHub 账号下。

第二步：申请 FRED API Key（免费）
1. 注册账号：https://fredaccount.stlouisfed.org/login/secure/
2. 登录后进入 My Account → API Keys → Request API Key
3. 申请后立即获得 API Key

第三步：添加 GitHub Secret
1. 进入你 Fork 后的仓库
2. 点击 Settings → Secrets and variables → Actions
3. 点击 New repository secret
4. Name 填写：FRED_API_KEY
5. Secret 填写：你申请到的 FRED API Key
6. 点击 Add secret

第四步：手动触发一次测试
1. 点击仓库页面的 Actions 标签
2. 左侧找到「每日黄金信号更新」
3. 点击 Run workflow
4. 等待约 1-2 分钟，绿色对勾表示成功

之后每天 UTC 01:00 自动运行，无需任何手动操作。

## 本地运行

pip install requests
export FRED_API_KEY="你的API Key"
python3 scripts/fetch_and_score.py

## 项目结构

gold-signal/
├── scripts/
│   └── fetch_and_score.py
├── .github/
│   └── workflows/
│       └── daily_update.yml
├── result.json
└── README.md

## License

MIT License

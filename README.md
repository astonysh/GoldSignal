# Gold Macro Signal System

[English](#gold-macro-signal-system) | [Türkçe](#altin-makro-sinyal-sistemi) | [中文](#黄金宏观信号系统)

🌐 **Live Demo:** [https://gsignal.pages.dev](https://gsignal.pages.dev)

> **Disclaimer:** This tool provides macroeconomic environment analysis only.
> It does not constitute investment advice of any kind.

## What is this?

A daily automated system that monitors three macroeconomic conditions
to determine whether the current environment is suitable for holding gold.

Scoring is based on a **Three-layer Regime Architecture**:

- **Layer 1: Macro Backdrop** (Macro Regime: Stagflation, Overheating, etc.)
- **Layer 2: Core Conditions** (Real Rates, Credit Stress, Structural Support)
- **Layer 3: Real-time Correction** (Volatility/Break Detection using GVZ)

Output signals are now **Regime-Adjusted**:
- HOLD — High confidence holding environment
- STRUCTURAL_SUPPORT — Headwinds offset by Central Bank demand
- WATCH — Mixed signals or Regime transition
- AVOID — Hostile macro environment

## Data Sources

All data from FRED (Federal Reserve Bank of St. Louis),
free and publicly available.

| Indicator | Series ID | Description |
|-----------|-----------|-------------|
| 10-Year TIPS Real Yield | DFII10 | Core valuation anchor |
| High-Yield Credit Spread | BAMLH0A0HYM2 | Systemic stress monitor |
| Dollar Index | DTWEXBGS | Reserve currency strength |
| Yield Curve (10Y-2Y) | T10Y2Y | Layer 1: Macro Regime |
| Breakeven Inflation | T10BIE | Layer 1: Inflation expectations |
| Gold Volatility Index | GVZ | Layer 3: Rule break detection |

## How to Deploy Your Own

Step 1: Fork this repository.
Click the Fork button at the top right.

Step 2: Get a free FRED API Key.
Register at: https://fredaccount.stlouisfed.org/login/secure/
Go to My Account → API Keys → Request API Key.

Step 3: Add GitHub Secret.
Go to your forked repository.
Click Settings → Secrets and variables → Actions.
Click New repository secret.
Name: FRED_API_KEY
Secret: your FRED API Key.
Click Add secret.

Step 4: Run manually to test.
Click the Actions tab in your repository.
Find "Daily Gold Signal Update" on the left.
Click Run workflow.
Wait 1-2 minutes. A green checkmark means success.

After setup, the script runs automatically every day at UTC 01:00.

## Local Run

pip install requests
export FRED_API_KEY="your_api_key_here"
python3 scripts/fetch_and_score.py

## Project Structure

GoldSignal/
├── scripts/
│   └── fetch_and_score.py
├── .github/
│   └── workflows/
│       └── daily_update.yml
├── result.json
└── README.md

## License

Apache License 2.0 — free to use, modify, and distribute.

---

# Altin Makro Sinyal Sistemi

🌐 **Canlı Demo:** [https://gsignal.pages.dev](https://gsignal.pages.dev)

> Sorumluluk Reddi: Bu arac yalnizca makroekonomik ortam analizi saglar.
> Herhangi bir yatirim tavsiyesi niteligini tasimaz.

## Bu Nedir?

Altin tutmanin mevcut makroekonomik ortamda uygun olup olmadigini
belirlemek icin uc makroekonomik kosulu her gun otomatik olarak izleyen bir sistem.

Puanlama **Üç Katmanlı Rejim Mimarisine** dayanmaktadır:

- **Katman 1: Makro Arka Plan** (Stagflasyon, Aşırı Isınma, vb.)
- **Katman 2: Temel Koşullar** (Reel Faizler, Kredi Baskısı, Yapısal Destek)
- **Katman 3: Gerçek Zamanlı Düzeltme** (GVZ kullanarak volatilite tespiti)

Sinyaller **Rejim Ayarlıdır**:
- HOLD (Tut)
- STRUCTURAL_SUPPORT (Yapısal Destek)
- WATCH (İzle)
- AVOID (Kaçın)

## Veri Kaynaklari

Tum veriler FRED (St. Louis Federal Rezerv Bankasi) kaynagindan alinmaktadir.

| Gosterge | Seri ID | Aciklama |
|----------|---------|----------|
| 10 Yillik TIPS Reel Getirisi | DFII10 | Kosul 1 temel verisi |
| Yuksek Getirili Kredi Spreadi | BAMLH0A0HYM2 | Kosul 2 temel verisi |
| Fed Bilancosi | WALCL | Kosul 2 yardimci verisi |
| Dolar Endeksi | DTWEXBGS | Kosul 3 duzeltme parametresi |

## Nasil Kurulur

Adim 1: Bu depoyu Fork layin.

Adim 2: Ucretsiz FRED API Anahtari alin.
https://fredaccount.stlouisfed.org/login/secure/ adresinden kayit olun.

Adim 3: GitHub Secret ekleyin.
Settings → Secrets and variables → Actions → New repository secret
Name: FRED_API_KEY
Secret: API anahtariniz

Adim 4: Actions sekmesinden manuel olarak calistirin ve test edin.

## Lisans

Apache Lisansı 2.0 — ozgurce kullanin, degistirin ve dagatin.

---

# 黄金宏观信号系统

🌐 **在线演示：** [https://gsignal.pages.dev](https://gsignal.pages.dev)

> 免责声明：本工具仅提供宏观环境数据分析，不构成任何投资建议。

## 这个项目是什么

每日自动监测三个宏观条件，判断当前宏观环境是否适合持有黄金。

评分基于**三层市场状态（Regime）架构**：

- **第一层：宏观底色**（宏观 Regime：滞胀、过热、复苏等）
- **第二层：核心条件**（实际利率、信用压力、结构性支撑）
- **第三层：实时修正**（利用 GVZ 进行波动率/变点检测）

综合信号现已经过 **Regime 修正**：
- HOLD（持有）— 高置信度持有环境
- STRUCTURAL_SUPPORT（结构性支撑）— 逆风被央行需求抵消
- WATCH（观望）— 信号混合或状态转换期
- AVOID（回避）— 恶劣的宏观环境

## 数据来源

全部来自 FRED（美联储圣路易斯分部），免费公开数据。

| 指标 | Series ID | 说明 |
|------|-----------|------|
| 10年期TIPS实际收益率 | DFII10 | 条件一核心数据 |
| 高收益债利差 | BAMLH0A0HYM2 | 条件二核心数据 |
| 美联储资产负债表 | WALCL | 条件二辅助数据 |
| 美元指数 | DTWEXBGS | 条件三调整参数 |

## 如何部署

第一步：Fork 这个仓库，点击右上角 Fork 按钮。

第二步：申请免费 FRED API Key。
注册地址：https://fredaccount.stlouisfed.org/login/secure/
登录后进入 My Account → API Keys → Request API Key。

第三步：添加 GitHub Secret。
进入你 Fork 后的仓库。
点击 Settings → Secrets and variables → Actions。
点击 New repository secret。
Name 填写：FRED_API_KEY
Secret 填写：你申请到的 FRED API Key。
点击 Add secret。

第四步：手动触发一次测试。
点击仓库页面的 Actions 标签。
左侧找到「每日黄金信号更新」。
点击 Run workflow。
等待约 1-2 分钟，绿色对勾表示成功。

之后每天 UTC 01:00 自动运行，无需任何手动操作。

## 本地运行

pip install requests
export FRED_API_KEY="你的API Key"
python3 scripts/fetch_and_score.py

## 许可证

Apache License 2.0 — 自由使用、修改和分发。

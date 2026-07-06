# 单股详情面板 + 框架结构调整 — 设计

日期：2026-07-06
状态：待用户确认

## 背景

现有 `HomeView` 已是「顶部导航 + 左自选 + 右主区」结构，右主区 `MarketView`
在单股态只显示 K 线图（外加一行 `symbol · N 根` 状态）。本次目标是把右主区做成
真正的「个股详情页」：报价摘要 + 基本面 + K 线，并微调导航栏。

## 已定决策

- **详情内容**：行情摘要 + 基本面。
- **对比功能**：保留，与详情共存 —— 右侧默认单股详情；左侧勾选 ≥2 只时切为归一化对比图。
- **市值字段**：接 AKShare 备源取总市值/流通市值。
- **右侧布局**（默认，待确认）：顶部信息条 + K 线全宽。
- **导航栏**（默认，待确认）：去掉「股票复盘」标题，搜索框占最左；右侧保留用户/退出。

## 数据来源盘点

| 字段 | 来源 | 是否需新代码 |
|---|---|---|
| 名称 / 市场 / 类型 / 上市日期 | DB `Instrument`（已存） | 否，直接读 |
| 现价 / 涨跌幅 / 今开·最高·最低·昨收 / 量·额 / 振幅 / 52周高低 | 前端从已取的 K 线 bars 派生（默认近 2 年，足够 52 周） | 前端派生 |
| PE(TTM) / PB(MRQ) | Baostock 日线字段 `peTTM`/`pbMRQ`（取最新交易日） | 后端新增 |
| 所属行业 | Baostock `query_stock_industry` | 后端新增 |
| 总市值 / 流通市值 | AKShare 备源（sina 系优先，带退避重试） | 后端新增 |

## 后端设计

### 新接口 `GET /api/instrument/{symbol}`

返回个股静态/低频信息（不含逐日行情，行情由前端从 `/api/kline` 派生）：

```
InstrumentDetailOut {
  symbol, name, market, type: str
  ipo_date: date | null
  industry: str | null
  pe_ttm: float | null
  pb_mrq: float | null
  total_mv: float | null   # 总市值(元)
  circ_mv: float | null    # 流通市值(元)
}
```

- 未知标的 → 404（复用现有 `UnknownSymbol` 语义）。
- 基本面字段任一取不到时返回 `null`，不使整个请求失败（前端显示「—」）。

### Provider 扩展

`DataProvider` 抽象新增一个方法（默认实现抛 `NotImplementedError`，只有实现的源提供）：

```
def get_instrument_detail(self, symbol: str) -> InstrumentDetail | None
```

- **BaostockProvider**：`query_stock_industry` 取行业；`query_history_k_data_plus`
  以 `peTTM,pbMRQ` 字段取最新交易日的 PE/PB。市值返回 None（交给备源）。
- **AkshareProvider**：取总市值/流通市值（sina 系端点优先，带退避与端点回退，
  遵循 [[data-source-findings]] 的坑 2）。行业/PE/PB 可留空。

### 服务层 `market_data.get_instrument_detail(...)`

- 从 DB 读取 `name/market/type/ipo_date`（`repo`）。
- 逐源调用 `get_instrument_detail` 并按字段**合并**（主源 Baostock 优先，缺失字段用备源补），
  与现有「主源抖动自动降级」风格一致。
- 任一源异常不致命，只记日志、该源字段留空。

## 前端设计

### 1. 导航栏（`HomeView.vue` topbar）

- 去掉 `<h1>股票复盘</h1>`；`<SearchBox />` 放最左。
- 右侧 `user`（email + 退出）不变。

### 2. 右主区（`MarketView.vue`）单股态

在现有单股分支的 `ChartToolbar` 之上插入详情信息条。空态/对比态不变。

- **新组件 `StockDetail.vue`**：接收 `symbol` 与已取的 `bars`，展示
  - 头部：名称 · 代码 · 市场
  - 报价：现价、涨跌幅（涨红跌绿，用现有 token）、今开/最高/最低/昨收、量/额、振幅、52周高低 —— 全部由 `bars` 派生（末根 vs 前一根算涨跌）
  - 基本面：PE、PB、行业、总市值、流通市值、上市日期 —— 来自 `useInstrument`
- **新 composable `useInstrument(symbolRef)`**：调 `/api/instrument/{symbol}`，随 symbol 变化重取。
- **新 api `api/instrument.ts`**：`fetchInstrument(symbol)`。
- **报价派生小工具**：从 `ApiBar[]` 算 现价/涨跌幅/振幅/52周高低 等，纯函数、可单测。

### 数据流

```
SearchBox.chart(symbol) ──▶ useSelection.view(symbol) ──▶ symbols=[symbol]
                                                              │
MarketView: primary=symbols[0]                                │
   ├─ useKline(primary,...) ─▶ bars ─▶ StockDetail 报价派生 + ChartView
   └─ useInstrument(primary) ─▶ 基本面 ─▶ StockDetail 基本面区
```

对比态（symbols.length ≥ 2）走原 `CompareChart`，不受影响。

## 组件边界

- `StockDetail.vue`：纯展示，输入 `symbol` + `bars` + `detail`，无副作用（取数在 `MarketView` 编排）。
- `useInstrument`：只管取详情，返回 `{ detail, loading, error }`。
- 报价派生：独立纯函数模块，输入 `bars` 输出摘要对象，可单测。

## 测试策略

- 后端：`get_instrument_detail` 服务层测试——主源字段齐全、主源缺市值备源补、
  未知标的 404、某源异常降级不致命。
- 前端：报价派生纯函数单测（正常/停牌末根/不足 52 周数据等边界）。

## 不做（YAGNI）

- 不改 K 线/对比现有逻辑与接口。
- 不新增财务报表、资金流、龙虎榜等（本期只 PE/PB/行业/市值/上市日）。
- 市值取不到时不阻塞，显示「—」。

## 待确认项

1. 右侧布局是否用「顶部信息条 + K 线全宽」（默认）。
2. 导航栏是否去掉标题（默认）。

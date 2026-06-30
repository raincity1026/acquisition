# UI 设计规范

> 全站 UI 的唯一标准。**唯一样式来源 = `frontend/src/styles/tokens.css`（设计令牌）**。
> 可视化参考页：开发期访问 `/design`。组件库：**PrimeVue 4**（主题在 `src/theme/preset.ts` 与令牌对齐）。
> 新写 UI 一律引用令牌变量，禁止散落硬编码颜色/间距/圆角。

---

## 1. 色彩

### 主色（品牌 + 主操作）
专业蓝 `--c-primary-50 … 900`，主色 = `--c-primary-600`（#2563eb）。用于：主按钮、链接、聚焦态、选中态。**红绿不作品牌色**（留给涨跌）。

### 中性 / 表面
- 页面底 `--c-bg`；卡片/弹层 `--c-surface-0`；区块/表头 `--c-surface-50`。
- 边框 `--c-border`（默认）/ `--c-border-strong`（输入）。
- 文字 `--c-text`（主）/ `--c-text-secondary`（次）/ `--c-text-tertiary`（辅助·占位）。

### 涨跌语义（A股：红涨绿跌）—— **仅用于行情/价格**
`--c-up`（涨·红）/ `--c-down`（跌·绿）/ `--c-flat`（平·灰）。每个配浅底 `--c-up-bg`/`--c-down-bg`。

### 功能反馈（表单/提示，非涨跌）
`--c-info`（=主色）/ `--c-success` / `--c-warning` / `--c-danger`（仅破坏性操作）。
> ⚠️ 红绿冲突原则：行情区只用涨红/跌绿；表单"成功"别在价格旁用绿色，"危险"红别与涨红同屏，避免误读。

## 2. 字体排印
- 字体栈 `--font-sans`（含 PingFang/雅黑）。
- 字号：`--fs-2xl 24`（页面主标题）/ `xl 20` / `lg 18`（区块标题）/ `md 16` / `base 14`（正文）/ `sm 13`（密集/表格）/ `caption 12`（角标）。
- 字重：`--fw-regular 400` / `medium 500`（标签·强调）/ `semibold 600`（标题·重要数字）。
- **数字一律 `tabular-nums` 等宽**（`.tnum` 工具类 / 表格默认），保证列对齐。

## 3. 间距（4px 基准）
`--space-1 4 … space-2 8 / 3 12 / 4 16 / 5 20 / 6 24 / 8 32 / 10 40`。组件内边距、间隔都从这取，别用任意值。

## 4. 圆角
`--radius-sm 4` / `--radius-md 6`（默认控件）/ `--radius-lg 8`（卡片·弹层）/ `--radius-pill`（标签·圆点）。

## 5. 阴影 / 层级
`--shadow-sm`（卡片）/ `--shadow-md`（下拉·弹层）/ `--shadow-lg`（对话框）。
z-index：`--z-sticky 100` / `--z-dropdown 1000` / `--z-modal 2000` / `--z-toast 3000`。

## 6. 用法指南（什么地方用什么）
| 场景 | 用什么 |
|---|---|
| 主操作（登录/查询/确认） | 实心主色 `Button` |
| 次操作（取消/返回） | `Button outlined` 或 `text` |
| 破坏性（删除分组） | `Button severity="danger"` + 二次确认 `Dialog` |
| 行情数字 | `.tnum` 等宽 + 涨红跌绿 + ± 前缀 |
| 区块/卡片 | `surface-0` 底 + `border` + `radius-lg` + `shadow-sm` |
| 区块标题/表头 | `surface-50` 底 + `text-secondary` |
| 弹层/下拉/菜单 | `shadow-md` + `radius-md` + `z-dropdown` |
| 对话框/输入弹窗 | PrimeVue `Dialog`（替代 `window.prompt/confirm`） |
| 数据表格 | PrimeVue `DataTable`（冻结列/虚拟滚动/排序）+ 涨跌染色 + 等宽数字 |

## 7. 迁移
现有手搓样式的组件（登录、自选侧栏、工具条、搜索、对比控件）按本规范逐步换成 PrimeVue + 令牌。新功能直接遵循，不再新增硬编码样式。

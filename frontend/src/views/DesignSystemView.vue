<script setup lang="ts">
import Button from 'primevue/button'
import Card from 'primevue/card'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { ref } from 'vue'

const primaryScale = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900]
const neutrals = [
  { name: 'surface-0 卡片底', v: '--c-surface-0' },
  { name: 'surface-50 区块底', v: '--c-surface-50' },
  { name: 'surface-100', v: '--c-surface-100' },
  { name: 'border 默认边框', v: '--c-border' },
  { name: 'border-strong 输入边框', v: '--c-border-strong' },
  { name: 'text 主文字', v: '--c-text' },
  { name: 'text-secondary 次要', v: '--c-text-secondary' },
  { name: 'text-tertiary 辅助', v: '--c-text-tertiary' },
]
const priceColors = [
  { name: '涨 up', v: '--c-up', sample: '+2.34%' },
  { name: '跌 down', v: '--c-down', sample: '-1.25%' },
  { name: '平 flat', v: '--c-flat', sample: '0.00%' },
]
const functional = [
  { name: 'info 信息/主色', v: '--c-info' },
  { name: 'success 成功', v: '--c-success' },
  { name: 'warning 警告', v: '--c-warning' },
  { name: 'danger 危险/删除', v: '--c-danger' },
]
const typeScale = [
  { token: '--fs-2xl', px: 24, w: 600, label: '页面主标题' },
  { token: '--fs-xl', px: 20, w: 600, label: '页面副标题' },
  { token: '--fs-lg', px: 18, w: 600, label: '区块标题' },
  { token: '--fs-md', px: 16, w: 500, label: '小标题' },
  { token: '--fs-base', px: 14, w: 400, label: '默认正文' },
  { token: '--fs-sm', px: 13, w: 400, label: '密集正文/表格' },
  { token: '--fs-caption', px: 12, w: 400, label: '角标/计数' },
]
const spacing = [
  ['--space-1', 4],
  ['--space-2', 8],
  ['--space-3', 12],
  ['--space-4', 16],
  ['--space-5', 20],
  ['--space-6', 24],
  ['--space-8', 32],
  ['--space-10', 40],
] as const
const radii = [
  ['--radius-sm', 4],
  ['--radius-md', 6],
  ['--radius-lg', 8],
] as const
const shadows = ['--shadow-sm', '--shadow-md', '--shadow-lg']

const usage = [
  ['主操作（登录/查询/确认）', '实心主色按钮 Button'],
  ['次操作（取消/返回）', '描边或文字按钮 Button.outlined/.text'],
  ['破坏性操作（删除分组）', 'danger 按钮 + 二次确认弹窗'],
  ['行情数字', 'tabular-nums 等宽 + 涨红跌绿 + ± 前缀'],
  ['区块/卡片', 'surface-0 底 + border + radius-lg + shadow-sm'],
  ['区块标题/表头', 'surface-50 底 + text-secondary'],
  ['弹层/下拉/菜单', 'shadow-md + radius-md + z-dropdown'],
  ['对话框', 'PrimeVue Dialog（替代 window.prompt/confirm）'],
]

// 数据表格示例：体现冻结列 + 涨跌染色 + 等宽数字 + 排序
const stocks = ref([
  { name: '贵州茅台', code: '600519.SH', price: 1240.0, pct: -1.25, chg: -15.7, vol: 2.53, amt: 31.4 },
  { name: '五粮液', code: '000858.SZ', price: 77.49, pct: -1.07, chg: -0.84, vol: 18.2, amt: 14.2 },
  { name: '宁德时代', code: '300750.SZ', price: 399.0, pct: 2.34, chg: 9.12, vol: 9.8, amt: 38.9 },
  { name: '比亚迪', code: '002594.SZ', price: 245.6, pct: 0.0, chg: 0.0, vol: 6.1, amt: 14.9 },
  { name: '中芯国际', code: '688981.SH', price: 88.2, pct: 4.01, chg: 3.4, vol: 22.5, amt: 19.6 },
])
const selectVal = ref('qfq')
const selectOpts = [
  { label: '前复权', value: 'qfq' },
  { label: '后复权', value: 'hfq' },
  { label: '不复权', value: 'none' },
]
const inputVal = ref('600519.SH')
const checked = ref(true)

const cls = (v: number) => (v > 0 ? 'text-up' : v < 0 ? 'text-down' : 'text-flat')
const pct = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(2)}%`
const num = (v: number, d = 2) => `${v > 0 ? '+' : ''}${v.toFixed(d)}`
</script>

<template>
  <div class="ds">
    <header class="ds-head">
      <h1>设计规范 · acquisition</h1>
      <p>全站 UI 的唯一标准。所有颜色/间距/圆角/字号都来自设计令牌（<code>styles/tokens.css</code>）。</p>
    </header>

    <!-- 色彩 -->
    <section>
      <h2>色彩</h2>
      <h3>主色（专业蓝，品牌与主操作）</h3>
      <div class="swatches">
        <div v-for="s in primaryScale" :key="s" class="swatch">
          <div class="chip" :style="{ background: `var(--c-primary-${s})` }"></div>
          <span class="lbl">{{ s }}</span>
        </div>
      </div>

      <h3>中性 / 表面（背景·边框·文字）</h3>
      <div class="swatches">
        <div v-for="n in neutrals" :key="n.v" class="swatch wide">
          <div class="chip bordered" :style="{ background: `var(${n.v})` }"></div>
          <span class="lbl">{{ n.name }}</span>
        </div>
      </div>

      <h3>涨跌语义（A股：红涨绿跌 · 仅用于行情）</h3>
      <div class="swatches">
        <div v-for="p in priceColors" :key="p.v" class="swatch wide">
          <div class="chip" :style="{ background: `var(${p.v})` }"></div>
          <span class="lbl">{{ p.name }}</span>
          <span class="lbl tnum" :style="{ color: `var(${p.v})` }">{{ p.sample }}</span>
        </div>
      </div>

      <h3>功能反馈（表单/提示，非涨跌）</h3>
      <div class="swatches">
        <div v-for="f in functional" :key="f.v" class="swatch wide">
          <div class="chip" :style="{ background: `var(${f.v})` }"></div>
          <span class="lbl">{{ f.name }}</span>
        </div>
      </div>
      <p class="note">
        ⚠️ 注意：行情区只用「涨红/跌绿」；表单成功别在价格旁用绿色、危险红别与涨红同框，避免误读。
      </p>
    </section>

    <!-- 字体 -->
    <section>
      <h2>字体排印</h2>
      <div class="type-list">
        <div v-for="t in typeScale" :key="t.token" class="type-row">
          <div class="type-meta">
            <code>{{ t.token }}</code>
            <span>{{ t.px }}px · {{ t.w }} · {{ t.label }}</span>
          </div>
          <div :style="{ fontSize: t.px + 'px', fontWeight: t.w }">
            股票复盘 Acquisition <span class="tnum">1,240.00 -1.25%</span>
          </div>
        </div>
      </div>
      <p class="note">数字统一 <code>tabular-nums</code> 等宽，保证表格列对齐。</p>
    </section>

    <!-- 间距 / 圆角 / 阴影 -->
    <section class="cols">
      <div>
        <h2>间距（4px 基准）</h2>
        <div v-for="[name, v] in spacing" :key="name" class="space-row">
          <span class="space-bar" :style="{ width: v + 'px' }"></span>
          <code>{{ name }}</code><span>{{ v }}px</span>
        </div>
      </div>
      <div>
        <h2>圆角</h2>
        <div class="radius-row">
          <div v-for="[name, v] in radii" :key="name" class="radius-box">
            <div class="rb" :style="{ borderRadius: v + 'px' }"></div>
            <code>{{ name }}</code><span>{{ v }}px</span>
          </div>
        </div>
        <h2 style="margin-top: 20px">阴影 / 层级</h2>
        <div class="shadow-row">
          <div v-for="s in shadows" :key="s" class="shadow-box" :style="{ boxShadow: `var(${s})` }">
            <code>{{ s }}</code>
          </div>
        </div>
      </div>
    </section>

    <!-- 组件（PrimeVue 主题化）-->
    <section>
      <h2>组件（PrimeVue · 已套用本主题）</h2>
      <div class="comp-grid">
        <div class="comp">
          <h3>按钮</h3>
          <div class="row">
            <Button label="主操作" />
            <Button label="次操作" outlined />
            <Button label="文字" text />
            <Button label="删除" severity="danger" outlined />
          </div>
          <div class="row">
            <Button label="小号" size="small" />
            <Button label="默认" />
            <Button icon="pi pi-search" label="查询" size="small" />
          </div>
        </div>
        <div class="comp">
          <h3>表单</h3>
          <div class="row">
            <InputText v-model="inputVal" placeholder="代码" />
            <Select v-model="selectVal" :options="selectOpts" option-label="label" option-value="value" />
          </div>
          <div class="row">
            <Checkbox v-model="checked" binary input-id="ck" /><label for="ck">加入对比</label>
            <Tag value="科创板" /><Tag value="停牌" severity="warn" />
          </div>
        </div>
      </div>

      <h3 style="margin-top: 8px">数据表格（冻结列 + 涨跌染色 + 等宽数字 + 排序）</h3>
      <Card>
        <template #content>
          <DataTable :value="stocks" scrollable scroll-height="240px" size="small" removable-sort>
            <Column field="name" header="名称" frozen sortable style="min-width: 120px" />
            <Column field="code" header="代码" style="min-width: 110px" />
            <Column field="price" header="最新价" sortable style="min-width: 100px">
              <template #body="{ data }"><span class="tnum">{{ data.price.toFixed(2) }}</span></template>
            </Column>
            <Column field="pct" header="涨跌幅" sortable style="min-width: 100px">
              <template #body="{ data }">
                <span class="tnum" :class="cls(data.pct)">{{ pct(data.pct) }}</span>
              </template>
            </Column>
            <Column field="chg" header="涨跌额" style="min-width: 100px">
              <template #body="{ data }">
                <span class="tnum" :class="cls(data.chg)">{{ num(data.chg) }}</span>
              </template>
            </Column>
            <Column field="vol" header="成交量(万手)" style="min-width: 120px">
              <template #body="{ data }"><span class="tnum">{{ data.vol.toFixed(1) }}</span></template>
            </Column>
            <Column field="amt" header="成交额(亿)" style="min-width: 120px">
              <template #body="{ data }"><span class="tnum">{{ data.amt.toFixed(1) }}</span></template>
            </Column>
          </DataTable>
        </template>
      </Card>
    </section>

    <!-- 用法指南 -->
    <section>
      <h2>用法指南（什么地方用什么）</h2>
      <table class="usage">
        <thead>
          <tr><th>场景</th><th>用什么</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in usage" :key="u[0]">
            <td>{{ u[0] }}</td>
            <td>{{ u[1] }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.ds {
  max-width: 1040px;
  margin: 0 auto;
  padding: 24px 20px 64px;
}
.ds-head h1 {
  font-size: var(--fs-2xl);
  font-weight: var(--fw-semibold);
  margin: 0 0 4px;
}
.ds-head p {
  color: var(--c-text-secondary);
  margin: 0 0 8px;
}
section {
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid var(--c-border);
}
h2 {
  font-size: var(--fs-lg);
  font-weight: var(--fw-semibold);
  margin: 0 0 12px;
}
h3 {
  font-size: var(--fs-sm);
  font-weight: var(--fw-medium);
  color: var(--c-text-secondary);
  margin: 16px 0 8px;
}
code {
  font-family: ui-monospace, Menlo, Consolas, monospace;
  font-size: 12px;
  background: var(--c-surface-100);
  padding: 1px 5px;
  border-radius: var(--radius-sm);
}
.note {
  font-size: var(--fs-sm);
  color: var(--c-text-secondary);
  margin: 10px 0 0;
}
/* 色块 */
.swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.swatch {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 64px;
}
.swatch.wide {
  width: 150px;
}
.chip {
  height: 44px;
  border-radius: var(--radius-md);
}
.chip.bordered {
  border: 1px solid var(--c-border);
}
.lbl {
  font-size: var(--fs-caption);
  color: var(--c-text-secondary);
}
/* 字体 */
.type-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.type-row {
  display: flex;
  align-items: baseline;
  gap: 16px;
}
.type-meta {
  width: 230px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.type-meta span {
  font-size: var(--fs-caption);
  color: var(--c-text-tertiary);
}
/* 间距/圆角/阴影 */
.cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}
.space-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: var(--fs-sm);
  color: var(--c-text-secondary);
}
.space-bar {
  height: 12px;
  background: var(--c-primary-300);
  border-radius: var(--radius-sm);
}
.radius-row,
.shadow-row {
  display: flex;
  gap: 16px;
}
.radius-box,
.shadow-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-caption);
  color: var(--c-text-secondary);
}
.rb {
  width: 56px;
  height: 56px;
  background: var(--c-primary-100);
  border: 1px solid var(--c-primary-300);
}
.shadow-box {
  width: 96px;
  height: 64px;
  justify-content: center;
  background: var(--c-surface-0);
  border-radius: var(--radius-lg);
}
/* 组件 */
.comp-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 8px;
}
.comp .row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
/* 用法表 */
.usage {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-sm);
}
.usage th,
.usage td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--c-border);
}
.usage th {
  background: var(--c-surface-50);
  color: var(--c-text-secondary);
  font-weight: var(--fw-medium);
}
</style>

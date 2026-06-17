import { ref } from 'vue'

// 当前图表选中的标的（单股 1 只 / 对比 ≥2 只）。跨组件共享。
const symbols = ref<string[]>([])
const MAX = 8

export function useSelection() {
  function view(symbol: string): void {
    symbols.value = [symbol] // 单股看图
  }
  function inCompare(symbol: string): boolean {
    return symbols.value.includes(symbol)
  }
  function toggleCompare(symbol: string): void {
    if (symbols.value.includes(symbol)) {
      if (symbols.value.length > 1) symbols.value = symbols.value.filter((s) => s !== symbol)
    } else if (symbols.value.length < MAX) {
      symbols.value = [...symbols.value, symbol]
    }
  }

  return { symbols, view, inCompare, toggleCompare }
}

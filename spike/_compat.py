"""baostock 仍调用 pandas 已移除的 DataFrame.append；这里补一个兼容垫片。
任何用到 baostock 的脚本须在 import baostock 之前 `import _compat`。"""
import pandas as pd

if not hasattr(pd.DataFrame, "append"):
    def _append(self, other, ignore_index=False, verify_integrity=False, sort=False):
        if isinstance(other, dict):
            other = pd.DataFrame([other])
        return pd.concat([self, other], ignore_index=ignore_index)
    pd.DataFrame.append = _append

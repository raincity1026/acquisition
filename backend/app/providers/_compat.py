"""baostock 仍调用 pandas 已移除的 ``DataFrame.append``（pandas≥2.0 删除）。
导入本模块即打上兼容垫片；必须在 ``import baostock`` 之前导入。"""

import pandas as pd

if not hasattr(pd.DataFrame, "append"):

    def _append(self, other, ignore_index=False, verify_integrity=False, sort=False):  # type: ignore[no-untyped-def]
        if isinstance(other, dict):
            other = pd.DataFrame([other])
        return pd.concat([self, other], ignore_index=ignore_index)

    pd.DataFrame.append = _append

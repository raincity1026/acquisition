"""导入本包即先打 pandas 兼容垫片，确保任何 ``import baostock`` 之前 pandas 可用。"""

from . import _compat as _compat  # noqa: F401

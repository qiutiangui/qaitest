# pytest 全局 fixtures
import sys
from pathlib import Path

# 将 app 目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

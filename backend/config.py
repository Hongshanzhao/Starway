import os
from dotenv import load_dotenv

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SQLite 数据库文件存放路径（会自动创建）
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'instance', 'career.db')

# 文件上传临时目录
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MBa

# 加载 .env 文件中的变量
load_dotenv()

ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
ALIYUN_API_KEY = os.getenv('ALIYUN_API_KEY')

# 适用于调试/测试模式
# - auto：按实际配置调用，未配置时降级本地模板
# - real：强制调用阿里云（会消耗额度），不配置则返回空或降级
# - local：永远不调用外部，使用简易本地模板
LLM_MODE = os.getenv('LLM_MODE', 'auto').lower()
LLM_FORCE_REAL = os.getenv('LLM_FORCE_REAL', '0') == '1'
LLM_MAX_CALLS_PER_RUN = int(os.getenv('LLM_MAX_CALLS_PER_RUN', '1000'))

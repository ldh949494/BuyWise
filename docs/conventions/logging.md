# 日志

运行时代码必须通过 Provider 入口使用结构化日志。

## Python

```python
from app.core.providers import get_provider

logger = get_provider("logging").get_logger(__name__)
logger.info("Product search completed", extra={"category": category})
```

后端 JSON 日志会在请求进行中包含当前 request ID。使用 `X-Request-ID` 响应头将客户端可见错误与日志关联。

不要记录完整请求体、AI prompt、上传文件内容、凭据或用户隐私文本。密码、token、secret、API key、authorization header 等常见敏感字段会被后端 formatter 脱敏。

避免在 `extra` 中使用 Python `LogRecord` 保留名；使用领域名，例如用 `stored_filename` 代替 `filename`。

命令行脚本、测试和 app script 可以使用 `print()`；运行时应用模块不得使用。

## Kotlin

不要添加 `console.log`、`System.out.println` 或直接 `Log.d`。后续引入 Kotlin logging provider 后，应通过应用日志 provider 输出。

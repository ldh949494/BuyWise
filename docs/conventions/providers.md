# Provider 模式

横切能力必须只有一个入口。功能模块不得直接导入认证、遥测、日志或错误处理的具体实现。

## 后端 Provider 入口

使用 `app.core.providers`：

```python
from app.core.providers import get_provider

auth = get_provider("auth")
logger = get_provider("logging").get_logger(__name__)
telemetry = get_provider("telemetry")
errors = get_provider("errors")
```

也可以使用类型化 helper：

```python
from app.core.providers import get_logging_provider

logger = get_logging_provider().get_logger(__name__)
```

## 禁止模式

功能模块不得直接导入横切实现：

```python
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.logging import configure_logging
```

## 所有权

- `auth`：认证和当前 principal 访问。
- `telemetry`：指标、追踪和 instrumentation。
- `logging`：logger 创建和日志配置。
- `errors`：全局异常 handler 注册和错误映射。

## 验证

`scripts/validate_providers.py` 会扫描后端导入，并在 app 模块绕过 `app.core.providers` 时失败。兼容 wrapper 只能存在于已批准的 core utility 文件中。

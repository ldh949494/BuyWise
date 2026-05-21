# 熵债垃圾回收

熵债是逐步累积的偏移，包括过长函数、重复 helper、过期注释、临时错误处理和命名不一致。

## 验证

运行确定性的熵债验证：

```powershell
python .\scripts\validate_entropy.py
```

只有在有意接受现有债务时才刷新基线：

```powershell
python .\scripts\validate_entropy.py --refresh-baseline
```

## 垃圾回收报告

生成只读清理报告：

```powershell
python .\scripts\entropy_gc.py
```

GitHub Models 可用时可追加 AI 建议：

```powershell
python .\scripts\entropy_gc.py --with-ai
```

报告写入 `artifacts/entropy-gc/`，该目录被 Git 忽略。

## 操作规则

不要自动按 GC 报告重写代码。把报告视为一组小而可 review 的清理 PR 队列。

# models 目录说明

`src/isoxml/models/` 主要包含两类内容：

- 根据 ISOXML XSD 自动生成的 dataclass 模型
- 少量手写的辅助逻辑，例如 DDI 相关封装和版本注册

如果你只是第三方使用者，通常不需要直接修改这个目录。  
如果你是维护者，或者需要重新生成模型，这份文档会更有用。

## 目录结构

- `base/v3/`
  由 ISOXML TaskFile v3 XSD 生成的模型

- `base/v4/`
  由 ISOXML TaskFile v4 XSD 生成的模型

- `ddi.py`
  DDI 辅助逻辑，包括通过 ID 加载 DDI 定义等能力

- `version_registry.py`
  ISOXML 模型版本注册表，用于按版本号解析对应模型模块

## 这些模型怎么来的

本项目使用 [xsdata](https://github.com/tefra/xsdata) 根据官方 XSD 生成 dataclass。

对应的 XSD 文件位于：

- [src/isoxml/reference/xsd](../reference/xsd)

## 重新生成模型

如果你更新了 XSD，或需要重新生成 v3 / v4 模型，可以使用：

```bash
.venv/bin/xsdata generate src/isoxml/reference/xsd/ISO11783_TaskFile_V3-3.xsd \
  --package isoxml.models.base.v3 \
  --structure-style clusters \
  --no-relative-imports

.venv/bin/xsdata generate src/isoxml/reference/xsd/ISO11783_TaskFile_V4-3.xsd \
  --package isoxml.models.base.v4 \
  --structure-style clusters \
  --no-relative-imports
```

## 维护建议

### 1. 不要随意手改生成文件

`base/v3/` 和 `base/v4/` 下的大部分文件都是生成产物。  
如果你直接修改这些文件，后续重新生成时会被覆盖。

更稳的做法是：

- 把通用逻辑放到生成文件之外
- 只在确实必要时，对生成产物做最小范围补丁
- 在 README 或提交信息中说明为什么需要手动修改

### 2. 版本支持通过注册表管理

模型版本不是靠硬编码分支判断，而是通过：

- [version_registry.py](version_registry.py)

来注册和解析。

这意味着以后如果新增 `v5`，只需要：

- 生成对应模型包
- 在版本注册处补注册

而不需要到处改 `if xml_version == "3"` 这类逻辑。

## 与第三方使用者相关的点

大多数第三方使用者只需要知道：

- 读出来的 `task_data` 是基于这些模型构建的
- v3 和 v4 有各自独立的 Python 类型
- 你可以直接导入并手动构造对象，例如：

```python
import isoxml.models.base.v4 as iso

customer = iso.Customer(id="CTR0001", last_name="demo_customer")
```

如果你只是在项目外部“使用库”，通常无需直接研究模型生成过程。

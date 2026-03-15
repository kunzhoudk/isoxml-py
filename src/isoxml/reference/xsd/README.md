# XSD 参考文件说明

这个目录保存了随包一起分发的 ISOXML XSD 文件副本。

这些文件来源于官方 ISOBUS 网站发布的 supporting documents：

- <https://www.isobus.net/isobus/file/supportingDocuments>

项目把它们放在 `src/isoxml/reference/xsd/` 下，是为了让运行时和开发工具都能直接使用，而不依赖仓库根目录下额外的 `resources/` 目录。

## 这些 XSD 在哪里被用到

### 1. 运行时 XSD 校验

[xsd_validation.py](../../xsd_validation.py) 会从这里解析对应版本的 TaskFile XSD，然后调用 `xmlschema.validate(...)`。

这会被以下能力直接使用：

- `validate_xsd(...)`
- `isoxml-validate-taskdata`
- `isoxml-vector-to-taskdata`
- `isoxml-convert-taskdata`
- taskdata 版本转换流程中的输出校验

### 2. 模型生成参考

[src/isoxml/models/README.md](../../models/README.md) 中的 `xsdata generate` 命令会直接引用这里的 XSD 文件，重新生成 v3 / v4 模型。

## 最重要的文件

通常最常用的是这两个：

- `ISO11783_TaskFile_V3-3.xsd`
- `ISO11783_TaskFile_V4-3.xsd`

其余文件也保留在同一目录下，因为它们属于同一套官方 schema 集合，便于：

- 检查导出结果
- 重新生成模型
- 对照官方结构排查问题

## 对第三方使用者意味着什么

如果你只是库使用者，最重要的一点是：

- 项目可以在本地直接完成 XSD 校验
- 不需要你额外下载 XSD 文件

也就是说，安装完库后，就可以直接运行：

```bash
uv run isoxml-validate-taskdata path/to/TASKDATA
```

或者在 Python 中调用：

```python
from isoxml import validate_xsd

validate_xsd(task_data, xml_version="4")
```

## 更新这些 XSD 时应注意

如果你准备升级这里的 XSD 文件，建议按这个顺序做：

1. 替换 `reference/xsd/` 中的目标文件
2. 重新生成 `models/base/v3` 或 `models/base/v4`
3. 跑测试
4. 验证 CLI 和 XSD 校验流程是否仍正常

不要只替换 XSD 而不验证模型和校验逻辑，否则容易出现版本不一致。

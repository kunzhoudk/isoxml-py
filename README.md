# ISOXML-PY

`isoxml` 是一个用于读写、校验、生成和转换 ISOXML TaskData 的 Python 工具库，面向精准农业、FMIS、处方图生成和农机数据交换场景。

项目当前重点覆盖：

- ISOXML TaskData 的读取、写出与打包
- ISOXML v3 / v4 的模型与版本转换
- Shapely 几何与 ISOXML 几何互转
- 网格二进制文件的编码与解码
- 从矢量数据生成 ISOXML taskdata
- 基于 XSD 的结构校验

## 适合谁使用

如果你正在做这些事情，这个项目会比较合适：

- 从 FMIS 或 GIS 数据生成 ISOXML
- 读取终端导出的 `TASKDATA.XML` / ZIP 包
- 将 Shapefile、GeoJSON 等矢量应用图转换为可导入农机终端的 ISOXML
- 在 Python 中分析、改写、重打包 ISOXML 数据
- 需要验证输出是否符合 ISOXML XSD

## 安装

基础安装：

```bash
pip install isoxml
```

如果你需要 notebook、可视化或开发依赖：

```bash
pip install .[dev]
```

当前基础安装已包含以下常用能力所需依赖：

- `geopandas`
- `shapely`
- `numpy`
- `xmlschema`

## 推荐使用 uv

如果你是在本地检出这个仓库并准备运行示例、CLI、测试或 notebook，推荐使用 [uv](https://docs.astral.sh/uv/)。

原因很简单：

- 这个项目的示例和文档默认使用 `uv run ...`
- `uv` 能更方便地管理虚拟环境和依赖
- 不需要你手动激活 `.venv` 才能运行大多数命令

### 1. 安装 uv

如果你的环境里还没有 `uv`，可以先安装：

```bash
pip install uv
```

### 2. 安装项目依赖

只安装基础依赖：

```bash
uv sync
```

安装开发依赖：

```bash
uv sync --extra dev
```

### 3. 使用 uv 运行项目

运行 CLI：

```bash
uv run isoxml-vector-to-taskdata --help
uv run isoxml-convert-taskdata --help
```

运行 Python 脚本：

```bash
uv run python examples/application_maps/prepare_test_shp_application_map_geojson.py
```

运行测试：

```bash
uv run pytest
```

运行静态检查：

```bash
uv run ruff check
```

统一代码格式：

```bash
uv run ruff format
uv run ruff check --fix
```

如果你只是作为库使用者，把它安装到你自己的项目里，那么 `pip install isoxml` 也完全可以。

## 快速开始

### 1. 读取 ISOXML

```python
from pathlib import Path
from isoxml import read_from_zip, read_from_path, read_from_xml

# 读取 ZIP
task_data, refs = read_from_zip(Path("TASKDATA.zip"))

# 读取 TASKDATA 目录
task_data, refs = read_from_path(Path("TASKDATA"))

# 从 XML 字符串读取
task_data = read_from_xml(xml_string)
```

### 2. 写出 ISOXML

```python
from pathlib import Path

import isoxml.models.base.v4 as iso
from isoxml import write_to_dir, write_to_zip

customer = iso.Customer(id="CTR0001", last_name="demo_customer")
farm = iso.Farm(id="FRM0001", designator="demo_farm", customer_id_ref=customer.id)

task_data = iso.Iso11783TaskData(
    management_software_manufacturer="isoxml-py",
    management_software_version="0.1.0",
    data_transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS,
    customers=[customer],
    farms=[farm],
)

write_to_dir(Path("output/TASKDATA"), task_data)
write_to_zip(Path("output/TASKDATA.zip"), task_data)
```

### 3. 从矢量数据生成 taskdata

Shapefile 示例：

```bash
uv run isoxml-vector-to-taskdata \
  examples/input/small/shp/Rx.shp \
  --boundary-path examples/input/small/boundary/Boundary.shp \
  --xml-version 4 \
  --grid-type 2 \
  --value-field rate \
  --output-dir examples/output/rx_grid
```

GeoJSON 示例：

```bash
uv run isoxml-vector-to-taskdata \
  examples/input/test_shp_application_map_with_boundary.geojson \
  --xml-version 4 \
  --grid-type 1 \
  --value-field dose \
  --output-dir examples/output/geojson_grid
```

### 4. 转换已有 taskdata 的版本 / grid 类型

```bash
uv run isoxml-convert-taskdata \
  examples/expected/small_xml_v3_type_1_auto.zip \
  --target-xml-version 4 \
  --target-grid-type 2 \
  --output-dir examples/output/converted_v4_type_2
```

### 5. 校验输出是否符合 XSD

```bash
uv run isoxml-validate-taskdata examples/output/converted_v4_type_2
```

## 命令行工具

项目提供了一组稳定的 CLI，可直接通过 `uv run` 或安装后的命令调用。

```bash
uv run isoxml-vector-to-taskdata --help
uv run isoxml-convert-taskdata --help
uv run isoxml-prepare-application-map-geojson --help
uv run isoxml-inspect-vector --help
uv run isoxml-inspect-grid --help
uv run isoxml-inspect-grid-overlay --help
uv run isoxml-validate-taskdata --help
uv run isoxml-validate-grid-bin --help
uv run isoxml-generate-pycode --help
```

这些命令分别适合：

- `isoxml-vector-to-taskdata`：从 Shapefile / GeoJSON / GPKG 生成 taskdata
- `isoxml-convert-taskdata`：在 XML 版本和 grid 类型之间转换
- `isoxml-prepare-application-map-geojson`：把 polygon 矢量标准化为内嵌边界的 GeoJSON 应用图
- `isoxml-inspect-vector`：检查输入矢量字段、坐标系和数值列
- `isoxml-inspect-grid`：查看 GRDxxxxx.bin 数据内容
- `isoxml-inspect-grid-overlay`：检查 GRDxxxxx.bin  与地块边界的空间对齐
- `isoxml-validate-taskdata`：做 XSD 校验
- `isoxml-validate-grid-bin`：检查 GRDxxxxx.bin 二进制文件
- `isoxml-generate-pycode`：从现有 TaskData 生成 Python 构造代码，便于调试、复现和二次编辑

## Python API 重点能力

### 版本校验

```python
from isoxml import validate_xsd

xsd_path = validate_xsd(task_data, xml_version="4")
print(xsd_path)
```

### taskdata 版本转换

```python
from isoxml import convert_taskdata_versions

result = convert_taskdata_versions(
    task_data,
    refs,
    target_xml_version=4,
    target_grid_type=2,
    validate_output=True,
)
```

### 几何转换

```python
import shapely as shp
import isoxml.models.base.v4 as iso
from isoxml import ShapelyConverterV4

converter = ShapelyConverterV4()
polygon = shp.from_wkt("POLYGON ((15.14 48.12, 15.15 48.12, 15.15 48.13, 15.14 48.12))")
iso_polygon = converter.to_iso_polygon(polygon, iso.PolygonType.PartfieldBoundary)
```

### grid（GRDxxxxx.bin） 编解码

```python
from isoxml import decode, encode_type2
from isoxml.models import DDEntity

ddi = DDEntity.from_id(6)
grid_bytes = encode_type2(numpy_array, grid_element, ddi_list=[ddi])
decoded = decode(grid_bytes, grid_element, ddi_list=[ddi])
```

## 示例与样例数据

示例集中在 [examples/README.md](examples/README.md)：

- `examples/application_maps/`：应用图示例
- `examples/input/`：输入样例
- `examples/expected/`：固定输出样例
- `examples/output/`：本地运行产物
- `examples/grid_overlay_viewer.ipynb`：grid overlay notebook
- `examples/partfield_viewer.ipynb`：partfield notebook

如果你想快速上手，建议优先看：

- [run_shp_to_taskdata.sh](examples/bash_script/run_shp_to_taskdata.sh)
- [run_geojson_to_taskdata.sh](examples/bash_script/run_geojson_to_taskdata.sh)
- [run_check_grid_overlay.sh](examples/bash_script/run_check_grid_overlay.sh)

## 项目结构

```text
src/isoxml/
  cli/                      命令行入口
  io/                       读取、写出、外部文件处理
  geometry/                 几何转换
  grid/                     grid 编解码
  models/                   XSD 生成的模型与辅助逻辑
  pipeline/                 高层工作流
  reference/                打包进库内的参考数据与 XSD
  xsd_validation.py         XSD 校验入口
```

## 开发说明

运行测试：

```bash
uv run pytest
```

运行静态检查：

```bash
uv run ruff check
```

如果你要重新生成基于 XSD 的 dataclass 模型，请先阅读：

- [src/isoxml/models/README.md](src/isoxml/models/README.md)
- [src/isoxml/reference/xsd/README.md](src/isoxml/reference/xsd/README.md)

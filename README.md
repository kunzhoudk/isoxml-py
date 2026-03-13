# ISOXML library for python 

a python library that handles import and export of ISOXML TaskData files as specified in ISO11783 part 10.
inspired by [isoxml-js](https://github.com/dev4Agriculture/isoxml-js) and powered by [xsdata](https://github.com/tefra/xsdata) XML bindings.

The main features:
* supports v3 and v4
* read/write directly from zip, TASKDATA-dir or any string
* conversion between shapely and isoxml geometries
* conversion of numpy array to grid data binary files
* [generate code](https://github.com/Josephinum-Research/isoxml-py/blob/main/examples/pycode_generator.py) from existing TASKDATA.XML (via xsdata)

## Installation
```
pip install isoxml
```

## Usage Examples

### import

```python
from isoxml.io import load_taskdata_from_zip

task_data, bin_data = load_taskdata_from_zip('/path/to/TASKDATA.zip')
```

### export

```python
import isoxml.models.base.v4 as iso
from isoxml.io import dump_taskdata_to_text

customer = iso.Customer(
    id="CTR0001",
    last_name="demo_customer"
)
farm = iso.Farm(
    id="FRM0001",
    designator="demo farm",
    customer_id_ref=customer.id
)
task_data = iso.Iso11783TaskData(
    management_software_manufacturer="josephinum research",
    management_software_version="0.0.0",
    data_transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS,
    customers=[customer],
    farms=[farm]
)

xml_content = dump_taskdata_to_text(task_data)

print(xml_content)
```

```xml
<ISO11783_TaskData VersionMajor="4" VersionMinor="3" ManagementSoftwareManufacturer="josephinum research" ManagementSoftwareVersion="0.0.0" DataTransferOrigin="1">
    <CTR A="CTR0001" B="demo_customer"/>
    <FRM A="FRM0001" B="demo farm" I="CTR0001"/>
</ISO11783_TaskData>
```

### more

[see examples](https://github.com/Josephinum-Research/isoxml-py/blob/main/examples)

## Project Layout

- `isoxml.models.base`: generated ISOXML dataclasses.
- `isoxml.io`: task data read/write and external file helpers.
- `isoxml.geometry`: Shapely conversion helpers.
- `isoxml.grids`: NumPy grid binary helpers.
- `isoxml.prescriptions`: high-level application map workflows.
- `isoxml.cli`: reusable CLI entry points.

Legacy imports under `isoxml.util`, `isoxml.converter`, and `isoxml.workflows` remain available as compatibility shims.

## 主要功能 | Main Features

### 1. ISOXML TaskData 处理
- **版本支持**：完整支持 ISO11783-10 v3 和 v4 标准
- **灵活的读写方式**：
  - 从 ZIP 压缩包直接读取/写入
  - 从 TASKDATA 目录读取/写入
  - 从字符串读取/写入
- **数据结构**：完整的 Python 类模型，类型安全

### 2. 应用图（处方图）生成
支持三种类型的应用图生成，用于精准农业变量施用作业：

#### 矢量型应用图（Vector-based Application Map）
- 基于多边形的处理区域定义
- 适合少数处理区域（< 20个）
- 每个区域独立设置施用参数
- 示例：[app_map_vector.py](examples/app_map_vector.py)

#### 网格型 Type 1（Grid Type 1）
- 使用查找表原理存储数据
- 适合少数不同值的情况
- 实际值存储在 XML 中
- 示例：[app_map_grid_type_1.py](examples/app_map_grid_type_1.py)

#### 网格型 Type 2（Grid Type 2）
- 数据直接编码为二进制文件
- 适合大量连续变化的数值
- XML文件保持较小（仅含缩放和偏移信息）
- 示例：[app_map_grid_type_2.py](examples/app_map_grid_type_2.py)

📄 **详细比较**: [应用图类型对比文档](docs/application_map_types_comparison.md)

### 3. 几何数据转换
- **Shapely ↔ ISOXML**：在 Shapely 几何对象和 ISOXML 几何之间无缝转换
- **支持的几何类型**：
  - Point（点）
  - LineString（线串）- 包括导航线
  - Polygon（多边形）- 地块边界、处理区域
- **坐标系统**：自动处理坐标转换（WGS84）

### 4. 网格数据处理
- **NumPy 数组转换**：将 NumPy 数组转换为 ISOXML 网格二进制文件
- **支持类型**：Grid Type 1 和 Grid Type 2
- **应用场景**：高分辨率处方图、土壤养分图

### 5. 代码生成
- 从现有 TASKDATA.XML 文件生成 Python 代码
- 基于 xsdata 工具链
- 便于学习和快速开发
- 示例：[pycode_generator.py](examples/pycode_generator.py)

### 6. 导航线和引导模式
- AB线导航（A-B Guidance）
- 曲线导航（Curve Guidance）
- 支持引导模式参数设置（幅宽、传播方向等）
- 示例：[guidance_pattern.py](examples/guidance_pattern.py)

## 应用图类型比较 | Application Map Type Comparison

| 特性 | 矢量型 | 网格型 Type 1 | 网格型 Type 2 |
|------|--------|--------------|--------------|
| **数据结构** | 多边形 | 网格 + 查找表 | 网格 + 直接编码 |
| **适用场景** | 少数区域 | 少数不同值 | 大量连续值 |
| **XML大小** | 中等 | 可能很大 | 较小 |
| **典型应用** | 分区施肥 | 等级施用 | 变量施肥 |

### 选择建议：
- **矢量型**：适合有明确边界的少数区域，如基于土壤类型的分区管理
- **Type 1**：适合固定等级的施用策略（低/中/高），如简单的分级施肥
- **Type 2**：适合基于遥感数据的高分辨率连续变量施用

详细说明请参阅：[应用图类型完整对比](docs/application_map_types_comparison.md)

## 硬件测试案例 | Hardware Test Cases

本库已在以下实际农业机械设备上测试验证：

### ✅ 矢量型应用图（Vector Application Map）
- **设备**：New Holland T7 + IntelliView 12 + Kverneland iXter B18
- **状态**：成功导入和显示
- **备注**：终端无法选择 DDI（需在生成时预设）

### ✅ 网格型 Type 2
- **设备 1**：Deutz-Fahr 6140.4 + Bogballe L20W
  - **状态**：成功导入和显示
- **设备 2**：New Holland T7 + IntelliView 12 + Kverneland iXter B18
  - **状态**：可导入和显示
  - **限制**：任务控制器（TC）不接受设定值

### 关键术语说明
- **DDI (Data Dictionary Item)**：数据字典项，定义数据类型（如施肥量、播种量等）
- **TC (Task Controller)**：任务控制器，农机上的 ISOBUS 控制单元
- **FMIS (Farm Management Information System)**：农场管理信息系统

## Dependencies

* [xsdata](https://github.com/tefra/xsdata) - Naive XML Bindings for python.
* [shapely](https://github.com/shapely/shapely) - a widely used library for editing and analyzing geometric objects.
* [numpy](https://github.com/numpy/numpy) - you know it, you love it

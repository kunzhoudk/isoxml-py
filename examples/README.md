# examples 目录说明

这个目录主要放三类内容：

- 可直接运行的示例脚本
- notebook 交互示例
- 输入样例、固定输出样例和本地运行产物

如果你是第一次使用这个项目，建议先从这里开始熟悉数据组织方式和常见工作流。

## 目录用途

- `application_maps/`
  应用图相关示例，包括矢量型应用图、grid type 1、grid type 2，以及从测试 SHP 生成 GeoJSON 应用图的脚本。

- `bash_script/`
  便于直接运行的命令示例，适合快速试跑。

- `input/`
  输入样例数据。包括 Shapefile、GeoJSON 等。

- `expected/`
  固定输出样例，会随仓库一起保存，适合文档、测试和 notebook 引用。

- `output/`
  本地运行输出目录。通常不作为固定样例使用。

- `grid_overlay_viewer.ipynb`
  用于查看 grid 与边界叠加效果的 notebook。

- `partfield_viewer.ipynb`
  用于查看 partfield 几何的 notebook。

## 推荐使用方式

对于脚本型能力，优先使用正式 CLI，而不是直接调用 `examples/` 下的文件。

```bash
uv run isoxml-vector-to-taskdata --help
uv run isoxml-convert-taskdata --help
uv run isoxml-prepare-application-map-geojson --help
uv run isoxml-inspect-grid-overlay --help
uv run isoxml-inspect-vector --help
uv run isoxml-validate-taskdata --help
```

## 快速示例

### 1. SHP -> taskdata

```bash
bash examples/bash_script/run_shp_to_taskdata.sh
```

这个脚本会：

- 读取 `examples/input/small/shp/Rx.shp`
- 读取边界 `examples/input/small/boundary/Boundary.shp`
- 生成 ISOXML 输出到 `examples/output/`

### 2. GeoJSON -> taskdata

```bash
bash examples/bash_script/run_geojson_to_taskdata.sh
```

这个脚本使用：

- [test_shp_application_map_with_boundary.geojson](input/test_shp_application_map_with_boundary.geojson)

该 GeoJSON 已包含：

- 处方区 feature
- 一个名为 `border` 的边界 feature

因此不需要额外提供 `--boundary-path`。

### 3. 从测试 SHP 生成标准化 GeoJSON 应用图

命令行方式：

```bash
uv run isoxml-prepare-application-map-geojson \
  examples/input/test_shp/20250415_211530.shp \
  --output-path examples/input/test_shp_application_map_with_boundary.geojson \
  --value-field value
```

Python 脚本方式：

```bash
uv run python examples/application_maps/prepare_test_shp_application_map_geojson.py
```

这个过程会把 polygon 矢量标准化为一个可直接喂给 `isoxml-vector-to-taskdata` 的 GeoJSON，并自动提取一个合并后的 `border` feature。

### 4. 检查 grid overlay

```bash
bash examples/bash_script/run_check_grid_overlay.sh
```

## notebook 说明

### `grid_overlay_viewer.ipynb`

适合做这些事情：

- 查看 grid 单元和地块边界是否对齐
- 查看格网值的颜色分布
- 对照 shapefile / geojson overlay

### `partfield_viewer.ipynb`

适合快速检查：

- partfield polygon
- 几何范围
- 读取后的可视化效果

## 给第三方使用者的建议

如果你只想快速验证这个项目是否适合你的数据，建议按这个顺序试：

1. 先跑 `run_shp_to_taskdata.sh`
2. 再跑 `run_geojson_to_taskdata.sh`
3. 用 `grid_overlay_viewer.ipynb` 看结果是否与原始数据对齐
4. 如果需要，将自己的矢量数据替换到 `examples/input/` 中试跑

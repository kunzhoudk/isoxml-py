import isoxml
from isoxml.resources import xsd_path


def test_public_api__when_importing_top_level__expect_expected_exports_available():
    assert isoxml.load_taskdata_from_path is not None
    assert isoxml.write_taskdata_zip is not None
    assert isoxml.from_numpy_array_to_type_2 is not None
    assert isoxml.ShapelyConverterV4 is not None
    assert isoxml.GridFromShpOptions is not None
    assert isoxml.convert_grid_from_shp is not None


def test_packaged_xsd__when_resolved__expect_schema_file_exists():
    assert xsd_path("4").exists()
    assert xsd_path("4").parent.name == "xsd"

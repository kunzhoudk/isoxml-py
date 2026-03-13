import isoxml
from isoxml.resources import xsd_path


def test_public_api__when_importing_top_level__expect_expected_exports_available():
    assert isoxml.load_taskdata_from_path is not None
    assert isoxml.write_taskdata_to_zip is not None
    assert isoxml.dump_taskdata_to_text is not None
    assert isoxml.merge_external_file_contents is not None
    assert isoxml.encode_grid_type_2_binary is not None
    assert isoxml.decode_grid_binary is not None
    assert isoxml.ShapelyConverterV4 is not None
    assert isoxml.GridFromShpOptions is not None
    assert isoxml.build_grid_taskdata_from_shapefile is not None

    assert not hasattr(isoxml, "isoxml_from_path")
    assert not hasattr(isoxml, "isoxml_to_zip")
    assert not hasattr(isoxml, "write_taskdata_zip")
    assert not hasattr(isoxml, "convert_grid_from_shp")


def test_packaged_xsd__when_resolved__expect_schema_file_exists():
    assert xsd_path("4").exists()
    assert xsd_path("4").parent.name == "xsd"

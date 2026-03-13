"""
if you want to make sure that your created TASKDATA is truly valid according to the XSD spec,
you can perform the following validation:
"""
import xmlschema
from xmlschema import XMLSchemaValidationError

import isoxml.models.base.v4 as iso
from isoxml.io import dump_taskdata_to_text
from isoxml.resources import xsd_path

xsd_file = xsd_path("4")

task_data_valid = iso.Iso11783TaskData(
    management_software_manufacturer="josephinum research",
    management_software_version="0.0.1",
    data_transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS
)

xml_content = dump_taskdata_to_text(task_data_valid)
xmlschema.validate(xml_content, xsd_file)

task_data_invalid = iso.Iso11783TaskData()

try:
    xmlschema.validate(dump_taskdata_to_text(task_data_invalid), xsd_file)
except XMLSchemaValidationError as e:
    print(e)

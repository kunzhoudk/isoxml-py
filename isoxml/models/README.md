# ISOXML Models README

This README explains what is inside `isoxml/models`:
- how schema-based model classes are generated from ISO11783 XSD files using [xsdata](https://github.com/tefra/xsdata) (commands below for TaskFile v3 and v4),
- and which non-generated helper logic exists in this directory (for example, `DDEntity.__bytes__()`).

## XSD code generation

```bash
xsdata resources/xsd/ISO11783_TaskFile_V3-3.xsd \
        --package isoxml.models.base.v3 \
        --subscriptable-types \
        --union-type \
        --structure-style clusters \
        --no-relative-imports        

xsdata resources/xsd/ISO11783_TaskFile_V4-3.xsd \
        --package isoxml.models.base.v4 \
        --subscriptable-types \
        --union-type \
        --structure-style clusters \
        --no-relative-imports 
        
```
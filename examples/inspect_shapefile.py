"""
Inspect a shapefile to extract information needed for prescription map generation.

This script will show:
- CRS (coordinate reference system)
- Field names and data types
- Geometry types
- Data bounds
- Sample records
- Value statistics for numeric fields
"""

from pathlib import Path

import geopandas as gpd


def inspect_shapefile(shp_path: Path) -> None:
    print(f"📂 Inspecting: {shp_path}\n")

    # Read the shapefile
    gdf = gpd.read_file(shp_path)

    # Basic info
    print("=" * 60)
    print("📊 BASIC INFORMATION")
    print("=" * 60)
    print(f"Total features: {len(gdf)}")
    print(f"Geometry types: {gdf.geometry.geom_type.unique().tolist()}")
    print(f"CRS: {gdf.crs}")
    # add how many polyons that multipolygon has
    if "MultiPolygon" in gdf.geometry.geom_type.unique():
        multipolygons = gdf[gdf.geometry.geom_type == "MultiPolygon"]
        print(f"  - MultiPolygons has : {len(multipolygons)} polygons")
    print()

    # Field information
    print("=" * 60)
    print("📋 FIELDS (ATTRIBUTES)")
    print("=" * 60)
    for col in gdf.columns:
        if col != "geometry":
            dtype = gdf[col].dtype
            print(f"  • {col:20s} ({dtype})")
    print()

    # Spatial bounds
    print("=" * 60)
    print("🗺️  SPATIAL BOUNDS")
    print("=" * 60)
    bounds = gdf.total_bounds
    print(f"  Min Lon/East:  {bounds[0]:.8f}")
    print(f"  Min Lat/North: {bounds[1]:.8f}")
    print(f"  Max Lon/East:  {bounds[2]:.8f}")
    print(f"  Max Lat/North: {bounds[3]:.8f}")
    print()

    # Sample data
    print("=" * 60)
    print("📝 SAMPLE DATA (first 5 rows)")
    print("=" * 60)
    # Show without geometry for cleaner output
    display_df = gdf.drop(columns=["geometry"]).head()
    print(display_df.to_string())
    print()

    # Statistics for numeric fields
    print("=" * 60)
    print("📈 NUMERIC FIELD STATISTICS")
    print("=" * 60)
    numeric_cols = gdf.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        for col in numeric_cols:
            print(f"\n  {col}:")
            print(f"    Min:    {gdf[col].min()}")
            print(f"    Max:    {gdf[col].max()}")
            print(f"    Mean:   {gdf[col].mean():.2f}")
            print(f"    Median: {gdf[col].median():.2f}")
            unique_count = gdf[col].nunique()
            print(f"    Unique values: {unique_count}")
            if unique_count <= 20:
                print(f"    Values: {sorted(gdf[col].unique().tolist())}")
    else:
        print("  No numeric fields found.")
    print()

    # Check for potential border vs zone indicators
    print("=" * 60)
    print("🔍 POTENTIAL FIELD IDENTIFIERS")
    print("=" * 60)
    text_cols = gdf.select_dtypes(include=["object"]).columns
    for col in text_cols:
        unique_vals = gdf[col].unique()
        if len(unique_vals) <= 20:
            print(f"\n  {col}: {unique_vals.tolist()}")
    print()

    # Recommendations
    print("=" * 60)
    print("💡 RECOMMENDATIONS FOR PRESCRIPTION MAP")
    print("=" * 60)
    print("\nTo generate a prescription map, you need:")
    print("  1. ✓ Field to identify border polygon (e.g., 'name' == 'border')")
    print("  2. ✓ Field with dose/application values (numeric)")
    print("  3. ✓ Polygons for treatment zones")
    print()

    # Try to auto-detect relevant fields
    print("Auto-detected candidates:")

    # Dose field candidates
    dose_candidates = []
    for col in numeric_cols:
        if any(
            keyword in col.lower()
            for keyword in ["dose", "rate", "amount", "value", "kg", "fertilizer"]
        ):
            dose_candidates.append(col)

    if dose_candidates:
        print(f"  • Dose field: {dose_candidates}")
    else:
        print(f"  • Dose field: Consider using one of: {list(numeric_cols)}")

    # Name field candidates
    name_candidates = []
    for col in text_cols:
        if any(
            keyword in col.lower()
            for keyword in ["name", "id", "type", "zone", "class"]
        ):
            name_candidates.append(col)

    if name_candidates:
        print(f"  • Name/ID field: {name_candidates}")
    else:
        print(f"  • Name/ID field: Consider using one of: {list(text_cols)}")

    print()
    print("=" * 60)


def main() -> None:
    # CHANGE THIS PATH to your shapefile
    shp_path = Path(__file__).parent / "input" / "big" / "shp" / "NDVI_Rx.shp"

    if not shp_path.exists():
        print(f"❌ File not found: {shp_path}")
        print(
            "\n📌 Please update the shp_path in the script to point to your shapefile."
        )
        return

    inspect_shapefile(shp_path)


if __name__ == "__main__":
    main()

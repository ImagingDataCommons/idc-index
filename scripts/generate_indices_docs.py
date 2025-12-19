#!/usr/bin/env python3
"""Utility script to automatically generate documentation for all IDC index tables.

This script:
1. Instantiates IDCClient from idc_index
2. Uses index table discovery functionality to find all available indices
3. Fetches schemas for all tables
4. Generates a markdown documentation page with column descriptions
5. Creates a Mermaid diagram showing relationships between tables based on shared column names
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from idc_index import IDCClient


def generate_mermaid_diagram(indices_schemas: dict) -> str:
    """Generate a Mermaid ER diagram showing relationships between tables.

    Args:
        indices_schemas: Dictionary mapping index names to their schemas

    Returns:
        String containing the Mermaid diagram markup
    """
    # Collect all columns per table
    table_columns: dict[str, set[str]] = {}
    for index_name, schema in indices_schemas.items():
        if schema and "columns" in schema:
            table_columns[index_name] = {col["name"] for col in schema["columns"]}

    # Find relationships based on shared column names
    relationships: list[tuple[str, str, str]] = []
    tables = list(table_columns.keys())

    for i, table1 in enumerate(tables):
        for table2 in tables[i + 1 :]:
            shared_columns = table_columns[table1] & table_columns[table2]
            # Only create relationships for meaningful shared columns
            meaningful_shared = [
                col
                for col in shared_columns
                if col
                in {
                    "SeriesInstanceUID",
                    "StudyInstanceUID",
                    "PatientID",
                    "collection_id",
                    "SOPInstanceUID",
                    "crdc_series_uuid",
                }
            ]
            if meaningful_shared:
                for col in meaningful_shared:
                    relationships.append((table1, table2, col))

    # Generate Mermaid markup using MyST directive syntax with zoom enabled
    lines = [
        "```{mermaid}",
        ":zoom:",
        "",
        "erDiagram",
    ]

    # Define entities with their columns
    for index_name, schema in indices_schemas.items():
        if not schema or "columns" not in schema:
            continue

        # Add entity definition
        lines.append(f"    {index_name} {{")
        # Include ALL columns from the schema
        for col in schema["columns"]:
            col_type = col.get("type", "STRING")
            col_name = col.get("name", "")
            # Escape special characters that might cause issues in Mermaid
            col_name_safe = col_name.replace("-", "_")
            lines.append(f"        {col_type} {col_name_safe}")
        lines.append("    }")

    # Add relationships
    for table1, table2, col in relationships:
        lines.append(f"    {table1} ||--o{{ {table2} : {col}")

    lines.append("```")
    return "\n".join(lines)


def generate_table_documentation(index_name: str, schema: dict) -> str:
    """Generate markdown documentation for a single table.

    Args:
        index_name: Name of the index table
        schema: Schema dictionary containing table_description and columns

    Returns:
        String containing the markdown documentation for the table
    """
    lines = [f"## `{index_name}`", ""]

    # Add table description if available
    if schema.get("table_description"):
        lines.append(schema["table_description"])
        lines.append("")

    # Add column information
    if "columns" in schema:
        lines.append("### Columns")
        lines.append("")

        for col in schema["columns"]:
            col_name = col.get("name", "")
            col_type = col.get("type", "STRING")
            col_mode = col.get("mode", "NULLABLE")
            col_desc = col.get("description", "")

            # Format: - **column_name** (TYPE, MODE): Description
            mode_str = f", {col_mode}" if col_mode else ""
            lines.append(f"- **`{col_name}`** (`{col_type}`{mode_str}): {col_desc}")

        lines.append("")

    return "\n".join(lines)


def generate_indices_documentation(output_path: Path) -> None:
    """Generate complete documentation for all available indices.

    Args:
        output_path: Path where the generated markdown file should be saved
    """
    print("Initializing IDCClient...")
    client = IDCClient()

    print(f"Discovered {len(client.indices_overview)} indices")

    # Fetch all schemas
    print("Fetching schemas for all indices...")
    indices_schemas: dict[str, dict] = {}
    for index_name in client.indices_overview:
        schema = client.get_index_schema(index_name)
        if schema:
            indices_schemas[index_name] = schema
            print(f"  ✓ {index_name}")
        else:
            print(f"  ✗ {index_name} (schema not available)")

    # Generate documentation
    print("\nGenerating documentation...")
    doc_lines = [
        "# Index Tables Reference",
        "",
        "This page provides a comprehensive reference for all index tables available in `idc-index`.",
        "The documentation is automatically generated from the schemas provided by `idc-index-data`.",
        "",
        "> **Note:** Column descriptions are sourced directly from the `idc-index-data` package schemas.",
        "> If you notice any missing or incorrect descriptions, please report them in the",
        "> [idc-index-data repository](https://github.com/ImagingDataCommons/idc-index-data).",
        "",
        "## Overview",
        "",
        "`idc-index` provides access to multiple index tables containing metadata about the files",
        "available in IDC. Each table serves a specific purpose and contains different metadata attributes.",
        "",
        "## Table Relationships",
        "",
        "The following diagram shows how the different index tables relate to each other",
        "based on shared column names:",
        "",
    ]

    # Add Mermaid diagram
    mermaid_diagram = generate_mermaid_diagram(indices_schemas)
    doc_lines.append(mermaid_diagram)
    doc_lines.append("")

    # Add documentation for each table
    doc_lines.append("## Available Index Tables")
    doc_lines.append("")

    # Sort tables: main indices first, then others alphabetically
    priority_tables = ["index", "prior_versions_index"]
    other_tables = sorted(
        [name for name in indices_schemas if name not in priority_tables]
    )
    sorted_tables = priority_tables + other_tables

    for index_name in sorted_tables:
        if index_name in indices_schemas:
            table_doc = generate_table_documentation(
                index_name, indices_schemas[index_name]
            )
            doc_lines.append(table_doc)

    # Write to file
    print(f"\nWriting documentation to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(doc_lines))

    print("✓ Documentation generated successfully!")
    print(f"  Total tables documented: {len(indices_schemas)}")
    print(f"  Output file: {output_path}")


def main() -> int:
    """Main entry point for the script."""
    # Determine output path
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    output_path = repo_root / "docs" / "indices_reference.md"

    try:
        generate_indices_documentation(output_path)
        return 0
    except Exception as e:
        print(f"Error generating documentation: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

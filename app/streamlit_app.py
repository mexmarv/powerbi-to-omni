import streamlit as st
import zipfile
import json
import yaml
import io
from pathlib import Path
from generator.dax_sql_generator import translate_dax_ast

st.set_page_config(layout="wide")
st.title("Power BI → Omni Semantic Layer Generator")

st.markdown("""
Drop a `.pbix` file to extract tables and DAX logic, convert to Omni YAML, and download the full model bundle.

**After downloading:**
- Upload the `.yml` files from the `/models/` folder to **Omni → Models → Import**
- The `.sql` files in the `/sql/` folder are optional previews of the DAX logic converted to SQL — useful for validation or testing in Databricks.
""")

uploaded_file = st.file_uploader("Drop your .pbix or .pbit file here", type=["pbix", "pbit"])

def extract_model(pbix_bytes):
    with zipfile.ZipFile(pbix_bytes) as z:
        for name in z.namelist():
            if name.endswith("model.json") or "DataModelSchema" in name:
                with z.open(name) as f:
                    return json.load(f)
    return None

if uploaded_file:
    model = extract_model(uploaded_file)
    if not model:
        st.error("No data model found in the PBIX file.")
    else:
        tables = []
        for table in model.get("model", {}).get("tables", []):
            tname = table.get("name")
            cols = [c["name"] for c in table.get("columns", [])]
            measures = [{"name": m["name"], "expression": m["expression"]} for m in table.get("measures", [])]
            tables.append({"name": tname, "columns": cols, "measures": measures})

        yaml_files = {}
        sql_files = {}

        for table in tables:
            with st.expander(f"Table: {table['name']}"):
                st.markdown("**Columns:**")
                st.write(table["columns"])
                st.markdown("**Measures:**")

                # Initialize YAML structure
                model_yaml = {
                    'semantic_model': {
                        'name': table['name'],
                        'description': f"{table['name']} model from Power BI",
                        'entities': [{'name': 'id', 'type': 'primary'}],
                        'defaults': {'agg_time_dimension': table['columns'][0] if table['columns'] else ''},
                        'dimensions': [{'name': col, 'type': 'time' if 'date' in col.lower() else 'categorical'} for col in table['columns']],
                        'measures': []
                    }
                }

                # Resolve measure dependencies
                measure_dict = {msr['name']: msr['expression'] for msr in table["measures"]}

                for m in table["measures"]:
                    st.code(f"{m['name']} = {m['expression']}", language='dax')

                    sql_expr = translate_dax_ast(m['expression'], measure_dict)
                    st.text_area(f"SQL for {m['name']}", sql_expr, height=80)

                    model_yaml['semantic_model']['measures'].append({
                        'name': m['name'],
                        'type': 'derived',
                        'expr': sql_expr
                    })

                    sql_files[f"{table['name']}_{m['name']}.sql"] = (
                        f"-- SQL for {m['name']}\nSELECT {sql_expr} FROM {table['name']};"
                    )

                # Save YAML string
                yml_str = yaml.dump(model_yaml, sort_keys=False)
                yaml_files[f"{table['name']}.yml"] = yml_str

        # Final download bundle
        if yaml_files:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for fname, content in yaml_files.items():
                    zip_file.writestr(f"models/{fname}", content)
                for fname, content in sql_files.items():
                    zip_file.writestr(f"sql/{fname}", content)
            st.download_button("Download All YAMLs and SQL as ZIP", zip_buffer.getvalue(), file_name="omni_model_bundle.zip")
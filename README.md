# Power BI to Omni Semantic Layer Generator (Streamlit)

This is a Streamlit web app that:
- Uploads `.pbix` or `.pbit` Power BI files
- Extracts embedded models
- Converts DAX measures to SQL
- Outputs Omni-compatible YAMLs
- Bundles YAML + SQL previews into one ZIP

## Run locally

```bash
git clone https://github.com/mexmarv/powerbi-to-omni.git
cd powerbi-to-omni/app
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then upload your `.pbix` and download the model bundle. Upload `/models/*.yml` to Omni under **Models → Import**.
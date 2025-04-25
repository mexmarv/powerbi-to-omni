# Power BI to Omni Semantic Layer Generator (Streamlit)
### Made with ❤️ by [Marvin Nahmias](https://github.com/mexmarv)
- 📧 [mexmarv@gmail.com](mailto:mexmarv@gmail.com)  
- 💼 [LinkedIn](https://www.linkedin.com/in/marvinnahmias)  
- 🌐 [about.me/marvinnahmias](https://about.me/marvinnahmias)

You can test it here: [PBI 2 OMNI Semantic Layer Conversion](https://pbi2omni.streamlit.app/)

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

Then upload your `.pbix` and download the model bundle.

### Omni Upload
- Upload the `.yml` files from `/models/` to **Omni → Models → Import**

### SQL Files
- The `.sql` files in `/sql/` are optional and show the converted DAX logic in SQL format — useful for testing in Databricks or manual validation.

# 🧠 Power BI → Omni Semantic Layer Generator

![Omni + Power BI](https://img.shields.io/badge/DAX%20→%20Omni-Translator-blueviolet)
![Built by Marvin Nahmias](https://img.shields.io/badge/Built%20by-Marvin%20Nahmias-blue)
[![GitHub](https://img.shields.io/github/stars/mexmarv/powerbi-to-omni?style=social)](https://github.com/mexmarv/powerbi-to-omni)

This tool extracts DAX measures from Power BI `.pbix` files and converts them into **SQL expressions and YAML models** compatible with [Omni](https://omni.co), with **Databricks as the backend**. It bridges business logic from Power BI to modern semantic layers.

You can test it here: [PBI 2 OMNI Semantic Layer Conversion](https://pbi2omni.streamlit.app/)

---

## ✅ Supported DAX Functions

| DAX Function             | Status       | Notes                                 |
|--------------------------|--------------|----------------------------------------|
| `SUM(...)`               | ✅ Full       | Aggregation                            |
| `DIVIDE(a, b)`           | ✅ Full       | Handles nested expressions             |
| `IF(cond, then, else)`   | ✅ Full       | Nested logic and comparisons           |
| `CALCULATE(...)`         | ✅ Full       | Includes `SAMEPERIODLASTYEAR`, `FILTER`, `ALL` |
| `FILTER(...)`            | ✅ Full       | Used within `CALCULATE`                |
| `ALL(...)`               | ✅ Full       | Context removal in calculations        |
| `ISBLANK(...)`           | ✅ Full       | Null check handling                    |
| `HASONEVALUE(...)`       | ✅ Full       | Selection context check                |
| `SELECTEDVALUE(...)`     | ✅ Full       | Simulated with `MAX(...)`              |
| `SWITCH(TRUE(), ...)`    | ✅ Full       | Translates to `CASE WHEN` structure    |
| `VAR ... RETURN`         | ✅ Full       | Variable logic                         |
| `RELATED(...)`           | ✅ Simulated  | Simulated with dot-notation            |
| `RANKX(...)`             | ✅ Simulated  | Simulated with `RANK() OVER ...`       |
| Logical ops (`&&`, `||`) | ✅ Full       | Full boolean and arithmetic logic      |
| Measure references       | ✅ Full       | Recursive resolution supported         |

---

## 🚧 Upcoming Additions

- `TOPN(...)`, `VALUES(...)`, `DISTINCT(...)`
- `REMOVEFILTERS(...)`, `EARLIER(...)`
- Iterative / row context logic (e.g. `RANKX` with `ALLSELECTED`)

---

## 🚀 How It Works

1. Upload a `.pbix` file
2. The tool extracts and parses the embedded model JSON
3. Translates each DAX measure into:
   - SQL expression
   - Omni-compatible YAML
4. Download, review or upload directly into Omni.

---

## 📂 Project Structure

```
powerbi-to-omni/
│
├── app/
│   ├── streamlit_app.py        # Main Streamlit interface
│   └── generator/
│       ├── dax_parser.py       # Tokenizer
│       ├── dax_sql_generator.py # Translator logic
│       └── resolve.py          # Measure and VAR resolver
├── test/
├── README.md
```

---

## 🧪 Try the Enterprise Sample

Test your full setup using the included:

- `enterprise_test.pbix`

These include:
- Nested VARs
- Time intelligence
- Dynamic filters
- Rank logic
- Context manipulation

---

## ✨ Built with ❤️ by Marvin Nahmias

- GitHub: [@mexmarv](https://github.com/mexmarv)
- LinkedIn: [Marvin Nahmias](https://www.linkedin.com/in/marvinnahmias)

---

> This tool is open source. Use it, fork it, improve it.
```markdown
# Example Demos

This folder contains runnable demo scripts that show how to use core components of the project.

---

### 🧠 ISTAT API Example
```python
from src.api.istat_api import IstatAPITester
api = IstatAPITester()
data = api.fetch_dataset_data("DCIS_POPRES1")
print(f"Retrieved {len(data)} records")
```
```python
from src.database.duckdb.manager import DuckDBManager
manager = DuckDBManager()
result = manager.execute_optimized_query("SELECT * FROM istat_observations LIMIT 10")
print(result)
```
```python
from src.integrations.powerbi.templates import TemplateGenerator
template = TemplateGenerator(repository=None, optimizer=None)
template.create_pbit_file(template, "output.pbit")
```

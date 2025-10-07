# Example.Demos
### 🧠 Dataset API Example
```python
from src.api.dataset_api import DatasetAPI

api = DatasetAPI()
data = api.fetch_data("population_data")
print(f"Retrieved {len(data)} records")
```

### 🗃️ DuckDB Query Example
```python
from src.database.duckdb.manager import DuckDBManager

manager = DuckDBManager()
result = manager.execute_query("SELECT * FROM population LIMIT 10")
print(result)
```

### ⚙️ Pipeline Example
```python
from src.pipeline.orchestrator import PipelineOrchestrator

pipeline = PipelineOrchestrator()
pipeline.run("population_ingest")
```

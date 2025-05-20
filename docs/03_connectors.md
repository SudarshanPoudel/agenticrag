# 3. Connectors

Connectors establish links to external data sources, particularly databases and APIs, allowing the system to query them without importing all data.

#### ExternalDBConnector

```python
from agenticrag.connectors import ExternalDBConnector

# Initialize
connector = ExternalDBConnector(
    external_db_store=external_db_store,
    meta_store=meta_store
)

# Connect to external database
connector.connect_db(
    name="analytics_db",
    connection_url_env_var="DATABASE_URL",
)
```

#### Custom Connector 
You can create your own data connectors like api connectors by inheriting BaseConnector class and writing custom logic to connect with api, as well as storing that information on store made for your own kind of data.

```python
from agenticrag.connectors import BaseConnector

class RESTApiConnector(BaseConnector):
    def __init__(self, meta_store, ...):
        pass


    def connect_api(self, name, base_url, auth_method, endpoints, description=None, ...):
        # Your Custom logic to connect with api
        pass
```

# TAFBackend

## Description
Welcome to the **TAFBackend**. This backend provides a RESTful and GraphQL API to communicate with the database that stores and manages data collected from boats and heatmaps. This README serves as documentation on how to interact with the backend's endpoints.

## IMPORTANT NOTE
As of now, this API is not deployed on a public server. To use it, you will need to **clone the repository** and run it locally.

## Setup Instructions
1. **Clone the Repository:**
```bash
git clone <repository_url>
cd TAFBackend
```
2. **Create a Python Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate    # For Windows
```
3. **Install Dependencies:**
```bash
pip install flask pandas graphene graphql-server-core werkzeug
```
4. **Run the Backend:**
```bash
python3 app.py
```
- This will create the `database.db` and necessary upload directories
- The backend will be available at `http://localhost:3000`

---

## Endpoint Documentation

### 1. **List Available Tables**
**Endpoint:** `GET /tables`  
**Description:** Returns a list of all valid tables in the database.  
**Example Usage:**
```python
import requests

response = requests.get("http://localhost:3000/tables")
print(response.json())
```

### 2. **GraphQL Endpoint**
**Endpoint:** `POST /graphql/<table_name>`  
**Description:** Query a specific table using GraphQL. You can filter by any column dynamically.  
**Example Usage (JavaScript):**
```javascript
const tableName = "boat_data";
const query = `
{
  data(boat_id: "b1") {
    boat_id
    data_temperature
    data_wind_velocity
  }
}`;

const fetchData = async () => {
  const response = await fetch(`http://localhost:3000/graphql/${tableName}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query })
  });

  const result = await response.json();
  console.log("GraphQL Data:", result.data);
};

fetchData().catch(console.error);
```

**Example Usage (Python):**
```python
import requests

table_name = "boat_data"
url = f"http://localhost:3000/graphql/{table_name}"
query = '''
{
  data(boat_id: "b1") {
    boat_id
    data_temperature
    data_wind_velocity
  }
}
'''

response = requests.post(url, json={"query": query})
print(response.json())
```
---

### 3. **Upload CSV to a Specific Table**
**Endpoint:** `POST /upload/<table_name>`
**Description:** Uploads a CSV file to the specified table. Automatically creates missing columns and adds the file name as `origin_file`.

**Example Usage:**
```python
import requests

table_name = "boat_data"  # or "heatmap_data"
file_path = "data.csv"
with open(file_path, "rb") as file:
    files = {"file": file}
    response = requests.post(f"http://localhost:3000/upload/{table_name}", files=files)

print(response.status_code)
print(response.json())
```
---

### 4. **List Unique Sources in a Table**
**Endpoint:** `GET /sources/<table_name>`
**Description:** Lists all unique `origin_file` entries in the specified table.

**Example Usage:**
```python
import requests

table_name = "boat_data"
response = requests.get(f"http://localhost:3000/sources/{table_name}")

if response.status_code == 200:
    print(response.json())
else:
    print("Error")
```
---

### 5. **Download CSV by Table and Origin File**
**Endpoint:** `GET /download/<table_name>/<origin_file>`
**Description:** Downloads all rows from the specified `origin_file` in the specified table as a CSV.

**Example Usage:**
```python
import requests

table_name = "boat_data"
origin_file = "data.csv"
response = requests.get(f"http://localhost:3000/download/{table_name}/{origin_file}")

if response.status_code == 200:
    with open("download.csv", "wb") as file:
        file.write(response.content)
    print("File downloaded successfully")
else:
    print("Error")
```
---

### 6. **Delete Data by Table and Origin File**
**Endpoint:** `DELETE /delete/<table_name>/<origin_file>`
**Description:** Deletes all rows matching the specified `origin_file` from the specified table.

**Example Usage:**
```python
import requests

table_name = "boat_data"
origin_file = "data.csv"
response = requests.delete(f"http://localhost:3000/delete/{table_name}/{origin_file}")

print(response.json())
```
---

## 🚀 **GraphQL Query Examples**

All GraphQL queries must specify the table in the endpoint URL.

### 1. **Filter by Single Column:**
```graphql
{
  data(boat_id: "b1") {
    boat_id
    data_temperature
    data_wind_velocity
  }
}
```

### 2. **Filter by Multiple Columns:**
```graphql
{
  data(boat_id: "b1", data_temperature: "22.5") {
    boat_id
    data_temperature
    data_wind_velocity
  }
}
```

### 3. **Retrieve All Data:**
```graphql
{
  data {
    boat_id
    data_temperature
    data_wind_velocity
  }
}
```

## Supported Tables

The system currently supports two tables:
- `boat_data`: For storing data related to boats
- `heatmap_data`: For storing heatmap information

Each table automatically stores the origin file name in the `origin_file` column and assigns an auto-incrementing `id` to each record.






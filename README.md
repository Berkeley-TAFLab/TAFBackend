# TAFBackend

## Description
Welcome to the **TAFBackend**. This backend provides a RESTful and GraphQL API to communicate with the database that stores and manages data collected from boats. This README serves as documentation on how to interact with the backend's endpoints.

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
pip install flask pandas graphene graphql-server flask-graphql
```
4. **Run the Backend:**
```bash
python3 app.py
```
- This will create the `database.db` and `/uploads` directory.
- The backend will be available at `http://127.0.0.1:5000`.

---

## Endpoint Documentation

### 1. **GraphQL Endpoint**
**Endpoint:** `POST /graphql`  
**Description:** Query the database using GraphQL. You can filter by any column dynamically.  
**Example Usage (JavaScript):**
```javascript
const query = `
{
  data(boat_id: "b1") {
    boat_id
    data_temperature
    data_wind_velocity
  }
}`;

const fetchData = async () => {
  const response = await fetch("http://127.0.0.1:5000/graphql", {
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

url = "http://127.0.0.1:5000/graphql"
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

### 2. **Upload CSV to Database**
**Endpoint:** `POST /upload`
**Description:** Uploads a CSV file to the backend database. Automatically creates missing columns and adds the file name as `origin_file`.

**Example Usage:**
```python
import requests

file_path = "data.csv"
with open(file_path, "rb") as file:
    files = {"file": file}
    response = requests.post("http://127.0.0.1:5000/upload", files=files)

print(response.status_code)
print(response.json())
```
---

### 3. **List Unique Sources**
**Endpoint:** `GET /sources`
**Description:** Lists all unique `origin_file` entries in the database.

**Example Usage:**
```python
import requests

response = requests.get("http://127.0.0.1:5000/sources")

if response.status_code == 200:
    print(response.json())
else:
    print("Error")
```
---

### 4. **Download CSV by `origin_file`**
**Endpoint:** `GET /download/<origin_file>`
**Description:** Downloads all rows from the specified `origin_file` as a CSV.

**Example Usage:**
```python
import requests

origin_file = "data.csv"
response = requests.get(f"http://127.0.0.1:5000/download/{origin_file}")

if response.status_code == 200:
    with open("download.csv", "wb") as file:
        file.write(response.content)
    print("File downloaded successfully")
else:
    print("Error")
```
---

### 5. **Delete Data by `origin_file`**
**Endpoint:** `DELETE /delete/<origin_file>`
**Description:** Deletes all rows matching the specified `origin_file`.

**Example Usage:**
```python
import requests

origin_file = "data.csv"
response = requests.delete(f"http://127.0.0.1:5000/delete/{origin_file}")

print(response.json())
```
---

## 🚀 **GraphQL Query Examples**

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

# TAFBackend 

## Description 
Please use this README as the documentation of how to use our endpoints to communicate with our database. These are the endpoints that will be exposed in our frontendUI that lets us store and modify data collected from our boats. 

## IMPORTANT NOTE 
As of January 29th, this API is not actively on an accessible machine. Thus, if you would like to use this API, please clone the repo and run the app.py file locally. 

### Current usage details 
1. Use git clone to clone the repo
2. Make sure the proper dependences are installed using `pip install flask pandas` . It is recommended that you create a python virtual environment first
3. Run the `app.py` program using `python3 app.py`. This will create the `database.db` and `/uploads` directory
4. At this point the backend will be listening on localhost:5000. Read below for the different endpoints you can interact with.

## Endpoint Documentation 
### 1. Get table names 
Endpoint: `GET /tables`<br/> 
Description: Gets a list of all tables in database<br/>
Example Usage: 
     
        import requests 
        response = requests.get('http:127.0.0.1:5000/tables')
        
        if response.status_code == 200: 
            print(response.text) 
        else: 
            print(f"Request failed with status code: {response.status_code}")
    

### 2. Upload CSV to Database
Endpoint: `POST /upload`<br/>
Description: Uploads CSV to backend database<br/>
Example Usage: 
    
        import requests
        
        file_path = "data.csv"
        with open(file_path, "rb") as file: 
            files = {"file": file}
            response = requests.post("http:127.0.0.1:5000/upload", files = files)

        print(response.status_code)
        print(response.json())

    

### 3. Download CSV From Database via Table name 
Endpoint: `GET /table/<table_name>/download`<br/>
Description: Download CSV from database <br/>
Example Usage: 
    
        import requests

        response = requests.get("http://127.0.0.1:5000/table/<table_name>/download")
        
        if response.status_code == 200):
            with open("download.csv", "wb") as file: 
                file.write(response.content)
            print("File downloaded successfully")
        else: 
            print("Error")
    

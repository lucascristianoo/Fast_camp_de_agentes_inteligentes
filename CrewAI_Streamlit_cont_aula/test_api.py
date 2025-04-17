import requests
import json

url ='http://127.0.0.1/research_candidates'

headers ={
    'accept' : 'application/json',
    'Content-Type' : 'aplication/json',
}

data ={
    'job_requirements': 'Data Engineer & Data Architect - Databricks Professional Certified - brasileiro que reside em São José dos Campos'
}

response = requests.post(url, headers=headers, json=data)

print(f"Status Code: {response.status_code}")
print("Response JSON:")
print(json.dumps(response.json(),indent=4, ensure_ascii=False))
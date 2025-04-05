import requests

url = "https://aaoihfjirymbeuwfgght.supabase.co/auth/v1/admin/users"
headers = {
    "apikey": 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhb2loZmppcnltYmV1d2ZnZ2h0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Mjc2MDc4OSwiZXhwIjoyMDU4MzM2Nzg5fQ.EjY5dxVUU5UFE-hiwQl43pgSIIKWC7EckhKJ_I6k-8s',
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhb2loZmppcnltYmV1d2ZnZ2h0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Mjc2MDc4OSwiZXhwIjoyMDU4MzM2Nzg5fQ.EjY5dxVUU5UFE-hiwQl43pgSIIKWC7EckhKJ_I6k-8s",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

print("Status:", response.status_code)

try:
    response_data = response.json()
    print("Response:", response_data)
except ValueError as e:
    print("Failed to decode JSON:", e)

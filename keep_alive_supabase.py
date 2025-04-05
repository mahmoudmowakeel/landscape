import requests

url = "https://aaoihfjirymbeuwfgght.supabase.co"
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhb2loZmppcnltYmV1d2ZnZ2h0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI3NjA3ODksImV4cCI6MjA1ODMzNjc4OX0.qM5VR4tzWwg0X7Q0lJy9-MWX3KaXKU_hLalJ1mmcx0s",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhb2loZmppcnltYmV1d2ZnZ2h0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI3NjA3ODksImV4cCI6MjA1ODMzNjc4OX0.qM5VR4tzWwg0X7Q0lJy9-MWX3KaXKU_hLalJ1mmcx0s",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print("Status:", response.status_code)

from cryptography.fernet import Fernet
from datetime import datetime
import json
import base64

# HARD-CODED SECRET KEY
SECRET_KEY = b"xBf-2rhcZgcKbpqfSpmtzwrv78TCt9DRsvoa1-szG8I="
fernet = Fernet(SECRET_KEY)

expire_date = input("Enter expire date (YYYY-MM-DD): ")

try:
    datetime.strptime(expire_date, "%Y-%m-%d")
except ValueError:
    print("Invalid date format")
    exit()

data = {
    "expire_date": expire_date
}

token = fernet.encrypt(json.dumps(data).encode())
license_code = base64.urlsafe_b64encode(token).decode()

print("\n===== LICENSE CODE =====\n")
print(license_code)
print("\n========================")

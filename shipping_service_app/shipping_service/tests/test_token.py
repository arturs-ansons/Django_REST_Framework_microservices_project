import base64, json


token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYwMzY0OTczLCJpYXQiOjE3NjAzNjQ2NzMsImp0aSI6IjcxMWMyNGViOTU2NDRlODk5MTRmMThkYTBlMjIyMzFlIiwidXNlcl9pZCI6IjE2IiwiaXNfYWRtaW4iOnRydWUsInVzZXJuYW1lIjoicmFtYm81In0.2utL45YD-HrLIUCYWkm-UIIBYWuwJprZUrxwRyQeAz4"
payload_part = token.split(".")[1]
payload_part += "=" * (-len(payload_part) % 4)
decoded_bytes = base64.urlsafe_b64decode(payload_part)
payload = json.loads(decoded_bytes)
print(json.dumps(payload, indent=4))

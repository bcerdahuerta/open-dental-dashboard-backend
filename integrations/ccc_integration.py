import requests

class CCCIntegration:
    BASE_URL = "https://carriers.dentalautomation.ai/api"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = None

    def authenticate(self):
        url = f"{self.BASE_URL}/signin"
        payload = {
            "username": self.username,
            "password": self.password
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.token = data.get("token")
            return self.token
        except requests.RequestException as e:
            raise Exception(f"Error al autenticar con CCC: {e}")

    def create_client(self, client_name):
        if not self.token:
            raise Exception("Token CCC no disponible. Llama a authenticate() primero.")

        url = f"{self.BASE_URL}/clients/true"
        headers = {"x-access-token": self.token}
        body = {
            "clientName": client_name,
            "pms": "622fbe140ebf37ed8642908c",
            "networkType": "OON",
            "clinics": []
        }

        try:
            response = requests.post(url, json=body, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error al crear cliente en CCC: {e}")
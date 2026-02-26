from locust import HttpUser, task, between

class WispHubAPIUser(HttpUser):
    # Wait between 1 and 3 seconds between tasks
    wait_time = between(1, 3)

    @task(3)
    def get_clients(self):
        """Simulate fetching the list of clients"""
        self.client.get("/api/v1/clients/")

    @task(2)
    def search_clients(self):
        """Simulate a flexible search"""
        self.client.get("/api/v1/clients/search?q=Esperanza")

    @task(1)
    def verify_client_identity(self):
        """Simulate verifying a client's identity"""
        payload = {
            "address": "BELLAVISTA",
            "internet_plan_price": 40000.0
        }
        # Usamos los datos reales del cliente Esperanza Benitez (ID 7)
        self.client.post("/api/v1/clients/7/verify", json=payload)

    @task(1)
    def get_internet_plans(self):
        """Simulate fetching internet plans"""
        self.client.get("/api/v1/internet-plans/")

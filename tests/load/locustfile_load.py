from locust import HttpUser, task, between, LoadTestShape

class CompradorEcommerce(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """ Executado no início: Faz o login e guarda o token de autenticação """
        credenciais = {
            "email": "aluno@uni7.edu.br",
            "senha": "teste123"
        }
        res = self.client.post("/api/login", json=credenciais, name="/api/login")
        
        if res.status_code == 200:
            body = res.json()
            self.token = body["access_token"]
            self.client.headers.update = ({
                "Authorization": f"Bearer {self.token}"
            })

        else:
            print(f"Falha no login: {res.status_code}")

    @task(2)
    def ver_catalogo(self):
        self.client.get("/api/produtos", name="/api/produtos")

    @task(4)
    def visualizar_produto(self):
        self.client.get("/api/produtos/1", name="/api/produtos/[id]")

    @task(2)
    def adicionar_ao_carrinho(self):
        payload = {"produto_id": 1, "quantidade": 1}
        self.client.post("/api/carrinho/itens", json=payload, name="/api/carrinho/itens")

    @task(1)
    def finalizar_compra(self):
        payload = {"metodo_pagamento": "cartao", "endereco_id": 1}
        self.client.post("/api/checkout", json=payload, name="/api/checkout")

class RampaDeTeste(LoadTestShape):
    stages = [
        {"duration": 300, "users": 250, "spawn_rate": 5},
        {"duration": 600, "users": 500, "spawn_rate": 5},
        {"duration": 900, "users": 750, "spawn_rate": 5},
        {"duration": 2700, "users": 1000, "spawn_rate": 5},
        {"duration": 3000, "users": 1200, "spawn_rate": 5},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None
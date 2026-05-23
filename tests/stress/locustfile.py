from locust import HttpUser, task, between, LoadTestShape

class CompradorEcommerce(HttpUser):
    # Simula o tempo que um usuário real leva lendo a tela antes de clicar
    wait_time = between(1, 3)

    def on_start(self):
        """
        Executado assim que o usuário virtual 'nasce'. 
        Ele faz o login para ganhar o token de acesso antes de comprar.
        """
        # Substitua '123456' pela senha real do usuário demo, se souber.
        credenciais = {
            "email": "aluno@uni7.edu.br",
            "password": "senha_demo" 
        }
        # Dispara o POST de login (ajuste a rota se o endpoint exato for diferente)
        self.client.post("/login", json=credenciais, name="/login")

    @task(2)
    def aceder_pagina_inicial(self):
        self.client.get("/")

    @task(4)
    def visualizar_produto(self):
        self.client.get("/produtos/1", name="/produtos/[id]")

    @task(2)
    def adicionar_ao_carrinho(self):
        payload = {"produto_id": 1, "quantidade": 1}
        self.client.post("/carrinho", json=payload, name="/carrinho")

    @task(1)
    def finalizar_compra(self):
        payload = {"metodo_pagamento": "cartao", "endereco_id": 1}
        self.client.post("/checkout", json=payload, name="/checkout")


class RampaDeTeste(LoadTestShape):
    stages = [
        {"duration": 300, "users": 250, "spawn_rate": 5},
        {"duration": 600, "users": 500, "spawn_rate": 5},
        {"duration": 900, "users": 750, "spawn_rate": 5},
        {"duration": 2700, "users": 1000, "spawn_rate": 5}, # Platô de 30 min
        {"duration": 3000, "users": 1200, "spawn_rate": 5},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None

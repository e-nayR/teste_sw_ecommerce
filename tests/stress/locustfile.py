from locust import HttpUser, task, between, LoadTestShape

class CompradorEcommerce(HttpUser):
    wait_time = between(1, 3)

    @task
    def aceder_pagina_inicial(self):
        self.client.get("/")

    @task(3)
    def visualizar_produto(self):
        self.client.get("/produtos/1", name="/produtos/[id]")

class RampaDeTeste(LoadTestShape):
    # Duração cumulativa e o spawn_rate ajustado para 5 usuários/s conforme o documento didático
    stages = [
        # Ronda 1: 250 utilizadores
        {"duration": 300, "users": 250, "spawn_rate": 5},
        
        # Ronda 2: 500 utilizadores
        {"duration": 600, "users": 500, "spawn_rate": 5},
        
        # Ronda 3: 750 utilizadores
        {"duration": 900, "users": 750, "spawn_rate": 5},
        
        # Ronda 4 (AVALIAÇÃO DE ESTABILIDADE): 1000 utilizadores mantidos em platô
        {"duration": 2700, "users": 1000, "spawn_rate": 5},
        
        # Ronda 5: Pico de 1200 utilizadores
        {"duration": 3000, "users": 1200, "spawn_rate": 5},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None
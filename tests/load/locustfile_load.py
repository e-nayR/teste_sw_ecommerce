from locust import HttpUser, task, between, LoadTestShape

class CompradorEcommerce(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """ Executado no início: Faz o login e guarda o token """
        # O SEGREDO FOI DESVENDADO: A API espera 'email' e 'senha' em português!
        credenciais = {
            "email": "aluno@uni7.edu.br",
            "senha": "teste123" 
        }
        
        # Como o erro indicava "body.senha", confirmamos que a API espera JSON mesmo (json=)
        resposta = self.client.post("/api/login", json=credenciais, name="/api/login")
        
        # Capturamos o token e injetamos na autorização das compras
        if resposta.status_code == 200:
            try:
                dados = resposta.json()
                if "access_token" in dados:
                    self.client.headers.update({"Authorization": f"Bearer {dados['access_token']}"})
            except ValueError:
                pass
        
        # 2. Envia como 'formulário' (data=) para evitar o erro 422
        resposta = self.client.post("/api/login", data=credenciais, name="/api/login")
        
        # 3. TRUQUE DE QA: Se a API devolver um token JSON, pegamos nele e forçamos no cabeçalho!
        if resposta.status_code == 200:
            try:
                dados = resposta.json()
                if "access_token" in dados:
                    token = dados["access_token"]
                    self.client.headers.update({"Authorization": f"Bearer {token}"})
            except ValueError:
                pass # Se não devolver JSON, significa que o Cookie funcionou.

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

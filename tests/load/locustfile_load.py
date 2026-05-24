from locust import HttpUser, task, between, LoadTestShape

class CompradorEcommerce(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """ Executado no início: Faz o login e guarda o token de autenticação """
        credenciais = {
            "email": "aluno@uni7.edu.br",
            "senha": "teste123"
        }
        # O argumento 'name' foi removido das rotas estáticas para evitar repetição
        res = self.client.post("/api/login", json=credenciais)
        
        if res.status_code == 200:
            body = res.json()
            self.token = body["access_token"]
            # Erro de sintaxe corrigido: removido o "=" depois de update
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
        else:
            print(f"Falha no login: {res.status_code}")

    @task(2)
    def ver_catalogo(self):
        self.client.get("/api/produtos")

    @task(4)
    def visualizar_produto(self):
        # Aqui o 'name' é mantido porque a URL é dinâmica (tem um ID que pode mudar)
        self.client.get("/api/produtos/1", name="/api/produtos/[id]")

    @task(2)
    def adicionar_ao_carrinho(self):
        payload = {"produto_id": 1, "quantidade": 1}
        self.client.post("/api/carrinho/itens", json=payload)

    @task(1)
    def finalizar_compra(self):
        # Payload corrigido conforme a documentação da sua API (evita o erro 422)
        payload = {"cartao": "1234-5678-9012-3456"}
        self.client.post("/api/checkout", data=payload)

class RampaDeTeste(LoadTestShape):
    # Isolamos a variável que se repetia em todas as linhas
    taxa_criacao = 5 
    
    stages = [
        {"duration": 300, "users": 250},
        {"duration": 600, "users": 500},
        {"duration": 900, "users": 750},
        {"duration": 2700, "users": 1000},
        {"duration": 3000, "users": 1200},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                # O script agora puxa a taxa global automaticamente
                return stage["users"], self.taxa_criacao 
        return None

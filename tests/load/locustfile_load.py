import random
from locust import HttpUser, task, between, events

class EcommerceLoadUser(HttpUser):
    """
    Simula o fluxo principal do usuário no e-commerce:
    Login -> Catálogo -> Ver Detalhes -> Adicionar ao Carrinho -> Checkout
    """
    wait_time = between(1, 3)
    
    def on_start(self):
        self.login()

    def login(self):
        """Realiza autenticação para obter acesso as rotas da API"""
        # Usando as credenciais demo padrão do sistema
        payload = {
            "email": "aluno@uni7.edu.br",
            "senha": "teste123"
        }
        with self.client.post("/api/login", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falha no login: {response.status_code}")

    @task(5)
    def navegar_e_comprar(self):
        """Fluxo principal de compra"""
        # 1. Catálogo de produtos
        with self.client.get("/api/produtos", name="/api/produtos") as response:
            if response.status_code == 200:
                produtos = response.json()
                # Passos que o usuário real realiza
                if produtos:
                    # 1. Seleciona um produto
                    produto_id = random.choice(produtos)['id']
                    
                    # 2. Ver detalhes do produto
                    self.client.get(f"/api/produtos/{produto_id}", name="/api/produtos/{id}")
                    
                    # 3. Adicionar ao carrinho
                    self.client.post("/api/carrinho/itens", json={
                        "produto_id": produto_id,
                        "quantidade": 1
                    }, name="/api/carrinho/itens")
                    
                    # 4. Ver carrinho e total
                    self.client.get("/api/carrinho", name="/api/carrinho")
                    self.client.get("/api/carrinho/total", name="/api/carrinho/total")
                    
                    # 5. Checkout (realiza pagamento)
                    self.client.post("/api/checkout", json={
                        "cartao": "1234-5678-9012-3456",
                        "desconto_percentual": 0
                    }, name="/api/checkout")

    @task(1)
    def consultar_meus_pedidos(self):
        """Simula o usuário verificando o histórico"""
        self.client.get("/api/pedidos", name="/api/pedidos")

    @task(2)
    def apenas_navegar(self):
        """Simula o usuário apenas olhando produtos sem comprar"""
        self.client.get("/api/produtos", name="/api/produtos")
        self.client.get("/api/health", name="/api/health")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("--- Iniciando Teste de Carga ---")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("--- Teste de Carga Finalizado ---")

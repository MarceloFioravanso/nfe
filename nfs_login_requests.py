import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re

# Carrega variáveis do arquivo .env
load_dotenv(dotenv_path=".env")

# Obtém as credenciais do arquivo .env
NFS_URL = os.getenv("NFS_URL")
CPF_CNPJ = os.getenv("CPF_CNPJ")
SENHA = os.getenv("SENHA")

def main():
    # Cria uma sessão para manter cookies entre requisições
    session = requests.Session()
    
    # Headers para simular um navegador
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    # Adiciona os headers à sessão
    session.headers.update(headers)
    
    try:
        print(f"Acessando {NFS_URL}...")
        
        # Primeiro acesso para obter cookies e possíveis tokens CSRF
        response = session.get(NFS_URL)
        if response.status_code != 200:
            print(f"Erro ao acessar a página: {response.status_code}")
            return
        
        # Fazer parse do HTML para extrair possíveis tokens/campos ocultos
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mostra o título da página acessada
        page_title = soup.title.text if soup.title else "Título não encontrado"
        print(f"Página acessada: {page_title}")
        
        # Procurar o formulário de login usando os seletores corretos
        # Primeiro procura elementos de login específicos identificados
        cpf_input = soup.find('input', {"name": "login_usuario", "class": re.compile(".*campo-texto.*")})
        senha_input = soup.find('input', {"name": "senha_usuario", "type": "password"})
        login_btn = soup.find('button', {"class": "btn-login"})
        
        if cpf_input and senha_input and login_btn:
            print("Elementos de formulário encontrados individualmente")
            # Encontrar o formulário pai
            form = cpf_input.find_parent('form')
            if not form:
                print("Formulário pai não encontrado, tentando outros métodos...")
                form = soup.find('form')
        else:
            # Fallback para o método antigo
            print("Não foi possível encontrar elementos específicos, tentando localizar o formulário...")
            form = soup.find('form', id='formLogin') or soup.find('form', {'action': True, 'method': True})
            
        if not form:
            print("Formulário de login não encontrado. Estrutura do site pode ter mudado.")
            return
        
        # Extract form action and method
        form_action = form.get('action', '')
        form_method = form.get('method', 'post').lower()
        
        # Verificar se o action é uma URL completa
        if form_action and not form_action.startswith('http'):
            # Se não for URL completa, concatenar com base URL
            base_url = '/'.join(NFS_URL.split('/')[:3])  # http(s)://dominio.com
            form_action = f"{base_url}{'' if form_action.startswith('/') else '/'}{form_action}"
        
        # Se não tiver action, usar a URL atual
        form_action = form_action or response.url
        
        print(f"Formulário encontrado: action={form_action}, method={form_method}")
        
        # Encontrar todos os campos ocultos que devem ser enviados
        hidden_inputs = {}
        for hidden in form.find_all("input", type="hidden"):
            if hidden.has_attr('name') and hidden.has_attr('value'):
                hidden_inputs[hidden['name']] = hidden['value']
                
        # Preparar dados para login usando os nomes corretos dos campos
        login_data = {
            **hidden_inputs,  # Incluir campos ocultos
            'login_usuario': CPF_CNPJ,  # Nome correto do campo de CPF/CNPJ
            'senha_usuario': SENHA,     # Nome correto do campo de senha
        }
        
        print("Realizando login...")
        
        # Enviar requisição de login
        if form_method == 'post':
            response = session.post(form_action, data=login_data)
        else:
            response = session.get(form_action, params=login_data)
        
        # Verificar se o login foi bem-sucedido
        if response.status_code != 200:
            print(f"Erro na requisição de login: {response.status_code}")
            return
            
        # Verificar se realmente foi redirecionado para área logada
        soup = BeautifulSoup(response.text, 'html.parser')
        page_title = soup.title.text if soup.title else "Título não encontrado"
        
        # Verificação simplificada - adapte conforme o site
        if "login" in response.url.lower() or "login" in page_title.lower():
            print("Falha no login. Verifique suas credenciais.")
        else:
            print(f"Login bem-sucedido! Página atual: {page_title}")
            print(f"URL após login: {response.url}")
            
            # Aqui você pode continuar com outras operações após o login
            # Por exemplo, acessar uma página específica, enviar formulários, etc.
        
    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")
    finally:
        # Encerra a sessão
        session.close()
        print("Sessão encerrada.")

if __name__ == "__main__":
    main()
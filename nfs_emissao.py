import os
import time
import base64
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import ElementNotInteractableException
import re

# Carrega .env
load_dotenv(dotenv_path=".env")

NFS_URL = os.getenv("NFS_URL")
CPF_CNPJ = os.getenv("CPF_CNPJ")
SENHA = os.getenv("SENHA")

# Configura o salvamento de arquivos HTML (True para salvar, False para desabilitar)
SALVAR_HTML = False

def resolver_captcha_clicavel(driver, wait):
    """
    Função para lidar com CAPTCHA que exige cliques em elementos específicos.
    Permite que o usuário informe as coordenadas para clicar.
    """
    print("\n" + "*"*50)
    print("CAPTCHA DE CLIQUE DETECTADO!")
    print("Este tipo de CAPTCHA requer que você clique em elementos específicos.")
    print("O script irá salvar uma screenshot para você identificar onde deve clicar.")
    print("*"*50 + "\n")
    
    # Salvar screenshot para visualização
    driver.save_screenshot("captcha_page.png")
    print(f"Screenshot da página com CAPTCHA salvo em {os.path.abspath('captcha_page.png')}")
    
    # Obter dimensões da viewport
    viewport_width = driver.execute_script("return window.innerWidth")
    viewport_height = driver.execute_script("return window.innerHeight")
    print(f"Dimensões da viewport: {viewport_width}x{viewport_height}")
    
    print("\nPara resolver este CAPTCHA, você tem as seguintes opções:")
    print("1. Informar as coordenadas x,y para clicar (separadas por vírgula, múltiplos cliques separados por espaço)")
    print("   Exemplo: 100,150 200,300 - isso irá clicar em (x=100,y=150) e depois em (x=200,y=300)")
    print("2. Informar um seletor CSS para o elemento a ser clicado")
    print("   Exemplo: #recaptcha-anchor")
    print("3. Digitar 'skip' para ignorar o CAPTCHA e tentar continuar")
    
    user_input = input("\nDigite as coordenadas, seletor CSS ou 'skip': ")
    
    if user_input.lower() == 'skip':
        print("Ignorando CAPTCHA por solicitação do usuário")
        return False
    
    # Verificar se o input parece coordenadas
    coord_pattern = re.compile(r'^\d+,\d+( \d+,\d+)*$')
    if coord_pattern.match(user_input):
        # Input são coordenadas x,y
        print("Detectadas coordenadas para clique.")
        coord_pairs = user_input.split()
        
        for coord_pair in coord_pairs:
            x, y = map(int, coord_pair.split(','))
            print(f"Clicando na posição: x={x}, y={y}")
            
            try:
                # Clique via JavaScript nas coordenadas especificadas
                driver.execute_script(f"document.elementFromPoint({x}, {y}).click();")
                print(f"Clique executado na posição ({x},{y})")
                time.sleep(1)  # Pequena pausa entre cliques
            except Exception as e:
                print(f"Erro ao clicar na posição ({x},{y}): {e}")
    else:
        # Assumimos que o input é um seletor CSS
        print(f"Tentando localizar elemento com seletor: {user_input}")
        try:
            element = driver.find_element(By.CSS_SELECTOR, user_input)
            print("Elemento encontrado! Tentando clicar...")
            element.click()
            print("Clique executado no elemento.")
        except Exception as e:
            print(f"Erro ao localizar ou clicar no elemento: {e}")
            return False
    
    # Aguardar um pouco para ver o resultado do clique
    time.sleep(3)
    
    # Salvar screenshot após o clique
    driver.save_screenshot("apos_clique_captcha.png")
    print(f"Screenshot após clique salvo em {os.path.abspath('apos_clique_captcha.png')}")
    
    print("\nVerificando se o CAPTCHA foi resolvido...")
    
    # Verifica se ainda há elementos de CAPTCHA visíveis
    captcha_ainda_presente = detect_captcha(driver)
    
    if captcha_ainda_presente:
        print("O CAPTCHA ainda parece estar presente. Deseja tentar um novo clique?")
        retry = input("Digite 'sim' para tentar novamente, ou qualquer outra coisa para continuar: ")
        
        if retry.lower() == 'sim':
            return resolver_captcha_clicavel(driver, wait)
    else:
        print("CAPTCHA parece ter sido resolvido com sucesso!")
    
    return True


def detect_captcha(driver):
    """Detecta se há elementos de CAPTCHA na página"""
    captcha_detected = False
    
    # Procura por textos relacionados
    captcha_texts = ["captcha", "verificação", "não sou um robô", "recaptcha", "robot"]
    for text in captcha_texts:
        elements = driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]")
        if elements:
            captcha_detected = True
            break
    
    # Procura por iframes do reCAPTCHA
    recaptcha_frames = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'], iframe[title*='recaptcha'], iframe[title*='CAPTCHA']")
    if recaptcha_frames:
        captcha_detected = True
    
    # Procura por imagens ou elementos específicos de CAPTCHA
    captcha_elements = driver.find_elements(By.CSS_SELECTOR, "[id*='captcha'], [class*='captcha'], [id*='recaptcha'], [class*='recaptcha']")
    if captcha_elements:
        captcha_detected = True
    
    return captcha_detected


def detectar_e_clicar_recaptcha(driver, wait):
    """
    Função específica para detectar e clicar na caixa de verificação 'Não sou um robô' do reCAPTCHA.
    """
    print("\n" + "*"*50)
    print("CAPTCHA reCAPTCHA DETECTADO!")
    print("Tentando resolver o checkbox 'Não sou um robô'...")
    print("*"*50 + "\n")
    
    # Salvar screenshot para visualização
    driver.save_screenshot("captcha_page.png")
    print(f"Screenshot da página com reCAPTCHA salvo em {os.path.abspath('captcha_page.png')}")
    
    # Tenta localizar o frame do reCAPTCHA primeiro, pois geralmente está em um iframe
    recaptcha_frames = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'], iframe[title*='reCAPTCHA'], iframe[name^='a-']")
    
    found_checkbox = False
    
    # Se encontrar frames, tenta mudar para eles e localizar o checkbox
    if (recaptcha_frames):
        print(f"Encontrou {len(recaptcha_frames)} possíveis frames de reCAPTCHA")
        
        for i, frame in enumerate(recaptcha_frames):
            try:
                print(f"Tentando frame {i+1}...")
                driver.switch_to.frame(frame)
                
                # Usa diferentes seletores para localizar a caixa de verificação
                recaptcha_checkbox = None
                
                # Método 1: Usando o ID específico
                try:
                    recaptcha_checkbox = driver.find_element(By.ID, "recaptcha-anchor")
                    print("Checkbox encontrado pelo ID 'recaptcha-anchor'")
                except:
                    print("Não encontrado pelo ID, tentando outros seletores...")
                
                # Método 2: Usando o papel e classe
                if not recaptcha_checkbox:
                    try:
                        recaptcha_checkbox = driver.find_element(
                            By.CSS_SELECTOR, ".recaptcha-checkbox[role='checkbox']"
                        )
                        print("Checkbox encontrado pelo seletor de classe e papel")
                    except:
                        print("Não encontrado pela classe e papel, tentando outro seletor...")
                
                # Método 3: Usando XPath mais genérico
                if not recaptcha_checkbox:
                    try:
                        recaptcha_checkbox = driver.find_element(
                            By.XPATH, "//*[@role='checkbox']"
                        )
                        print("Checkbox encontrado pelo papel 'checkbox'")
                    except:
                        print("Não encontrado pelo papel, tentando seletor final...")
                
                # Método 4: Qualquer elemento clicável no frame
                if not recaptcha_checkbox:
                    try:
                        recaptcha_checkbox = driver.find_element(
                            By.CSS_SELECTOR, ".recaptcha-checkbox, [role='checkbox'], div[tabindex='0']"
                        )
                        print("Checkbox encontrado por seletor genérico")
                    except:
                        print(f"Nenhum checkbox encontrado no frame {i+1}")
                
                # Se encontrou o checkbox, tenta clicar
                if recaptcha_checkbox:
                    # Verifica se já está marcado
                    is_checked = recaptcha_checkbox.get_attribute("aria-checked")
                    if is_checked == "true":
                        print("Checkbox já está marcado!")
                        found_checkbox = True
                        break
                    
                    try:
                        # Pausa para garantir que o elemento está pronto
                        time.sleep(1)
                        print("Tentando clicar no checkbox...")
                        recaptcha_checkbox.click()
                        print("Clique no checkbox realizado!")
                        found_checkbox = True
                        
                        # Espera para ver se o CAPTCHA foi aceito
                        time.sleep(3)
                        
                        # Verifica se foi marcado com sucesso
                        try:
                            is_checked = recaptcha_checkbox.get_attribute("aria-checked")
                            if is_checked == "true":
                                print("Checkbox foi marcado com sucesso!")
                            else:
                                print("Checkbox não foi marcado, pode ser necessário resolver um desafio adicional.")
                        except:
                            print("Não foi possível verificar o estado do checkbox após o clique.")
                        
                        break
                    except Exception as click_error:
                        print(f"Erro ao clicar no checkbox: {click_error}")
                        # Tenta com JavaScript
                        try:
                            driver.execute_script("arguments[0].click();", recaptcha_checkbox)
                            print("Clique via JavaScript realizado!")
                            found_checkbox = True
                            time.sleep(3)
                            break
                        except Exception as js_error:
                            print(f"Erro ao clicar via JavaScript: {js_error}")
                
                # Volta ao contexto principal antes de tentar outro frame
                driver.switch_to.default_content()
            except Exception as frame_error:
                print(f"Erro ao processar frame {i+1}: {frame_error}")
                # Volta ao contexto principal antes de tentar outro frame
                driver.switch_to.default_content()
    
    # Se não encontrou nos frames ou não havia frames, tenta no documento principal
    if not found_checkbox:
        print("Tentando localizar o checkbox no documento principal...")
        try:
            recaptcha_checkbox = driver.find_element(By.CSS_SELECTOR, "#recaptcha-anchor, .recaptcha-checkbox[role='checkbox']")
            recaptcha_checkbox.click()
            print("Checkbox encontrado e clicado no documento principal!")
            found_checkbox = True
        except:
            print("Não foi possível encontrar o checkbox no documento principal.")
    
    # Se encontramos e clicamos no checkbox, verifica se há desafios adicionais
    if found_checkbox:
        # Volta ao contexto principal para verificar
        driver.switch_to.default_content()
        time.sleep(3)  # Aguarda para ver se aparece um desafio
        
        # Salva screenshot após interagir com o reCAPTCHA
        driver.save_screenshot("apos_recaptcha_checkbox.png")
        print(f"Screenshot após interação salvo em {os.path.abspath('apos_recaptcha_checkbox.png')}")
        
        # Verifica se há um frame de desafio (selecionar imagens)
        challenge_frames = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'][title*='challenge'], iframe[title*='desafio']")
        if challenge_frames:
            print("ATENÇÃO: Detectado desafio adicional de reCAPTCHA (selecionar imagens).")
            print("Este tipo de desafio requer intervenção manual.")
            return resolver_captcha_clicavel(driver, wait)  # Usa a função para CAPTCHA de clique
        
        return True
    
    # Se chegou aqui, não conseguimos resolver automaticamente
    print("Não foi possível resolver o reCAPTCHA automaticamente.")
    print("Tentando método manual...")
    return resolver_captcha_clicavel(driver, wait)  # Cai no método manual


def detect_and_handle_captcha(driver, wait):
    """
    Detecta e trata o CAPTCHA, incluindo o tipo específico reCAPTCHA.
    """
    # Primeiro verifica se é um reCAPTCHA (a caixa de seleção "Não sou um robô")
    recaptcha_present = False
    
    # Verifica por elementos específicos de reCAPTCHA
    try:
        # Busca por iframes de reCAPTCHA
        recaptcha_frames = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'], iframe[title*='reCAPTCHA'], iframe[name^='a-']")
        if recaptcha_frames:
            recaptcha_present = True
            print("reCAPTCHA detectado (iframe encontrado).")
    except:
        pass
    
    # Busca por texto "reCAPTCHA"
    if not recaptcha_present:
        try:
            recaptcha_text = driver.find_elements(By.XPATH, "//*[contains(text(), 'reCAPTCHA') or contains(text(), 'não sou um robô')]")
            if recaptcha_text:
                recaptcha_present = True
                print("reCAPTCHA detectado (texto encontrado).")
        except:
            pass
    
    # Se for reCAPTCHA, usa função específica
    if recaptcha_present:
        return detectar_e_clicar_recaptcha(driver, wait)
    
    # Caso contrário, verifica por outros tipos de CAPTCHA
    captcha_detected = detect_captcha(driver)
    
    # Se CAPTCHA for detectado, tenta resolver
    if captcha_detected:
        print("CAPTCHA genérico detectado.")
        return resolver_captcha_clicavel(driver, wait)
    
    return False  # Não detectou CAPTCHA


def main():
    print("Iniciando configuração do Chrome...")
    
    # Configurações do Chrome
    chrome_opts = Options()
    
    # Para facilitar o debug inicial, mantenha o modo headless comentado
    # e descomente apenas após confirmar que tudo está funcionando
    chrome_opts.add_argument("--headless=new")
    
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    print("Iniciando o navegador...")
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_opts)
        
        print(f"Acessando URL: {NFS_URL}")
        driver.get(NFS_URL)
        
        # Debug: salva screenshot para verificar o que está sendo carregado
        driver.save_screenshot("/tmp/pagina_inicial.png")
        print(f"Screenshot salvo em /tmp/pagina_inicial.png")
        
        # Debug: mostra o título e URL atual
        print(f"Título da página: {driver.title}")
        print(f"URL atual: {driver.current_url}")
        
        # Para debug: salvar fonte HTML da página (se habilitado)
        if SALVAR_HTML:
            with open("/tmp/pagina_html.txt", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("HTML da página salvo em /tmp/pagina_html.txt")
        
        # Aguarda o formulário de login estar visível
        wait = WebDriverWait(driver, 20)
        
        # Agora usamos os seletores exatos obtidos da página
        print("Localizando elementos usando seletores exatos...")
        
        # Localizando por nome e classe (seletores mais precisos)
        try:
            cpf_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='login_usuario'][class*='campo-texto']")
            ))
            senha_input = driver.find_element(
                By.CSS_SELECTOR, "input[name='senha_usuario'][type='password']"
            )
            login_btn = driver.find_element(
                By.CSS_SELECTOR, "button.btn-login"
            )
            
            print("Elementos encontrados com seletores exatos!")
            
            # Aguardar até que os elementos estejam interagíveis
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='login_usuario']")))
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='senha_usuario']")))
            
            print("Preenchendo os campos com credenciais...")
            
            # Tentar métodos diferentes de preenchimento
            try:
                # Primeiro limpa os campos
                cpf_input.clear()
                senha_input.clear()
                
                # Preenche os campos
                cpf_input.send_keys(CPF_CNPJ)
                senha_input.send_keys(SENHA)
                
                driver.save_screenshot("/tmp/antes_login.png")
                print("Screenshot antes do login salvo em /tmp/antes_login.png")
                
                print("Clicando no botão de login...")
                login_btn.click()
                
            except Exception as e:
                print(f"Erro ao interagir com elementos: {e}")
                print("Tentando com JavaScript...")
                
                driver.execute_script(f"document.querySelector('input[name=\"login_usuario\"]').value = '{CPF_CNPJ}';")
                driver.execute_script(f"document.querySelector('input[name=\"senha_usuario\"]').value = '{SENHA}';")
                driver.execute_script("document.querySelector('button.btn-login').click();")
            
            # Aguarda pela mudança de URL ou por um elemento que indica login bem-sucedido
            try:
                wait.until(lambda d: d.current_url != NFS_URL)
                print("URL mudou após o login!")
            except:
                print("URL não mudou, verificando por outros indicadores de login...")
            
            # Tira screenshot depois do login
            time.sleep(5)  # Pausa maior para garantir que tudo carregou
            driver.save_screenshot("/tmp/apos_login.png")
            print(f"Screenshot após o login salvo em /tmp/apos_login.png")
            
            # Verifica se há qualquer mensagem de erro na página
            try:
                error_msgs = driver.find_elements(By.XPATH, "//*[contains(text(), 'incorreto') or contains(text(), 'inválido') or contains(text(), 'erro')]")
                if error_msgs:
                    print("Possíveis mensagens de erro encontradas:")
                    for msg in error_msgs[:3]:  # Mostra apenas as 3 primeiras
                        print(f"- {msg.text}")
            except:
                pass
            
            # Mostra informações atuais
            print(f"URL após tentativa de login: {driver.current_url}")
            print(f"Título após tentativa de login: {driver.title}")
            
            # Verifica se o login foi bem-sucedido
            if "login" in driver.current_url.lower():
                print("Falha no login - ainda estamos na página de login")
            else:
                print("Login parece ter sido bem-sucedido!")
                # Salva o HTML da página após login para análise (se habilitado)
                if SALVAR_HTML:
                    with open("/tmp/pagina_apos_login.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print("HTML da página após login salvo em /tmp/pagina_apos_login.html")
                
                # Aguarda e clica no botão "Acessar" após o login
                try:
                    print("Procurando o botão 'Acessar' após o login...")
                    # Tenta encontrar o botão de acesso fiscal por diferentes métodos
                    acesso_fiscal_btn = None
                    
                    # Método 1: Busca pelo seletor CSS específico
                    try:
                        acesso_fiscal_btn = wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "a.link_acesso_fiscal")
                        ))
                        print("Botão 'Acessar' encontrado pelo seletor CSS")
                    except:
                        print("Não encontrado pela classe, tentando outra estratégia...")
                    
                    # Método 2: Busca por XPath procurando pelo texto
                    if not acesso_fiscal_btn:
                        try:
                            acesso_fiscal_btn = driver.find_element(
                                By.XPATH, "//a[contains(text(), 'Acessar') and contains(@class, 'botao_cor_tema')]"
                            )
                            print("Botão 'Acessar' encontrado pelo texto e classe")
                        except:
                            print("Não encontrado pelo texto e classe, tentando outra estratégia...")
                    
                    # Método 3: Busca por JavaScript onclick
                    if not acesso_fiscal_btn:
                        try:
                            acesso_fiscal_btn = driver.find_element(
                                By.XPATH, "//a[contains(@onclick, 'onClickAcessoFiscal')]"
                            )
                            print("Botão 'Acessar' encontrado pela função onclick")
                        except:
                            print("Não encontrado pela função onclick, tentando outras estratégias...")
                    
                    # Método 4: Busca por qualquer link com 'Acessar'
                    if not acesso_fiscal_btn:
                        try:
                            acesso_fiscal_btn = driver.find_element(
                                By.XPATH, "//a[contains(text(), 'Acessar')]"
                            )
                            print("Botão 'Acessar' encontrado pelo texto genérico")
                        except:
                            print("Não foi possível encontrar o botão 'Acessar' por nenhum método")
                    
                    # Se encontrou o botão, tenta clicar
                    if acesso_fiscal_btn:
                        print("Tentando clicar no botão 'Acessar'...")
                        driver.save_screenshot("/tmp/antes_acesso_fiscal.png")
                        
                        try:
                            # Método 1: Clique direto
                            acesso_fiscal_btn.click()
                            print("Clique no botão 'Acessar' realizado com sucesso")
                        except Exception as e:
                            print(f"Erro ao clicar diretamente: {e}")
                            
                            # Método 2: Clique via JavaScript
                            try:
                                print("Tentando clicar via JavaScript...")
                                driver.execute_script("arguments[0].click();", acesso_fiscal_btn)
                                print("Clique via JavaScript realizado")
                            except Exception as js_e:
                                print(f"Erro ao clicar via JavaScript: {js_e}")
                                
                                # Método 3: Executar a função onclick diretamente
                                try:
                                    print("Tentando executar a função onclick diretamente...")
                                    driver.execute_script("WGFViewManutencaoAcessoFiscalAtendePortal.onClickAcessoFiscal()")
                                    print("Função onclick executada diretamente")
                                except Exception as fn_e:
                                    print(f"Erro ao executar a função onclick: {fn_e}")
                        
                        # Aguarda a página carregar após o clique
                        time.sleep(3)
                        
                        # NOVO: Tira screenshot imediatamente após clicar no botão Acessar
                        print("Tirando screenshot imediatamente após clicar em 'Acessar'...")
                        driver.save_screenshot("/tmp/imediatamente_apos_acessar.png")
                        print(f"Screenshot salvo em /tmp/imediatamente_apos_acessar.png")
                        print(f"URL imediatamente após clicar: {driver.current_url}")
                        print(f"Título da página: {driver.title}")
                        
                        # Aguarda um pouco mais para garantir que a página termine de carregar
                        time.sleep(5)
                        driver.save_screenshot("/tmp/apos_acesso_fiscal.png")
                        print(f"Screenshot adicional após 5 segundos: /tmp/apos_acesso_fiscal.png")
                        print(f"URL após aguardar mais 5s: {driver.current_url}")
                        print(f"Título após aguardar mais 5s: {driver.title}")
                        
                        # Verifica e lida com CAPTCHA após clicar no botão "Acessar"
                        print("Verificando se existe CAPTCHA na página...")
                        captcha_handled = detect_and_handle_captcha(driver, wait)
                        
                        if captcha_handled:
                            print("CAPTCHA tratado, continuando navegação...")
                            # Salva screenshot após tratar o CAPTCHA
                            driver.save_screenshot("/tmp/apos_captcha.png")
                            print(f"URL após tratar CAPTCHA: {driver.current_url}")
                            print(f"Título após tratar CAPTCHA: {driver.title}")
                            
                            # Espera adicional após resolver o CAPTCHA
                            time.sleep(5)
                            print("Continuando após espera pós-CAPTCHA...")
                            driver.save_screenshot("/tmp/continuando_apos_captcha.png")
                            
                            # Prosseguir com a automação após o CAPTCHA
                            print("Verificando se chegamos na página principal após o CAPTCHA...")
                            # Você pode adicionar aqui a navegação para emissão de NF após o CAPTCHA
                            # Por exemplo, procurar e clicar em um botão "Emitir Nota Fiscal"
                            
                        else:
                            print("Nenhum CAPTCHA detectado ou não foi possível tratá-lo.")
                        
                    else:
                        print("AVISO: Botão 'Acessar' não encontrado na página após login!")
                
                except Exception as btn_e:
                    print(f"Erro ao interagir com o botão 'Acessar': {btn_e}")
                
        except Exception as e:
            print(f"Erro ao localizar elementos com seletores exatos: {e}")
            # Voltar para as estratégias alternativas anteriores
            login_strategies = [
                # Estratégia 1: seletores básicos pelo ID
                {"cpf": (By.ID, "login_usuario"), "senha": (By.ID, "senha_usuario"), "botao": (By.ID, "btnLogin")},
                # Estratégia 2: XPath genérico para campos de login/senha
                {
                    "cpf": (By.XPATH, "//input[@type='text' and (contains(@id, 'login') or contains(@name, 'login') or contains(@id, 'cpf') or contains(@name, 'cpf'))]"),
                    "senha": (By.XPATH, "//input[@type='password']"),
                    "botao": (By.XPATH, "//button[contains(@id, 'login') or contains(@id, 'btn') or contains(text(), 'Entrar')]")
                },
                # Estratégia 3: CSS selectors mais genéricos
                {
                    "cpf": (By.CSS_SELECTOR, "input[type='text']"),
                    "senha": (By.CSS_SELECTOR, "input[type='password']"),
                    "botao": (By.CSS_SELECTOR, "button, input[type='submit']")
                }
            ]
            
            cpf_input = None
            senha_input = None
            login_btn = None
            
            for i, strategy in enumerate(login_strategies):
                try:
                    print(f"Tentando estratégia {i+1} para encontrar elementos...")
                    cpf_input = wait.until(EC.presence_of_element_located(strategy["cpf"]))
                    senha_input = driver.find_element(*strategy["senha"])
                    login_btn = driver.find_element(*strategy["botao"])
                    print(f"Elementos encontrados com estratégia {i+1}!")
                    break
                except Exception as e:
                    print(f"Estratégia {i+1} falhou: {e}")
                    continue
            
            if not all([cpf_input, senha_input, login_btn]):
                raise Exception("Não foi possível encontrar todos os elementos necessários para login")
            
            print("Elementos de login encontrados:")
            print(f"CPF/CNPJ input: {cpf_input.get_attribute('outerHTML')}")
            print(f"Senha input: {senha_input.get_attribute('outerHTML')}")
            print(f"Botão login: {login_btn.get_attribute('outerHTML')}")
            
            # Aguarda até que os elementos sejam interagíveis
            wait.until(EC.element_to_be_clickable(strategy["cpf"]))
            wait.until(EC.element_to_be_clickable(strategy["senha"]))
            
            print("Preenchendo os campos com credenciais...")
            
            # MÉTODO 1: Tentativa padrão com clear/sendkeys
            try:
                cpf_input.clear()
                cpf_input.send_keys(CPF_CNPJ)
                senha_input.clear()
                senha_input.send_keys(SENHA)
            except ElementNotInteractableException:
                # MÉTODO 2: Se falhar, usa JavaScript para preencher os campos
                print("Usando JavaScript para preencher os campos...")
                driver.execute_script(f"arguments[0].value = '{CPF_CNPJ}';", cpf_input)
                driver.execute_script(f"arguments[0].value = '{SENHA}';", senha_input)
            
            driver.save_screenshot("/tmp/antes_login.png")
            print("Screenshot antes do login salvo em /tmp/antes_login.png")
            
            # Tenta clicar no botão de login com diferentes métodos
            try:
                # MÉTODO 1: Clique padrão
                print("Tentando clicar no botão de login...")
                login_btn.click()
            except ElementNotInteractableException:
                try:
                    # MÉTODO 2: Clique com JavaScript
                    print("Usando JavaScript para clicar no botão...")
                    driver.execute_script("arguments[0].click();", login_btn)
                except Exception as js_error:
                    print(f"Erro ao usar JavaScript para clicar: {js_error}")
                    
                    # MÉTODO 3: Envio do formulário
                    print("Tentando enviar o formulário diretamente...")
                    form = driver.find_element(By.TAG_NAME, "form")
                    form.submit()
            
            # Aguarda pela mudança de URL ou por um elemento que indica login bem-sucedido
            try:
                wait.until(lambda d: d.current_url != NFS_URL)
                print("URL mudou após o login!")
            except:
                print("URL não mudou, verificando por outros indicadores de login...")
            
            # Tira screenshot depois do login
            time.sleep(5)  # Pausa maior para garantir que tudo carregou
            driver.save_screenshot("/tmp/apos_login.png")
            print(f"Screenshot após o login salvo em /tmp/apos_login.png")
            
            # Verifica se há qualquer mensagem de erro na página
            try:
                error_msgs = driver.find_elements(By.XPATH, "//*[contains(text(), 'incorreto') or contains(text(), 'inválido') or contains(text(), 'erro')]")
                if error_msgs:
                    print("Possíveis mensagens de erro encontradas:")
                    for msg in error_msgs[:3]:  # Mostra apenas as 3 primeiras
                        print(f"- {msg.text}")
            except:
                pass
            
            # Mostra informações atuais
            print(f"URL após tentativa de login: {driver.current_url}")
            print(f"Título após tentativa de login: {driver.title}")
            
            # Verifica se o login foi bem-sucedido
            if "login" in driver.current_url.lower():
                print("Falha no login - ainda estamos na página de login")
            else:
                print("Login parece ter sido bem-sucedido!")
                # Salva o HTML da página após login para análise (se habilitado)
                if SALVAR_HTML:
                    with open("/tmp/pagina_apos_login.html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print("HTML da página após login salvo em /tmp/pagina_apos_login.html")
                
                # Aguarda e clica no botão "Acessar" após o login
                try:
                    print("Procurando o botão 'Acessar' após o login...")
                    # Tenta encontrar o botão de acesso fiscal por diferentes métodos
                    acesso_fiscal_btn = None
                    
                    # Método 1: Busca pelo seletor CSS específico
                    try:
                        acesso_fiscal_btn = wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "a.link_acesso_fiscal")
                        ))
                        print("Botão 'Acessar' encontrado pelo seletor CSS")
                    except:
                        print("Não encontrado pela classe, tentando outra estratégia...")
                    
                    # Método 2: Busca por XPath procurando pelo texto
                    if not acesso_fiscal_btn:
                        try:
                            acesso_fiscal_btn = driver.find_element(
                                By.XPATH, "//a[contains(text(), 'Acessar') and contains(@class, 'botao_cor_tema')]"
                            )
                            print("Botão 'Acessar' encontrado pelo texto e classe")
                        except:
                            print("Não encontrado pelo texto e classe, tentando outra estratégia...")
                    
                    # Método 3: Busca por JavaScript onclick
                    if not acesso_fiscal_btn:
                        try:
                            acesso_fiscal_btn = driver.find_element(
                                By.XPATH, "//a[contains(@onclick, 'onClickAcessoFiscal')]"
                            )
                            print("Botão 'Acessar' encontrado pela função onclick")
                        except:
                            print("Não encontrado pela função onclick, tentando outras estratégias...")
                    
                    # Método 4: Busca por qualquer link com 'Acessar'
                    if not acesso_fiscal_btn:
                        try:
                            acesso_fiscal_btn = driver.find_element(
                                By.XPATH, "//a[contains(text(), 'Acessar')]"
                            )
                            print("Botão 'Acessar' encontrado pelo texto genérico")
                        except:
                            print("Não foi possível encontrar o botão 'Acessar' por nenhum método")
                    
                    # Se encontrou o botão, tenta clicar
                    if acesso_fiscal_btn:
                        print("Tentando clicar no botão 'Acessar'...")
                        driver.save_screenshot("/tmp/antes_acesso_fiscal.png")
                        
                        try:
                            # Método 1: Clique direto
                            acesso_fiscal_btn.click()
                            print("Clique no botão 'Acessar' realizado com sucesso")
                        except Exception as e:
                            print(f"Erro ao clicar diretamente: {e}")
                            
                            # Método 2: Clique via JavaScript
                            try:
                                print("Tentando clicar via JavaScript...")
                                driver.execute_script("arguments[0].click();", acesso_fiscal_btn)
                                print("Clique via JavaScript realizado")
                            except Exception as js_e:
                                print(f"Erro ao clicar via JavaScript: {js_e}")
                                
                                # Método 3: Executar a função onclick diretamente
                                try:
                                    print("Tentando executar a função onclick diretamente...")
                                    driver.execute_script("WGFViewManutencaoAcessoFiscalAtendePortal.onClickAcessoFiscal()")
                                    print("Função onclick executada diretamente")
                                except Exception as fn_e:
                                    print(f"Erro ao executar a função onclick: {fn_e}")
                        
                        # Aguarda a página carregar após o clique
                        time.sleep(3)
                        
                        # NOVO: Tira screenshot imediatamente após clicar no botão Acessar
                        print("Tirando screenshot imediatamente após clicar em 'Acessar'...")
                        driver.save_screenshot("/tmp/imediatamente_apos_acessar.png")
                        print(f"Screenshot salvo em /tmp/imediatamente_apos_acessar.png")
                        print(f"URL imediatamente após clicar: {driver.current_url}")
                        print(f"Título da página: {driver.title}")
                        
                        # Aguarda um pouco mais para garantir que a página termine de carregar
                        time.sleep(5)
                        driver.save_screenshot("/tmp/apos_acesso_fiscal.png")
                        print(f"Screenshot adicional após 5 segundos: /tmp/apos_acesso_fiscal.png")
                        print(f"URL após aguardar mais 5s: {driver.current_url}")
                        print(f"Título após aguardar mais 5s: {driver.title}")
                        
                        # Verifica e lida com CAPTCHA após clicar no botão "Acessar"
                        print("Verificando se existe CAPTCHA na página...")
                        captcha_handled = detect_and_handle_captcha(driver, wait)
                        
                        if captcha_handled:
                            print("CAPTCHA tratado, continuando navegação...")
                            # Salva screenshot após tratar o CAPTCHA
                            driver.save_screenshot("/tmp/apos_captcha.png")
                            print(f"URL após tratar CAPTCHA: {driver.current_url}")
                            print(f"Título após tratar CAPTCHA: {driver.title}")
                            
                            # Espera adicional após resolver o CAPTCHA
                            time.sleep(5)
                            print("Continuando após espera pós-CAPTCHA...")
                            driver.save_screenshot("/tmp/continuando_apos_captcha.png")
                            
                            # Prosseguir com a automação após o CAPTCHA
                            print("Verificando se chegamos na página principal após o CAPTCHA...")
                            # Você pode adicionar aqui a navegação para emissão de NF após o CAPTCHA
                            # Por exemplo, procurar e clicar em um botão "Emitir Nota Fiscal"
                            
                        else:
                            print("Nenhum CAPTCHA detectado ou não foi possível tratá-lo.")
                        
                    else:
                        print("AVISO: Botão 'Acessar' não encontrado na página após login!")
                
                except Exception as btn_e:
                    print(f"Erro ao interagir com o botão 'Acessar': {btn_e}")
                
    except Exception as e:
        print(f"Erro durante a automação: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()
            print("Navegador fechado.")

if __name__ == "__main__":
    main()
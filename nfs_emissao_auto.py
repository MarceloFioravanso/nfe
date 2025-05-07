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
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException, WebDriverException, NoSuchElementException
import chromedriver_autoinstaller
import re
import random
import logging
from datetime import datetime
import platform

# Configuração de log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=f'logs/nfse_emissao_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    filemode='w'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logger = logging.getLogger('NFSe_Automacao')

# Pasta para salvar os screenshots
SCREENSHOTS_FOLDER = "logs/imagens"
# Garante que a pasta existe
os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)

# Função para salvar screenshots na pasta correta
def salvar_screenshot(driver, nome_arquivo):
    """Salva um screenshot na pasta de imagens com o nome especificado"""
    caminho_completo = os.path.join(SCREENSHOTS_FOLDER, nome_arquivo)
    try:
        driver.save_screenshot(caminho_completo)
        logger.info(f"Screenshot salvo em {caminho_completo}")
    except Exception as e:
        logger.error(f"Erro ao salvar screenshot {nome_arquivo}: {e}")

# Instala automaticamente o ChromeDriver compatível
logger.info("Verificando e instalando ChromeDriver compatível...")
chromedriver_autoinstaller.install()

# Carrega .env
logger.info("Carregando variáveis de ambiente do arquivo .env...")
load_dotenv(dotenv_path=".env")

# Verifica se as variáveis foram carregadas corretamente
NFS_URL = os.getenv("NFS_URL", "https://nfse-cachoeirinha.atende.net/autoatendimento/servicos/nfse?redirected=1")
CPF_CNPJ = os.getenv("CPF_CNPJ")
SENHA = os.getenv("SENHA")
PAGINA_DESTINO = "https://nfse-cachoeirinha.atende.net/?rot=1&aca=1#!/sistema/66"

# Verifica se as variáveis estão definidas
if not NFS_URL:
    logger.error("ERRO: A variável NFS_URL não está definida no arquivo .env")
    logger.info("Por favor, crie ou edite o arquivo .env com o seguinte conteúdo:")
    logger.info("NFS_URL=https://nfse-cachoeirinha.atende.net/autoatendimento/servicos/nfse?redirected=1")
    logger.info("CPF_CNPJ=seu_cpf_ou_cnpj")
    logger.info("SENHA=sua_senha")
    exit(1)

if not CPF_CNPJ or not SENHA:
    logger.warning("AVISO: Credenciais (CPF_CNPJ e/ou SENHA) não definidas no arquivo .env")
    # Perguntar interativamente se não estiverem definidas
    if not CPF_CNPJ:
        CPF_CNPJ = input("Por favor, digite seu CPF ou CNPJ: ")
    if not SENHA:
        import getpass
        SENHA = getpass.getpass("Por favor, digite sua senha: ")

logger.info(f"URL configurada: {NFS_URL}")
logger.info(f"CPF/CNPJ configurado: {CPF_CNPJ[:4]}{'*' * (len(CPF_CNPJ) - 4) if len(CPF_CNPJ) > 4 else '*****'}")
logger.info(f"Senha configurada: {'*' * 8}")

# Configura o salvamento de arquivos HTML (True para salvar, False para desabilitar)
SALVAR_HTML = True

def salvar_html(driver, nome_arquivo):
    """Função auxiliar para salvar o HTML da página atual"""
    if SALVAR_HTML:
        try:
            with open(f"logs/html/{nome_arquivo}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.info(f"HTML da página salvo em logs/html/{nome_arquivo}.html")
        except Exception as e:
            logger.error(f"Erro ao salvar HTML: {e}")

def simular_digitacao_humana(elemento, texto):
    """Simula digitação humana inserindo caracteres um a um com tempos variáveis entre eles"""
    # Limpa o campo primeiro
    elemento.clear()
    
    # Velocidades de digitação variáveis
    for caractere in texto:
        elemento.send_keys(caractere)
        # Pequena pausa aleatória para simular digitação real
        time.sleep(random.uniform(0.05, 0.15))
    
    # Pausa final após completar a digitação
    time.sleep(random.uniform(0.2, 0.5))

def verificar_mensagens_erro(driver):
    """
    Verifica se há mensagens de erro na página e retorna uma lista com as mensagens encontradas.
    """
    mensagens = []
    
    # Padrões de texto que podem indicar erro
    padroes_erro = [
        "incorreto", "inválido", "erro", "falha", "não foi possível", 
        "credenciais", "não encontrado", "bloqueado", "expirado", "não autorizado"
    ]
    
    # Busca por elementos que contenham esses textos
    for padrao in padroes_erro:
        try:
            elementos = driver.find_elements(
                By.XPATH, 
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{padrao}')]"
            )
            for elem in elementos:
                try:
                    texto = elem.text.strip()
                    if texto and len(texto) > 3 and texto not in mensagens:
                        mensagens.append(texto)
                except:
                    pass
        except:
            continue
    
    # Busca por elementos de alerta/erro específicos
    seletores_erro = [
        ".alert", ".error", ".mensagem-erro", ".aviso", 
        "[class*='alert']", "[class*='error']", "[class*='erro']", 
        "[role='alert']", ".toast-error", ".toast-warning"
    ]
    
    for seletor in seletores_erro:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
            for elem in elementos:
                try:
                    texto = elem.text.strip()
                    if texto and len(texto) > 3 and texto not in mensagens:
                        mensagens.append(texto)
                except:
                    pass
        except:
            continue
    
    return mensagens

def verificar_login_sucesso(driver):
    """
    Verifica se o login foi bem-sucedido usando vários métodos.
    Retorna True se o login for bem-sucedido, False caso contrário.
    """
    # Método 1: Verificar se há elementos que indicam que estamos logados
    logger.info("Verificando se o login foi bem-sucedido...")
    
    elementos_pos_login = [
        "a.link_acesso_fiscal",  # Link específico após login
        "a[onclick*='onClickAcessoFiscal']",  # Botão com função específica
        ".menu-logado",  # Menu para usuário logado
        ".user-info",  # Informações do usuário
        ".logout",  # Botão de logout
        ".sair",  # Botão de sair
        "[title='Sair']",  # Elemento com título "Sair"
        "a[href*='logout']",  # Link para logout
        ".botao_cor_tema",  # Botão com tema colorido (geralmente disponível após login)
        ".area-logada"  # Área de usuário logado
    ]
    
    for seletor in elementos_pos_login:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
            if elementos:
                logger.info(f"Elemento de login bem-sucedido encontrado: {seletor}")
                return True
        except:
            continue
    
    # Método 2: Verificar pelo texto na página
    textos_pos_login = [
        "Bem-vindo", "Olá", "logado como", "minha conta", 
        "área do contribuinte", "serviços disponíveis", "acessar", "emitir nota"
    ]
    
    for texto in textos_pos_login:
        try:
            elementos = driver.find_elements(
                By.XPATH, 
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{texto}')]"
            )
            if elementos:
                logger.info(f"Texto indicativo de login bem-sucedido encontrado: '{texto}'")
                return True
        except:
            continue
    
    # Método 3: Verificar se há mensagens de erro
    mensagens_erro = verificar_mensagens_erro(driver)
    if mensagens_erro:
        logger.error("Mensagens de erro encontradas, login provavelmente falhou:")
        for msg in mensagens_erro:
            logger.error(f"- {msg}")
        return False
    
    # Se não encontrou elementos de sucesso nem elementos de erro, é inconclusivo
    logger.warning("Não foi possível determinar com certeza se o login foi bem-sucedido.")
    return False

def esperar_pagina_carregar(driver, timeout=30):
    """
    Aguarda a página carregar completamente usando diferentes técnicas
    """
    logger.info("Aguardando carregamento completo da página...")
    start_time = time.time()
    
    # Método 1: Aguardar document.readyState
    try:
        wait_curto = WebDriverWait(driver, min(timeout, 10))
        wait_curto.until(lambda d: d.execute_script('return document.readyState') == 'complete')
    except:
        logger.warning("Tempo esgotado aguardando document.readyState == 'complete'")
    
    # Método 2: Aguardar jQuery (se existir)
    try:
        jquery_present = driver.execute_script("return typeof jQuery !== 'undefined'")
        if jquery_present:
            wait_curto = WebDriverWait(driver, min(timeout, 5))
            wait_curto.until(lambda d: d.execute_script('return jQuery.active') == 0)
    except:
        logger.warning("Tempo esgotado aguardando jQuery.active == 0 ou jQuery não encontrado")
    
    # Método 3: Aguardar AJAX (se aplicável)
    # Pausa genérica para permitir processamento AJAX
    remaining_time = timeout - (time.time() - start_time)
    if remaining_time > 0:
        time.sleep(min(remaining_time, 2))
    
    elapsed = time.time() - start_time
    logger.info(f"Página carregada em {elapsed:.2f} segundos")

def clicar_acessar_fiscal(driver):
    """
    Função específica para clicar no botão 'Acessar' após o login.
    Tenta diferentes abordagens para encontrar e clicar no botão.
    """
    logger.info("Procurando o botão 'Acessar' após o login...")
    
    # Lista de seletores para o botão 'Acessar' em ordem de especificidade
    seletores_botao = [
        # Específicos para NFSe Cachoeirinha
        "a.link_acesso_fiscal",
        "a[onclick*='onClickAcessoFiscal']",
        "a.botao_cor_tema",
        
        # Mais genéricos
        ".botao_cor_tema",
        "a.btn-primary",
        ".botao-acesso",
        "[title='Acessar']"
    ]
    
    # Tenta cada seletor
    for seletor in seletores_botao:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
            
            if elementos:
                logger.info(f"Botão 'Acessar' encontrado com seletor: {seletor}")
                
                # Tenta tornar o elemento visível se estiver oculto
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elementos[0])
                time.sleep(0.5)
                
                # Tenta métodos diferentes de clique
                try:
                    logger.info("Tentando clicar diretamente...")
                    elementos[0].click()
                    logger.info("Clique direto realizado com sucesso")
                    return True
                except Exception as e:
                    logger.warning(f"Clique direto falhou: {e}")
                    
                    try:
                        logger.info("Tentando clicar via JavaScript...")
                        driver.execute_script("arguments[0].click();", elementos[0])
                        logger.info("Clique via JavaScript realizado com sucesso")
                        return True
                    except Exception as e2:
                        logger.warning(f"Clique via JavaScript falhou: {e2}")
                        
                        # Último recurso - executa função onclick diretamente
                        try:
                            onclick = elementos[0].get_attribute("onclick")
                            if onclick:
                                logger.info(f"Tentando executar onclick: {onclick}")
                                driver.execute_script(onclick)
                                logger.info("Execução de função onclick bem-sucedida")
                                return True
                        except Exception as e3:
                            logger.warning(f"Execução de onclick falhou: {e3}")
                
                # Se chegou aqui, todas as tentativas de clique falharam para este elemento
                logger.warning("Todas as tentativas de clique falharam para este seletor, tentando o próximo...")
        
        except Exception as e:
            logger.warning(f"Erro ao procurar/interagir com seletor {seletor}: {e}")
    
    # Tenta encontrar por texto também
    try:
        elementos_texto = driver.find_elements(By.XPATH, "//a[contains(text(), 'Acessar')] | //button[contains(text(), 'Acessar')]")
        if elementos_texto:
            logger.info("Botão 'Acessar' encontrado por texto")
            elementos_texto[0].click()
            return True
    except Exception as e:
        logger.warning(f"Erro ao buscar botão por texto: {e}")
    
    # Se chegou aqui, nenhum seletor funcionou
    logger.error("Não foi possível encontrar ou clicar no botão 'Acessar'")
    return False

def aguardar_pagina_destino(driver, url_destino, tempo_maximo=300, intervalo=5):
    """
    Aguarda até que a página de destino seja carregada, ou até atingir o tempo máximo.
    
    Args:
        driver: WebDriver do Selenium
        url_destino: URL que estamos esperando carregar
        tempo_maximo: Tempo máximo de espera em segundos (padrão: 5 minutos)
        intervalo: Intervalo entre verificações em segundos
        
    Returns:
        bool: True se a página de destino foi carregada, False caso contrário
    """
    logger.info(f"Aguardando navegação para a página de destino: {url_destino}")
    logger.info(f"Timeout configurado: {tempo_maximo} segundos")
    
    tempo_inicio = time.time()
    url_atual = driver.current_url
    
    while time.time() - tempo_inicio < tempo_maximo:
        # Verifica se a URL atual contém a URL de destino
        url_atual = driver.current_url
        logger.info(f"URL atual: {url_atual}")
        
        if url_destino in url_atual:
            logger.info(f"Página de destino alcançada após {time.time() - tempo_inicio:.2f} segundos")
            return True
        
        # Verifica todas as guias abertas
        for handle in driver.window_handles:
            # Alterna para esta guia
            driver.switch_to.window(handle)
            # Verifica se esta guia tem a URL de destino
            if url_destino in driver.current_url:
                logger.info(f"Página de destino encontrada em uma nova guia após {time.time() - tempo_inicio:.2f} segundos")
                return True
        
        # Volta para a guia original se houver múltiplas guias
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[0])
        
        # Exibe tempo já decorrido
        tempo_decorrido = time.time() - tempo_inicio
        tempo_restante = tempo_maximo - tempo_decorrido
        
        if int(tempo_decorrido) % 30 == 0:  # Log a cada 30 segundos
            logger.info(f"Aguardando... {tempo_decorrido:.0f}s decorridos, {tempo_restante:.0f}s restantes")
            # Tire um screenshot a cada 30 segundos
            salvar_screenshot(driver, f"aguardando_{int(tempo_decorrido)}s.png")
        
        # Pausa antes da próxima verificação
        time.sleep(intervalo)
    
    logger.error(f"Tempo esgotado ({tempo_maximo}s) aguardando a página de destino")
    logger.error(f"URL atual: {url_atual}")
    logger.error(f"URL esperada: {url_destino}")
    return False

def fechar_aviso(driver):
    """
    Tenta fechar o aviso na página de destino clicando no botão Fechar.
    """
    logger.info("Procurando botão 'Fechar' para fechar o aviso...")
    
    # Lista de seletores possíveis para o botão Fechar
    seletores_fechar = [
        "button[name='fechar']",
        "button.botao[name='fechar']",
        "button.__estrutura_componente_base.botao.botao-com-variante",
        "button[myaccesskey='f']",
        "button[zn_id='8']",
        ".botao-com-variante[name='fechar']"
    ]
    
    for seletor in seletores_fechar:
        try:
            # Espera pelo botão ficar visível e clicável
            wait = WebDriverWait(driver, 10)
            fechar_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, seletor)))
            
            logger.info(f"Botão 'Fechar' encontrado com seletor: {seletor}")
            salvar_screenshot(driver, "antes_fechar_aviso.png")
            
            # Tenta clicar no botão
            fechar_btn.click()
            logger.info("Botão 'Fechar' clicado com sucesso")
            time.sleep(2)  # Pequena pausa para o aviso fechar
            salvar_screenshot(driver, "apos_fechar_aviso.png")
            return True
        except Exception as e:
            logger.warning(f"Tentativa de clicar no botão 'Fechar' com seletor {seletor} falhou: {e}")
    
    # Tenta encontrar por texto também
    try:
        elementos_texto = driver.find_elements(By.XPATH, "//button[contains(text(), 'Fechar')]")
        if elementos_texto:
            logger.info("Botão 'Fechar' encontrado por texto")
            elementos_texto[0].click()
            logger.info("Botão 'Fechar' clicado com sucesso")
            time.sleep(2)
            return True
    except Exception as e:
        logger.warning(f"Erro ao buscar botão 'Fechar' por texto: {e}")
    
    # Última tentativa - usar JavaScript para clicar em qualquer botão com nome "fechar"
    try:
        driver.execute_script("document.querySelector('button[name=\"fechar\"]').click();")
        logger.info("Botão 'Fechar' clicado via JavaScript")
        time.sleep(2)
        return True
    except Exception as e:
        logger.warning(f"Clique via JavaScript no botão 'Fechar' falhou: {e}")
    
    logger.error("Não foi possível encontrar ou clicar no botão 'Fechar'")
    return False

def realizar_login(driver, cpf_cnpj, senha):
    """
    Realiza o login no sistema NFSe
    """
    logger.info("Iniciando processo de login...")
    
    # Localiza os elementos de login
    try:
        # Tenta encontrar os campos por vários seletores, começando pelos mais específicos
        logger.info("Tentando localizar elementos do formulário de login...")
        
        # Primeiro tenta seletores específicos para o sistema NFSe de Cachoeirinha
        try:
            wait = WebDriverWait(driver, 10)
            cpf_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[name='login_usuario']")
            ))
            senha_input = driver.find_element(By.CSS_SELECTOR, "input[name='senha_usuario']")
            login_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-login")
            logger.info("Elementos de login encontrados com seletores específicos para NFSe Cachoeirinha")
        except Exception as e:
            logger.warning(f"Não foi possível encontrar elementos com seletores específicos: {e}")
            
            # Tenta com seletores mais genéricos
            try:
                wait = WebDriverWait(driver, 10)
                cpf_input = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[type='text'][id*='login'], input[type='text'][name*='login'], input[type='text'][id*='cpf'], input[type='text'][name*='cpf'], input[type='text']")
                ))
                senha_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .btn-login, #btnLogin")
                logger.info("Elementos de login encontrados com seletores genéricos")
            except Exception as e2:
                logger.error(f"Não foi possível encontrar elementos de login: {e2}")
                return False
        
        # Aguarda até que os elementos estejam interagíveis
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, cpf_input.tag_name + "[name='" + cpf_input.get_attribute("name") + "']")))
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, senha_input.tag_name + "[name='" + senha_input.get_attribute("name") + "']")))
        
        logger.info("Preenchendo CPF/CNPJ...")
        cpf_input.click()
        time.sleep(random.uniform(0.1, 0.3))
        simular_digitacao_humana(cpf_input, cpf_cnpj)
        
        logger.info("Preenchendo senha...")
        senha_input.click()
        time.sleep(random.uniform(0.1, 0.3))
        simular_digitacao_humana(senha_input, senha)
        
        # Captura estado antes do login
        salvar_screenshot(driver, "antes_login.png")
        logger.info("Screenshot antes do login salvo")
        
        logger.info("Clicando no botão de login...")
        login_btn.click()
        logger.info("Botão de login clicado")
        
        # Captura estado após clicar
        salvar_screenshot(driver, "apos_clique_login.png")
        
        # Aguarda processamento do login
        esperar_pagina_carregar(driver, timeout=20)
        time.sleep(5)  # Aguarda um pouco mais
        
        # Captura estado após processamento
        salvar_screenshot(driver, "apos_login.png")
        logger.info("Screenshot após processamento de login salvo")
        
        # Salva HTML para análise
        salvar_html(driver, "pagina_apos_login")
        
        # Verifica se o login foi bem-sucedido
        return verificar_login_sucesso(driver)
        
    except Exception as e:
        logger.error(f"Erro durante o processo de login: {e}")
        return False

def main():
    logger.info("Iniciando automação do sistema NFSe")
    
    # Verifica o sistema operacional
    sistema_operacional = platform.system()
    logger.info(f"Sistema Operacional detectado: {sistema_operacional}")
    
    try:
        # PASSO 1: INICIANDO O NAVEGADOR
        logger.info("Configurando navegador...")
        
        # Configurações do Chrome
        chrome_opts = Options()
        chrome_opts.add_argument("--start-maximized")
        chrome_opts.add_argument("--disable-notifications")
        
        # Inicia o navegador
        driver = webdriver.Chrome(options=chrome_opts)
        logger.info("Navegador iniciado com sucesso!")
        
        # PASSO 2: NAVEGANDO PARA A PÁGINA INICIAL
        logger.info(f"Acessando URL: {NFS_URL}")
        driver.get(NFS_URL)
        
        # Aguarda carregamento da página
        esperar_pagina_carregar(driver, timeout=30)
        
        # Captura estado inicial
        salvar_screenshot(driver, "pagina_inicial.png")
        logger.info(f"Screenshot inicial salvo em {os.path.abspath('logs/imagens/pagina_inicial.png')}")
        
        # Log informativo
        logger.info(f"Título da página: {driver.title}")
        logger.info(f"URL atual: {driver.current_url}")
        
        # Salvar HTML inicial
        salvar_html(driver, "pagina_inicial")
        
        # PASSO 3: PROCESSO DE LOGIN
        logger.info("Iniciando processo de login...")
        login_sucesso = realizar_login(driver, CPF_CNPJ, SENHA)
        
        if login_sucesso:
            logger.info("LOGIN REALIZADO COM SUCESSO!")
            
            # PASSO 4: ACESSAR ÁREA FISCAL
            logger.info("Tentando acessar área fiscal...")
            acessar_sucesso = clicar_acessar_fiscal(driver)
            
            if acessar_sucesso:
                logger.info("Botão 'Acessar' clicado com sucesso!")
                
                # AVISO SOBRE CAPTCHA NESTE MOMENTO
                logger.info("\n" + "*"*80)
                logger.info("ATENÇÃO: RESOLVA O CAPTCHA AGORA!")
                logger.info("Um CAPTCHA deve aparecer após clicar no botão 'Acessar'.")
                logger.info("Por favor resolva o CAPTCHA manualmente na janela do navegador.")
                logger.info("*"*80 + "\n")
                
                # Pausa para permitir resolução manual de CAPTCHA
                input("Pressione ENTER depois de resolver o CAPTCHA para continuar...")
                
                # PASSO 5: AGUARDAR REDIRECIONAMENTO PARA A PÁGINA DE DESTINO
                logger.info(f"Aguardando redirecionamento para: {PAGINA_DESTINO}")
                logger.info("Este processo pode levar vários minutos. Por favor, aguarde...")
                
                # Aguarda até 5 minutos (300 segundos) pelo redirecionamento
                destino_alcancado = aguardar_pagina_destino(driver, PAGINA_DESTINO, tempo_maximo=300)
                
                if destino_alcancado:
                    logger.info("PÁGINA DE DESTINO ALCANÇADA COM SUCESSO!")
                    # Captura estado final
                    salvar_screenshot(driver, "pagina_destino.png")
                    salvar_html(driver, "pagina_destino")
                    
                    # PASSO 6: FECHAR AVISO NA PÁGINA DE DESTINO
                    logger.info("Tentando fechar o aviso na página de destino...")
                    aviso_fechado = fechar_aviso(driver)
                    
                    if aviso_fechado:
                        logger.info("AVISO FECHADO COM SUCESSO!")
                        salvar_screenshot(driver, "apos_fechar_aviso.png")
                    else:
                        logger.warning("Não foi possível fechar o aviso automaticamente. Pode ser necessário fechá-lo manualmente.")
                    
                    logger.info("AUTENTICAÇÃO CONCLUÍDA COM SUCESSO!")
                    logger.info("Agora você pode continuar com as operações na área fiscal")
                    
                else:
                    logger.error("Não foi possível alcançar a página de destino no tempo limite.")
                    logger.error("Verifique manualmente se o sistema está funcionando corretamente.")
                    
            else:
                logger.error("Não foi possível clicar no botão 'Acessar'")
                salvar_screenshot(driver, "falha_acessar.png")
        else:
            logger.error("Falha no login!")
            salvar_screenshot(driver, "falha_login.png")
            salvar_html(driver, "pagina_falha_login")
            
            # Verifica mensagens de erro
            mensagens_erro = verificar_mensagens_erro(driver)
            if mensagens_erro:
                logger.error("Mensagens de erro encontradas:")
                for msg in mensagens_erro:
                    logger.error(f"- {msg}")
            
            logger.error("Sugestões de resolução:")
            logger.error("1. Verifique se suas credenciais estão corretas")
            logger.error("2. Verifique se não há limite de tentativas de login")
            logger.error("3. Tente acessar o site manualmente para confirmar se está funcionando")
    
    except Exception as e:
        logger.error(f"Erro durante a automação: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        if 'driver' in locals():
            salvar_screenshot(driver, "erro_execucao.png")
            logger.info("Screenshot do erro salvo em logs/imagens/erro_execucao.png")
            salvar_html(driver, "pagina_erro")
        
        logger.error("\nSUGESTÕES PARA RESOLVER O PROBLEMA:")
        logger.error("1. Certifique-se de que o arquivo .env existe e contém as variáveis necessárias")
        logger.error("2. Verifique se sua conexão com a internet está estável")
        logger.error("3. Tente acessar o site manualmente para confirmar que está funcionando")
        
    finally:
        # Para manter a janela aberta após a execução, pergunte ao usuário se deseja fechar
        if 'driver' in locals():
            fechar = input("Deseja fechar o navegador? (s/n): ")
            if fechar.lower() == 's':
                driver.quit()
                logger.info("Navegador fechado.")
            else:
                logger.info("Navegador mantido aberto. Você pode fechá-lo manualmente quando terminar.")
                logger.info("DICA: Aproveite para navegar manualmente e entender como o site funciona.")

if __name__ == "__main__":
    main()
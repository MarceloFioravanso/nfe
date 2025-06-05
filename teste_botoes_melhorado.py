"""
Teste das funções de clique nos botões "Próximo" e "Emitir" melhoradas.
Este script foi criado para verificar se as melhorias implementadas resolvem o problema
com os botões específicos que estavam apresentando dificuldades.
"""
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import traceback

# Importa as funções melhoradas
from nfs_emissao_auto import procurar_e_clicar, procurar_e_clicar_proximo, esperar_pagina_carregar, salvar_screenshot
from finalizar_emissao import clicar_emitir_avancado

# Configuração do logger
def configurar_logger():
    # Cria pasta de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Formato da data para o nome do arquivo de log
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Configuração do logger
    logger = logging.getLogger("teste_botoes")
    logger.setLevel(logging.DEBUG)
    
    # Handler para arquivo
    file_handler = logging.FileHandler(f"logs/teste_botoes_{data_hora}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato para os logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Adiciona os handlers ao logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def iniciar_driver():
    """Inicializa o driver do Chrome com as opções necessárias"""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--ignore-certificate-errors")
    
    # Descomenta essa linha abaixo se quiser executar em modo headless (sem interface gráfica)
    # chrome_options.add_argument("--headless")
    
    service = Service("chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

def testar_proximo(driver, logger, url):
    """Testa o botão Próximo na página especificada"""
    logger.info(f"Acessando URL para teste do botão 'Próximo': {url}")
    
    try:
        driver.get(url)
        esperar_pagina_carregar(driver, 10)
        logger.info("Página carregada com sucesso")
        
        # Salvar screenshot antes de tentar clicar no botão
        salvar_screenshot(driver, "antes_clicar_proximo.png")
        
        # Tentar clicar no botão "Próximo" usando a função procurar_e_clicar_proximo melhorada
        logger.info("Tentando clicar no botão 'Próximo'...")
        if procurar_e_clicar_proximo(driver):
            logger.info("SUCESSO: Botão 'Próximo' foi clicado corretamente!")
            salvar_screenshot(driver, "apos_clicar_proximo_sucesso.png")
            return True
        else:
            logger.error("FALHA: Não foi possível clicar no botão 'Próximo'")
            salvar_screenshot(driver, "erro_clicar_proximo.png")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao testar botão 'Próximo': {e}")
        logger.debug(traceback.format_exc())
        salvar_screenshot(driver, "erro_teste_proximo.png")
        return False

def testar_emitir(driver, logger, url):
    """Testa o botão Emitir na página especificada"""
    logger.info(f"Acessando URL para teste do botão 'Emitir': {url}")
    
    try:
        driver.get(url)
        esperar_pagina_carregar(driver, 10)
        logger.info("Página carregada com sucesso")
        
        # Salvar screenshot antes de tentar clicar no botão
        salvar_screenshot(driver, "antes_clicar_emitir.png")
        
        # Seletores para o botão Emitir
        seletores_emitir = [
            # Seletor exato do HTML problemático
            "button.__estrutura_componente_base.botao.botao-com-variante.estrutura_botao.disabled_user_select.estrutura_botao_colorido",
            "button[name='confirmar']",
            "button[myaccesskey='e']",
            "button[disabledenableaftersubmit='enable']",
            
            # Seletores alternativos
            "button[name='emitir']", 
            "button.botao-primario",
            "button.__estrutura_componente_base.botao.botao-primario", 
            "button[type='submit']"
        ]
        
        # Método 1: Usar a função procurar_e_clicar do módulo principal
        logger.info("Método 1: Testando com procurar_e_clicar...")
        if procurar_e_clicar(driver, seletores_emitir, texto_botao="Emitir", max_tentativas=3, espera=1):
            logger.info("SUCESSO: Botão 'Emitir' foi clicado corretamente com método 1!")
            salvar_screenshot(driver, "apos_clicar_emitir_metodo1_sucesso.png")
            return True
        else:
            logger.warning("Método 1 falhou, tentando método 2...")
            
        # Método 2: Usar a função clicar_emitir_avancado do módulo finalizar_emissao
        logger.info("Método 2: Testando com clicar_emitir_avancado...")
        if clicar_emitir_avancado(driver, logger, max_tentativas=3, espera=1):
            logger.info("SUCESSO: Botão 'Emitir' foi clicado corretamente com método 2!")
            salvar_screenshot(driver, "apos_clicar_emitir_metodo2_sucesso.png")
            return True
        else:
            logger.error("FALHA: Não foi possível clicar no botão 'Emitir' com nenhum método")
            salvar_screenshot(driver, "erro_clicar_emitir.png")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao testar botão 'Emitir': {e}")
        logger.debug(traceback.format_exc())
        salvar_screenshot(driver, "erro_teste_emitir.png")
        return False

def main():
    logger = configurar_logger()
    logger.info("Iniciando teste dos botões 'Próximo' e 'Emitir' melhorados")
    
    driver = None
    
    try:
        driver = iniciar_driver()
        logger.info("Driver iniciado com sucesso")
        
        # URLs para teste - substitua pelas URLs reais das páginas onde os botões estão
        url_proximo = input("Digite a URL para testar o botão 'Próximo': ")
        url_emitir = input("Digite a URL para testar o botão 'Emitir': ")
        
        # Teste do botão Próximo
        if url_proximo:
            resultado_proximo = testar_proximo(driver, logger, url_proximo)
            logger.info(f"Resultado do teste do botão 'Próximo': {'SUCESSO' if resultado_proximo else 'FALHA'}")
        
        # Teste do botão Emitir
        if url_emitir:
            resultado_emitir = testar_emitir(driver, logger, url_emitir)
            logger.info(f"Resultado do teste do botão 'Emitir': {'SUCESSO' if resultado_emitir else 'FALHA'}")
        
    except Exception as e:
        logger.error(f"Erro durante execução dos testes: {e}")
        logger.debug(traceback.format_exc())
    finally:
        if driver:
            logger.info("Fechando o driver...")
            driver.quit()
            
    logger.info("Testes finalizados.")

if __name__ == "__main__":
    main()

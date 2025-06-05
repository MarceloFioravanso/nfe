"""
Teste da funcionalidade de detectar e clicar no botão "Emitir Nota Fiscal" 
após a emissão de uma nota para continuar com a próxima.
"""
import time
import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Importa os módulos para teste
from detectar_continuar_emissao import detectar_botao_emitir_proxima_nota, clicar_botao_emitir_proxima_nota

# Configuração de logging
def configurar_logger():
    os.makedirs("logs", exist_ok=True)
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger = logging.getLogger("teste_continuar_emissao")
    logger.setLevel(logging.DEBUG)
    
    file_handler = logging.FileHandler(f"logs/teste_continuar_{data_hora}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Função para salvar screenshot
def salvar_screenshot(driver, nome_arquivo):
    try:
        os.makedirs("logs/imagens", exist_ok=True)
        caminho = f"logs/imagens/{nome_arquivo}"
        driver.save_screenshot(caminho)
        logger.info(f"Screenshot salvo em {caminho}")
    except Exception as e:
        logger.error(f"Erro ao salvar screenshot: {e}")

def iniciar_driver(logger):
    """Inicializa o driver do Chrome com as opções necessárias e instala o chromedriver automaticamente"""
    # Instala o ChromeDriver automaticamente
    try:
        import chromedriver_autoinstaller
        chromedriver_autoinstaller.install()
        logger.info("ChromeDriver instalado automaticamente")
    except ImportError:
        logger.warning("Pacote chromedriver_autoinstaller não encontrado, usando caminho padrão")
        # Tenta instalar o pacote
        import subprocess
        import sys
        try:
            logger.info("Tentando instalar o pacote chromedriver_autoinstaller...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "chromedriver_autoinstaller"])
            import chromedriver_autoinstaller
            chromedriver_autoinstaller.install()
            logger.info("ChromeDriver instalado automaticamente")
        except Exception as e:
            logger.error(f"Erro ao instalar chromedriver_autoinstaller: {e}")
    except Exception as e:
        logger.error(f"Erro ao instalar ChromeDriver automaticamente: {e}")
    
    # Configura as opções do Chrome
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
    
    try:
        # Tenta criar o driver usando o ChromeDriver instalado automaticamente
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        return driver
    except Exception as e:
        logger.error(f"Erro ao iniciar o driver do Chrome: {e}")
        
        # Tentativa alternativa com o serviço explícito
        try:
            logger.info("Tentando iniciar o driver com o serviço explícito...")
            service = Service("chromedriver.exe")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(60)
            return driver
        except Exception as e2:
            logger.error(f"Também falhou ao iniciar o driver com serviço explícito: {e2}")
            raise

def teste_deteccao_botao(driver, logger):
    """Testa a detecção e o clique no botão 'Emitir Nota Fiscal' após a emissão de uma nota"""
    try:
        # URL para teste - usando arquivo HTML local
        import os
        arquivo_html = os.path.join(os.getcwd(), "pagina_teste_emitir_nota.html")
        url = f"file:///{arquivo_html.replace('\\', '/')}"
        
        logger.info(f"Acessando arquivo HTML local para teste: {arquivo_html}")
        driver.get(url)
        time.sleep(2)  # Aguarda o carregamento completo da página
        
        # Salva screenshot inicial
        salvar_screenshot(driver, "antes_deteccao_botao.png")
        
        # Testa a detecção do botão
        logger.info("Testando a detecção do botão 'Emitir Nota Fiscal'...")
        botao_detectado = detectar_botao_emitir_proxima_nota(driver)
        
        if botao_detectado:
            logger.info("SUCESSO: Botão 'Emitir Nota Fiscal' para próxima nota foi detectado!")
            
            # Pergunta se quer clicar no botão
            clicar = input("O botão foi detectado. Deseja testar o clique? (s/n): ")
            
            if clicar.lower() == 's':
                logger.info("Testando o clique no botão...")
                clique_sucesso = clicar_botao_emitir_proxima_nota(driver)
                
                if clique_sucesso:
                    logger.info("SUCESSO: Botão 'Emitir Nota Fiscal' foi clicado corretamente!")
                    salvar_screenshot(driver, "apos_clique_botao.png")
                    time.sleep(5)  # Aguarda para ver o resultado do clique
                    return True
                else:
                    logger.error("FALHA: Não foi possível clicar no botão, mesmo tendo sido detectado")
                    salvar_screenshot(driver, "falha_clique_botao.png")
                    return False
            else:
                logger.info("Teste de clique cancelado pelo usuário")
                return True
        else:
            logger.error("FALHA: Botão 'Emitir Nota Fiscal' para próxima nota não foi detectado")
            salvar_screenshot(driver, "falha_deteccao_botao.png")
            
            # Se não detectou o botão, verifica elementos na página para diagnóstico
            logger.info("Verificando elementos na página para diagnóstico...")
            
            # Procura por spans
            spans = driver.find_elements(By.TAG_NAME, 'span')
            logger.info(f"Total de elementos span encontrados: {len(spans)}")
            for i, span in enumerate(spans[:10]):  # Limita a 10 elementos para não sobrecarregar o log
                try:
                    texto = span.text
                    classe = span.get_attribute('class')
                    logger.info(f"Span {i+1}: Texto='{texto}', Classe='{classe}'")
                except:
                    logger.info(f"Span {i+1}: [Erro ao obter atributos]")
            
            # Procura por botões e links
            botoes = driver.find_elements(By.TAG_NAME, 'button')
            logger.info(f"Total de botões encontrados: {len(botoes)}")
            links = driver.find_elements(By.TAG_NAME, 'a')
            logger.info(f"Total de links encontrados: {len(links)}")
            
            return False
            
    except Exception as e:
        logger.error(f"Erro durante teste de detecção de botão: {e}")
        import traceback
        logger.error(traceback.format_exc())
        salvar_screenshot(driver, "erro_teste_deteccao.png")
        return False

def main():
    logger = configurar_logger()
    logger.info("Iniciando teste de detecção do botão 'Emitir Nota Fiscal' após emissão")
    
    driver = None
    
    try:
        driver = iniciar_driver(logger)
        logger.info("Driver iniciado com sucesso")
        
        resultado = teste_deteccao_botao(driver, logger)
        logger.info(f"Resultado do teste: {'SUCESSO' if resultado else 'FALHA'}")
        
    except Exception as e:
        logger.error(f"Erro durante execução do teste: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if driver:
            logger.info("Fechando o driver...")
            driver.quit()
            
    logger.info("Teste finalizado.")

if __name__ == "__main__":
    main()

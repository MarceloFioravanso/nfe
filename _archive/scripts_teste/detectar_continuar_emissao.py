"""
Módulo para detectar e clicar no botão 'Emitir Nota Fiscal' após uma emissão bem-sucedida,
permitindo continuar automaticamente para emitir a próxima nota.
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# Configuração de logger
logger = logging.getLogger(__name__)

def detectar_botao_emitir_proxima_nota(driver):
    """
    Detecta se estamos na tela que permite continuar para emitir a próxima nota.
    
    Args:
        driver: WebDriver do Selenium
        
    Returns:
        bool: True se a tela de continuação foi detectada, False caso contrário
    """
    try:
        logger.info("Verificando se estamos na tela para emitir próxima nota...")
        
        # Aguarda um momento para a página carregar completamente
        time.sleep(2)
        
        # Procura pelo texto indicativo
        texto_emitir_nota = driver.find_elements(By.XPATH, "//span[contains(@class, 'componente_card_texto_titulo') and contains(text(), 'Emitir Nota Fiscal')]")
        if texto_emitir_nota:
            logger.info("Tela para emitir próxima nota detectada!")
            return True
            
        # Procura também por outros indicadores
        outros_indicadores = [
            "//h1[contains(text(), 'Emissão de Nota Fiscal')]",
            "//h2[contains(text(), 'Emitir Nota Fiscal')]",
            "//div[contains(text(), 'Emitir nova nota')]"
        ]
        
        for xpath in outros_indicadores:
            elementos = driver.find_elements(By.XPATH, xpath)
            if elementos and elementos[0].is_displayed():
                logger.info(f"Tela para emitir próxima nota detectada via indicador: {xpath}")
                return True
                
        logger.info("Não estamos na tela para emitir próxima nota.")
        return False
        
    except Exception as e:
        logger.warning(f"Erro ao verificar tela para próxima nota: {e}")
        return False

def clicar_botao_emitir_proxima_nota(driver):
    """
    Clica no botão 'Emitir Nota Fiscal' para iniciar a emissão da próxima nota.
    
    Args:
        driver: WebDriver do Selenium
        
    Returns:
        bool: True se o clique foi bem-sucedido, False caso contrário
    """
    try:
        logger.info("Tentando clicar no botão 'Emitir Nota Fiscal' para próxima nota...")
        
        # Lista de possíveis seletores para o botão
        seletores = [
            "a.componente_card",
            "div.componente_card",
            "a[title='Emitir Nota Fiscal']",
            "button[title='Emitir Nota Fiscal']",
            "a[onclick*='emitirNota']",
            "a.botao_cor_tema"
        ]
        
        # Tenta cada seletor
        for seletor in seletores:
            elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
            elementos_visiveis = [e for e in elementos if e.is_displayed()]
            
            for elemento in elementos_visiveis:
                # Verifica se o elemento contém o texto "Emitir Nota Fiscal"
                if "Emitir Nota Fiscal" in elemento.text:
                    logger.info(f"Botão 'Emitir Nota Fiscal' encontrado com seletor: {seletor}")
                    
                    # Rola até o elemento
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                    time.sleep(1)
                    
                    # Tenta diferentes métodos de clique
                    metodos = [
                        {"nome": "clique direto", "func": lambda: elemento.click()},
                        {"nome": "JavaScript", "func": lambda: driver.execute_script("arguments[0].click();", elemento)},
                        {"nome": "ActionChains", "func": lambda: ActionChains(driver).move_to_element(elemento).click().perform()}
                    ]
                    
                    for metodo in metodos:
                        try:
                            logger.info(f"Tentando clicar com método: {metodo['nome']}")
                            metodo["func"]()
                            logger.info(f"Botão 'Emitir Nota Fiscal' para próxima nota clicado via {metodo['nome']}")
                            
                            # Aguarda a página carregar
                            time.sleep(2)
                            
                            # Verifica se a página mudou
                            try:
                                WebDriverWait(driver, 10).until(
                                    lambda d: "Emitir Nota Fiscal" not in d.page_source or 
                                             "componente_card_texto_titulo" not in d.page_source
                                )
                                logger.info("Página mudou após o clique.")
                                return True
                            except:
                                logger.warning("A página não parece ter mudado após o clique.")
                                continue
                                
                        except Exception as e:
                            logger.warning(f"Clique via {metodo['nome']} falhou: {e}")
        
        # Tenta por XPath se os seletores falharem
        xpaths = [
            "//span[contains(@class, 'componente_card_texto_titulo') and contains(text(), 'Emitir Nota Fiscal')]/ancestor::a",
            "//span[contains(@class, 'componente_card_texto_titulo') and contains(text(), 'Emitir Nota Fiscal')]/ancestor::div",
            "//span[contains(text(), 'Emitir Nota Fiscal')]/ancestor::a",
            "//a[contains(text(), 'Emitir Nota Fiscal')]"
        ]
        
        for xpath in xpaths:
            elementos = driver.find_elements(By.XPATH, xpath)
            if elementos and elementos[0].is_displayed():
                logger.info(f"Botão 'Emitir Nota Fiscal' encontrado por XPath: {xpath}")
                
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elementos[0])
                    time.sleep(1)
                    elementos[0].click()
                    logger.info("Botão 'Emitir Nota Fiscal' clicado via XPath")
                    
                    # Aguarda a página carregar
                    time.sleep(2)
                    return True
                    
                except Exception as e:
                    logger.warning(f"Clique XPath falhou: {e}")
                    try:
                        driver.execute_script("arguments[0].click();", elementos[0])
                        logger.info("Botão clicado via JavaScript (XPath)")
                        time.sleep(2)
                        return True
                    except Exception as e2:
                        logger.warning(f"Clique JavaScript (XPath) falhou: {e2}")
        
        # Se tudo falhou, tenta clicar em qualquer elemento com o texto "Emitir Nota Fiscal"
        elementos_texto = driver.find_elements(By.XPATH, "//*[contains(text(), 'Emitir Nota Fiscal')]")
        for elemento in elementos_texto:
            if elemento.is_displayed():
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                    driver.execute_script("arguments[0].click();", elemento)
                    logger.info("Tentativa final de clique bem-sucedida")
                    time.sleep(2)
                    return True
                except:
                    pass
                    
        logger.error("Não foi possível encontrar ou clicar no botão para emitir próxima nota")
        return False
        
    except Exception as e:
        logger.error(f"Erro ao tentar clicar no botão para próxima nota: {e}")
        return False

def continuar_emissao_apos_nota(driver):
    """
    Função principal que verifica se estamos na tela para continuar emitindo notas
    e clica no botão para iniciar a próxima emissão.
    
    Args:
        driver: WebDriver do Selenium
        
    Returns:
        bool: True se a continuação foi bem-sucedida, False caso contrário
    """
    logger.info("Verificando se é possível continuar para a próxima nota...")
    
    # Primeiro detecta se estamos na tela certa
    if detectar_botao_emitir_proxima_nota(driver):
        # Em seguida tenta clicar no botão
        return clicar_botao_emitir_proxima_nota(driver)
    
    return False

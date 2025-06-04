"""
Módulo para finalizar a emissão da nota fiscal eletrônica (NFS-e)
Implementa funções para clicar nos botões "Próximo" e "Emitir" após a verificação do valor líquido.
"""
import time
import logging
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains

# Função para salvar screenshots na pasta correta
def salvar_screenshot(driver, nome_arquivo, logger=None):
    """Salva um screenshot na pasta de imagens com o nome especificado"""
    # Garante que a pasta de screenshots existe
    os.makedirs("logs/imagens", exist_ok=True)
    
    caminho_completo = os.path.join("logs/imagens", nome_arquivo)
    try:
        driver.save_screenshot(caminho_completo)
        if logger:
            logger.info(f"Screenshot salvo em {caminho_completo}")
        return True
    except Exception as e:
        if logger:
            logger.error(f"Erro ao salvar screenshot {nome_arquivo}: {e}")
        return False

def esperar_pagina_carregar(driver, timeout=10, logger=None):
    """
    Aguarda a página carregar completamente
    """
    if logger:
        logger.info("Aguardando carregamento completo da página...")
    
    # Método 1: Aguardar document.readyState
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        if logger:
            logger.info("Página carregou completamente")
    except Exception as e:
        if logger:
            logger.warning(f"Tempo esgotado aguardando document.readyState: {e}")
    
    # Método 2: Verificar se jQuery está ativo (se disponível)
    try:
        jquery_present = driver.execute_script("return typeof jQuery !== 'undefined'")
        if jquery_present:
            WebDriverWait(driver, min(timeout, 3)).until(
                lambda d: d.execute_script('return jQuery.active') == 0
            )
            if logger:
                logger.info("Requisições jQuery completadas")
    except:
        if logger:
            logger.debug("jQuery não disponível ou tempo esgotado")
    
    # Pausa adicional para garantir que elementos dinâmicos foram carregados
    time.sleep(1)

def verificar_se_emitiu_nota(driver, logger=None):
    """
    Verifica se a nota fiscal foi emitida com sucesso
    """
    if logger:
        logger.info("Verificando se a nota fiscal foi emitida...")
    
    # Lista de indicadores de sucesso na emissão
    indicadores_sucesso = [
        # Mensagens de texto
        "//div[contains(text(), 'emitida com sucesso')]",
        "//span[contains(text(), 'emitida com sucesso')]",
        "//p[contains(text(), 'emitida com sucesso')]",
        "//div[contains(text(), 'Nota Fiscal gerada')]",
        "//div[contains(text(), 'NFS-e gerada')]",
        "//span[contains(text(), 'Nota Fiscal gerada')]",
        
        # Elementos visuais de sucesso
        "//img[contains(@src, 'sucesso')]",
        "//i[contains(@class, 'success')]",
        "//div[contains(@class, 'success')]",
        "//div[contains(@class, 'concluido')]",
        
        # Elementos com número da nota
        "//div[contains(text(), 'Número da nota')]",
        "//span[contains(text(), 'Número da nota')]",
        "//label[contains(text(), 'Número da nota')]"
    ]
    
    time.sleep(3)  # Aguarda um pouco para a mensagem de sucesso aparecer
    
    sucesso = False
    mensagem = ""
    
    # Verifica cada indicador
    for xpath in indicadores_sucesso:
        try:
            elementos = driver.find_elements(By.XPATH, xpath)
            if elementos:
                for elem in elementos:
                    if elem.is_displayed():
                        mensagem = elem.text
                        sucesso = True
                        if logger:
                            logger.info(f"Indicador de sucesso encontrado: '{mensagem}'")
                        break
            if sucesso:
                break
        except Exception as e:
            if logger:
                logger.debug(f"Erro ao verificar indicador de sucesso: {e}")
    
    # Se não encontrou indicadores específicos, verifica por textos genéricos
    if not sucesso:
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            palavras_chave = ["emitida com sucesso", "gerada com sucesso", "nota fiscal gerada", "nfse emitida"]
            
            for palavra in palavras_chave:
                if palavra in body_text:
                    sucesso = True
                    mensagem = f"Detectado texto indicativo de sucesso: '{palavra}'"
                    if logger:
                        logger.info(mensagem)
                    break
        except Exception as e:
            if logger:
                logger.debug(f"Erro ao verificar texto na página: {e}")
    
    # Salva screenshot para análise posterior
    salvar_screenshot(driver, "verificacao_emissao_nota.png", logger)
    
    return sucesso, mensagem

def clicar_proximo_apos_verificacao(driver, logger=None):
    """
    Clica no botão "Próximo" após a verificação do valor líquido
    
    Args:
        driver: WebDriver do Selenium
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se o clique for bem-sucedido, False caso contrário
    """
    if logger is None:
        logger = logging.getLogger('finalizar_emissao')
    
    try:
        logger.info("Tentando clicar no botão 'Próximo' após verificação do valor líquido...")
        
        # Salva o estado antes de clicar
        salvar_screenshot(driver, "antes_clicar_proximo.png", logger)
        
        # Lista de seletores para o botão "Próximo"
        seletores_proximo = [
            'button[name="botao_proximo"]',
            'button.__estrutura_componente_base.botao.botao-com-variante.estrutura_botao.disabled_user_select.estrutura_botao_janela_proximo[name="botao_proximo"][myaccesskey="p"]',
            'button.__estrutura_componente_base.botao.botao-com-variante.estrutura_botao[name="botao_proximo"]',
            'button.estrutura_botao_janela_proximo[name="botao_proximo"]',
            'button.__estrutura_componente_base.botao.botao-com-variante.estrutura_botao.disabled_user_select.estrutura_botao_janela_proximo',
            'button[myaccesskey="p"]',
            # Seletores adicionais
            'button.botao_proximo',
            'button.botao-com-variante[type="submit"]',
            'button:not([disabled])[name*="proximo"]',
            'button:not([disabled])[id*="proximo"]',
            'button:not([disabled])[title*="Próximo"]',
            'button:not([disabled])[aria-label*="Próximo"]',
            # Seletor exato do HTML fornecido
            'button.__estrutura_componente_base.botao.botao-com-variante.estrutura_botao.disabled_user_select.estrutura_botao_janela_proximo'
        ]
        
        # Tenta encontrar e clicar no botão "Próximo"
        botao_proximo = None
        for seletor in seletores_proximo:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                elementos_visiveis = [e for e in elementos if e.is_displayed()]
                
                if elementos_visiveis:
                    botao_proximo = elementos_visiveis[0]
                    logger.info(f"Botão 'Próximo' encontrado com seletor: {seletor}")
                    break
            except Exception as e:
                logger.debug(f"Erro ao procurar botão 'Próximo' com seletor {seletor}: {e}")
        
        # Se não encontrou por CSS, tenta por XPath
        if not botao_proximo:
            xpath_seletores = [
                "//button[contains(text(), 'Próximo')]",
                "//button[contains(@name, 'proximo')]",
                "//button[contains(@id, 'proximo')]",
                "//button[@myaccesskey='p']",
                "//button[contains(@class, 'proximo')]",
                "//button[contains(@title, 'Próximo')]",
                "//span[contains(text(), 'Próximo')]/parent::button"
            ]
            
            for xpath in xpath_seletores:
                try:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    elementos_visiveis = [e for e in elementos if e.is_displayed()]
                    
                    if elementos_visiveis:
                        botao_proximo = elementos_visiveis[0]
                        logger.info(f"Botão 'Próximo' encontrado com XPath: {xpath}")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar botão 'Próximo' com XPath {xpath}: {e}")
        
        if botao_proximo:
            # Rola até o botão para garantir que esteja visível
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_proximo)
            time.sleep(1)
            
            # Tenta clicar no botão com diferentes métodos
            metodos = [
                {"nome": "clique direto", "func": lambda: botao_proximo.click()},
                {"nome": "JavaScript", "func": lambda: driver.execute_script("arguments[0].click();", botao_proximo)},
                {"nome": "ActionChains", "func": lambda: ActionChains(driver).move_to_element(botao_proximo).click().perform()},
                {"nome": "JavaScript avançado", "func": lambda: driver.execute_script(
                    """
                    var evt = new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    arguments[0].dispatchEvent(evt);
                    """, 
                    botao_proximo
                )}
            ]
            
            for metodo in metodos:
                try:
                    logger.info(f"Tentando clicar com método: {metodo['nome']}")
                    metodo["func"]()
                    logger.info(f"Botão 'Próximo' clicado com sucesso via {metodo['nome']}")
                    
                    # Aguarda a página carregar
                    time.sleep(2)
                    esperar_pagina_carregar(driver, 5, logger)
                    
                    # Salva screenshot para verificação
                    salvar_screenshot(driver, f"apos_clicar_proximo_{metodo['nome'].replace(' ', '_')}.png", logger)
                    
                    # Verifica se a página mudou após o clique
                    try:
                        # Procura por elementos que indicam que a página foi alterada
                        nova_pagina = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 
                                'button[name*="emitir"], button[name*="confirmar"], '
                                'button[name*="finalizar"], button[name*="gerar"], '
                                'input[name*="confirmacao"], input[id*="confirmacao"]'
                            ))
                        )
                        logger.info(f"Navegação confirmada: Encontrados elementos da próxima página após clique via {metodo['nome']}")
                        return True
                    except:
                        # Se não encontrou elementos específicos, verifica se a URL mudou
                        logger.warning(f"Não foi possível confirmar com certeza se a navegação após clique via {metodo['nome']} ocorreu com sucesso")
                        continue  # Tenta o próximo método se não confirmou a navegação
                    
                except Exception as e:
                    logger.warning(f"Clique via {metodo['nome']} falhou: {e}")
                    continue  # Tenta o próximo método
            
            # Se chegou aqui, nenhum método funcionou completamente
            logger.warning("Todos os métodos de clique foram tentados, mas não foi possível confirmar a navegação")
            
            # Última tentativa - procura diretamente por botões na próxima etapa
            try:
                # Se há um botão "Emitir" visível, consideramos que o clique funcionou
                botoes_emitir = driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Emitir') or contains(@name, 'emitir') or contains(@id, 'emitir')]")
                botoes_emitir_visiveis = [b for b in botoes_emitir if b.is_displayed()]
                
                if botoes_emitir_visiveis:
                    logger.info("Botão 'Emitir' encontrado - navegação bem-sucedida")
                    return True
            except:
                pass
                
            # Presume que algo aconteceu, mesmo sem confirmação
            return True
            
        else:
            logger.error("Botão 'Próximo' não encontrado")
            salvar_screenshot(driver, "erro_botao_proximo_nao_encontrado.png", logger)
            
            # Analisa a página para entender o contexto atual
            try:
                botoes = driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"Encontrados {len(botoes)} botões na página")
                for i, botao in enumerate(botoes):
                    if i < 5:  # Limita a 5 botões para não poluir o log
                        try:
                            texto = botao.text
                            classe = botao.get_attribute("class") or ""
                            nome = botao.get_attribute("name") or ""
                            logger.info(f"Botão {i+1}: texto='{texto}', classe='{classe}', nome='{nome}'")
                        except:
                            pass
            except:
                pass
                
            return False
            
    except Exception as e:
        logger.error(f"Erro ao tentar clicar no botão 'Próximo': {e}")
        import traceback
        logger.error(traceback.format_exc())
        salvar_screenshot(driver, "erro_excecao_botao_proximo.png", logger)
        return False

def clicar_emitir(driver, logger=None):
    """
    Clica no botão "Emitir" para finalizar a emissão da nota fiscal
    
    Args:
        driver: WebDriver do Selenium
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se o clique for bem-sucedido, False caso contrário
    """
    if logger is None:
        logger = logging.getLogger('finalizar_emissao')
    
    try:
        logger.info("Tentando clicar no botão 'Emitir' para finalizar a nota fiscal...")
        
        # Salva o estado antes de clicar
        salvar_screenshot(driver, "antes_clicar_emitir.png", logger)
        
        # Aguarda um momento para que a página esteja completamente carregada
        esperar_pagina_carregar(driver, 10, logger)
        
        # Lista de seletores para o botão "Emitir"
        seletores_emitir = [
            'button[name="emitir"]',
            'button[name="botao_emitir"]',
            'button.__estrutura_componente_base.botao.botao-com-variante.estrutura_botao[name="emitir"]',
            'button.estrutura_botao_emitir',
            'button.botao_emitir',
            'button.__estrutura_componente_base.botao.botao-com-variante.estrutura_botao.disabled_user_select[name="emitir"]',
            'button:not([disabled])[name*="emitir"]',
            'button:not([disabled])[id*="emitir"]',
            'button:not([disabled])[title*="Emitir"]',
            'button:not([disabled])[aria-label*="Emitir"]',
            'button.botao-com-variante[name="emitir"]',
            'button.__estrutura_componente_base.botao.botao-com-variante'
        ]
        
        # Tenta encontrar e clicar no botão "Emitir"
        botao_emitir = None
        for seletor in seletores_emitir:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                elementos_visiveis = [e for e in elementos if e.is_displayed()]
                
                if elementos_visiveis:
                    botao_emitir = elementos_visiveis[0]
                    logger.info(f"Botão 'Emitir' encontrado com seletor: {seletor}")
                    break
            except Exception as e:
                logger.debug(f"Erro ao procurar botão 'Emitir' com seletor {seletor}: {e}")
        
        # Se não encontrou por CSS, tenta por XPath
        if not botao_emitir:
            xpath_seletores = [
                "//button[contains(text(), 'Emitir')]",
                "//button[contains(@name, 'emitir')]",
                "//button[contains(@id, 'emitir')]",
                "//button[contains(@class, 'emitir')]",
                "//button[contains(@title, 'Emitir')]",
                "//span[contains(text(), 'Emitir')]/parent::button",
                "//button[text()='Emitir']"
            ]
            
            for xpath in xpath_seletores:
                try:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    elementos_visiveis = [e for e in elementos if e.is_displayed()]
                    
                    if elementos_visiveis:
                        botao_emitir = elementos_visiveis[0]
                        logger.info(f"Botão 'Emitir' encontrado com XPath: {xpath}")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar botão 'Emitir' com XPath {xpath}: {e}")
        
        if botao_emitir:
            # Rola até o botão para garantir que esteja visível
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botao_emitir)
            time.sleep(1)
            
            # Pergunta ao usuário se deseja realmente emitir a nota
            confirmacao = input("\nATENÇÃO: Você está prestes a emitir a nota fiscal. Deseja continuar? (s/n): ").strip().lower()
            if confirmacao != 's':
                logger.info("Emissão cancelada pelo usuário")
                return False
                
            # Tenta clicar no botão com diferentes métodos
            metodos = [
                {"nome": "clique direto", "func": lambda: botao_emitir.click()},
                {"nome": "JavaScript", "func": lambda: driver.execute_script("arguments[0].click();", botao_emitir)},
                {"nome": "ActionChains", "func": lambda: ActionChains(driver).move_to_element(botao_emitir).click().perform()},
                {"nome": "JavaScript avançado", "func": lambda: driver.execute_script(
                    """
                    var evt = new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    arguments[0].dispatchEvent(evt);
                    """, 
                    botao_emitir
                )}
            ]
            
            for metodo in metodos:
                try:
                    logger.info(f"Tentando clicar com método: {metodo['nome']}")
                    metodo["func"]()
                    logger.info(f"Botão 'Emitir' clicado com sucesso via {metodo['nome']}")
                    
                    # Aguarda a página carregar após o clique
                    time.sleep(3)
                    esperar_pagina_carregar(driver, 10, logger)
                    
                    # Salva screenshot para verificação
                    salvar_screenshot(driver, f"apos_clicar_emitir_{metodo['nome'].replace(' ', '_')}.png", logger)
                    
                    # Verifica se a nota foi emitida com sucesso
                    sucesso, mensagem = verificar_se_emitiu_nota(driver, logger)
                    
                    if sucesso:
                        logger.info(f"Nota fiscal emitida com sucesso! {mensagem}")
                        return True
                    else:
                        logger.warning(f"Clique via {metodo['nome']} não confirmou emissão da nota")
                        continue  # Tenta o próximo método
                    
                except Exception as e:
                    logger.warning(f"Clique via {metodo['nome']} falhou: {e}")
                    continue  # Tenta o próximo método
            
            # Se chegou aqui, nenhum método funcionou completamente
            logger.warning("Todos os métodos de clique foram tentados, mas não foi possível confirmar a emissão")
            
            # Última verificação - procura por indicadores de sucesso
            final_sucesso, final_mensagem = verificar_se_emitiu_nota(driver, logger)
            
            if final_sucesso:
                logger.info(f"Nota fiscal emitida com sucesso após múltiplas tentativas! {final_mensagem}")
                return True
            else:
                logger.warning("Não foi possível confirmar se a nota foi emitida")
                return False
                
        else:
            logger.error("Botão 'Emitir' não encontrado")
            salvar_screenshot(driver, "erro_botao_emitir_nao_encontrado.png", logger)
            
            # Analisa a página para entender o contexto atual
            try:
                botoes = driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"Encontrados {len(botoes)} botões na página")
                for i, botao in enumerate(botoes):
                    if i < 5:  # Limita a 5 botões para não poluir o log
                        try:
                            texto = botao.text
                            classe = botao.get_attribute("class") or ""
                            nome = botao.get_attribute("name") or ""
                            logger.info(f"Botão {i+1}: texto='{texto}', classe='{classe}', nome='{nome}'")
                        except:
                            pass
            except:
                pass
                
            return False
            
    except Exception as e:
        logger.error(f"Erro ao tentar clicar no botão 'Emitir': {e}")
        import traceback
        logger.error(traceback.format_exc())
        salvar_screenshot(driver, "erro_excecao_botao_emitir.png", logger)
        return False

def finalizar_emissao_nota(driver, logger=None):
    """
    Executa o processo completo de finalização da nota fiscal:
    1. Clica no botão 'Próximo' após verificação do valor líquido
    2. Clica no botão 'Emitir' na tela de confirmação
    
    Args:
        driver: WebDriver do Selenium
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se todo o processo for bem-sucedido, False caso contrário
    """
    if logger is None:
        logger = logging.getLogger('finalizar_emissao')
    
    logger.info("Iniciando processo de finalização da nota fiscal...")
    
    # Primeiro clica em "Próximo"
    proximo_ok = clicar_proximo_apos_verificacao(driver, logger)
    
    if not proximo_ok:
        logger.error("Não foi possível clicar no botão 'Próximo'. Processo de finalização interrompido.")
        return False
    
    # Aguarda um momento entre os dois cliques
    logger.info("Aguardando carregamento da página de confirmação antes de emitir...")
    time.sleep(3)
    esperar_pagina_carregar(driver, 10, logger)
    
    # Então clica em "Emitir"
    emitir_ok = clicar_emitir(driver, logger)
    
    if not emitir_ok:
        logger.error("Não foi possível clicar no botão 'Emitir'. Verifique manualmente se a nota foi emitida.")
        return False
    
    # Verifica se a nota foi emitida com sucesso
    logger.info("Verificando confirmação final da emissão da nota...")
    sucesso_final, mensagem_final = verificar_se_emitiu_nota(driver, logger)
    
    if sucesso_final:
        logger.info(f"SUCESSO NA EMISSÃO DA NOTA FISCAL! {mensagem_final}")
        salvar_screenshot(driver, "nota_fiscal_emitida_com_sucesso.png", logger)
        return True
    else:
        logger.warning("Não foi possível confirmar com certeza a emissão da nota. Verifique manualmente.")
        return False

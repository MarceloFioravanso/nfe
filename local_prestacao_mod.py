from selenium.webdriver.common.keys import Keys
import time
import logging

def preencher_local_prestacao(driver, local_codigo="8561", logger=None):
    """
    Preenche o campo de local da prestação do serviço com o código especificado.
    Após preencher, simula pressionar ENTER e espera 3 segundos para que as opções
    do campo de serviço sejam carregadas.
    
    Args:
        driver: WebDriver do Selenium
        local_codigo: Código do local da prestação (padrão: 8561 - mesmo município)
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se o preenchimento foi bem-sucedido, False caso contrário
    """
    if logger is None:
        logger = logging.getLogger('preencher_servico')
    
    try:
        logger.info(f"Preenchendo local da prestação com código {local_codigo}...")
        
        # Seletores possíveis para o campo de local da prestação
        local_seletores = [
            'input[name="LocalPrestacao.codigoReceita"]',
            'input[aria-label="Local da Prestação"]',
            'select[name*="local"]',
            'select[id*="local"]',
            'select[name*="municipio"]',
            'select.local-prestacao',
            'input[placeholder*="Local"]'
        ]
        
        # Primeiro, tenta input
        campo_local = None
        for seletor in local_seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos:
                    campo_local = elementos[0]
                    logger.info(f"Campo Local da Prestação encontrado com seletor: {seletor}")
                    break
            except Exception as e:
                logger.debug(f"Erro ao procurar campo com seletor {seletor}: {e}")
        
        # Se não encontrou, tenta por XPath
        if not campo_local:
            xpath_seletores = [
                "//label[contains(text(), 'Local')]/following::input[1]",
                "//label[contains(text(), 'Local')]/following::select[1]",
                "//th[contains(text(), 'Local')]/following::input[1]"
            ]
            
            for xpath in xpath_seletores:
                try:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    if elementos:
                        campo_local = elementos[0]
                        logger.info(f"Campo Local da Prestação encontrado com XPath: {xpath}")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar campo com XPath {xpath}: {e}")
        
        if not campo_local:
            logger.warning("Campo Local da Prestação não encontrado, continuando mesmo assim")
            return False
        
        # Verificar se é input ou select
        tag_name = campo_local.tag_name.lower()
        
        if tag_name == 'input':
            # Preencher o campo com o valor padrão "8561"
            campo_local.clear()
            simular_digitacao_humana(campo_local, local_codigo)
            logger.info(f"Local da Prestação preenchido com: {local_codigo}")
            
            # Simula pressionar a tecla ENTER e aguarda a atualização dos campos dependentes
            campo_local.send_keys(Keys.ENTER)
            logger.info("Tecla ENTER pressionada após preencher local da prestação")
            
            # Aguarda a atualização da página (3 segundos conforme indicado)
            time.sleep(3)
            logger.info("Aguardando 3 segundos para o carregamento das opções de serviço")
            return True
            
        elif tag_name == 'select':
            # É um select, tenta selecionar por valor ou texto
            try:
                select = Select(campo_local)
                
                # Tenta selecionar por valor primeiro
                try:
                    select.select_by_value(local_codigo)
                    logger.info(f"Local da Prestação selecionado por valor: {local_codigo}")
                    time.sleep(3)  # Aumentado para 3 segundos para dar tempo de carregar as opções de serviço
                    return True
                except:
                    # Tenta selecionar por texto visível
                    try:
                        for opcao in select.options:
                            if local_codigo in opcao.text:
                                select.select_by_visible_text(opcao.text)
                                logger.info(f"Local da Prestação selecionado por texto: {opcao.text}")
                                time.sleep(3)  # Aumentado para 3 segundos
                                return True
                    except Exception as e2:
                        logger.warning(f"Erro ao selecionar local por texto: {e2}")
                
                # Último recurso: JavaScript
                try:
                    driver.execute_script(f"arguments[0].value = '{local_codigo}'; arguments[0].dispatchEvent(new Event('change'));", campo_local)
                    logger.info(f"Local da Prestação selecionado via JavaScript: {local_codigo}")
                    time.sleep(3)  # Aumentado para 3 segundos
                    return True
                except Exception as e3:
                    logger.error(f"Erro ao selecionar local via JavaScript: {e3}")
                    return False
                    
            except Exception as e:
                logger.error(f"Erro ao manipular select de Local da Prestação: {e}")
                return False
        else:
            logger.warning(f"Campo Local da Prestação encontrado é do tipo {tag_name}, não suportado")
            return False
    
    except Exception as e:
        logger.error(f"Erro ao preencher local da prestação: {e}")
        return False

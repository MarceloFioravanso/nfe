import time
import random
import logging
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.support.ui import Select

def formatar_valor_monetario(valor):
    """
    Formata um valor numérico para o formato monetário sem pontos nos milhares, 
    apenas com vírgula decimal. Garante que não haja separadores de milhar.
    
    Args:
        valor: Valor numérico a ser formatado
        
    Returns:
        str: Valor formatado como string (ex: 1234.56 -> "1234,56")
    """
    if valor is None or pd.isna(valor):
        return "0,00"
    
    try:
        # Converte para float se for string
        if isinstance(valor, str):
            # Remove possíveis caracteres de formatação
            valor_limpo = valor.replace("R$", "").strip()
            
            # Detecta se já está no formato brasileiro (com vírgula como separador decimal)
            if ',' in valor_limpo and '.' in valor_limpo:
                # Formato "1.234,56" - remove pontos e substitui vírgula por ponto para converter para float
                valor_calc = valor_limpo.replace(".", "").replace(",", ".")
            elif ',' in valor_limpo:
                # Formato "1234,56" - com vírgula como separador decimal
                valor_calc = valor_limpo.replace(",", ".")
            else:
                # Formato "1234.56" ou sem separador decimal
                valor_calc = valor_limpo
                
            try:
                valor = float(valor_calc)
            except ValueError as e:
                logging.warning(f"Erro ao converter valor para float: {e}. Tentando limpeza adicional.")
                # Tenta limpar mais agressivamente, removendo todos os caracteres não numéricos exceto ponto
                import re
                valor_calc_limpo = re.sub(r'[^\d.]', '', valor_calc)
                valor = float(valor_calc_limpo)
        
        # Formata para o padrão simplificado sem pontos nos milhares (1234.56 -> "1234,56")
        # Converte para string com 2 casas decimais, substituindo ponto por vírgula
        # O uso de :.2f garante que não haja separadores de milhar, apenas o decimal
        valor_formatado = f"{valor:.2f}".replace(".", ",")
        
        # Verificação extra para garantir que não haja pontos de milhar
        if '.' in valor_formatado:
            valor_formatado = valor_formatado.replace(".", "")
        
        # Validação final
        # Verifica se o resultado segue o formato esperado: dígitos seguidos por vírgula e dois dígitos
        import re
        if not re.match(r'^\d+,\d{2}$', valor_formatado):
            logging.warning(f"Formato final inválido: '{valor_formatado}', tentando corrigir")
            # Se o formato não estiver correto, tenta uma abordagem direta
            valor_formatado = f"{float(valor):.2f}".replace(".", ",")
            
        return valor_formatado
    except Exception as e:
        logging.warning(f"Erro ao formatar valor monetário: {e}. Retornando valor formatado simples.")
        try:
            # Última tentativa de garantir o formato correto
            if isinstance(valor, (int, float)):
                return f"{valor:.2f}".replace(".", ",")
            else:
                # Remove qualquer formatação existente e converte para o formato desejado
                valor_str = str(valor)
                # Remove todos os pontos (separadores de milhar)
                valor_str = valor_str.replace(".", "")
                # Se houver vírgula, mantém apenas a última
                if ',' in valor_str:
                    partes = valor_str.split(',')
                    if len(partes) > 2:
                        valor_str = partes[0] + ',' + partes[-1]
                # Retorna o valor formatado ou zero se não conseguir converter
                return valor_str.replace(".", ",")
        except:
            return "0,00"

def simular_digitacao_humana(elemento, texto, pressionar_enter=False, pressionar_tab=False):
    """
    Simula digitação humana inserindo caracteres um a um.
    
    Args:
        elemento: Elemento web onde será feita a digitação
        texto: Texto a ser digitado
        pressionar_enter: Se True, pressiona a tecla ENTER após digitar
        pressionar_tab: Se True, pressiona a tecla TAB após digitar
    """
    # Limpa o campo primeiro
    elemento.clear()
    
    # Velocidades de digitação variáveis
    for caractere in texto:
        elemento.send_keys(caractere)
        # Pequena pausa aleatória para simular digitação real
        time.sleep(random.uniform(0.05, 0.15))
    
    # Pausa final após completar a digitação
    time.sleep(random.uniform(0.2, 0.5))
    
    from selenium.webdriver.common.keys import Keys
    
    # Se necessário, pressiona a tecla ENTER
    if pressionar_enter:
        elemento.send_keys(Keys.ENTER)
        # Aguarda o processamento após pressionar ENTER
        time.sleep(3)
    
    # Se necessário, pressiona a tecla TAB
    if pressionar_tab:
        elemento.send_keys(Keys.TAB)
        # Aguarda o processamento após pressionar TAB
        time.sleep(1)

# Mantém a antiga função para compatibilidade
simular_digitacao_humana_servico = simular_digitacao_humana

def preencher_local_prestacao(driver, local_codigo="8561", logger=None):
    """
    Preenche o campo de local da prestação do serviço com o código especificado.
    Após preencher, simula pressionar ENTER e espera 4 segundos para que as opções
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
            'input[name*="local"]',
            'input[id*="local"]',
            'select[name*="local"]',
            'select[id*="local"]',
            'select[name*="municipio"]',
            'select.local-prestacao',
            'input[placeholder*="Local"]',
            'input[name*="LocalPrestacao"]',
            'input[data-cy*="local"]',
            'input[class*="local"]'
        ]
        
        # Primeiro, tenta input
        campo_local = None
        for seletor in local_seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos and elementos[0].is_displayed():
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
                "//th[contains(text(), 'Local')]/following::input[1]",
                "//div[contains(text(), 'Local')]/following::input[1]",
                "//span[contains(text(), 'Local')]/following::input[1]",
                "//*[contains(text(), 'Local da Prestação') or contains(text(), 'Local de Prestação')]/following::input[1]"
            ]
            
            for xpath in xpath_seletores:
                try:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    if elementos and elementos[0].is_displayed():
                        campo_local = elementos[0]
                        logger.info(f"Campo Local da Prestação encontrado com XPath: {xpath}")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar campo com XPath {xpath}: {e}")
        
        if not campo_local:
            logger.warning("Campo Local da Prestação não encontrado, continuando mesmo assim")
            # Salva screenshot para verificação
            salvar_screenshot_servico(driver, "erro_campo_local_nao_encontrado.png", logger)
            return False
        
        # Verificar se é input ou select
        tag_name = campo_local.tag_name.lower()
        
        if tag_name == 'input':
            # Scroll até o elemento para garantir visibilidade
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_local)
            time.sleep(0.5)
            
            # Tenta clicar no campo para garantir o foco
            try:
                campo_local.click()
                time.sleep(0.3)
            except:
                logger.debug("Não foi possível clicar no campo Local da Prestação, continuando mesmo assim")
            
            # Preencher o campo com o código especificado e pressionar ENTER
            campo_local.clear()
            # Usa a versão modificada que pressiona ENTER automaticamente
            simular_digitacao_humana(campo_local, local_codigo, pressionar_enter=True)
            logger.info(f"Local da Prestação preenchido com {local_codigo} e tecla ENTER pressionada")
            
            # Screenshot para verificação
            salvar_screenshot_servico(driver, "apos_preencher_local_prestacao.png", logger)
            
            # Verifica se o campo ainda mantém o foco (se sim, pressiona ENTER novamente)
            try:
                from selenium.webdriver.common.keys import Keys
                active_element = driver.switch_to.active_element
                if active_element == campo_local:
                    logger.info("Campo Local da Prestação ainda com foco, pressionando ENTER novamente")
                    active_element.send_keys(Keys.ENTER)
            except:
                pass
            
            # Aguarda a atualização da página para que as opções de serviço sejam carregadas
            # Tempo aumentado para garantir carregamento completo
            time.sleep(5)
            logger.info("Aguardando 5 segundos para o carregamento completo das opções de serviço")
            return True
            
        elif tag_name == 'select':
            # É um select, tenta selecionar por valor ou texto
            try:
                # Scroll até o elemento para garantir visibilidade
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_local)
                time.sleep(0.5)
                
                select = Select(campo_local)
                
                # Tenta selecionar por valor primeiro
                try:
                    select.select_by_value(local_codigo)
                    logger.info(f"Local da Prestação selecionado por valor: {local_codigo}")
                    # Dispara evento change para garantir atualização da UI
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", campo_local)
                    time.sleep(4)  # Aumentado para 4 segundos para garantir carregamento
                    return True
                except:
                    # Tenta selecionar por texto visível
                    try:
                        for opcao in select.options:
                            if local_codigo in opcao.text:
                                select.select_by_visible_text(opcao.text)
                                logger.info(f"Local da Prestação selecionado por texto: {opcao.text}")
                                # Dispara evento change para garantir atualização da UI
                                driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", campo_local)
                                time.sleep(4)  # Aumentado para 4 segundos
                                return True
                    except Exception as e2:
                        logger.warning(f"Erro ao selecionar local por texto: {e2}")
                
                # Último recurso: JavaScript
                try:
                    driver.execute_script(f"arguments[0].value = '{local_codigo}'; arguments[0].dispatchEvent(new Event('change'));", campo_local)
                    logger.info(f"Local da Prestação selecionado via JavaScript: {local_codigo}")
                    time.sleep(4)  # Aumentado para 4 segundos
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
        import traceback
        logger.error(traceback.format_exc())
        return False

def preencher_codigo_servico(driver, codigo_servico="1701", logger=None):
    """
    Seleciona o código de serviço no formulário.
    
    Args:
        driver: WebDriver do Selenium
        codigo_servico: Código do serviço a ser selecionado (padrão: 1701)
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se o preenchimento foi bem-sucedido, False caso contrário
    """
    if logger is None:
        logger = logging.getLogger('preencher_servico')
    
    try:
        logger.info(f"Selecionando código de serviço {codigo_servico}...")
        
        # Aguarda um momento para garantir que a página está pronta após o Local da Prestação
        time.sleep(2)
        
        # Seletores possíveis para o campo de código de serviço
        servico_seletores = [
            'select[name="ListaServico.codigo"]',
            'select[aria-label="Lista de Serviço"]',
            'select[name*="servico"]',
            'select[id*="servico"]',
            'select[name*="codigo"]',
            'select[name*="lista"]',
            'select.lista-servico',
            'select.input_lista_servico',
            'select[data-cy*="servico"]',
            'select[class*="servico"]'
        ]
        
        # Tenta encontrar o campo de seleção de serviço
        campo_servico = None
        for seletor in servico_seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos and elementos[0].is_displayed():
                    campo_servico = elementos[0]
                    logger.info(f"Campo código de serviço encontrado com seletor: {seletor}")
                    break
            except Exception as e:
                logger.debug(f"Erro ao procurar campo serviço com seletor {seletor}: {e}")
        
        # Se não encontrou, tenta por XPath
        if not campo_servico:
            xpath_seletores = [
                "//label[contains(text(), 'Serviço')]/following::select[1]",
                "//label[contains(text(), 'Lista')]/following::select[1]",
                "//label[contains(text(), 'Código')]/following::select[1]",
                "//th[contains(text(), 'Serviço')]/following::select[1]",
                "//select[contains(@name, 'servico') or contains(@name, 'Servico')]",
                "//div[contains(text(), 'Serviço')]/following::select[1]",
                "//span[contains(text(), 'Serviço')]/following::select[1]"
            ]
            
            for xpath in xpath_seletores:
                try:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    if elementos and elementos[0].is_displayed():
                        campo_servico = elementos[0]
                        logger.info(f"Campo código de serviço encontrado com XPath: {xpath}")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar campo serviço com XPath {xpath}: {e}")
        
        # Se ainda não encontrou, tenta procurar qualquer select na página como último recurso
        if not campo_servico:
            try:
                selects = driver.find_elements(By.TAG_NAME, 'select')
                selects_visiveis = [s for s in selects if s.is_displayed()]
                
                if selects_visiveis:
                    campo_servico = selects_visiveis[0]
                    logger.info(f"Campo código de serviço encontrado como primeiro select visível na página")
            except Exception as e:
                logger.debug(f"Erro ao procurar qualquer select visível: {e}")
        
        if not campo_servico:
            # Salva screenshot para diagnóstico
            salvar_screenshot_servico(driver, "erro_campo_servico_nao_encontrado.png", logger)
            logger.error("Campo de código de serviço não encontrado")
            return False
        
        # Scroll para o elemento ficar visível
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_servico)
            time.sleep(0.5)
        except:
            pass
        
        # Tenta clicar no campo para garantir o foco
        try:
            campo_servico.click()
            time.sleep(0.5)
        except:
            logger.debug("Não foi possível clicar no campo de serviço, continuando mesmo assim")
        
        # Seleciona o código de serviço
        try:
            select = Select(campo_servico)
            
            # Verifica se as opções estão carregadas e espera se necessário
            tentativas = 0
            max_tentativas = 8  # Aumentado para dar mais tempo para carregamento
            
            while tentativas < max_tentativas:
                options = select.options
                if len(options) > 1:  # Tem opções além de "Selecione..."
                    logger.info(f"Opções de serviço carregadas: {len(options)} opções disponíveis")
                    break
                    
                logger.info(f"Aguardando carregamento das opções do serviço (tentativa {tentativas+1}/{max_tentativas})...")
                
                # Adiciona tentativa de reforçar o carregamento das opções
                try:
                    if tentativas > 2:  # A partir da terceira tentativa
                        # Tenta clicar novamente
                        campo_servico.click()
                        logger.info("Tentando forçar o carregamento de opções com click adicional")
                        
                        # Tenta disparar eventos JavaScript para forçar atualização
                        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", campo_servico)
                        driver.execute_script("arguments[0].dispatchEvent(new Event('focus'));", campo_servico)
                except:
                    pass
                
                time.sleep(2)
                tentativas += 1
            
            # Salva screenshot para verificar estado do dropdown
            salvar_screenshot_servico(driver, "dropdown_servico.png", logger)
            
            # Log das opções disponíveis para diagnóstico
            if len(select.options) > 0:
                opcoes_text = [f"{i}:{opt.text}" for i, opt in enumerate(select.options[:20])]  # Mostra até 20 opções
                logger.info(f"Opções disponíveis: {opcoes_text}")
            else:
                logger.warning("Nenhuma opção de serviço disponível")
                salvar_screenshot_servico(driver, "opcoes_servico_indisponiveis.png", logger)
            
            # Tenta selecionar por valor primeiro
            try:
                select.select_by_value(codigo_servico)
                logger.info(f"Código de serviço selecionado por valor: {codigo_servico}")
                time.sleep(1)
                
                # Salva screenshot após seleção bem-sucedida
                salvar_screenshot_servico(driver, "servico_selecionado_por_valor.png", logger)
                return True
            except Exception as e:
                logger.debug(f"Erro ao selecionar serviço por valor: {e}")
                
                # Tenta selecionar por texto visível (procurando pelo código)
                try:
                    for opcao in select.options:
                        if codigo_servico in opcao.text:
                            select.select_by_visible_text(opcao.text)
                            logger.info(f"Código de serviço selecionado por texto: {opcao.text}")
                            time.sleep(1)
                            
                            # Salva screenshot após seleção bem-sucedida
                            salvar_screenshot_servico(driver, "servico_selecionado_por_texto_exato.png", logger)
                            return True
                            
                    # Se não encontrou o código específico, verifica o texto completo das opções
                    textos_esperados = [
                        "1701", 
                        "Assessoria ou consultoria", 
                        "1701 - Assessoria ou consultoria",
                        "Assessoria",
                        "Consultoria"
                    ]
                    
                    for texto in textos_esperados:
                        for opcao in select.options:
                            if texto.lower() in opcao.text.lower():
                                select.select_by_visible_text(opcao.text)
                                logger.info(f"Código de serviço selecionado pelo texto parcial: '{texto}' em '{opcao.text}'")
                                time.sleep(1)
                                
                                # Salva screenshot após seleção bem-sucedida
                                salvar_screenshot_servico(driver, "servico_selecionado_por_texto_parcial.png", logger)
                                return True
                    
                    # Se ainda não encontrou, tenta selecionar a primeira opção válida após a opção "Selecione"
                    if len(select.options) > 1:
                        select.select_by_index(1)  # Seleciona a segunda opção (índice 1)
                        logger.info(f"Selecionou a primeira opção disponível: {select.options[1].text}")
                        time.sleep(1)
                        
                        # Salva screenshot após seleção bem-sucedida
                        salvar_screenshot_servico(driver, "servico_selecionado_primeira_opcao.png", logger)
                        return True
                    
                except Exception as e2:
                    logger.debug(f"Erro ao selecionar serviço por texto: {e2}")
            
            # Último recurso: JavaScript
            try:
                driver.execute_script(f"arguments[0].value = '{codigo_servico}'; arguments[0].dispatchEvent(new Event('change'));", campo_servico)
                logger.info(f"Código de serviço selecionado via JavaScript: {codigo_servico}")
                time.sleep(1)
                
                # Salva screenshot após seleção via JavaScript
                salvar_screenshot_servico(driver, "servico_selecionado_javascript.png", logger)
                return True
            except Exception as e3:
                logger.error(f"Erro ao selecionar serviço via JavaScript: {e3}")
                
                # Tenta clicar no campo e selecionar um índice arbitrário como último recurso
                try:
                    campo_servico.click()
                    time.sleep(0.5)
                    select.select_by_index(1)  # Seleciona a segunda opção
                    logger.info("Selecionou a segunda opção como último recurso")
                    time.sleep(1)
                    
                    # Salva screenshot após seleção por índice
                    salvar_screenshot_servico(driver, "servico_selecionado_ultimo_recurso.png", logger)
                    return True
                except Exception as e4:
                    logger.error(f"Falha em todas as tentativas de selecionar serviço: {e4}")
                    salvar_screenshot_servico(driver, "falha_selecao_servico.png", logger)
                    return False
                
        except Exception as e:
            logger.error(f"Erro ao manipular campo de código de serviço: {e}")
            salvar_screenshot_servico(driver, "erro_manipular_campo_servico.png", logger)
            return False
    
    except Exception as e:
        logger.error(f"Erro ao selecionar código de serviço: {e}")
        import traceback
        logger.error(traceback.format_exc())
        salvar_screenshot_servico(driver, "erro_geral_selecao_servico.png", logger)
        return False

def preencher_valor_servico(driver, dados_nota, logger=None):
    """
    Preenche o valor do serviço no formulário.
    
    Args:
        driver: WebDriver do Selenium
        dados_nota: Dicionário com os dados da nota fiscal
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se o preenchimento foi bem-sucedido, False caso contrário
    """
    if logger is None:
        logger = logging.getLogger('preencher_servico')
    
    try:
        # Obtém o valor do serviço dos dados da nota
        valor_servico = dados_nota.get('valor_servico', '')
        
        # Verifica se o valor está disponível
        if not valor_servico or pd.isna(valor_servico):
            logger.error("Valor do serviço não informado nos dados da nota")
            return False
        
        # Formata o valor para o padrão brasileiro (com vírgula como separador decimal)
        valor_formatado = formatar_valor_monetario(valor_servico)
        
        logger.info(f"Preenchendo valor do serviço: {valor_formatado}")
        
        # Seletores possíveis para o campo de valor do serviço
        valor_seletores = [
            'input[name="valorServico"]',
            'input[aria-label="Valor do Serviço"]',
            'input[name*="valor"]',
            'input[id*="valor"]',
            'input.valor-servico'
        ]
        
        # Tenta encontrar o campo de valor do serviço
        campo_valor = None
        for seletor in valor_seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos:
                    campo_valor = elementos[0]
                    logger.info(f"Campo valor do serviço encontrado com seletor: {seletor}")
                    break
            except Exception as e:
                logger.debug(f"Erro ao procurar campo valor com seletor {seletor}: {e}")
        
        # Se não encontrou, tenta por XPath
        if not campo_valor:
            xpath_seletores = [
                "//label[contains(text(), 'Valor')]/following::input[1]",
                "//th[contains(text(), 'Valor')]/following::input[1]"
            ]
            
            for xpath in xpath_seletores:
                try:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    if elementos:
                        campo_valor = elementos[0]
                        logger.info(f"Campo valor do serviço encontrado com XPath: {xpath}")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar campo valor com XPath {xpath}: {e}")
        
        if not campo_valor:
            logger.error("Campo de valor do serviço não encontrado")
            return False
        
        # Preenche o valor do serviço
        try:
            # Limpa o campo
            campo_valor.clear()
            time.sleep(0.5)
            
            # Preenche usando simulação de digitação humana
            simular_digitacao_humana(campo_valor, valor_formatado)
            logger.info(f"Valor do serviço preenchido: {valor_formatado}")
            return True
                
        except Exception as e:
            logger.error(f"Erro ao preencher valor do serviço: {e}")
            return False
    
    except Exception as e:
        logger.error(f"Erro ao processar preenchimento do valor do serviço: {e}")
        return False
        
def preencher_descricao_servico(driver, dados_nota, logger=None):
    """
    Preenche o campo de discriminação/descrição do serviço.
    
    Args:
        driver: WebDriver do Selenium
        dados_nota: Dicionário com os dados da nota fiscal
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se o preenchimento foi bem-sucedido, False caso contrário
    """
    if logger is None:
        logger = logging.getLogger('preencher_servico')
        
    try:        # Obtém a descrição básica do serviço
        descricao_servico = dados_nota.get('descricao_servico', '')
        if not descricao_servico or pd.isna(descricao_servico):
            logger.warning("Descrição do serviço não informada nos dados, usando descrição padrão")
            descricao_servico = "Serviços prestados conforme contrato."
          # Compõe a data de vencimento a partir dos campos separados (X, Y, Z)
        vencimento_dia = dados_nota.get('vencimento_dia', '')
        vencimento_mes = dados_nota.get('vencimento_mes', '')
        vencimento_ano = dados_nota.get('vencimento_ano', '')
        
        # Formata o vencimento se os componentes existirem
        vencimento = ''
        if vencimento_dia and vencimento_mes and vencimento_ano:
            # Certifica-se de que todos são do tipo correto
            try:
                dia = str(int(vencimento_dia)).zfill(2)
                mes = str(int(vencimento_mes)).zfill(2)
                ano = str(int(vencimento_ano))
                
                # Formata como DD/MM/AAAA
                vencimento = f"{dia}/{mes}/{ano}"
                logger.info(f"Data de vencimento composta: {vencimento}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro ao formatar componentes de data: {e}")
                # Tenta usar o campo vencimento diretamente se disponível
                venc_direto = dados_nota.get('vencimento', '')
                if venc_direto and not pd.isna(venc_direto):
                    if isinstance(venc_direto, pd.Timestamp) or hasattr(venc_direto, 'strftime'):
                        vencimento = venc_direto.strftime("%d/%m/%Y")
        else:
            # Se não tiver componentes separados, tenta o campo direto
            venc_direto = dados_nota.get('vencimento', '')
            if venc_direto and not pd.isna(venc_direto):
                if isinstance(venc_direto, pd.Timestamp) or hasattr(venc_direto, 'strftime'):
                    vencimento = venc_direto.strftime("%d/%m/%Y")
                  # Obtém o número da parcela (da coluna AL)
        parcela = dados_nota.get('parcela', '')
          # Obtém o número do pedido ou ordem de compra
        numero_pedido = dados_nota.get('numero_pedido', '')
        
        # Remove casas decimais do número do pedido, se for um número
        if numero_pedido and not pd.isna(numero_pedido):
            try:
                # Tenta converter para float e depois para int para remover casas decimais
                if isinstance(numero_pedido, (int, float)) or (isinstance(numero_pedido, str) and numero_pedido.replace('.', '', 1).isdigit()):
                    numero_pedido = str(int(float(numero_pedido)))
            except:
                # Se falhar, mantém o valor original
                pass
        
        # Adiciona informações complementares à descrição do serviço
        descricao_completa = [descricao_servico]
        
        # Adiciona linha em branco após a descrição principal
        descricao_completa.append("")
        
        # Adiciona informações de número de pedido (com linha em branco após), somente se válido
        if numero_pedido and not pd.isna(numero_pedido):
            descricao_completa.append(f"Nº PEDIDO/ORDEM DE COMPRA: {numero_pedido}")
            descricao_completa.append("")
        
        # Adiciona informações de vencimento (com linha em branco após)
        if vencimento:
            descricao_completa.append(f"VENCIMENTO: {vencimento}")
            descricao_completa.append("")
            
        # Adiciona informações de parcela (com linha em branco após), somente se válido
        if parcela and not pd.isna(parcela):
            descricao_completa.append(f"PARCELA: {parcela}")
            descricao_completa.append("")
        
        # Adiciona informações de PIX/depósito
        descricao_completa.extend([
            "DADOS PARA PIX OU DEPÓSITO:",
            "",
            "PIX: (51) 99775-6607",
            "BANCO: 748 - SICREDI",
            "AGÊNCIA: 0116", 
            "CONTA: 17240-7",
            "TITULAR: LAFIORAVANSO CONSULTORIA EMPRESARIAL LTDA.",
            "CNPJ: 02.572.042/0001-22"
        ])
        
        # Junta todas as linhas com quebras de linha
        descricao_servico = "\n".join(descricao_completa)
        
        logger.info("Preenchendo discriminação do serviço com informações adicionais...")
        
        # Seletores possíveis para o campo de descrição
        descricao_seletores = [
            'textarea[aria-label="Discriminação do Serviço"]', 
            'textarea[name*="discriminacao"]',
            'textarea[id*="discriminacao"]',
            'textarea[name*="descricao"]',
            'textarea[id*="descricao"]'
        ]
        
        # Tenta encontrar o campo de descrição
        campo_descricao = None
        for seletor in descricao_seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos:
                    campo_descricao = elementos[0]
                    logger.info(f"Campo descrição do serviço encontrado com seletor: {seletor}")
                    break
            except Exception as e:
                logger.debug(f"Erro ao procurar campo descrição com seletor {seletor}: {e}")
                
        # Se não encontrou, tenta por XPath
        if not campo_descricao:
            xpath_seletores = [
                "//label[contains(text(), 'Discriminação')]/following::textarea[1]",
                "//label[contains(text(), 'Descrição')]/following::textarea[1]",
                "//textarea"  # Último recurso: qualquer textarea na página
            ]
            
            for xpath in xpath_seletores:
                try:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    if elementos:
                        campo_descricao = elementos[0]
                        logger.info(f"Campo descrição do serviço encontrado com XPath: {xpath}")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar campo descrição com XPath {xpath}: {e}")
                    
        if not campo_descricao:
            logger.warning("Campo de descrição do serviço não encontrado, continuando mesmo assim")
            return False
            
        # Preenche a descrição do serviço
        try:
            campo_descricao.clear()
            simular_digitacao_humana(campo_descricao, descricao_servico)
            logger.info(f"Descrição do serviço preenchida com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao preencher descrição do serviço: {e}")
            return False
            
    except Exception as e:
        logger.warning(f"Erro ao processar descrição do serviço: {e}")
        return False  # Não falha o processo se a descrição der erro

def preencher_dados_servico(driver, dados_nota, logger=None):
    """
    Preenche os dados do serviço no formulário de emissão de nota fiscal.
    
    Args:
        driver: WebDriver do Selenium
        dados_nota (dict): Dados mapeados da nota fiscal
        logger: Logger opcional
        
    Returns:
        bool: True se o preenchimento foi bem-sucedido, False caso contrário
    """
    if logger is None:
        # Configura um logger básico se nenhum for fornecido
        logger = logging.getLogger('preencher_servico')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
    try:
        logger.info("Iniciando preenchimento dos dados do serviço...")
        
        # Aguarda a página carregar
        time.sleep(2)
        
        # 1. Preencher Local da Prestação com "8561"
        local_ok = preencher_local_prestacao(driver, "8561", logger)
        if not local_ok:
            logger.warning("Falha ao preencher local da prestação, continuando mesmo assim...")
        
        # 2. Selecionar o item "1701" na lista de serviços
        codigo_ok = preencher_codigo_servico(driver, "1701", logger)
        if not codigo_ok:
            logger.error("Falha ao selecionar código do serviço")
            return False
        
        # 3. Preencher o Valor do Serviço
        valor_ok = preencher_valor_servico(driver, dados_nota, logger)
        if not valor_ok:
            logger.error("Falha ao preencher valor do serviço")
            return False
            
        # 4. Preencher a descrição do serviço
        descricao_ok = preencher_descricao_servico(driver, dados_nota, logger)
        if not descricao_ok:
            logger.warning("Falha ao preencher descrição do serviço, continuando mesmo assim...")
        
        logger.info("Dados do serviço preenchidos com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro durante preenchimento dos dados do serviço: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# Importa o módulo de tributos se disponível
try:
    from preencher_tributos import preencher_tributos_federais
    tributos_importados = True
except ImportError:
    tributos_importados = False

# Funções auxiliares para uso direto pelo script principal
def preencher_formulario_servico(driver, dados_nota, logger=None):
    """
    Função auxiliar para ser chamada diretamente no script principal.
    Preenche todos os campos do serviço em uma só chamada.
    
    Args:
        driver: WebDriver do Selenium
        dados_nota: Dicionário com os dados da nota fiscal
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se o preenchimento foi bem-sucedido, False caso contrário
    """
    return preencher_dados_servico(driver, dados_nota, logger)

def preencher_formulario_tributos(driver, dados_nota, logger=None):
    """
    Função auxiliar para preencher os tributos federais.
    
    Args:
        driver: WebDriver do Selenium
        dados_nota: Dicionário com os dados da nota fiscal
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se o preenchimento foi bem-sucedido, False caso contrário
    """
    if tributos_importados:
        return preencher_tributos_federais(driver, dados_nota, logger)
    else:
        if logger:
            logger.warning("Módulo de tributos não disponível. Os campos de tributos não serão preenchidos.")
        return True
    
def salvar_screenshot_servico(driver, nome_arquivo, logger=None):
    """
    Salva um screenshot na pasta de logs
    
    Args:
        driver: WebDriver do Selenium
        nome_arquivo: Nome do arquivo para salvar
        logger: Logger para registro de logs (opcional)
        
    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    if logger is None:
        logger = logging.getLogger('preencher_servico')
        
    try:
        import os
        pasta_screenshots = "logs/imagens"
        # Garante que a pasta existe
        os.makedirs(pasta_screenshots, exist_ok=True)
        
        caminho_completo = os.path.join(pasta_screenshots, nome_arquivo)
        driver.save_screenshot(caminho_completo)
        logger.info(f"Screenshot salvo em {caminho_completo}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar screenshot {nome_arquivo}: {e}")
        return False

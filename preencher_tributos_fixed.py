import time
import logging
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

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

def preencher_tributos_federais(driver, dados_nota, logger=None):
    """
    Preenche os campos de tributos federais (IR, PIS, COFINS, CSLL) e verifica
    o valor líquido calculado.
    
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
        logger.info("Iniciando preenchimento dos tributos federais...")
        wait = WebDriverWait(driver, 10)
        
        # Obtém os valores dos tributos e formata-os corretamente
        # Tenta múltiplas chaves para cada tributo para compatibilidade
        valor_ir = formatar_valor_monetario(
            dados_nota.get('irrf', 
                dados_nota.get('valor_ir', 
                    dados_nota.get('ir', 
                        dados_nota.get('valor_irrf', 0)
                    )
                )
            )
        )
        
        valor_pis = formatar_valor_monetario(
            dados_nota.get('pis', 
                dados_nota.get('valor_pis', 
                    dados_nota.get('pispasep', 
                        dados_nota.get('valor_pispasep', 0)
                    )
                )
            )
        )
        
        valor_cofins = formatar_valor_monetario(
            dados_nota.get('cofins', 
                dados_nota.get('valor_cofins', 
                    dados_nota.get('valor_cof', 0)
                )
            )
        )
        
        valor_csll = formatar_valor_monetario(
            dados_nota.get('csll', 
                dados_nota.get('valor_csll', 
                    dados_nota.get('contribuicao', 
                        dados_nota.get('valor_contribuicao', 0)
                    )
                )
            )
        )
        
        # Exibe os valores formatados para debug
        logger.info(f"Valores dos tributos (formatados):")
        logger.info(f"IR: {valor_ir}")
        logger.info(f"PIS: {valor_pis}")
        logger.info(f"COFINS: {valor_cofins}")
        logger.info(f"CSLL: {valor_csll}")
        
        # Calcula a soma dos tributos para conferência posterior
        def converter_para_float(valor_texto):
            try:
                if isinstance(valor_texto, str):
                    return float(valor_texto.replace(".", "").replace(",", "."))
                elif isinstance(valor_texto, (int, float)):
                    return float(valor_texto)
                return 0.0
            except:
                return 0.0
        
        total_tributos = (
            converter_para_float(valor_ir) + 
            converter_para_float(valor_pis) + 
            converter_para_float(valor_cofins) + 
            converter_para_float(valor_csll)
        )
        logger.info(f"Total de tributos calculado: {total_tributos:.2f}")
        
        # Valor bruto do serviço
        valor_servico = converter_para_float(dados_nota.get('valor_servico', dados_nota.get('valor_bruto', 0)))
        logger.info(f"Valor bruto do serviço: {valor_servico:.2f}")
        
        # Calcula o valor líquido esperado (valor serviço - tributos)
        valor_liquido_calculado_internamente = valor_servico - total_tributos
        logger.info(f"Valor líquido calculado internamente: {valor_liquido_calculado_internamente:.2f}")        # Procura pela página ou seção de tributos federais
        # Verifica se já está na tela correta ou precisa clicar em algum botão
        try:
            # Seletores expandidos para detectar campos de tributos com diferentes formatos
            campos_tributos_seletores = [
                'input[name*="IR"], input[name*="PIS"], input[name*="COFINS"], input[name*="CSLL"], input[name*="irrf"], input[name*="pis"], input[name*="cofins"], input[name*="csll"]',
                'input[id*="IR"], input[id*="PIS"], input[id*="COFINS"], input[id*="CSLL"], input[id*="irrf"], input[id*="pis"], input[id*="cofins"], input[id*="csll"]',
                'input[aria-label*="IR"], input[aria-label*="PIS"], input[aria-label*="COFINS"], input[aria-label*="CSLL"]',
                'input[placeholder*="IR"], input[placeholder*="PIS"], input[placeholder*="COFINS"], input[placeholder*="CSLL"]'
            ]
            
            # Verifica todos os seletores para campos de tributos
            campos_visiveis = []
            for seletor in campos_tributos_seletores:
                campos_pre_verificacao = driver.find_elements(By.CSS_SELECTOR, seletor)
                campos_visiveis.extend([c for c in campos_pre_verificacao if c.is_displayed()])
                if campos_visiveis:
                    logger.info(f"Campos de tributos encontrados com seletor: {seletor}")
                    break
            
            if not campos_visiveis:
                logger.info("Nenhum campo de tributo visível, tentando encontrar botão para avançar...")
                
                # Verifica se está em uma tela de abas e se existe uma aba de tributos para clicar
                abas_tributos = [
                    "//a[contains(text(), 'Tributos')]",
                    "//a[contains(text(), 'Tributação')]",
                    "//li[contains(text(), 'Tributos')]",
                    "//div[contains(@class, 'tab')][contains(text(), 'Tributo')]",
                    "//span[contains(text(), 'Tributos')]"
                ]
                
                for xpath_aba in abas_tributos:
                    elementos = driver.find_elements(By.XPATH, xpath_aba)
                    elementos_visiveis = [e for e in elementos if e.is_displayed() and e.is_enabled()]
                    
                    if elementos_visiveis:
                        logger.info(f"Encontrou aba de tributos: {xpath_aba}")
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elementos_visiveis[0])
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", elementos_visiveis[0])
                            logger.info("Clicou na aba de tributos")
                            time.sleep(3)  # Aguarda a atualização da UI
                            
                            # Verifica novamente os campos após clicar na aba
                            for seletor in campos_tributos_seletores:
                                campos = driver.find_elements(By.CSS_SELECTOR, seletor)
                                campos_visiveis = [c for c in campos if c.is_displayed()]
                                if campos_visiveis:
                                    break
                                    
                            if campos_visiveis:
                                logger.info("Campos de tributos encontrados após clicar na aba")
                                break
                        except Exception as e:
                            logger.warning(f"Erro ao clicar na aba de tributos: {e}")
                
                # Se ainda não encontrou campos, procura por botões de próximo/avançar
                if not campos_visiveis:
                    botoes_proxima_etapa = [
                        "//button[contains(text(), 'Próximo')]",
                        "//button[contains(text(), 'Avançar')]",
                        "//a[contains(text(), 'Tributação')]",
                        "//button[contains(text(), 'Tributos')]",
                        "//a[contains(@href, 'tributo')]",
                        "//input[contains(@value, 'Próximo')]",
                        "//input[contains(@value, 'Avançar')]",
                        "//button[contains(@class, 'next')]",
                        "//button[contains(@class, 'avancar')]",
                        "//button[contains(@id, 'next')]",
                        "//button[contains(@id, 'avancar')]",
                        "//span[contains(text(), 'Próximo')]/parent::button",
                        "//span[contains(text(), 'Avançar')]/parent::button",
                        "//i[contains(@class, 'arrow-right')]/parent::button",
                        "//i[contains(@class, 'fa-arrow-right')]/parent::button"
                    ]
                    
                    botao_encontrado = False
                    for xpath_botao in botoes_proxima_etapa:
                        botoes = driver.find_elements(By.XPATH, xpath_botao)
                        botoes_visiveis = [b for b in botoes if b.is_displayed() and b.is_enabled()]
                        
                        if botoes_visiveis:
                            logger.info(f"Encontrou botão para avançar para os tributos: {xpath_botao}")
                            try:
                                # Scroll para o botão ficar visível
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botoes_visiveis[0])
                                time.sleep(1)
                                
                                # Tenta diferentes formas de clicar no botão
                                try:
                                    botoes_visiveis[0].click()
                                    logger.info("Clicou no botão para avançar para os tributos (clique direto)")
                                except Exception as e_click:
                                    logger.debug(f"Clique direto falhou: {e_click}, tentando com JavaScript")
                                    # Se o clique direto falhar, tenta com JavaScript
                                    driver.execute_script("arguments[0].click();", botoes_visiveis[0])
                                    logger.info("Clicou no botão para avançar para os tributos (via JavaScript)")
                                
                                # Implementa verificação adicional para garantir que o clique foi registrado
                                pre_url = driver.current_url
                                pre_html = driver.page_source[:100]  # Só uma pequena amostra para comparação
                                
                                # Aguarda mais tempo para a página carregar
                                time.sleep(5)
                                
                                # Verifica se houve alguma mudança na página
                                pos_url = driver.current_url
                                pos_html = driver.page_source[:100]
                                
                                if pre_url != pos_url or pre_html != pos_html:
                                    logger.info("Página foi atualizada após clicar no botão")
                                else:
                                    logger.warning("Nenhuma mudança detectada após clicar no botão, tentando novamente")
                                    # Tenta um terceiro método de clique
                                    try:
                                        from selenium.webdriver.common.action_chains import ActionChains
                                        actions = ActionChains(driver)
                                        actions.move_to_element(botoes_visiveis[0]).click().perform()                                        logger.info("Tentativa de clique via ActionChains")
                                        time.sleep(5)
                                    except Exception as e_action:
                                        logger.warning(f"Erro na tentativa ActionChains: {e_action}")
                                
                                botao_encontrado = True
                                
                                # Salva um screenshot após avançar
                                try:
                                    driver.save_screenshot("logs/imagens/apos_avanco_tributos.png")
                                    logger.info("Screenshot salvo após avançar para os tributos")
                                except Exception as e_ss:
                                    logger.debug(f"Erro ao salvar screenshot: {e_ss}")
                                    
                                break
                            except Exception as e:
                                logger.warning(f"Erro ao clicar no botão de próxima etapa: {e}")
                    
                    # Se não encontrou nenhum botão específico, tenta uma abordagem genérica
                    if not botao_encontrado:
                        # Procura por qualquer botão visível que possa ser o próximo
                        logger.info("Tentando encontrar qualquer botão de avançar...")
                        botoes_genericos = driver.find_elements(By.TAG_NAME, "button")
                        botoes_inputs = driver.find_elements(By.TAG_NAME, "input")
                        botoes_as = driver.find_elements(By.TAG_NAME, "a")  # Links também podem ser botões
                        
                        todos_botoes = botoes_genericos + botoes_inputs + botoes_as
                        botoes_possiveis = []
                        
                        for botao in todos_botoes:
                            try:
                                if botao.is_displayed() and botao.is_enabled():
                                    texto = botao.text.lower() if hasattr(botao, 'text') and botao.text else ""
                                    valor = botao.get_attribute("value").lower() if botao.get_attribute("value") else ""
                                    classe = botao.get_attribute("class").lower() if botao.get_attribute("class") else ""
                                    id_botao = botao.get_attribute("id").lower() if botao.get_attribute("id") else ""
                                    
                                    if ("prox" in texto or "avan" in texto or "next" in texto or "seguinte" in texto or
                                        "prox" in valor or "avan" in valor or "next" in valor or "seguinte" in valor or
                                        "prox" in classe or "avan" in classe or "next" in classe or "btn-next" in classe or
                                        "prox" in id_botao or "avan" in id_botao or "next" in id_botao):
                                        botoes_possiveis.append(botao)
                            except Exception as e_btn:
                                logger.debug(f"Erro ao analisar botão: {e_btn}")
                                continue
                        
                        if botoes_possiveis:
                            try:
                                logger.info(f"Encontrados {len(botoes_possiveis)} botões possíveis de avançar")
                                # Clica no primeiro botão possível
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", botoes_possiveis[0])
                                time.sleep(1)
                                
                                # Tenta três métodos de clique
                                try:
                                    # 1. Clique direto
                                    botoes_possiveis[0].click()
                                    logger.info("Clicou em botão genérico para avançar (clique direto)")
                                except:
                                    try:
                                        # 2. Clique via JavaScript
                                        driver.execute_script("arguments[0].click();", botoes_possiveis[0])
                                        logger.info("Clicou em botão genérico para avançar (via JavaScript)")
                                    except:
                                        # 3. Clique via ActionChains
                                        from selenium.webdriver.common.action_chains import ActionChains
                                        actions = ActionChains(driver)
                                        actions.move_to_element(botoes_possiveis[0]).click().perform()
                                        logger.info("Clicou em botão genérico para avançar (via ActionChains)")
                                
                                # Aguarda carregamento
                                time.sleep(5)
                                
                                # Salva screenshot
                                try:
                                    driver.save_screenshot("logs/imagens/apos_clique_generico.png")
                                    logger.info("Screenshot salvo após clique em botão genérico")
                                except:
                                    pass
                            except Exception as e:
                                logger.warning(f"Erro ao clicar em botão genérico: {e}")
            else:
                logger.info("Os campos de tributos já estão visíveis, não é necessário avançar")
        except Exception as e:
            logger.debug(f"Erro ao procurar botão para avançar para os tributos: {e}")
            
        # Aguarda um momento extra para garantir que qualquer evento JavaScript seja completado
        time.sleep(5)  # Aumentado de 3 para 5 segundos para garantir carregamento completo
          # Verifica se existem iframes que possam conter os campos de tributos
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        if frames:
            logger.info(f"Encontrados {len(frames)} iframes na página, verificando se contêm campos de tributos")
            
            # Salva o HTML atual para diagnóstico
            try:
                html_content = driver.page_source
                import os
                os.makedirs("logs/html", exist_ok=True)
                with open("logs/html/antes_verificacao_iframe.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("HTML salvo antes da verificação de iframes")
            except Exception as e_html:
                logger.debug(f"Erro ao salvar HTML: {e_html}")
            
            # Guarda o contexto atual
            driver.switch_to.default_content()  # Garante que estamos na página principal
            
            # Armazena os iframes que contêm campos de tributos
            iframes_com_campos = []
            
            # Seletores expandidos para campos de tributos (tanto campos diretamente visíveis quanto campos dentro de iframes)
            campo_seletores_css = [
                'input[name*="IR"], input[name*="PIS"], input[name*="COFINS"], input[name*="CSLL"]',
                'input[id*="IR"], input[id*="PIS"], input[id*="COFINS"], input[id*="CSLL"]',
                'input[name*="irrf"], input[name*="pis"], input[name*="cofins"], input[name*="csll"]',
                'input[id*="irrf"], input[id*="pis"], input[id*="cofins"], input[id*="csll"]',
                'input[aria-label*="IR"], input[aria-label*="PIS"], input[aria-label*="COFINS"], input[aria-label*="CSLL"]',
                'input[placeholder*="IR"], input[placeholder*="PIS"], input[placeholder*="COFINS"], input[placeholder*="CSLL"]',
                'input[type="text"][name*="trib"], input[type="number"][name*="trib"]'
            ]
            
            # Tenta cada iframe
            for i, frame in enumerate(frames):
                try:
                    logger.info(f"Verificando iframe {i+1}/{len(frames)}")
                    driver.switch_to.default_content()  # Volta ao contexto principal
                    
                    # Tenta obter ID ou nome do iframe para diagnóstico
                    try:
                        frame_id = frame.get_attribute("id") or "sem-id"
                        frame_name = frame.get_attribute("name") or "sem-nome"
                        logger.info(f"Iframe {i+1}: id='{frame_id}', name='{frame_name}'")
                    except Exception as e_attr:
                        logger.debug(f"Não foi possível obter atributos do iframe {i+1}: {e_attr}")
                    
                    # Tenta mudar para o iframe
                    driver.switch_to.frame(frame)
                    
                    # Verifica se o iframe contém campos de tributos usando múltiplos seletores
                    campos_encontrados = False
                    for seletor in campo_seletores_css:
                        try:
                            campos_teste = driver.find_elements(By.CSS_SELECTOR, seletor)
                            campos_visiveis = [c for c in campos_teste if c.is_displayed()]
                            
                            if campos_visiveis:
                                logger.info(f"Campos de tributos encontrados no iframe {i+1} usando seletor: {seletor}")
                                campos_encontrados = True
                                iframes_com_campos.append(i)
                                break
                        except Exception as e_sel:
                            logger.debug(f"Erro ao usar seletor {seletor} no iframe {i+1}: {e_sel}")
                    
                    # Se não encontrou com CSS, tenta com XPath
                    if not campos_encontrados:
                        xpath_seletores = [
                            "//input[contains(@name, 'IR') or contains(@name, 'PIS') or contains(@name, 'COFINS') or contains(@name, 'CSLL')]",
                            "//input[contains(@id, 'IR') or contains(@id, 'PIS') or contains(@id, 'COFINS') or contains(@id, 'CSLL')]",
                            "//input[contains(@name, 'irrf') or contains(@name, 'pis') or contains(@name, 'cofins') or contains(@name, 'csll')]",
                            "//input[contains(@placeholder, 'IR') or contains(@placeholder, 'PIS') or contains(@placeholder, 'COFINS') or contains(@placeholder, 'CSLL')]",
                            "//label[contains(text(), 'IR') or contains(text(), 'PIS') or contains(text(), 'COFINS') or contains(text(), 'CSLL')]/following::input[1]",
                            "//div[contains(text(), 'Tributos Federais') or contains(text(), 'Tributos')]//input",
                            "//fieldset[contains(.,'Tributos')]//input",
                            "//table[contains(.,'Tributos')]//input",
                            "//h3[contains(text(), 'Tributos')]/following::input",
                            "//legend[contains(text(), 'Tributos')]/following::input"
                        ]
                        
                        for xpath in xpath_seletores:
                            try:
                                elementos = driver.find_elements(By.XPATH, xpath)
                                elementos_visiveis = [e for e in elementos if e.is_displayed()]
                                
                                if elementos_visiveis:
                                    logger.info(f"Campos de tributos encontrados no iframe {i+1} usando XPath: {xpath}")
                                    campos_encontrados = True
                                    iframes_com_campos.append(i)
                                    break
                            except Exception as e_xpath:
                                logger.debug(f"Erro ao usar XPath {xpath} no iframe {i+1}: {e_xpath}")
                    
                    # Para diagnóstico avançado, procura por qualquer texto que mencione os tributos
                    if not campos_encontrados:
                        try:
                            elemento_texto_tributos = driver.find_elements(By.XPATH, 
                                "//*[contains(text(), 'IR') or contains(text(), 'PIS') or contains(text(), 'COFINS') or contains(text(), 'CSLL') or contains(text(), 'Tributo')]")
                            elementos_visiveis = [e for e in elemento_texto_tributos if e.is_displayed()]
                            
                            if elementos_visiveis:
                                logger.info(f"Texto relacionado a tributos encontrado no iframe {i+1}, mas não foram encontrados campos de input")
                                for el in elementos_visiveis[:3]:  # Limita a 3 elementos para não poluir o log
                                    try:
                                        logger.info(f"Texto encontrado: '{el.text}', tag: {el.tag_name}")
                                    except:
                                        pass
                        except Exception as e_texto:
                            logger.debug(f"Erro ao buscar textos de tributos no iframe {i+1}: {e_texto}")
                    
                    # Para diagnóstico, captura o HTML do iframe atual
                    try:
                        iframe_html = driver.page_source
                        with open(f"logs/html/iframe_{i+1}.html", "w", encoding="utf-8") as f:
                            f.write(iframe_html)
                        logger.info(f"HTML do iframe {i+1} salvo para análise")
                    except Exception as e_iframe_html:
                        logger.debug(f"Erro ao salvar HTML do iframe {i+1}: {e_iframe_html}")
                    
                    # Volta ao contexto principal apenas se não encontrou campos
                    if not campos_encontrados:
                        driver.switch_to.default_content()
                    else:
                        # Se encontrou campos, mantém o contexto neste iframe
                        logger.info(f"Mantendo o contexto no iframe {i+1} onde foram encontrados campos de tributos")
                        break
                        
                except Exception as e:
                    logger.debug(f"Erro ao verificar iframe {i+1}: {e}")
                    # Volta ao contexto principal em caso de erro
                    try:
                        driver.switch_to.default_content()
                    except Exception as e_switch:
                        logger.debug(f"Erro ao voltar ao contexto principal: {e_switch}")
            
            # Se verificou todos os iframes e não encontrou campos, volta ao contexto principal
            if not iframes_com_campos:
                logger.warning("Nenhum campo de tributo encontrado nos iframes, voltando ao contexto principal")
                try:
                    driver.switch_to.default_content()
                except Exception as e_switch:
                    logger.debug(f"Erro ao voltar ao contexto principal: {e_switch}")
            
            # Salva screenshot após verificação de iframes
            try:
                driver.save_screenshot("logs/imagens/verificacao_iframes.png")
                logger.info("Screenshot salvo após verificação de iframes")
            except Exception as e_ss:
                logger.debug(f"Erro ao salvar screenshot: {e_ss}")
        
        # Mapeamento dos campos de tributos federais com seletores mais abrangentes
        campos_tributos = {
            'IR': {
                'seletor': 'input[aria-label*="IR"], input[name="Valores.tributoFederalIr"], input[name*="IR"], input[id*="IR"], input[id*="IRRF"], input[placeholder*="IR"], input[name*="irrf"], input[id*="irrf"], input[name*="Irrf"], input[class*="ir"], input[class*="irrf"], input[data-cy*="ir"], input[data-cy*="irrf"], input[data-name*="IR"], input[data-id*="IR"], input[data-target*="IR"], input[data-field*="IR"], input[title*="IR"], input[aria-describedby*="IR"], input[name*="retencao"][name*="IR"], input[name*="imposto"][name*="renda"]',
                'valor': valor_ir,
                'obrigatorio': False
            },
            'PIS': {
                'seletor': 'input[aria-label*="PIS"], input[name="Valores.tributoFederalPis"], input[name*="PIS"], input[id*="PIS"], input[placeholder*="PIS"], input[name*="pis"], input[id*="pis"], input[class*="pis"], input[data-cy*="pis"], input[data-name*="PIS"], input[data-id*="PIS"], input[data-target*="PIS"], input[data-field*="PIS"], input[title*="PIS"], input[aria-describedby*="PIS"], input[name*="retencao"][name*="PIS"]',
                'valor': valor_pis,
                'obrigatorio': False
            },
            'COFINS': {
                'seletor': 'input[aria-label*="COFINS"], input[name="Valores.tributoFederalCofins"], input[name*="COFINS"], input[id*="COFINS"], input[placeholder*="COFINS"], input[name*="cofins"], input[id*="cofins"], input[class*="cofins"], input[data-cy*="cofins"], input[data-name*="COFINS"], input[data-id*="COFINS"], input[data-target*="COFINS"], input[data-field*="COFINS"], input[title*="COFINS"], input[aria-describedby*="COFINS"], input[name*="retencao"][name*="COFINS"]',
                'valor': valor_cofins,
                'obrigatorio': False
            },
            'CSLL': {
                'seletor': 'input[aria-label*="Contribuição Social"], input[name="Valores.tributoFederalContribuicaoSocial"], input[name*="CSLL"], input[id*="CSLL"], input[name*="ContribuicaoSocial"], input[placeholder*="Contribuição"], input[placeholder*="CSLL"], input[name*="csll"], input[id*="csll"], input[name*="contribuicao"], input[class*="csll"], input[class*="contribuicao"], input[data-cy*="csll"], input[data-cy*="contribuicao"], input[data-name*="CSLL"], input[data-id*="CSLL"], input[data-target*="CSLL"], input[data-field*="CSLL"], input[title*="CSLL"], input[aria-describedby*="CSLL"], input[name*="retencao"][name*="CSLL"], input[name*="contribuicao"][name*="social"]',
                'valor': valor_csll,
                'obrigatorio': False
            }
        }
        
        # Tenta encontrar todos os campos antes de preencher
        campos_encontrados = {}
        for nome_campo, config in campos_tributos.items():
            try:
                # Expande os seletores para aumentar a chance de encontrar o campo
                seletores_expandidos = config['seletor'].split(', ')
                
                for seletor in seletores_expandidos:
                    elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                    elementos_visiveis = []
                    
                    # Verifica quais elementos estão realmente visíveis
                    for elem in elementos:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                elementos_visiveis.append(elem)
                        except:
                            pass
                            
                    if elementos_visiveis:
                        campos_encontrados[nome_campo] = elementos_visiveis[0]
                        logger.info(f"Campo {nome_campo} encontrado com seletor: {seletor}")
                        break
            except Exception as e:
                logger.debug(f"Erro ao procurar campo {nome_campo}: {e}")
                  # Se não encontrou por CSS, tenta por XPath com expressões mais abrangentes
        if not campos_encontrados or len(campos_encontrados) < len(campos_tributos):
            xpath_campos = {
                'IR': [
                    # Busca por rótulos seguidos por input
                    "//label[contains(text(), 'IR') or contains(text(), 'IRRF') or contains(text(), 'Imposto de Renda')]/following::input[1]",
                    "//span[contains(text(), 'IR') or contains(text(), 'IRRF')]/following::input[1]",
                    "//div[contains(text(), 'IR') or contains(text(), 'IRRF')]/following::input[1]",
                    "//td[contains(text(), 'IR') or contains(text(), 'IRRF')]/following::input[1]",
                    "//th[contains(text(), 'IR') or contains(text(), 'IRRF')]/following::input[1]",
                    # Busca em tabelas
                    "//tr[contains(.,'IR') or contains(.,'IRRF')]//input",
                    "//tr[contains(.,'Imposto de Renda')]//input",
                    # Busca por elementos próximos
                    "//*[contains(text(), 'IR') or contains(text(), 'IRRF')]/parent::*/following::input[1]",
                    "//*[contains(text(), 'IR') or contains(text(), 'IRRF')]/parent::*/parent::*/following::input[1]",
                    # Busca em seção de tributos
                    "//fieldset[contains(.,'Tributo')]//input[contains(@name,'IR') or contains(@name,'irrf') or contains(@id,'IR') or contains(@id,'irrf')]",
                    "//div[contains(.,'Tributo')]//input[contains(@name,'IR') or contains(@name,'irrf') or contains(@id,'IR') or contains(@id,'irrf')]"
                ],
                'PIS': [
                    # Busca por rótulos seguidos por input
                    "//label[contains(text(), 'PIS')]/following::input[1]",
                    "//span[contains(text(), 'PIS')]/following::input[1]",
                    "//div[contains(text(), 'PIS')]/following::input[1]",
                    "//td[contains(text(), 'PIS')]/following::input[1]",
                    "//th[contains(text(), 'PIS')]/following::input[1]",
                    # Busca em tabelas
                    "//tr[contains(.,'PIS')]//input",
                    # Busca por elementos próximos
                    "//*[contains(text(), 'PIS')]/parent::*/following::input[1]",
                    "//*[contains(text(), 'PIS')]/parent::*/parent::*/following::input[1]",
                    # Busca em seção de tributos
                    "//fieldset[contains(.,'Tributo')]//input[contains(@name,'PIS') or contains(@name,'pis') or contains(@id,'PIS') or contains(@id,'pis')]",
                    "//div[contains(.,'Tributo')]//input[contains(@name,'PIS') or contains(@name,'pis') or contains(@id,'PIS') or contains(@id,'pis')]"
                ],
                'COFINS': [
                    # Busca por rótulos seguidos por input
                    "//label[contains(text(), 'COFINS')]/following::input[1]",
                    "//span[contains(text(), 'COFINS')]/following::input[1]",
                    "//div[contains(text(), 'COFINS')]/following::input[1]",
                    "//td[contains(text(), 'COFINS')]/following::input[1]",
                    "//th[contains(text(), 'COFINS')]/following::input[1]",
                    # Busca em tabelas
                    "//tr[contains(.,'COFINS')]//input",
                    # Busca por elementos próximos
                    "//*[contains(text(), 'COFINS')]/parent::*/following::input[1]",
                    "//*[contains(text(), 'COFINS')]/parent::*/parent::*/following::input[1]",
                    # Busca em seção de tributos
                    "//fieldset[contains(.,'Tributo')]//input[contains(@name,'COFINS') or contains(@name,'cofins') or contains(@id,'COFINS') or contains(@id,'cofins')]",
                    "//div[contains(.,'Tributo')]//input[contains(@name,'COFINS') or contains(@name,'cofins') or contains(@id,'COFINS') or contains(@id,'cofins')]"
                ],
                'CSLL': [
                    # Busca por rótulos seguidos por input
                    "//label[contains(text(), 'CSLL') or contains(text(), 'Contribuição') or contains(text(), 'Social')]/following::input[1]",
                    "//span[contains(text(), 'CSLL') or contains(text(), 'Contribuição') or contains(text(), 'Social')]/following::input[1]",
                    "//div[contains(text(), 'CSLL') or contains(text(), 'Contribuição') or contains(text(), 'Social')]/following::input[1]",
                    "//td[contains(text(), 'CSLL') or contains(text(), 'Contribuição') or contains(text(), 'Social')]/following::input[1]",
                    "//th[contains(text(), 'CSLL') or contains(text(), 'Contribuição') or contains(text(), 'Social')]/following::input[1]",
                    # Busca em tabelas
                    "//tr[contains(.,'CSLL')]//input",
                    "//tr[contains(.,'Contribuição Social')]//input",
                    # Busca por elementos próximos
                    "//*[contains(text(), 'CSLL') or contains(text(), 'Contribuição Social')]/parent::*/following::input[1]",
                    "//*[contains(text(), 'CSLL') or contains(text(), 'Contribuição Social')]/parent::*/parent::*/following::input[1]",
                    # Busca em seção de tributos
                    "//fieldset[contains(.,'Tributo')]//input[contains(@name,'CSLL') or contains(@name,'csll') or contains(@name,'contribuicao') or contains(@id,'CSLL') or contains(@id,'csll')]",
                    "//div[contains(.,'Tributo')]//input[contains(@name,'CSLL') or contains(@name,'csll') or contains(@name,'contribuicao') or contains(@id,'CSLL') or contains(@id,'csll')]"
                ]
            }
            
            for nome_campo, xpaths in xpath_campos.items():
                if nome_campo not in campos_encontrados:
                    for xpath in xpaths:
                        try:
                            elementos = driver.find_elements(By.XPATH, xpath)
                            elementos_visiveis = [e for e in elementos if e.is_displayed()]
                            if elementos_visiveis:
                                campos_encontrados[nome_campo] = elementos_visiveis[0]
                                logger.info(f"Campo {nome_campo} encontrado com XPath: {xpath}")
                                break
                        except Exception as e:
                            logger.debug(f"Erro ao procurar campo {nome_campo} por XPath {xpath}: {e}")
          # Tentativa adicional: buscar por inputs numéricos na ordem esperada
        if not campos_encontrados or len(campos_encontrados) < len(campos_tributos):
            logger.info("Tentando estratégia alternativa: buscar por inputs numéricos")
            
            # Busca todos os inputs que aceitam números, com seletores mais abrangentes
            inputs_numericos = driver.find_elements(By.CSS_SELECTOR, 
                'input[type="number"], input[type="text"], input:not([type]), input[pattern*="[0-9]"], input.valor, input.money, input.currency, input[step]')
            
            # Filtra apenas os visíveis e habilitados
            inputs_visiveis = []
            inputs_com_atributos = []
            for inp in inputs_numericos:
                try:
                    if inp.is_displayed() and inp.is_enabled() and inp not in campos_encontrados.values():
                        # Verifica se não é um campo que já sabemos que tem outra função
                        placeholder = (inp.get_attribute("placeholder") or "").lower()
                        name = (inp.get_attribute("name") or "").lower()
                        id_campo = (inp.get_attribute("id") or "").lower()
                        classe = (inp.get_attribute("class") or "").lower()
                        data_atributos = {}
                        
                        # Coleta todos os atributos data-* para análise
                        for attr in ["data-name", "data-id", "data-field", "data-target", "data-label"]:
                            data_atributos[attr] = (inp.get_attribute(attr) or "").lower()
                        
                        # Verifica se não é um campo que sabemos que tem outra função
                        if any(termo in placeholder or termo in name or termo in id_campo for termo in
                            ["valor serv", "bruto", "liquido", "total", "nota", "documento"]):
                            continue
                        
                        # Analisa se pode ser um campo de tributo baseado em seus atributos
                        pontuacao = 0
                        for palavra in ["ir", "irrf", "pis", "cofins", "csll", "contribuicao", "tributo"]:
                            if palavra in name or palavra in id_campo or palavra in placeholder:
                                pontuacao += 5  # Alta pontuação para atributos principais
                            if palavra in classe:
                                pontuacao += 3  # Pontuação média para classe
                            for attr_valor in data_atributos.values():
                                if palavra in attr_valor:
                                    pontuacao += 2  # Pontuação para data-atributos
                        
                        # Se tiver alta pontuação, é um bom candidato
                        if pontuacao > 0:
                            inputs_com_atributos.append((inp, pontuacao, name, id_campo))
                        
                        # Adiciona à lista geral
                        inputs_visiveis.append(inp)
                except Exception as e_inp:
                    logger.debug(f"Erro ao analisar input: {e_inp}")
                    pass
            
            # Primeiro tenta pelos inputs com atributos que podem indicar tributos
            if inputs_com_atributos:
                logger.info(f"Encontrados {len(inputs_com_atributos)} inputs com atributos relacionados a tributos")
                # Ordena pela pontuação (maior primeiro)
                inputs_com_atributos.sort(key=lambda x: x[1], reverse=True)
                
                # Identifica campos específicos pelo nome/id
                for inp, pontuacao, name, id_campo in inputs_com_atributos:
                    if "ir" in name or "ir" in id_campo or "irrf" in name or "irrf" in id_campo:
                        if "IR" not in campos_encontrados:
                            campos_encontrados["IR"] = inp
                            logger.info(f"Campo IR associado ao input por atributo (pontuação: {pontuacao})")
                    elif "pis" in name or "pis" in id_campo:
                        if "PIS" not in campos_encontrados:
                            campos_encontrados["PIS"] = inp
                            logger.info(f"Campo PIS associado ao input por atributo (pontuação: {pontuacao})")
                    elif "cofins" in name or "cofins" in id_campo:
                        if "COFINS" not in campos_encontrados:
                            campos_encontrados["COFINS"] = inp
                            logger.info(f"Campo COFINS associado ao input por atributo (pontuação: {pontuacao})")
                    elif "csll" in name or "csll" in id_campo or "contribuicao" in name or "contribuicao" in id_campo:
                        if "CSLL" not in campos_encontrados:
                            campos_encontrados["CSLL"] = inp
                            logger.info(f"Campo CSLL associado ao input por atributo (pontuação: {pontuacao})")
            
            # Se ainda não encontrou todos os campos, tenta pelo posicionamento
            nomes_campos = ["IR", "PIS", "COFINS", "CSLL"]
            faltantes = [nome for nome in nomes_campos if nome not in campos_encontrados]
            
            if faltantes and len(inputs_visiveis) >= len(faltantes):
                logger.info(f"Encontrados {len(inputs_visiveis)} inputs numéricos visíveis para preencher {len(faltantes)} campos faltantes")
                
                # Caso especial: tenta verificar se os inputs seguem uma ordem lógica
                # Verifica se estão todos agrupados (possivelmente em sequência numa tabela)
                inputs_organizados = []
                try:
                    # Ordena por posição vertical, depois horizontal
                    inputs_organizados = sorted(inputs_visiveis, 
                                           key=lambda e: (e.location['y'], e.location['x']))
                    
                    # Identifica grupos de inputs próximos (provavelmente na mesma linha/tabela)
                    grupos = []
                    grupo_atual = [inputs_organizados[0]] if inputs_organizados else []
                    y_anterior = inputs_organizados[0].location['y'] if inputs_organizados else 0
                    
                    for inp in inputs_organizados[1:]:
                        y_atual = inp.location['y']
                        # Se estiver a menos de 10 pixels de distância vertical, considera do mesmo grupo
                        if abs(y_atual - y_anterior) < 10:
                            grupo_atual.append(inp)
                        else:
                            if grupo_atual:
                                grupos.append(grupo_atual)
                            grupo_atual = [inp]
                        y_anterior = y_atual
                    
                    if grupo_atual:
                        grupos.append(grupo_atual)
                    
                    # Se encontrou um grupo com pelo menos o número de campos que precisamos
                    for grupo in grupos:
                        if len(grupo) >= len(faltantes):
                            logger.info(f"Encontrado grupo de {len(grupo)} inputs possivelmente relacionados")
                            # Usa os primeiros N inputs do grupo para os campos faltantes
                            for i, nome in enumerate(faltantes):
                                if i < len(grupo) and nome not in campos_encontrados:
                                    campos_encontrados[nome] = grupo[i]
                                    logger.info(f"Campo {nome} associado a input do grupo pela posição {i+1}")
                            break
                except Exception as e_pos:
                    logger.debug(f"Erro ao analisar posição dos inputs: {e_pos}")
                
                # Se ainda não conseguiu pelo agrupamento, tenta input por input
                for i, nome in enumerate(faltantes):
                    if nome not in campos_encontrados and i < len(inputs_visiveis):
                        campos_encontrados[nome] = inputs_visiveis[i]
                        logger.info(f"Campo {nome} associado a input numérico pela posição {i+1}")
            
            # Último recurso: verifica se há elementos de formulário numerados ou seguindo padrões
            if not campos_encontrados or len(campos_encontrados) < len(nomes_campos):
                try:
                    # Busca inputs com números (pode ser que tenham o padrão campo1, campo2, etc.)
                    numerados = driver.find_elements(By.CSS_SELECTOR, '[id*="1"], [id*="2"], [id*="3"], [id*="4"], [name*="1"], [name*="2"], [name*="3"], [name*="4"]')
                    numerados_visiveis = [n for n in numerados if n.is_displayed() and n.is_enabled() and n.tag_name == 'input']
                    
                    if len(numerados_visiveis) >= len(nomes_campos):
                        logger.info(f"Encontrados {len(numerados_visiveis)} inputs possivelmente numerados")
                        # Tenta associar por padrão numérico
                        for i, nome in enumerate(nomes_campos):
                            if nome not in campos_encontrados:
                                for num in numerados_visiveis:
                                    id_num = (num.get_attribute("id") or "").lower()
                                    name_num = (num.get_attribute("name") or "").lower()
                                    # Verifica se o número corresponde à posição (1-based)
                                    if f"{i+1}" in id_num or f"{i+1}" in name_num:
                                        campos_encontrados[nome] = num
                                        logger.info(f"Campo {nome} associado ao input numerado {i+1}")
                                        break
                except Exception as e_num:
                    logger.debug(f"Erro ao buscar inputs numerados: {e_num}")
          # Verifica se algum campo é um input hidden
        if not campos_encontrados or len(campos_encontrados) < len(campos_tributos):
            logger.info("Verificando inputs hidden que possam ser campos de tributos")
            # Busca todos os inputs hidden e também campos invisíveis que possam ser mostrados com JavaScript
            hidden_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="hidden"], input[style*="display: none"], input[style*="visibility: hidden"], input[aria-hidden="true"]')
            
            nomes_campos = ["IR", "PIS", "COFINS", "CSLL"]
            for inp in hidden_inputs:
                try:
                    nome = inp.get_attribute("name") or ""
                    id_campo = inp.get_attribute("id") or ""
                    classe = inp.get_attribute("class") or ""
                    data_name = inp.get_attribute("data-name") or ""
                    data_id = inp.get_attribute("data-id") or ""
                    data_field = inp.get_attribute("data-field") or ""
                    
                    nome_lower = nome.lower()
                    id_lower = id_campo.lower()
                    classe_lower = classe.lower()
                    data_name_lower = data_name.lower()
                    data_id_lower = data_id.lower()
                    data_field_lower = data_field.lower()
                    
                    # Verifica todas as propriedades para cada campo
                    for campo in nomes_campos:
                        campo_lower = campo.lower()
                        
                        # Se o campo ainda não foi encontrado e há correspondência em algum atributo
                        if campo not in campos_encontrados:
                            # Campos específicos para IR
                            if campo == "IR" and (
                                campo_lower in nome_lower or 
                                "irrf" in nome_lower or 
                                "imposto" in nome_lower and "renda" in nome_lower or
                                campo_lower in id_lower or 
                                "irrf" in id_lower or
                                campo_lower in classe_lower or
                                campo_lower in data_name_lower or
                                campo_lower in data_id_lower or
                                campo_lower in data_field_lower or
                                "irrf" in data_name_lower or
                                "irrf" in data_id_lower or
                                "irrf" in data_field_lower
                            ):
                                campos_encontrados[campo] = inp
                                logger.info(f"Campo {campo} encontrado como input hidden/invisível (nome: {nome}, id: {id_campo})")
                            
                            # Campos específicos para PIS
                            elif campo == "PIS" and (
                                campo_lower in nome_lower or
                                "pispasep" in nome_lower or
                                campo_lower in id_lower or
                                "pispasep" in id_lower or
                                campo_lower in classe_lower or
                                campo_lower in data_name_lower or
                                campo_lower in data_id_lower or
                                campo_lower in data_field_lower
                            ):
                                campos_encontrados[campo] = inp
                                logger.info(f"Campo {campo} encontrado como input hidden/invisível (nome: {nome}, id: {id_campo})")
                            
                            # Campos específicos para COFINS
                            elif campo == "COFINS" and (
                                campo_lower in nome_lower or
                                campo_lower in id_lower or
                                campo_lower in classe_lower or
                                campo_lower in data_name_lower or
                                campo_lower in data_id_lower or
                                campo_lower in data_field_lower
                            ):
                                campos_encontrados[campo] = inp
                                logger.info(f"Campo {campo} encontrado como input hidden/invisível (nome: {nome}, id: {id_campo})")
                            
                            # Campos específicos para CSLL
                            elif campo == "CSLL" and (
                                campo_lower in nome_lower or
                                "contribuicao" in nome_lower or
                                "social" in nome_lower or
                                campo_lower in id_lower or
                                "contribuicao" in id_lower or
                                "social" in id_lower or
                                campo_lower in classe_lower or
                                campo_lower in data_name_lower or
                                campo_lower in data_id_lower or
                                campo_lower in data_field_lower or
                                "contribuicao" in data_name_lower or
                                "social" in data_name_lower or
                                "contribuicao" in data_id_lower or
                                "social" in data_id_lower or
                                "contribuicao" in data_field_lower or
                                "social" in data_field_lower
                            ):
                                campos_encontrados[campo] = inp
                                logger.info(f"Campo {campo} encontrado como input hidden/invisível (nome: {nome}, id: {id_campo})")
                                
                except Exception as e_hidden:
                    logger.debug(f"Erro ao analisar input hidden: {e_hidden}")
        
        # Salva um screenshot para diagnóstico dos campos encontrados        try:
            driver.save_screenshot("logs/imagens/campos_tributos_encontrados.png")
            logger.info("Screenshot salvo em logs/imagens/campos_tributos_encontrados.png")
        except:
            pass
            
        if not campos_encontrados:
            logger.warning("Nenhum dos campos de tributos federais foi encontrado. Verifique se está na tela correta.")
            
            # Tenta buscar mais informações sobre a página atual
            try:
                page_title = driver.title
                current_url = driver.current_url
                logger.info(f"Título da página atual: {page_title}")
                logger.info(f"URL atual: {current_url}")
                
                # Salva o HTML da página para análise
                html_content = driver.page_source
                import os
                os.makedirs("logs/html", exist_ok=True)
                with open("logs/html/pagina_tributos.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("HTML da página salvo em logs/html/pagina_tributos.html")
                
                # Salva screenshot para diagnóstico
                try:
                    driver.save_screenshot("logs/imagens/campos_tributos_nao_encontrados.png")
                    logger.info("Screenshot salvo em logs/imagens/campos_tributos_nao_encontrados.png")
                except Exception as e_ss:
                    logger.debug(f"Erro ao salvar screenshot: {e_ss}")
                
                # Verifica se existem mensagens de erro visíveis na página
                mensagens_erro = driver.find_elements(By.XPATH, "//*[contains(text(), 'erro') or contains(text(), 'Erro') or contains(text(), 'falha') or contains(text(), 'Falha')]")
                for msg in mensagens_erro:
                    if msg.is_displayed():
                        logger.warning(f"Mensagem de erro encontrada na página: {msg.text}")
                
                # Tenta uma última estratégia: procurar por qualquer campo de input que possa estar em uma seção de tributos
                logger.info("Tentando estratégia de emergência: buscar por seções ou elementos que possam indicar tributos")
                
                # Busca por textos relacionados a tributos
                termos_tributos = ["tributo", "federal", "imposto", "retenção", "IR", "PIS", "COFINS", "CSLL", "IRRF", "contribuição"]
                
                for termo in termos_tributos:
                    try:
                        elementos = driver.find_elements(By.XPATH, f"//*[contains(text(), '{termo}')]")
                        elementos_visiveis = [e for e in elementos if e.is_displayed()]
                        
                        if elementos_visiveis:
                            logger.info(f"Encontrados {len(elementos_visiveis)} elementos com o termo '{termo}'")
                            # Lista os primeiros elementos encontrados
                            for i, elem in enumerate(elementos_visiveis[:5]):  # Limita a 5 elementos
                                try:
                                    logger.info(f"Elemento {i+1} com termo '{termo}': Tag '{elem.tag_name}', Texto: '{elem.text[:50]}...'")
                                    
                                    # Verifica se há campos de input próximos
                                    try:
                                        # Busca inputs no mesmo contêiner
                                        parent_xpath = "ancestor::div[1]"
                                        inputs_proximos = elem.find_elements(By.XPATH, f"{parent_xpath}//input")
                                        
                                        if inputs_proximos:
                                            logger.info(f"Encontrados {len(inputs_proximos)} inputs próximos ao termo '{termo}'")
                                            # Salva detalhes desses inputs para diagnóstico
                                            for j, inp in enumerate(inputs_proximos[:3]):  # Limita a 3 inputs
                                                inp_type = inp.get_attribute("type") or "sem tipo"
                                                inp_name = inp.get_attribute("name") or "sem nome"
                                                inp_id = inp.get_attribute("id") or "sem id"
                                                inp_value = inp.get_attribute("value") or "sem valor"
                                                inp_visible = "visível" if inp.is_displayed() else "invisível"
                                                inp_enabled = "habilitado" if inp.is_enabled() else "desabilitado"
                                                
                                                logger.info(f"Input {j+1}: tipo='{inp_type}', nome='{inp_name}', id='{inp_id}', "
                                                           f"valor='{inp_value}', {inp_visible}, {inp_enabled}")
                                    except Exception as e_prox:
                                        logger.debug(f"Erro ao verificar inputs próximos: {e_prox}")
                                except Exception as e_elem:
                                    logger.debug(f"Erro ao analisar elemento: {e_elem}")
                    except Exception as e_termo:
                        logger.debug(f"Erro ao buscar termo '{termo}': {e_termo}")
                
                # Pergunta ao usuário se deseja continuar mesmo sem encontrar os campos
                continuar = input("Nenhum campo de tributo federal foi encontrado. Deseja continuar mesmo assim? (s/n): ")
                if continuar.lower() == 's':
                    logger.warning("Usuário optou por continuar mesmo sem campos de tributos encontrados")
                    # Cria campos fictícios apenas para não quebrar o fluxo
                    campos_encontrados = {
                        "IR": None,
                        "PIS": None,
                        "COFINS": None,
                        "CSLL": None
                    }
                    return True
                else:
                    logger.warning("Usuário optou por interromper o processo devido à falta de campos de tributos")
                    return False
                    
            except Exception as e:
                logger.debug(f"Erro ao coletar informações da página: {e}")
                
            return False
        
        logger.info(f"Campos de tributos encontrados: {', '.join(campos_encontrados.keys())}")
        
        # Se nem todos os campos foram encontrados, avisa mas continua o processo
        if len(campos_encontrados) < len(campos_tributos):
            logger.warning(f"Apenas {len(campos_encontrados)} de {len(campos_tributos)} campos de tributos foram encontrados")
            campos_faltantes = set(campos_tributos.keys()) - set(campos_encontrados.keys())
            logger.warning(f"Campos não encontrados: {', '.join(campos_faltantes)}")
            
        logger.info(f"Campos de tributos encontrados: {', '.join(campos_encontrados.keys())}")
          # Agora preenche os campos encontrados
        from selenium.webdriver.common.keys import Keys
        
        for nome_campo, elemento in campos_encontrados.items():
            valor = campos_tributos[nome_campo]['valor']
            if valor is None or valor == '':
                valor = '0,00'
            
            logger.info(f"Preenchendo {nome_campo} com valor: {valor}")
            
            try:
                # Verifica se é um campo hidden
                is_hidden = elemento.get_attribute("type") == "hidden"
                
                if is_hidden:
                    # Para campos hidden, usa JavaScript para definir seu valor
                    logger.info(f"Campo {nome_campo} é hidden, preenchendo via JavaScript")
                    try:
                        driver.execute_script(f"arguments[0].value = '{valor}';", elemento)
                        # Tenta disparar eventos para garantir que o valor seja registrado
                        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", elemento)
                        driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", elemento)
                        logger.info(f"Campo hidden {nome_campo} preenchido via JavaScript com: {valor}")
                        
                        # Verificação adicional para campos hidden
                        try:
                            valor_atual = elemento.get_attribute("value")
                            if valor_atual:
                                logger.info(f"Valor atual do campo hidden {nome_campo}: {valor_atual}")
                        except:
                            pass
                    except Exception as e_js:
                        logger.warning(f"Erro ao preencher campo hidden {nome_campo} via JavaScript: {e_js}")
                else:
                    # Para campos visíveis, usa a abordagem normal
                    try:
                        # Verifica primeiro se o elemento está realmente visível e acessível
                        if not elemento.is_displayed():
                            logger.info(f"Campo {nome_campo} não está visível, tentando torná-lo visível")
                            try:
                                # Tenta remover atributos que podem estar escondendo o elemento
                                driver.execute_script("""
                                    arguments[0].style.display = 'block';
                                    arguments[0].style.visibility = 'visible';
                                    arguments[0].removeAttribute('hidden');
                                    arguments[0].removeAttribute('aria-hidden');
                                """, elemento)
                                time.sleep(0.5)  # Espera a mudança fazer efeito
                            except:
                                pass
                        
                        # Scroll para o elemento ficar visível
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                        time.sleep(0.5)
                        
                        # Limpa o campo antes de preencher
                        try:
                            elemento.clear()
                        except Exception as e_clear:
                            logger.debug(f"Não foi possível limpar o campo {nome_campo}: {e_clear}")
                            try:
                                # Alternativa: selecionar todo o texto e deletá-lo
                                driver.execute_script("arguments[0].select();", elemento)
                                elemento.send_keys(Keys.DELETE)
                            except:
                                pass
                        
                        # Tenta clicar no campo para garantir o foco
                        try:
                            elemento.click()
                            time.sleep(0.3)
                        except Exception as e_click:
                            logger.debug(f"Não foi possível clicar no campo {nome_campo}: {e_click}, tentando alternativa")
                            try:
                                # Alternativa usando JavaScript
                                driver.execute_script("arguments[0].focus();", elemento)
                                time.sleep(0.3)
                            except:
                                pass
                        
                        # Verifica se o campo está habilitado
                        if elemento.is_enabled():
                            # Preenche usando a função de simulação se disponível
                            try:
                                from preencher_dados_servico import simular_digitacao_humana
                                simular_digitacao_humana(elemento, valor, pressionar_tab=True)
                            except ImportError:
                                # Fallback: preenche diretamente
                                elemento.send_keys(valor)
                                elemento.send_keys(Keys.TAB)  # Pressiona TAB para perder o foco
                            
                            # Verifica se o preenchimento funcionou verificando o valor do campo
                            time.sleep(0.5)
                            valor_atual = elemento.get_attribute("value")
                            if not valor_atual:
                                logger.warning(f"Campo {nome_campo} parece não ter sido preenchido corretamente. Tentando via JavaScript.")
                                # Tenta com JavaScript
                                driver.execute_script(f"arguments[0].value = '{valor}';", elemento)
                                driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", elemento)
                            else:
                                logger.info(f"Campo {nome_campo} preenchido com: {valor}, valor atual: {valor_atual}")
                            
                            time.sleep(1)  # Pausa para processamento
                        else:
                            logger.warning(f"Campo {nome_campo} está desabilitado, tentando preenchimento via JavaScript")
                            # Tenta preencher campo desabilitado via JavaScript (algumas páginas habilitam depois)
                            driver.execute_script(f"arguments[0].value = '{valor}';", elemento)
                            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", elemento)
                    except Exception as e_visivel:
                        logger.warning(f"Erro ao preencher campo visível {nome_campo}: {e_visivel}, tentando via JavaScript")
                        # Último recurso: tenta com JavaScript direto
                        try:
                            driver.execute_script(f"arguments[0].value = '{valor}';", elemento)
                            driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", elemento)
                            logger.info(f"Campo {nome_campo} preenchido via JavaScript direto")
                        except Exception as e_js_final:
                            logger.warning(f"Falha no preenchimento final via JavaScript: {e_js_final}")
            except Exception as e:
                logger.warning(f"Erro ao preencher campo {nome_campo}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        # Aguarda um momento para o cálculo do valor líquido
        logger.info("Aguardando o cálculo automático do valor líquido...")
        time.sleep(4)  # 4 segundos para garantir o cálculo
        
        # Verifica se o valor líquido calculado está correto
        try:
            # Obtém o valor líquido da planilha/dados e formata corretamente
            valor_liquido_esperado_planilha = formatar_valor_monetario(
                dados_nota.get('valor_liquido', 
                    dados_nota.get('liquido', 
                        dados_nota.get('vl_liquido', 
                            dados_nota.get('valor_liq', None)
                        )
                    )
                )
            )
            
            # Calcula o valor líquido esperado com base nos dados fornecidos
            valor_liquido_calculado_formatado = formatar_valor_monetario(valor_liquido_calculado_internamente)
            
            # Determina qual valor líquido usar para verificação (planilha ou calculado)
            if valor_liquido_esperado_planilha and valor_liquido_esperado_planilha != '0,00':
                valor_liquido_esperado = valor_liquido_esperado_planilha
                logger.info(f"Usando valor líquido da planilha: {valor_liquido_esperado}")
            else:
                valor_liquido_esperado = valor_liquido_calculado_formatado
                logger.info(f"Usando valor líquido calculado: {valor_liquido_esperado}")
            
            # Localiza o campo de valor líquido com múltiplos seletores
            campo_valor_liquido = None
            seletores_liquido = [
                'input[aria-label="Valor Líquido"]', 
                'input[name="Valores.valorLiquido"]',
                'input[id*="valorLiquido"]', 
                'input[name*="liquido"]',
                'input[placeholder*="Líquido"]',
                'input[name*="ValorLiquido"]',
                'input[class*="liquido"]',
                'input[data-cy*="liquido"]'
            ]
            
            for seletor in seletores_liquido:
                try:
                    elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                    elementos_visiveis = [e for e in elementos if e.is_displayed()]
                    if elementos_visiveis:
                        campo_valor_liquido = elementos_visiveis[0]
                        logger.info(f"Campo valor líquido encontrado com seletor: {seletor}")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar campo valor líquido com seletor {seletor}: {e}")
            
            # Se não encontrou por CSS, tenta por XPath
            if not campo_valor_liquido:
                xpath_liquido = [
                    "//label[contains(text(), 'Líquido')]/following::input[1]",
                    "//label[contains(text(), 'Valor Líquido')]/following::input[1]",
                    "//span[contains(text(), 'Líquido')]/following::input[1]",
                    "//div[contains(text(), 'Valor Líquido')]/following::input[1]"
                ]
                
                for xpath in xpath_liquido:
                    try:
                        elementos = driver.find_elements(By.XPATH, xpath)
                        if elementos and elementos[0].is_displayed():
                            campo_valor_liquido = elementos[0]
                            logger.info(f"Campo valor líquido encontrado com XPath: {xpath}")
                            break
                    except Exception as e:
                        logger.debug(f"Erro ao procurar campo valor líquido com XPath {xpath}: {e}")
            
            if campo_valor_liquido:
                # Scroll para o campo ficar visível
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo_valor_liquido)
                time.sleep(0.5)
                
                valor_liquido_calculado = campo_valor_liquido.get_attribute('value')
                
                logger.info(f"Valor líquido calculado pelo sistema: {valor_liquido_calculado}")
                logger.info(f"Valor líquido esperado: {valor_liquido_esperado}")
                
                # Normaliza os valores para comparação
                # Remove pontos e mantém apenas dígitos e vírgulas
                def normalizar_valor(valor):
                    # Garante que seja uma string
                    valor_str = str(valor)
                    # Remove R$ e espaços
                    valor_str = valor_str.replace("R$", "").strip()
                    # Normaliza separadores
                    if '.' in valor_str and ',' in valor_str:  # Formato 1.234,56
                        valor_str = valor_str.replace(".", "")
                    # Mantém apenas dígitos e vírgulas
                    return ''.join([c for c in valor_str if c.isdigit() or c == ','])
                
                valor_calc_normalizado = normalizar_valor(valor_liquido_calculado)
                valor_esp_normalizado = normalizar_valor(valor_liquido_esperado)
                
                # Verifica se os valores são iguais (com uma margem de tolerância para arredondamentos)
                def valores_proximos(valor1, valor2, tolerancia=0.02):
                    # Converte para float
                    v1 = float(valor1.replace(',', '.'))
                    v2 = float(valor2.replace(',', '.'))
                    # Verifica se a diferença é menor que a tolerância
                    diferenca = abs(v1 - v2)
                    return diferenca <= tolerancia
                
                if valor_calc_normalizado == valor_esp_normalizado:
                    logger.info("VERIFICAÇÃO OK: O valor líquido está correto (valores exatamente iguais)")
                elif valores_proximos(valor_calc_normalizado, valor_esp_normalizado):
                    logger.info("VERIFICAÇÃO OK: O valor líquido está correto (dentro da margem de tolerância)")
                else:
                    logger.warning(f"VERIFICAÇÃO FALHOU: Valor líquido calculado ({valor_liquido_calculado}) é diferente do esperado ({valor_liquido_esperado})")
                    
                    # Salva um screenshot para análise
                    try:
                        driver.save_screenshot("logs/imagens/verificacao_valor_liquido.png")
                        logger.info("Screenshot salvo em logs/imagens/verificacao_valor_liquido.png")
                    except:
                        pass
                    
                    # Pergunta ao usuário se deseja continuar mesmo com a diferença
                    resposta = input(f"O valor líquido calculado ({valor_liquido_calculado}) é diferente do valor esperado ({valor_liquido_esperado}). Deseja continuar? (s/n): ")
                    if resposta.lower() != 's':
                        logger.warning("Processo interrompido pelo usuário devido à diferença no valor líquido")
                        return False
            else:
                logger.warning("Campo de valor líquido não encontrado para verificação")
                # Tenta mesmo assim continuar se houver valor líquido calculado
                logger.info(f"Valor líquido calculado internamente: {valor_liquido_calculado_formatado}")
        except Exception as e:
            logger.warning(f"Erro ao verificar o valor líquido: {e}")
            import traceback
            logger.warning(traceback.format_exc())
        
        # Salva um screenshot após preencher todos os campos
        try:
            driver.save_screenshot("logs/imagens/tributos_federais_preenchidos.png")
            logger.info("Screenshot salvo em logs/imagens/tributos_federais_preenchidos.png")
        except:
            pass
            
        logger.info("Tributos federais preenchidos com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao preencher tributos federais: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Salva um screenshot em caso de erro
        try:
            driver.save_screenshot("logs/imagens/erro_tributos_federais.png")
            logger.info("Screenshot do erro salvo em logs/imagens/erro_tributos_federais.png")
        except:
            pass
        return False

# Função principal para ser chamada pelo script principal
def preencher_tributos(driver, dados_nota, logger=None):
    """
    Função auxiliar para ser chamada diretamente pelo script principal.
    """
    return preencher_tributos_federais(driver, dados_nota, logger)

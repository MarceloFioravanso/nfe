import time
import pandas as pd
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def salvar_screenshot_auxiliar(driver, nome_arquivo, screenshot_folder="logs/imagens"):
    """Salva um screenshot na pasta de imagens com o nome especificado"""
    import os
    caminho_completo = os.path.join(screenshot_folder, nome_arquivo)
    try:
        driver.save_screenshot(caminho_completo)
        print(f"Screenshot salvo em {caminho_completo}")
    except Exception as e:
        print(f"Erro ao salvar screenshot {nome_arquivo}: {e}")

def simular_digitacao_humana_auxiliar(elemento, texto):
    """Simula digitação humana inserindo caracteres um a um"""
    import random
    # Limpa o campo primeiro
    elemento.clear()
    
    # Velocidades de digitação variáveis
    for caractere in texto:
        elemento.send_keys(caractere)
        # Pequena pausa aleatória para simular digitação real
        time.sleep(random.uniform(0.05, 0.15))
    
    # Pausa final após completar a digitação
    time.sleep(random.uniform(0.2, 0.5))

def buscar_empresa_por_cnpj(driver, cnpj, nome_empresa, logger=None):
    """
    Busca empresa pelo CNPJ e seleciona nos resultados de pesquisa.
    
    Args:
        driver: WebDriver do Selenium
        cnpj: CNPJ da empresa para busca
        nome_empresa: Nome da empresa para confirmar na seleção de resultados
        logger: Logger opcional para registrar mensagens
        
    Returns:
        bool: True se a busca e seleção foi bem-sucedida, False caso contrário
    """
    if logger is None:
        # Configura um logger básico se nenhum for fornecido
        logger = logging.getLogger('busca_empresa')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # Formata o CNPJ para exibição segura
    cnpj_exibicao = f"{cnpj[:4]}****{cnpj[-2:]}" if len(cnpj) > 6 else "****"
    
    try:
        logger.info(f"Buscando empresa com CNPJ: {cnpj_exibicao} - {nome_empresa}")
        wait = WebDriverWait(driver, 10)
        
        # Procura pelo campo de busca de CNPJ/Razão Social com uma lista ampliada de seletores
        campo_busca_seletores = [
            'input[name="Tomador.nomeRazao"]'
        ]
        
        campo_busca = None
        for seletor in campo_busca_seletores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                if elementos:
                    campo_busca = elementos[0]
                    logger.info(f"Campo de busca de CNPJ encontrado com seletor: {seletor}")
                    break
            except Exception as e:
                logger.warning(f"Erro ao procurar campo com seletor {seletor}: {e}")
        
        if not campo_busca:
            logger.error("Campo de busca de CNPJ/Razão Social não encontrado")
            salvar_screenshot_auxiliar(driver, "erro_campo_busca_cnpj_nao_encontrado.png")
            return False
          # Clica no campo de busca
        campo_busca.click()
        time.sleep(0.5)
        
        # Limpa o campo e insere o CNPJ
        campo_busca.clear()
        simular_digitacao_humana_auxiliar(campo_busca, cnpj)
        logger.info(f"CNPJ inserido no campo de busca")
        salvar_screenshot_auxiliar(driver, "apos_inserir_cnpj.png")
        
        # Aguarda os resultados (uma única espera é suficiente)
        logger.info("Procurando resultados da busca de CNPJ...")
        time.sleep(2.5)
        salvar_screenshot_auxiliar(driver, "resultados_busca.png")
        
        # Função auxiliar para verificar se um texto contém o CNPJ ou nome da empresa
        def texto_contem_empresa(texto, cnpj, nome_empresa):
            if not texto:
                return False
                
            texto = texto.upper()
            nome_empresa = nome_empresa.upper()
            
            # Limpeza de CNPJ para comparação
            cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
            if len(cnpj_limpo) > 8:  # Só compara se tiver dígitos suficientes
                cnpj_formatado = f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}" if len(cnpj_limpo) >= 14 else cnpj_limpo
                
                # Verifica várias possibilidades de formato de CNPJ no texto
                if (cnpj_limpo in texto or 
                    cnpj_formatado in texto or 
                    cnpj_limpo[:8] in texto):  # Primeiros 8 dígitos
                    return True
            
            # Verifica se o texto contém parte significativa do nome da empresa
            palavras_chave = nome_empresa.split()
            palavras_significativas = [p for p in palavras_chave if len(p) > 3 and p.upper() not in ["LTDA", "EIRELI", "COMERCIO", "SERVICOS", "EMPRESARIAL"]]
            
            for palavra in palavras_significativas:
                if palavra.upper() in texto:
                    return True
                    
            # Verifica se é a MUNDIAL especificamente
            if "MUNDIAL" in texto and "MUNDIAL" in nome_empresa:
                return True
                
            return False
          # Busca específica por td com name="nomeRazao" ou qualquer célula de tabela com o nome/CNPJ
        try:
            logger.info("Tentando localizar células com os dados da empresa...")
            
            # Lista simplificada de seletores principais para células que podem conter resultados
            celulas_seletores = [
                'td[name="nomeRazao"]'
            ]
            
            # Tenta cada seletor em ordem até encontrar a empresa
            for seletor in celulas_seletores:
                elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
                logger.info(f"Seletor '{seletor}': encontrados {len(elementos)} elementos")
                
                for elemento in elementos:
                    texto_elemento = elemento.text.strip() if elemento.text else ""
                    
                    # Pula elementos sem texto
                    if not texto_elemento:
                        continue
                        
                    logger.info(f"Analisando elemento com texto: {texto_elemento}")
                    
                    # Verifica se este elemento contém informações da empresa
                    if texto_contem_empresa(texto_elemento, cnpj, nome_empresa):
                        logger.info(f"Empresa encontrada: {texto_elemento}")
                        salvar_screenshot_auxiliar(driver, "empresa_encontrada.png")
                        
                        # Tenta clicar diretamente primeiro (método que está funcionando)
                        try:
                            elemento.click()
                            logger.info("Empresa selecionada com sucesso!")
                            salvar_screenshot_auxiliar(driver, "apos_selecionar_empresa.png")
                            time.sleep(1)
                            return True
                        except Exception as e:
                            # Se falhar o clique direto, tenta com JavaScript como fallback
                            logger.warning(f"Clique direto falhou, tentando com JavaScript: {e}")
                            try:
                                driver.execute_script("arguments[0].click();", elemento)
                                logger.info("Empresa selecionada via JavaScript")
                                salvar_screenshot_auxiliar(driver, "apos_selecionar_empresa_js.png")
                                time.sleep(1)
                                return True
                            except Exception as js_error:
                                logger.error(f"Clique via JavaScript também falhou: {js_error}")
        except Exception as e:
            logger.error(f"Erro ao buscar por células com dados da empresa: {e}")
        
        logger.error(f"Empresa '{nome_empresa}' não encontrada nos resultados da busca")
        salvar_screenshot_auxiliar(driver, "empresa_nao_encontrada.png")
        return False
    
    except Exception as e:
        logger.error(f"Erro ao buscar empresa por CNPJ: {e}")
        salvar_screenshot_auxiliar(driver, "erro_busca_cnpj.png")
        return False

# Função para uso direto após seleção do tipo de tomador
def preencher_busca_cnpj(driver, cnpj, nome_empresa, logger=None):
    """
    Função auxiliar para ser chamada diretamente no script principal.
    """
    # Adiciona um log para depuração sempre que essa função for chamada
    if logger:
        logger.info(f"INICIANDO BUSCA ÚNICA DA EMPRESA: {nome_empresa}")
    return buscar_empresa_por_cnpj(driver, cnpj, nome_empresa, logger)

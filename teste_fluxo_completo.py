"""
Teste do fluxo completo de emissão de NFS-e com verificação de:
1. Checkbox "Endereço Alternativo"
2. Botões "Próximo" e "Emitir"

Este script ajuda a verificar se todas as funcionalidades implementadas
estão funcionando corretamente em um fluxo completo de emissão.
"""
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# Tenta importar as funções de detecção de checkbox e finalização
try:
    from finalizar_emissao import (
        clicar_proximo_apos_verificacao, 
        clicar_emitir, 
        finalizar_emissao_nota, 
        salvar_screenshot,
        esperar_pagina_carregar
    )
except ImportError:
    # Funções alternativas caso o módulo não seja encontrado
    def clicar_proximo_apos_verificacao(driver, logger):
        logger.warning("Módulo finalizar_emissao não está disponível")
        return False
    
    def clicar_emitir(driver, logger):
        logger.warning("Módulo finalizar_emissao não está disponível")
        return False
    
    def finalizar_emissao_nota(driver, logger):
        logger.warning("Módulo finalizar_emissao não está disponível")
        return False
    
    def salvar_screenshot(driver, nome_arquivo, logger=None):
        try:
            os.makedirs("logs/imagens", exist_ok=True)
            caminho_completo = os.path.join("logs/imagens", nome_arquivo)
            driver.save_screenshot(caminho_completo)
            if logger:
                logger.info(f"Screenshot salvo em {caminho_completo}")
        except Exception as e:
            if logger:
                logger.error(f"Erro ao salvar screenshot {nome_arquivo}: {e}")
    
    def esperar_pagina_carregar(driver, timeout=10, logger=None):
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except:
            pass
        time.sleep(2)

# Configura o logger
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=f'logs/teste_fluxo_completo.log',
    filemode='w'
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logger = logging.getLogger('teste_fluxo_completo')

# Garante que as pastas existem
os.makedirs("logs/imagens", exist_ok=True)
os.makedirs("logs/html", exist_ok=True)

def salvar_html(driver, nome_arquivo):
    """Função para salvar o HTML da página para análise"""
    try:
        with open(f"logs/html/{nome_arquivo}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info(f"HTML da página salvo em logs/html/{nome_arquivo}.html")
    except Exception as e:
        logger.error(f"Erro ao salvar HTML: {e}")

def verificar_checkbox_endereco_alternativo(driver):
    """
    Verifica se o checkbox "Endereço Alternativo" está presente e marcado
    """
    logger.info("Verificando se o checkbox 'Endereço Alternativo' está marcado...")
    endereco_alternativo_selecionado = False
    checkbox_encontrado = False
    
    try:
        # Seletores possíveis para o checkbox
        seletores_checkbox = [
            'input[name="usaEnderecoAlternativo"]',
            'input[aria-label="Endereço Alternativo"]',
            'input.__estrutura_componente_base.campo.estrutura_check_tipo_toggle[name="usaEnderecoAlternativo"]',
            'input.estrutura_check_tipo_toggle[name="usaEnderecoAlternativo"]',
            'input[type="checkbox"][name*="endereco"]',
            'input[type="checkbox"][aria-label*="endereco"]',
            'input[type="checkbox"][id*="endereco"]'
        ]
        
        for seletor in seletores_checkbox:
            checkboxes = driver.find_elements(By.CSS_SELECTOR, seletor)
            if checkboxes:
                checkbox = checkboxes[0]
                checkbox_encontrado = True
                
                # Verifica usando múltiplos métodos
                is_selected_attr = checkbox.is_selected()
                is_checked_attr = checkbox.get_attribute("checked") == "true"
                has_checked_class = "checked" in (checkbox.get_attribute("class") or "")
                aria_checked = checkbox.get_attribute("aria-checked") == "true"
                
                # Combinação dos resultados
                endereco_alternativo_selecionado = any([is_selected_attr, is_checked_attr, has_checked_class, aria_checked])
                
                logger.info(f"Checkbox 'Endereço Alternativo' encontrado com seletor: {seletor}")
                logger.info(f"Estado do checkbox - is_selected(): {is_selected_attr}")
                logger.info(f"Estado do checkbox - atributo checked: {is_checked_attr}")
                logger.info(f"Estado do checkbox - classe checked: {has_checked_class}")
                logger.info(f"Estado do checkbox - aria-checked: {aria_checked}")
                logger.info(f"Conclusão: Checkbox 'Endereço Alternativo' está {'MARCADO' if endereco_alternativo_selecionado else 'DESMARCADO'}")
                break
        
        # Se não encontrou por CSS, tenta por XPath
        if not checkbox_encontrado:
            xpath_seletores = [
                "//input[@name='usaEnderecoAlternativo']",
                "//input[@aria-label='Endereço Alternativo']",
                "//label[contains(text(), 'Endereço Alternativo')]/preceding-sibling::input",
                "//label[contains(text(), 'Endereço Alternativo')]/following-sibling::input",
                "//label[contains(., 'Endereço Alternativo')]//input",
                "//input[contains(@name, 'endereco') and @type='checkbox']"
            ]
            
            for xpath in xpath_seletores:
                elementos = driver.find_elements(By.XPATH, xpath)
                if elementos:
                    checkbox = elementos[0]
                    checkbox_encontrado = True
                    
                    # Verifica usando múltiplos métodos
                    is_selected_attr = checkbox.is_selected()
                    is_checked_attr = checkbox.get_attribute("checked") == "true"
                    has_checked_class = "checked" in (checkbox.get_attribute("class") or "")
                    aria_checked = checkbox.get_attribute("aria-checked") == "true"
                    
                    # Combinação dos resultados
                    endereco_alternativo_selecionado = any([is_selected_attr, is_checked_attr, has_checked_class, aria_checked])
                    
                    logger.info(f"Checkbox 'Endereço Alternativo' encontrado com XPath: {xpath}")
                    logger.info(f"Estado do checkbox - is_selected(): {is_selected_attr}")
                    logger.info(f"Estado do checkbox - atributo checked: {is_checked_attr}")
                    logger.info(f"Estado do checkbox - classe checked: {has_checked_class}")
                    logger.info(f"Estado do checkbox - aria-checked: {aria_checked}")
                    logger.info(f"Conclusão: Checkbox 'Endereço Alternativo' está {'MARCADO' if endereco_alternativo_selecionado else 'DESMARCADO'}")
                    break
        
        salvar_screenshot(driver, "verificacao_endereco_alternativo_teste_fluxo.png", logger)
        
        if not checkbox_encontrado:
            logger.warning("Checkbox 'Endereço Alternativo' não foi encontrado")
            return False, False
        
        return checkbox_encontrado, endereco_alternativo_selecionado
        
    except Exception as e:
        logger.error(f"Erro ao verificar checkbox 'Endereço Alternativo': {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, False

def teste_fluxo_completo():
    """
    Testa o fluxo completo de emissão de nota fiscal com:
    1. Detecção do checkbox "Endereço Alternativo"
    2. Clique nos botões "Próximo" e "Emitir"
    """
    logger.info("Iniciando teste de fluxo completo de emissão de NFSe")
    
    # Instala automaticamente o ChromeDriver compatível
    chromedriver_autoinstaller.install()
    
    # Configura o driver do Chrome
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)
    
    try:
        # Acessa a página de emissão de NFS-e
        logger.info("Acessando o site de emissão de NFS-e...")
        driver.get("https://nfse-cachoeirinha.atende.net/autoatendimento/servicos/nfse?redirected=1")
        
        # Aguarda a página carregar
        time.sleep(5)
        
        # Salva um screenshot para análise
        salvar_screenshot(driver, "teste_fluxo_pagina_inicial.png", logger)
        
        # Mostra instruções para o usuário
        logger.info("\n" + "="*80)
        logger.info("INSTRUÇÕES PARA O TESTE DE FLUXO COMPLETO:")
        logger.info("1. Faça login no sistema")
        logger.info("2. Navegue até a emissão de nota fiscal")
        logger.info("3. Selecione uma empresa tomadora que utilize 'Endereço Alternativo'")
        logger.info("4. Quando estiver na página com o checkbox 'Endereço Alternativo', pressione ENTER")
        logger.info("="*80 + "\n")
        
        input("Pressione ENTER quando estiver na página com o checkbox 'Endereço Alternativo'...")
        
        # Verifica checkbox "Endereço Alternativo"
        checkbox_encontrado, checkbox_selecionado = verificar_checkbox_endereco_alternativo(driver)
        
        if not checkbox_encontrado:
            logger.error("FALHA: Não foi possível encontrar o checkbox 'Endereço Alternativo'")
            input("Pressione ENTER para tentar continuar com o teste dos botões mesmo assim...")
        elif checkbox_selecionado:
            logger.info("SUCESSO: Checkbox 'Endereço Alternativo' está marcado")
        else:
            logger.warning("ATENÇÃO: Checkbox 'Endereço Alternativo' foi encontrado, mas não está marcado")
            
            # Pergunta se o usuário quer marcar o checkbox para o teste
            marcar = input("Deseja marcar o checkbox 'Endereço Alternativo' para o teste? (s/n): ")
            
            if marcar.lower() == 's':
                try:
                    # Procura o checkbox novamente
                    seletores = [
                        'input[name="usaEnderecoAlternativo"]',
                        'input[aria-label="Endereço Alternativo"]'
                    ]
                    
                    for seletor in seletores:
                        checkboxes = driver.find_elements(By.CSS_SELECTOR, seletor)
                        if checkboxes:
                            checkbox = checkboxes[0]
                            
                            # Tenta clicar para marcar
                            checkbox.click()
                            logger.info("Checkbox clicado para marcar 'Endereço Alternativo'")
                            
                            # Verifica se foi marcado
                            checkbox_encontrado, checkbox_selecionado = verificar_checkbox_endereco_alternativo(driver)
                            if checkbox_selecionado:
                                logger.info("SUCESSO: Checkbox 'Endereço Alternativo' foi marcado manualmente")
                                break
                            else:
                                logger.warning("Não foi possível marcar o checkbox")
                except Exception as e:
                    logger.error(f"Erro ao tentar marcar o checkbox: {e}")
        
        # Se o checkbox estiver marcado, tenta clicar em "Próximo" diretamente
        if checkbox_selecionado:
            logger.info("Tentando clicar em 'Próximo' diretamente (simulando o fluxo com endereço alternativo)")
            botao_proximo_ok = clicar_proximo_apos_verificacao(driver, logger)
            
            if botao_proximo_ok:
                logger.info("SUCESSO: Botão 'Próximo' clicado com sucesso após verificar checkbox!")
                # Aguarda carregamento
                time.sleep(3)
                esperar_pagina_carregar(driver, 5, logger)
            else:
                logger.warning("Não foi possível clicar no botão 'Próximo' automaticamente")
                # Pede para o usuário clicar manualmente
                input("Por favor, clique manualmente no botão 'Próximo' e depois pressione ENTER...")
        else:
            input("Após preencher os dados de endereço ou quando estiver pronto para testar o botão 'Próximo', pressione ENTER...")
        
        # Segunda fase do teste - chegando na etapa dos tributos
        logger.info("\n" + "="*80)
        logger.info("SEGUNDA FASE DO TESTE - VERIFICAÇÃO DE VALOR LÍQUIDO E FINALIZAÇÃO")
        logger.info("1. Preencha todos os campos necessários até chegar na etapa de tributos")
        logger.info("2. Quando estiver na página de tributos e valor líquido, pressione ENTER")
        logger.info("="*80 + "\n")
        
        input("Pressione ENTER quando estiver na página de verificação de valor líquido...")
        
        # Salva o estado atual
        salvar_screenshot(driver, "tela_verificacao_valor_liquido.png", logger)
        salvar_html(driver, "tela_verificacao_valor_liquido")
        
        # Simulando o fluxo de finalização
        finalizar = input("Deseja testar o processo de finalização (clique em 'Próximo' e depois em 'Emitir')? (s/n): ")
        
        if finalizar.lower() == 's':
            logger.info("Iniciando o processo de finalização da nota fiscal...")
            
            # Testa a função completa de finalização
            if finalizar_emissao_nota:
                finalizar_ok = finalizar_emissao_nota(driver, logger)
                
                if finalizar_ok:
                    logger.info("TESTE COMPLETO BEM-SUCEDIDO: Nota fiscal emitida com sucesso!")
                else:
                    logger.warning("Houve problemas durante o processo de finalização")
            else:
                logger.error("Módulo de finalização não disponível")
        else:
            logger.info("Teste de finalização pulado pelo usuário")
            
        input("\nTeste concluído. Pressione ENTER para encerrar...")
        
    except Exception as e:
        logger.error(f"Erro durante o teste de fluxo completo: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Salva um screenshot final
        try:
            salvar_screenshot(driver, "teste_fluxo_final.png", logger)
        except:
            pass
            
        # Fecha o navegador
        driver.quit()

if __name__ == "__main__":
    teste_fluxo_completo()

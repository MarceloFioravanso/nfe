"""
Teste para verificar se o checkbox "Endereço Alternativo" está sendo detectado corretamente 
após a seleção da empresa tomadora.
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import os

# Configura o logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('teste_endereco_alternativo')

# Garante que a pasta de screenshots existe
os.makedirs("logs/imagens", exist_ok=True)

# Função para salvar screenshots na pasta correta
def salvar_screenshot(driver, nome_arquivo):
    """Salva um screenshot na pasta de imagens com o nome especificado"""
    caminho_completo = os.path.join("logs/imagens", nome_arquivo)
    try:
        driver.save_screenshot(caminho_completo)
        logger.info(f"Screenshot salvo em {caminho_completo}")
    except Exception as e:
        logger.error(f"Erro ao salvar screenshot {nome_arquivo}: {e}")

def teste_endereco_alternativo():
    """
    Testa a capacidade de detectar se o checkbox "Endereço Alternativo" está marcado
    após a seleção da empresa tomadora.
    """
    logger.info("Iniciando teste de detecção do checkbox Endereço Alternativo")
    
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
        try:
            salvar_screenshot(driver, "teste_endereco_alternativo_pagina_inicial.png")
            logger.info("Screenshot salvo da página inicial")
        except Exception as e:
            logger.warning(f"Erro ao salvar screenshot: {e}")
        
        # Mostra instruções para o usuário
        logger.info("\n" + "="*60)
        logger.info("INSTRUÇÕES PARA O TESTE:")
        logger.info("1. Faça login no sistema")
        logger.info("2. Selecione uma empresa tomadora")
        logger.info("3. Quando estiver na página com o checkbox 'Endereço Alternativo', pressione ENTER para continuar o teste")
        logger.info("="*60 + "\n")
        
        input("Pressione ENTER quando estiver na página com o checkbox 'Endereço Alternativo'...")
        
        # Tenta encontrar o checkbox "Endereço Alternativo"
        logger.info("Procurando pelo checkbox 'Endereço Alternativo'...")
        
        # Lista de seletores possíveis para o checkbox
        seletores_checkbox = [
            'input[name="usaEnderecoAlternativo"]',
            'input[aria-label="Endereço Alternativo"]',
            'input.__estrutura_componente_base.campo.estrutura_check_tipo_toggle[name="usaEnderecoAlternativo"]',
            'input.estrutura_check_tipo_toggle[name="usaEnderecoAlternativo"]'
        ]
        
        checkbox_encontrado = False
        
        # Tenta encontrar o checkbox por CSS
        for seletor in seletores_checkbox:
            try:
                checkboxes = driver.find_elements(By.CSS_SELECTOR, seletor)
                if checkboxes:
                    checkbox = checkboxes[0]
                    checkbox_encontrado = True
                    esta_selecionado = checkbox.is_selected()
                    logger.info(f"Checkbox 'Endereço Alternativo' encontrado com seletor: {seletor}")
                    logger.info(f"Checkbox está {'MARCADO' if esta_selecionado else 'DESMARCADO'}")
                    
                    # Salva um screenshot para análise
                    salvar_screenshot(driver, "teste_endereco_alternativo_checkbox_encontrado.png")
                    
                    # Tenta clicar no checkbox para alternar seu estado
                    try:
                        checkbox.click()
                        logger.info("Clicou no checkbox para alternar seu estado")
                        time.sleep(1)
                        
                        # Verifica o novo estado
                        novo_estado = checkbox.is_selected()
                        logger.info(f"Novo estado do checkbox: {'MARCADO' if novo_estado else 'DESMARCADO'}")
                        
                        # Salva um screenshot para análise
                        salvar_screenshot(driver, "teste_endereco_alternativo_checkbox_alterado.png")
                        
                        # Restaura o estado original
                        if novo_estado != esta_selecionado:
                            checkbox.click()
                            logger.info("Restaurou o estado original do checkbox")
                            time.sleep(1)
                            salvar_screenshot(driver, "teste_endereco_alternativo_checkbox_restaurado.png")
                    except Exception as e:
                        logger.warning(f"Não foi possível clicar no checkbox: {e}")
                    
                    break
            except Exception as e:
                logger.debug(f"Erro ao procurar checkbox com seletor {seletor}: {e}")
        
        # Se não encontrou por CSS, tenta por XPath
        if not checkbox_encontrado:
            logger.info("Tentando encontrar o checkbox por XPath...")
            xpath_seletores = [
                "//input[@name='usaEnderecoAlternativo']",
                "//input[@aria-label='Endereço Alternativo']",
                "//label[contains(text(), 'Endereço Alternativo')]/preceding-sibling::input",
                "//label[contains(text(), 'Endereço Alternativo')]/following-sibling::input"
            ]
            
            for xpath in xpath_seletores:
                try:
                    elementos = driver.find_elements(By.XPATH, xpath)
                    if elementos:
                        checkbox = elementos[0]
                        checkbox_encontrado = True
                        esta_selecionado = checkbox.is_selected()
                        logger.info(f"Checkbox 'Endereço Alternativo' encontrado com XPath: {xpath}")
                        logger.info(f"Checkbox está {'MARCADO' if esta_selecionado else 'DESMARCADO'}")
                        
                        salvar_screenshot(driver, "teste_endereco_alternativo_checkbox_encontrado.png")
                        break
                except Exception as e:
                    logger.debug(f"Erro ao procurar checkbox com XPath {xpath}: {e}")
        
        if not checkbox_encontrado:
            logger.error("Checkbox 'Endereço Alternativo' não encontrado")
            
            # Exibe informações sobre elementos da página para diagnóstico
            try:
                # Procura por todos os inputs do tipo checkbox
                checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
                logger.info(f"Encontrados {len(checkboxes)} checkboxes na página:")
                
                for i, checkbox in enumerate(checkboxes):
                    try:
                        nome = checkbox.get_attribute("name") or ""
                        aria_label = checkbox.get_attribute("aria-label") or ""
                        classe = checkbox.get_attribute("class") or ""
                        visivel = checkbox.is_displayed()
                        logger.info(f"Checkbox {i+1}: name='{nome}', aria-label='{aria_label}', class='{classe}', visível={visivel}")
                    except:
                        logger.info(f"Checkbox {i+1}: (erro ao obter propriedades)")
                        
                # Procura por todos os labels também
                labels = driver.find_elements(By.TAG_NAME, "label")
                logger.info(f"Encontrados {len(labels)} labels na página:")
                
                for i, label in enumerate(labels):
                    try:
                        texto = label.text
                        if texto and ("endereço" in texto.lower() or "alternativo" in texto.lower()):
                            logger.info(f"Label {i+1} relevante: '{texto}'")
                    except:
                        pass
            except Exception as e:
                logger.error(f"Erro ao analisar elementos da página: {e}")
                
            salvar_screenshot(driver, "teste_endereco_alternativo_checkbox_nao_encontrado.png")
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        # Pergunta se deseja fechar o navegador
        fechar = input("Deseja fechar o navegador? (s/n): ")
        if fechar.lower() == 's':
            driver.quit()
            logger.info("Navegador fechado")
        else:
            logger.info("Navegador mantido aberto para análise")

if __name__ == "__main__":
    teste_endereco_alternativo()

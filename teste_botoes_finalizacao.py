"""
Teste para verificar se os botões "Próximo" e "Emitir" são encontrados corretamente.
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
from finalizar_emissao import clicar_proximo_apos_verificacao, clicar_emitir

# Configura o logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('teste_botoes')

def teste_botoes_proximo_emitir():
    """
    Testa a capacidade de encontrar os botões "Próximo" e "Emitir".
    """
    logger.info("Iniciando teste de detecção dos botões Próximo e Emitir")
    
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
            driver.save_screenshot("logs/imagens/teste_botoes_pagina_inicial.png")
            logger.info("Screenshot salvo em logs/imagens/teste_botoes_pagina_inicial.png")
        except Exception as e:
            logger.warning(f"Erro ao salvar screenshot: {e}")
        
        # Mostra instruções para o usuário
        logger.info("\n" + "="*60)
        logger.info("INSTRUÇÕES PARA O TESTE:")
        logger.info("1. Faça login no sistema")
        logger.info("2. Navegue até a página que contém os botões 'Próximo' e 'Emitir'")
        logger.info("3. Quando estiver na página correta, pressione ENTER para continuar o teste")
        logger.info("="*60 + "\n")
        
        input("Pressione ENTER quando estiver na página com os botões para testá-los...")
        
        # Tenta encontrar o botão "Próximo"
        logger.info("Procurando pelo botão 'Próximo'...")
        proximo_encontrado = clicar_proximo_apos_verificacao(driver, logger)
        
        if proximo_encontrado:
            logger.info("SUCESSO: Botão 'Próximo' encontrado e clicado!")
            
            # Aguarda a próxima página carregar
            time.sleep(3)
            
            # Tenta encontrar o botão "Emitir"
            logger.info("Procurando pelo botão 'Emitir'...")
            emitir_encontrado = clicar_emitir(driver, logger)
            
            if emitir_encontrado:
                logger.info("SUCESSO: Botão 'Emitir' encontrado e clicado!")
                
                # Aqui seria o momento em que a nota seria emitida
                # Mas como é um teste, interrompe antes da emissão final
                logger.info("TESTE CONCLUÍDO COM SUCESSO!")
                
                # Pergunta se deseja continuar com a emissão real
                continuar = input("Deseja continuar com a emissão real da nota? (s/n): ")
                if continuar.lower() != 's':
                    logger.info("Emissão cancelada pelo usuário")
            else:
                logger.error("FALHA: Botão 'Emitir' não encontrado")
        else:
            logger.error("FALHA: Botão 'Próximo' não encontrado")
            
            # Verifica se há elementos na página que podem nos ajudar a entender o problema
            try:
                botoes = driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"Encontrados {len(botoes)} botões na página:")
                
                for i, botao in enumerate(botoes):
                    try:
                        texto = botao.text
                        classe = botao.get_attribute("class") or ""
                        nome = botao.get_attribute("name") or ""
                        visivel = botao.is_displayed()
                        logger.info(f"Botão {i+1}: texto='{texto}', classe='{classe}', nome='{nome}', visível={visivel}")
                    except:
                        logger.info(f"Botão {i+1}: (erro ao obter propriedades)")
            except Exception as e:
                logger.error(f"Erro ao analisar botões: {e}")
    
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
    teste_botoes_proximo_emitir()

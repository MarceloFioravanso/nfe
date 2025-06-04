"""
Script para processar múltiplas notas fiscais do Excel em sequência.
Este script estende as funcionalidades do nfs_emissao_auto.py, permitindo
processar várias notas pendentes em uma única execução.

Como usar:
1. Execute este script para ver todas as notas pendentes no Excel
2. Escolha quantas notas deseja processar:
   - Digite um número específico (ex: 3)
   - Digite "todas" para processar todas as notas pendentes
   - Digite "cancelar" para sair sem processar
3. As notas serão processadas em sequência, uma após a outra
4. Após cada nota, o script atualiza o Excel automaticamente
5. Se ocorrer um erro, você tem a opção de continuar com a próxima nota

Benefícios:
- Economiza tempo ao processar múltiplas notas em uma única execução
- Mantém o navegador aberto entre as notas, evitando relogin
- Atualiza o Excel após cada nota, garantindo que o progresso seja salvo
- Permite acompanhar o status de todas as notas pendentes
"""
import os
import time
import logging
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from pathlib import Path

# Tenta importar o módulo principal de emissão de notas
try:
    from nfs_emissao_auto import (
        logger, carregar_dados_excel, mapear_dados_nota, salvar_screenshot, salvar_html,
        esperar_pagina_carregar, realizar_login, clicar_acessar_fiscal, fechar_aviso,
        aguardar_pagina_destino, clicar_emitir_nota_fiscal, clicar_proximo,
        verificar_emissao_iniciada, selecionar_tipo_tomador, atualizar_numero_nota_excel,
        extrair_numero_nota, EXCEL_PATH, NFS_URL, CPF_CNPJ, SENHA, PAGINA_DESTINO
    )
except ImportError as e:
    print(f"ERRO: Não foi possível importar módulos do nfs_emissao_auto.py: {e}")
    print("Certifique-se de que o arquivo nfs_emissao_auto.py está presente no diretório atual.")
    exit(1)

# Configuração adicional de log específico para processamento múltiplo
log_filename = f'logs/multiplas_notas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_filename,
    filemode='w'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
logger = logging.getLogger('Processamento_Multiplo_NFSe')

# Pasta para salvar os screenshots
SCREENSHOTS_FOLDER = "logs/imagens"
# Garante que a pasta existe
os.makedirs(SCREENSHOTS_FOLDER, exist_ok=True)

def encontrar_notas_pendentes(df):
    """
    Encontra todas as notas pendentes a serem processadas (linhas sem número na primeira coluna mas com dados válidos).
    
    Args:
        df (pd.DataFrame): DataFrame com os dados do Excel
        
    Returns:
        list: Lista de dicionários com dados das notas pendentes a serem processadas ou lista vazia se não encontrar
    """
    try:
        if df is None or df.empty:
            logger.error("DataFrame está vazio ou é None")
            return []
        
        logger.info("Procurando por notas pendentes a serem processadas...")
        
        # Assumindo que a primeira coluna contém os números das notas
        primeira_coluna = df.columns[0]
        logger.info(f"Analisando coluna: {primeira_coluna}")
        
        notas_pendentes = []
        
        # Encontra todas as linhas sem número mas que tenham dados válidos
        for idx in range(len(df)):
            linha = df.iloc[idx]
            numero_nota = linha[primeira_coluna]
            empresa = linha['Empresa - Razão Social']
            cnpj = linha['CNPJ']
            
            # Verifica se o número da nota está vazio
            numero_vazio = pd.isna(numero_nota) or numero_nota == "" or numero_nota is None
            
            # Verifica se a linha tem dados válidos (empresa ou CNPJ)
            tem_dados = not (pd.isna(empresa) or pd.isna(cnpj))
            
            if numero_vazio and tem_dados:
                logger.info(f"Encontrada nota pendente na posição {idx + 1} (linha {idx + 3} do Excel)")
                
                # Adiciona os dados desta linha como dicionário
                dados_nota = linha.to_dict()
                
                notas_pendentes.append({
                    'linha_excel': idx + 3,  # +3 porque pandas é 0-based, Excel começa na linha 1, e temos 2 linhas de header
                    'dados': dados_nota
                })
        
        # Log das notas encontradas
        if notas_pendentes:
            logger.info(f"Total de {len(notas_pendentes)} notas pendentes encontradas.")
            
            # Log com detalhes de cada nota (mascarando informações sensíveis)
            for i, nota in enumerate(notas_pendentes):
                logger.info(f"\nDados da nota pendente {i+1} (linha {nota['linha_excel']} do Excel):")
                for coluna, valor in nota['dados'].items():
                    if pd.notna(valor) and valor != "":
                        # Mascarar CNPJ se necessário
                        if 'CNPJ' in coluna and len(str(valor)) > 6:
                            valor_log = f"{str(valor)[:4]}****{str(valor)[-2:]}"
                        else:
                            valor_log = valor
                        logger.info(f"  {coluna}: {valor_log}")
            
            return notas_pendentes
        else:
            logger.warning("Não foi encontrada nenhuma linha sem número com dados válidos. Todas as notas podem já ter sido processadas.")
            return []
        
    except Exception as e:
        logger.error(f"Erro ao procurar notas pendentes: {e}")
        return []

def processar_notas_pendentes():
    """
    Função principal para processar todas as notas pendentes encontradas no Excel.
    """
    # Importa módulos necessários no escopo local da função
    import os
    import platform
    import sys
    import traceback
    
    # PASSO 1: CARREGAMENTO DOS DADOS DO EXCEL
    logger.info("="*80)
    logger.info("INICIANDO AUTOMAÇÃO DE EMISSÃO DE MÚLTIPLAS NOTAS FISCAIS")
    logger.info("="*80)
    
    # Carrega os dados do Excel
    df_excel = carregar_dados_excel(EXCEL_PATH)
    if df_excel is None:
        logger.error("Falha ao carregar dados do Excel. Encerrando automação.")
        return
    
    # Encontra todas as notas pendentes
    notas_pendentes = encontrar_notas_pendentes(df_excel)
    if not notas_pendentes:
        logger.info("Nenhuma nota pendente encontrada. Todas as notas podem já ter sido processadas.")
        return
    
    logger.info(f"Foram encontradas {len(notas_pendentes)} notas pendentes para processamento.")
    
    # Pergunta ao usuário quantas notas deseja processar
    total_notas = len(notas_pendentes)
    
    print("\n" + "="*60)
    print(f"TOTAL DE NOTAS PENDENTES: {total_notas}")
    for i, nota in enumerate(notas_pendentes):
        empresa = nota['dados'].get('Empresa - Razão Social', 'Empresa não identificada')
        valor = nota['dados'].get('Total', 'Valor não disponível')
        print(f"{i+1}. {empresa} - R$ {valor}")
    print("="*60 + "\n")
    
    resposta = input(f"Quantas notas você deseja processar? (Digite um número, 'todas' ou 'cancelar'): ")
    
    if resposta.lower() == 'cancelar':
        logger.info("Processamento cancelado pelo usuário.")
        return
    elif resposta.lower() == 'todas':
        notas_para_processar = total_notas
    else:
        try:
            notas_para_processar = int(resposta)
            if notas_para_processar < 1:
                logger.warning("Número inválido. Processando apenas 1 nota.")
                notas_para_processar = 1
            elif notas_para_processar > total_notas:
                logger.warning(f"Número excede o total de notas pendentes. Processando todas as {total_notas} notas.")
                notas_para_processar = total_notas
        except ValueError:
            logger.warning("Entrada inválida. Processando apenas 1 nota.")
            notas_para_processar = 1
    
    logger.info(f"Serão processadas {notas_para_processar} nota(s) pendente(s).")
      # Variáveis para controlar o progresso
    notas_processadas = 0
    notas_com_sucesso = 0
    driver = None
    
    print("\n" + "="*60)
    print(f"INÍCIO DO PROCESSAMENTO DE {notas_para_processar} NOTA(S)")
    print("="*60)
    
    # Processa cada nota na sequência
    for indice_nota in range(notas_para_processar):
        proxima_nota = notas_pendentes[indice_nota]
        
        # Atualiza a barra de progresso
        print(f"\nProcessando nota {indice_nota + 1} de {notas_para_processar}:")
        exibir_barra_progresso(indice_nota + 1, notas_para_processar)
        
        logger.info(f"\n{'='*40}")
        logger.info(f"PROCESSANDO NOTA {indice_nota + 1} DE {notas_para_processar}")
        logger.info(f"{'='*40}")
        
        # Mapeia os dados da nota
        dados_nota = mapear_dados_nota(proxima_nota['dados'])
        if dados_nota is None:
            logger.error(f"Falha ao mapear dados da nota {indice_nota + 1}. Pulando para a próxima.")
            continue
        
        linha_excel = proxima_nota['linha_excel']
        logger.info(f"Nota a ser processada encontrada na linha {linha_excel} do Excel")
        
        # Verifica o sistema operacional
        sistema_operacional = platform.system()
        logger.info(f"Sistema Operacional detectado: {sistema_operacional}")
        
        try:
            # PASSO 2: INICIANDO O NAVEGADOR (apenas para a primeira nota)
            if indice_nota == 0 or driver is None:
                logger.info("Configurando navegador...")
                
                # Configurações do Chrome
                chrome_opts = Options()
                chrome_opts.add_argument("--start-maximized")
                chrome_opts.add_argument("--disable-notifications")
                
                # Inicia o navegador
                driver = webdriver.Chrome(options=chrome_opts)
                driver.set_window_size(1920, 1080)
                logger.info("Navegador iniciado com sucesso!")
                
                # PASSO 3: NAVEGANDO PARA A PÁGINA INICIAL
                logger.info(f"Acessando URL: {NFS_URL}")
                driver.get(NFS_URL)
                
                # Aguarda carregamento da página
                esperar_pagina_carregar(driver, timeout=30)
                
                # Captura estado inicial
                salvar_screenshot(driver, f"pagina_inicial_nota_{indice_nota+1}.png")
                logger.info(f"Screenshot inicial salvo")
                
                # Log informativo
                logger.info(f"Título da página: {driver.title}")
                logger.info(f"URL atual: {driver.current_url}")
                
                # Salvar HTML inicial
                salvar_html(driver, f"pagina_inicial_nota_{indice_nota+1}")
                
                # PASSO 3: PROCESSO DE LOGIN
                logger.info("Iniciando processo de login...")
                login_sucesso = realizar_login(driver, CPF_CNPJ, SENHA)
                
                if not login_sucesso:
                    logger.error("Falha no login. Impossível continuar a automação.")
                    break
                
                logger.info("LOGIN REALIZADO COM SUCESSO!")
                
                # PASSO 4: ACESSAR ÁREA FISCAL
                logger.info("Tentando acessar área fiscal...")
                acessar_sucesso = clicar_acessar_fiscal(driver)
                
                if not acessar_sucesso:
                    logger.error("Não foi possível acessar a área fiscal. Impossível continuar.")
                    break
                
                logger.info("Botão 'Acessar' clicado com sucesso!")
                
                # AVISO SOBRE CAPTCHA NESTE MOMENTO
                logger.info("\n" + "*"*80)
                logger.info("ATENÇÃO: RESOLVA O CAPTCHA AGORA!")
                logger.info("Um CAPTCHA deve aparecer após clicar no botão 'Acessar'.")
                logger.info("Por favor resolva o CAPTCHA manualmente na janela do navegador.")
                logger.info("*"*80 + "\n")
                
                # Pausa para permitir resolução manual de CAPTCHA
                input("Pressione ENTER depois de resolver o CAPTCHA para continuar...")
                
                # PASSO 5: AGUARDAR REDIRECIONAMENTO PARA A PÁGINA DE DESTINO
                logger.info(f"Aguardando redirecionamento para: {PAGINA_DESTINO}")
                logger.info("Este processo pode levar vários minutos. Por favor, aguarde...")
                
                # Aguarda até 5 minutos (300 segundos) pelo redirecionamento
                destino_alcancado = aguardar_pagina_destino(driver, PAGINA_DESTINO, tempo_maximo=300)
                
                if not destino_alcancado:
                    logger.error("Não foi possível alcançar a página de destino. Impossível continuar.")
                    break
                
                logger.info("PÁGINA DE DESTINO ALCANÇADA COM SUCESSO!")
                
                # Captura estado final
                salvar_screenshot(driver, f"pagina_destino_nota_{indice_nota+1}.png")
                salvar_html(driver, f"pagina_destino_nota_{indice_nota+1}")
                
                # PASSO 6: FECHAR AVISO NA PÁGINA DE DESTINO
                logger.info("Tentando fechar o aviso na página de destino...")
                fechar_aviso(driver)  # Continuamos mesmo se não conseguirmos fechar
            
            # Para todas as notas (incluindo a primeira), seguimos o fluxo:
            # Se não for a primeira nota, voltamos para a página principal (se necessário)
            if indice_nota > 0:
                try:
                    # Verificar se precisamos voltar à página principal
                    if not "sistema/66" in driver.current_url:
                        logger.info("Voltando para a página principal para processar a próxima nota...")
                        driver.get(PAGINA_DESTINO)
                        esperar_pagina_carregar(driver, timeout=30)
                        salvar_screenshot(driver, f"pagina_principal_nota_{indice_nota+1}.png")
                    
                    # Tenta fechar aviso, se houver
                    fechar_aviso(driver)
                except Exception as e:
                    logger.error(f"Erro ao retornar à página principal: {e}")
                    logger.warning("Tentando continuar mesmo assim...")
            
            # PASSO 7: CLICAR NO BOTÃO "EMITIR NOTA FISCAL"
            logger.info("Tentando clicar no botão 'Emitir Nota Fiscal'...")
            emitir_nota_sucesso = clicar_emitir_nota_fiscal(driver)
            
            if not emitir_nota_sucesso:
                logger.error(f"Não foi possível clicar no botão 'Emitir Nota Fiscal'. Pulando nota {indice_nota+1}.")
                continue
            
            logger.info("BOTÃO 'EMITIR NOTA FISCAL' CLICADO COM SUCESSO!")
            logger.info("Aguardando carregamento da próxima página...")
            time.sleep(3)  # Pausa para carregamento
            
            # PASSO 8: CLICAR NO BOTÃO "PRÓXIMO"
            logger.info("Tentando clicar no botão 'Próximo'...")
            proximo_sucesso = clicar_proximo(driver)
            
            if not proximo_sucesso:
                logger.error(f"Não foi possível clicar no botão 'Próximo'. Pulando nota {indice_nota+1}.")
                continue
            
            logger.info("BOTÃO 'PRÓXIMO' CLICADO COM SUCESSO!")
            
            # Verificar se o fluxo de emissão foi iniciado corretamente
            time.sleep(3)  # Pequena pausa para carregamento
            emissao_iniciada = verificar_emissao_iniciada(driver)
            
            if not emissao_iniciada:
                logger.error(f"Não foi possível iniciar o fluxo de emissão. Pulando nota {indice_nota+1}.")
                continue
            
            logger.info("FLUXO DE EMISSÃO DE NOTA FISCAL INICIADO COM SUCESSO!")
            
            # PASSO 9: SELECIONAR TIPO DO TOMADOR
            logger.info("Selecionando 'Pessoa Jurídica' como tipo do tomador...")
            selecao_sucesso = selecionar_tipo_tomador(driver, tipo="Pessoa Jurídica")
            
            if not selecao_sucesso:
                logger.error(f"Não foi possível selecionar o tipo de tomador. Pulando nota {indice_nota+1}.")
                continue
            
            logger.info("TIPO DO TOMADOR 'PESSOA JURÍDICA' SELECIONADO COM SUCESSO!")
            salvar_screenshot(driver, f"tipo_tomador_nota_{indice_nota+1}.png")
            
            # A partir daqui, o processamento é diferente para cada nota e mais complexo
            # Será necessário importar todos os módulos que fazem parte da emissão de nota
            # E continuar o fluxo... Isso exigiria adicionar mais código aqui.
            
            # Por ora, vamos solicitar ao usuário para continuar manualmente
            logger.info("A configuração inicial foi feita com sucesso.")
            logger.info("Agora você deve continuar o processo manualmente:")
            logger.info("1. Busque pela empresa usando o CNPJ")
            logger.info("2. Preencha os dados do tomador")
            logger.info("3. Preencha os dados do serviço e tributos")
            logger.info("4. Finalize a emissão da nota")
            
            input(f"\nPor favor, termine o processo manualmente e pressione ENTER quando a nota {indice_nota+1} estiver emitida...")
              # Após a emissão manual, pergunta pelo número da nota
            numero_nota_manual = input("\nDigite o número da nota fiscal que acabou de ser emitida (deixe em branco para pular): ")
            
            if numero_nota_manual.strip():
                # Atualiza o Excel com o número da nota
                print(f"\nAtualizando Excel com o número da nota: {numero_nota_manual}...")
                logger.info(f"Atualizando Excel com o número informado: {numero_nota_manual}")
                atualizacao_sucesso = atualizar_numero_nota_excel(
                    EXCEL_PATH, linha_excel, numero_nota_manual)
                
                if atualizacao_sucesso:
                    print("✓ Arquivo Excel atualizado com sucesso!")
                    logger.info("ARQUIVO EXCEL ATUALIZADO COM SUCESSO!")
                    notas_com_sucesso += 1
                else:
                    print("✗ Falha ao atualizar o arquivo Excel!")
                    logger.error("FALHA AO ATUALIZAR O ARQUIVO EXCEL")
                    print("  Por favor, atualize manualmente o número da nota na planilha.")
            else:
                print("⚠ Nenhum número de nota informado. O Excel não será atualizado.")
                logger.warning("Nenhum número de nota informado. O Excel não será atualizado.")
            
            # Incrementa o contador de notas processadas
            notas_processadas += 1
            
            # Se não for a última nota, pergunta se deseja continuar
            if indice_nota < notas_para_processar - 1:
                continuar = input(f"Deseja continuar com a próxima nota? (s/n): ")
                if continuar.lower() != 's':
                    logger.info("Interrompendo o processamento de notas por escolha do usuário.")
                    break
            
        except Exception as e:
            logger.error(f"Erro durante o processamento da nota {indice_nota+1}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            if driver:
                salvar_screenshot(driver, f"erro_execucao_nota_{indice_nota+1}.png")
                logger.info(f"Screenshot do erro salvo")
                salvar_html(driver, f"pagina_erro_nota_{indice_nota+1}")
            
            # Perguntar se deseja continuar com a próxima nota
            if indice_nota < notas_para_processar - 1:  # Se não for a última nota
                continuar = input(f"Ocorreu um erro no processamento da nota {indice_nota+1}. Deseja continuar com a próxima nota? (s/n): ")
                if continuar.lower() != 's':
                    logger.info("Interrompendo o processamento de notas por escolha do usuário.")
                    break
      # Ao final do processamento de todas as notas
    logger.info("\n" + "="*80)
    logger.info(f"PROCESSAMENTO DE NOTAS CONCLUÍDO")
    logger.info(f"Notas processadas: {notas_processadas} de {notas_para_processar}")
    logger.info(f"Notas concluídas com sucesso: {notas_com_sucesso}")
    logger.info("="*80 + "\n")
    
    # Exibir relatório final visual para o usuário
    print("\n" + "="*60)
    print("             RELATÓRIO FINAL DE PROCESSAMENTO             ")
    print("="*60)
    print(f"Notas processadas:      {notas_processadas} de {notas_para_processar}")
    print(f"Notas com sucesso:      {notas_com_sucesso}")
    print(f"Taxa de sucesso:        {(notas_com_sucesso/notas_para_processar)*100:.1f}%")
    
    # Calcula o tempo total de processamento (aproximado)
    tempo_medio = notas_processadas * 2  # estimativa de 2 minutos por nota
    print(f"Tempo aproximado:       {tempo_medio} minutos")
    
    # Data e hora do relatório
    from datetime import datetime
    print(f"Concluído em:          {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*60)
    
    # Caminho do log para consulta
    print(f"\nLog completo disponível em: {log_filename}")
    
    # Para manter a janela aberta após a execução
    if driver:
        print("\n" + "-"*60)
        fechar = input("Deseja fechar o navegador? (s/n): ")
        if fechar.lower() == 's':
            driver.quit()
            logger.info("Navegador fechado.")
            print("Navegador fechado.")
        else:
            logger.info("Navegador mantido aberto. Você pode fechá-lo manualmente quando terminar.")
            print("Navegador mantido aberto. Você pode fechá-lo manualmente quando terminar.")

def modo_teste():
    """
    Executa o script em modo de teste, apenas mostrando as notas pendentes
    sem iniciar o navegador ou processar as notas.
    """
    print("\n" + "="*80)
    print("MODO DE TESTE - VERIFICAÇÃO DE NOTAS PENDENTES")
    print("="*80)
    
    # Carrega os dados do Excel
    df_excel = carregar_dados_excel(EXCEL_PATH)
    if df_excel is None:
        print("Falha ao carregar dados do Excel.")
        return
    
    # Encontra todas as notas pendentes
    notas_pendentes = encontrar_notas_pendentes(df_excel)
    if not notas_pendentes:
        print("\nNenhuma nota pendente encontrada no Excel.")
        return
    
    # Exibe as notas pendentes
    print(f"\nForam encontradas {len(notas_pendentes)} notas pendentes para emissão:")
    print("\n" + "-"*80)
    print(f"{'Linha':<7} | {'Empresa':<30} | {'CNPJ':<20} | {'Valor (R$)':<12}")
    print("-"*80)
    
    # Exibe informações sobre cada nota pendente
    for nota in notas_pendentes:
        linha = nota['linha_excel']
        empresa = nota['dados'].get('Empresa - Razão Social', 'N/A')
        if isinstance(empresa, str) and len(empresa) > 28:
            empresa = empresa[:25] + "..."
            
        cnpj = nota['dados'].get('CNPJ', 'N/A')
        if cnpj and len(str(cnpj)) > 6:
            cnpj = f"{str(cnpj)[:4]}...{str(cnpj)[-4:]}"
            
        valor = nota['dados'].get('Total', 0)
        
        print(f"{linha:<7} | {empresa:<30} | {cnpj:<20} | R$ {valor:<10}")
    
    print("-"*80)
    print(f"\nTotal de notas pendentes: {len(notas_pendentes)}")
    print("\nPara processar estas notas, execute este script sem a opção --teste")
    print("="*80)

def exibir_barra_progresso(atual, total, tamanho=30):
    """
    Exibe uma barra de progresso no console.
    
    Args:
        atual (int): Posição atual do progresso
        total (int): Valor total do progresso
        tamanho (int): Tamanho da barra em caracteres
    """
    concluido = int(tamanho * atual / total)
    barra = '█' * concluido + '░' * (tamanho - concluido)
    percentual = 100 * (atual / total)
    print(f"\r[{barra}] {percentual:.1f}% ({atual}/{total})", end='')
    
    # Se completou, adiciona quebra de linha
    if atual == total:
        print()

if __name__ == "__main__":
    import sys
    
    # Verifica se o script está sendo executado em modo de teste
    if len(sys.argv) > 1 and (sys.argv[1] == "--teste" or sys.argv[1] == "--dry-run"):
        modo_teste()
    else:
        processar_notas_pendentes()

"""
Script para verificar e exibir todas as notas pendentes no Excel.
Útil para conferir quais notas serão processadas antes de iniciar a emissão.

Como usar:
1. Execute este script para ver um resumo de todas as notas pendentes no Excel
2. O script mostrará uma tabela com: linha do Excel, empresa, CNPJ e valor
3. Um arquivo de texto 'notas_pendentes.txt' será gerado com estas informações
4. Nenhuma ação será tomada sobre as notas - este é apenas um relatório

Benefícios:
- Verifica rapidamente quantas notas estão pendentes de emissão
- Fornece um relatório em formato de texto para referência
- Não modifica nenhum dado, apenas exibe informações
- Ajuda a planejar o tempo necessário para processar todas as notas
"""
import os
import pandas as pd
import logging
from datetime import datetime

# Configuração de log
log_filename = f'logs/verificacao_notas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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
logger = logging.getLogger('Verificacao_Notas')

# Garante que a pasta de logs existe
os.makedirs('logs', exist_ok=True)

# Caminho do arquivo Excel
EXCEL_PATH = r"C:\Users\pesqu\OneDrive\LAF\Adm_Fioravanso\Planejamentos_Controles\Financeiro\_Controle NotaFiscal.xlsx"

def carregar_dados_excel(caminho_excel):
    """
    Carrega os dados do arquivo Excel e retorna um DataFrame.
    
    Args:
        caminho_excel (str): Caminho para o arquivo Excel
        
    Returns:
        pd.DataFrame: DataFrame com os dados do Excel ou None se houver erro
    """
    try:
        logger.info(f"Carregando dados do arquivo Excel: {caminho_excel}")
        
        # Verifica se o arquivo existe
        if not os.path.exists(caminho_excel):
            logger.error(f"Arquivo Excel não encontrado: {caminho_excel}")
            return None
        
        # Carrega o arquivo Excel
        # Assume que os dados estão na primeira planilha, com cabeçalho na linha 3 (índice 2)
        df = pd.read_excel(caminho_excel, sheet_name=0, header=2)
        
        logger.info(f"Arquivo Excel carregado com sucesso. {len(df)} linhas encontradas.")
        logger.info(f"Colunas disponíveis: {', '.join(list(df.columns))}")
        
        return df
        
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo Excel: {e}")
        return None

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
            empresa = linha.get('Empresa - Razão Social', None)
            cnpj = linha.get('CNPJ', None)
            
            # Verifica se o número da nota está vazio
            numero_vazio = pd.isna(numero_nota) or numero_nota == "" or numero_nota is None
            
            # Verifica se a linha tem dados válidos (empresa ou CNPJ)
            tem_dados = False
            if empresa is not None and cnpj is not None:
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
            return notas_pendentes
        else:
            logger.warning("Não foi encontrada nenhuma linha sem número com dados válidos. Todas as notas podem já ter sido processadas.")
            return []
        
    except Exception as e:
        logger.error(f"Erro ao procurar notas pendentes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def verificar_notas_pendentes():
    """
    Função principal para verificar e exibir as notas pendentes no Excel.
    """
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE NOTAS FISCAIS PENDENTES NO EXCEL")
    print("="*60)
    
    # Tenta usar o caminho do módulo principal se disponível
    try:
        from nfs_emissao_auto import EXCEL_PATH as CAMINHO_EXCEL
        print(f"Usando caminho do Excel do módulo principal: {CAMINHO_EXCEL}")
    except ImportError:
        CAMINHO_EXCEL = EXCEL_PATH
        print(f"Usando caminho do Excel padrão: {CAMINHO_EXCEL}")
    
    # Pergunta se deseja usar um caminho diferente
    usar_outro_caminho = input("\nDeseja especificar outro caminho para o arquivo Excel? (s/n): ").lower() == 's'
    if usar_outro_caminho:
        CAMINHO_EXCEL = input("Digite o caminho completo do arquivo Excel: ").strip()
        if CAMINHO_EXCEL.startswith('"') and CAMINHO_EXCEL.endswith('"'):
            CAMINHO_EXCEL = CAMINHO_EXCEL[1:-1]
    
    # Carrega os dados do Excel
    df_excel = carregar_dados_excel(CAMINHO_EXCEL)
    if df_excel is None:
        print("\nERRO: Falha ao carregar dados do Excel.")
        return
    
    # Encontra as notas pendentes
    notas_pendentes = encontrar_notas_pendentes(df_excel)
    
    if not notas_pendentes:
        print("\nNenhuma nota pendente encontrada no Excel.")
        return
    
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
    print("\nPara emitir estas notas, execute o script 'processa_multiplas_notas.py'")
    
    # Salva as informações em um arquivo de texto
    try:
        with open('notas_pendentes.txt', 'w', encoding='utf-8') as f:
            f.write(f"NOTAS FISCAIS PENDENTES - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Linha':<7} | {'Empresa':<30} | {'CNPJ':<20} | {'Valor (R$)':<12}\n")
            f.write("-"*80 + "\n")
            
            for nota in notas_pendentes:
                linha = nota['linha_excel']
                empresa = nota['dados'].get('Empresa - Razão Social', 'N/A')
                if isinstance(empresa, str) and len(empresa) > 28:
                    empresa = empresa[:25] + "..."
                    
                cnpj = nota['dados'].get('CNPJ', 'N/A')
                if cnpj and len(str(cnpj)) > 6:
                    cnpj = f"{str(cnpj)[:4]}...{str(cnpj)[-4:]}"
                    
                valor = nota['dados'].get('Total', 0)
                
                f.write(f"{linha:<7} | {empresa:<30} | {cnpj:<20} | R$ {valor:<10}\n")
            
            f.write("-"*80 + "\n")
            f.write(f"Total de notas pendentes: {len(notas_pendentes)}\n")
        
        print(f"\nAs informações foram salvas no arquivo 'notas_pendentes.txt'")
    except Exception as e:
        print(f"\nErro ao salvar informações em arquivo: {e}")

if __name__ == "__main__":
    verificar_notas_pendentes()
    input("\nPressione ENTER para encerrar...")

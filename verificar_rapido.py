"""
Script simples para verificar notas pendentes no Excel sem iniciar processamento.
Este script é independente e não requer outros arquivos do projeto.
"""
import os
import pandas as pd
from datetime import datetime

def verificar_notas_excel(caminho_excel=None):
    """
    Verifica notas pendentes no arquivo Excel e mostra um relatório.
    """
    print("\n" + "="*60)
    print("VERIFICADOR RÁPIDO DE NOTAS FISCAIS PENDENTES")
    print("="*60)
    
    # Definir caminho padrão se não especificado
    if not caminho_excel:
        caminho_excel = r"C:\Users\pesqu\OneDrive\LAF\Adm_Fioravanso\Planejamentos_Controles\Financeiro\_Controle NotaFiscal.xlsx"
        
        # Perguntar se deseja usar outro caminho
        usar_outro = input(f"\nCaminho padrão: {caminho_excel}\nDeseja especificar outro caminho? (s/n): ").lower() == 's'
        if usar_outro:
            caminho_excel = input("Digite o caminho completo do arquivo Excel: ").strip()
            if caminho_excel.startswith('"') and caminho_excel.endswith('"'):
                caminho_excel = caminho_excel[1:-1]
    
    # Verificar se arquivo existe
    if not os.path.exists(caminho_excel):
        print(f"\nERRO: O arquivo {caminho_excel} não foi encontrado.")
        return
    
    try:
        # Carregar dados do Excel (pulando 2 linhas de cabeçalho)
        print(f"\nCarregando arquivo: {caminho_excel}")
        df = pd.read_excel(caminho_excel, sheet_name=0, header=2)
        print(f"Arquivo carregado com sucesso. Analisando {len(df)} linhas...")
        
        # Identificar primeira coluna (que contém números de notas)
        primeira_coluna = df.columns[0]
        
        # Encontrar notas pendentes (sem número mas com dados)
        notas_pendentes = []
        
        for idx in range(len(df)):
            linha = df.iloc[idx]
            numero_nota = linha[primeira_coluna]
            empresa = linha.get('Empresa - Razão Social', '')
            cnpj = linha.get('CNPJ', '')
            
            # Verificar se está vazio o número da nota
            numero_vazio = pd.isna(numero_nota) or numero_nota == "" or numero_nota is None
            
            # Verificar se tem dados válidos
            tem_dados = not (pd.isna(empresa) or pd.isna(cnpj) or empresa == "" or cnpj == "")
            
            if numero_vazio and tem_dados:
                notas_pendentes.append({
                    'linha_excel': idx + 3,  # +3 porque Excel é 1-based e temos 2 linhas de header
                    'empresa': empresa,
                    'cnpj': cnpj,
                    'valor': linha.get('Total', 0)
                })
        
        # Mostrar resultados
        if not notas_pendentes:
            print("\nNenhuma nota pendente encontrada no Excel!")
            return
        
        print(f"\nForam encontradas {len(notas_pendentes)} notas pendentes:")
        print("\n" + "-"*70)
        print(f"{'Linha':<7} | {'Empresa':<35} | {'CNPJ':<15} | {'Valor (R$)':<10}")
        print("-"*70)
        
        for nota in notas_pendentes:
            linha = nota['linha_excel']
            empresa = nota['empresa']
            if isinstance(empresa, str) and len(empresa) > 33:
                empresa = empresa[:30] + "..."
                
            cnpj = nota['cnpj']
            if cnpj and len(str(cnpj)) > 11:
                cnpj = f"{str(cnpj)[:4]}...{str(cnpj)[-4:]}"
                
            valor = nota['valor']
            
            print(f"{linha:<7} | {empresa:<35} | {cnpj:<15} | R$ {valor:<8}")
        
        print("-"*70)
        print(f"\nTotal de notas pendentes: {len(notas_pendentes)}")
        print("\nPara processar estas notas, execute o script 'processa_notas.bat'")
        
        # Salvar em arquivo texto
        arquivo_saida = f'notas_pendentes_{datetime.now().strftime("%Y%m%d_%H%M")}.txt'
        try:
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                f.write(f"RELATÓRIO DE NOTAS FISCAIS PENDENTES - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("-"*70 + "\n")
                f.write(f"{'Linha':<7} | {'Empresa':<35} | {'CNPJ':<15} | {'Valor (R$)':<10}\n")
                f.write("-"*70 + "\n")
                
                for nota in notas_pendentes:
                    linha = nota['linha_excel']
                    empresa = nota['empresa']
                    if isinstance(empresa, str) and len(empresa) > 33:
                        empresa = empresa[:30] + "..."
                        
                    cnpj = nota['cnpj']
                    if cnpj and len(str(cnpj)) > 11:
                        cnpj = f"{str(cnpj)[:4]}...{str(cnpj)[-4:]}"
                        
                    valor = nota['valor']
                    
                    f.write(f"{linha:<7} | {empresa:<35} | {cnpj:<15} | R$ {valor:<8}\n")
                
                f.write("-"*70 + "\n")
                f.write(f"\nTotal de notas pendentes: {len(notas_pendentes)}")
            
            print(f"\nRelatório salvo em: {arquivo_saida}")
        except Exception as e:
            print(f"\nErro ao salvar relatório: {e}")
    
    except Exception as e:
        print(f"\nERRO ao processar arquivo Excel: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    verificar_notas_excel()
    
    print("\nPressione Enter para sair...", end="")
    input()

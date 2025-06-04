# Sistema de Automação para Emissão de NFS-e

Este sistema automatiza a emissão de Notas Fiscais de Serviço Eletrônicas (NFS-e) a partir de dados em uma planilha Excel.

## Principais Arquivos

### Scripts Principais:

1. **nfs_emissao_auto.py**  
   Script original que processa uma nota fiscal por vez.

2. **processa_multiplas_notas.py**  
   Versão melhorada que processa várias notas em sequência em uma única execução.

3. **verificar_notas_pendentes.py**  
   Ferramenta para verificar quantas notas pendentes existem sem iniciar o processamento.

### Scripts Auxiliares:

- **preencher_tributos.py**: Preenche os campos de tributos federais (IR, PIS, COFINS, CSLL)
- **finalizar_emissao.py**: Contém funções para finalizar a emissão da nota
- **busca_empresa.py**: Funções para buscar empresas por CNPJ

## Fluxo de Trabalho

### 1. Verificar Notas Pendentes
```
python verificar_notas_pendentes.py
```
Este comando mostra todas as notas pendentes na planilha e gera um relatório em `notas_pendentes.txt`.

### 2. Processar Múltiplas Notas
```
python processa_multiplas_notas.py
```
Este comando:
- Lista todas as notas pendentes
- Permite escolher quantas notas processar
- Processa as notas em sequência, atualizando o Excel após cada uma
- Mantém o navegador aberto entre as notas

### 3. Processar Uma Nota (método original)
```
python nfs_emissao_auto.py
```
Este comando processa uma única nota fiscal.

## Diferenças entre os Scripts

| Funcionalidade | nfs_emissao_auto.py | processa_multiplas_notas.py |
|---------------|-------------------|---------------------------|
| Notas processadas | Uma única nota | Múltiplas notas em sequência |
| Atualização do Excel | Após processar a nota | Após cada nota individual |
| Sessão do navegador | Nova para cada execução | Uma única sessão para todas as notas |
| Interface | Básica | Detalhada com lista de notas |
| Recuperação de erro | Encerra em caso de erro | Permite continuar com próxima nota |

## Como Funciona o Processamento Múltiplo

O script `processa_multiplas_notas.py`:

1. Carrega a planilha Excel e encontra todas as notas pendentes (sem número de nota)
2. Mostra uma lista numerada das notas pendentes com detalhes
3. Pergunta quantas notas o usuário deseja processar
4. Inicia o navegador e faz login apenas uma vez
5. Para cada nota selecionada:
   - Navega para a página de emissão
   - Preenche os dados da nota fiscal
   - Finaliza a emissão ou aguarda confirmação manual
   - Atualiza o Excel com o número da nota emitida
6. Após processar todas as notas, mostra um relatório final

## Requisitos

- Python 3.6+
- Google Chrome
- Bibliotecas Python (instaláveis via `pip install -r requirements.txt`):
  - pandas
  - selenium
  - openpyxl
  - python-dotenv
  - chromedriver-autoinstaller

## Configuração

1. Certifique-se de que o caminho para o arquivo Excel está correto em `nfs_emissao_auto.py`
2. Crie um arquivo `.env` com suas credenciais de acesso ao sistema:
   ```
   NFS_URL=https://nfse-exemplo.atende.net
   CPF_CNPJ=seu_cpf_ou_cnpj
   SENHA=sua_senha
   ```

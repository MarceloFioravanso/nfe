# Automação de E-mails para Notas Fiscais

Este projeto automatiza o envio de e-mails com notas fiscais anexadas, utilizando a biblioteca `exchangelib` para interagir com o Exchange.

## Estrutura do Projeto
- `email_automation.py`: Script principal para renomear arquivos, criar rascunhos de e-mail e processar informações.
- `entrada/`: Pasta onde os arquivos PDF e XML devem ser colocados.
- `layout_email.txt`: Modelo de e-mail utilizado para criar os rascunhos.
- `informacoes_notas.xlsx`: Arquivo Excel com as informações das notas e e-mails dos destinatários.
- `emails_encontrados.xlsx`: Arquivo Excel gerado com os e-mails encontrados nos últimos 3 anos.

## Configuração
1. Crie um arquivo `.env` com as seguintes variáveis de ambiente:
   ```dotenv
   EMAIL_USUARIO=seu_email@exemplo.com
   EMAIL_SENHA=sua_senha
   # Opcional, caso use ews sem autodiscover:
   EMAIL_SERVER=servidor_ews.exemplo.com
   # Ou, se usar endpoint EWS:
   EMAIL_SERVICE_ENDPOINT=https://ews.exemplo.com/EWS/Exchange.asmx
   ```

2. Preencha o arquivo `informacoes_notas.xlsx` com as colunas:
   - `Numero`: Número da nota fiscal.
   - `Email`: E-mail do(s) destinatário(s). Para múltiplos, separe por `;`.
   - `Empresa (reduzido)`: Código ou nome reduzido da empresa (usado no sufixo de arquivos).

3. Coloque os arquivos PDF e XML na pasta `entrada/` antes de executar.

## Execução
1. Instale as dependências:
   ```bash
   pip install exchangelib python-dotenv pandas openpyxl PyPDF2
   ```

2. Execute o script principal:
   ```bash
   python email_automation.py
   ```

## Funcionalidades
- Renomeia arquivos PDF/XML adicionando prefixo `ANO_Numero - Empresa` usando o número interno do PDF (próximo a “Número da NFS-e”) ou do XML.
- Lê informações de `informacoes_notas.xlsx` (Número, Email, Empresa) para gerar rascunhos no Exchange.
- Suporta múltiplos destinatários separados por `;`.
- Gera rascunhos de e-mail com assunto, corpo via template (`layout_email.txt`) e anexos.
- (Opcional) Com `--historico`, gera relatório `historico_envios.xlsx` com envios dos últimos 3 anos.
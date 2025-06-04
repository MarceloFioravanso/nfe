# Sistema de Automação de Notas Fiscais de Serviço Eletrônicas (NFS-e)

Este sistema permite automatizar a emissão de múltiplas notas fiscais a partir de uma planilha Excel, incluindo a identificação de notas pendentes, processamento em lote e atualização automática da planilha.

## Scripts Principais

1. **verificar_notas_pendentes.py** - Mostra quais notas estão pendentes de emissão no Excel
2. **processa_multiplas_notas.py** - Processa múltiplas notas em sequência em uma única execução
3. **nfs_emissao_auto.py** - Script original para processamento de uma nota por vez

## Como Usar

### Para Verificar Notas Pendentes

Execute o arquivo batch:
```
verificar_notas.bat
```

Ou diretamente em Python:
```
python verificar_notas_pendentes.py
```

Isto mostrará uma lista com todas as notas pendentes no Excel e gerará um relatório em `notas_pendentes.txt`.

### Para Processar Múltiplas Notas

Execute o arquivo batch:
```
processa_notas.bat
```

Ou diretamente em Python:
```
python processa_multiplas_notas.py
```

O sistema irá:
1. Listar todas as notas pendentes encontradas
2. Perguntar quantas notas deseja processar (uma, várias ou todas)
3. Processar as notas em sequência, atualizando o Excel após cada uma

### Para Testar Sem Processar (Modo Teste)

Execute:
```
verificar_teste.bat
```

Ou diretamente em Python:
```
python processa_multiplas_notas.py --teste
```

## Como Funciona

O sistema identifica notas pendentes no Excel procurando por linhas que:
- Não possuem número de nota preenchido na primeira coluna
- Possuem dados válidos (empresa e CNPJ) preenchidos

Para cada nota pendente, o sistema:
1. Acessa o sistema de emissão de NFS-e usando Selenium
2. Preenche os dados da nota fiscal
3. Finaliza a emissão (automaticamente ou com confirmação manual)
4. Atualiza a planilha Excel com o número da nota emitida

## Vantagens do Processamento Múltiplo

- **Economia de Tempo**: Processa várias notas em uma única execução
- **Sessão Única**: Mantém o navegador aberto entre notas, evitando relogin
- **Segurança**: Atualiza o Excel após cada nota, garantindo que o progresso seja salvo
- **Flexibilidade**: Permite escolher quantas notas processar de cada vez
- **Recuperação de Erros**: Opção de continuar para a próxima nota em caso de falhas

## Requisitos

- Python 3.6+
- Google Chrome
- Bibliotecas Python (instaláveis via `pip install -r requirements.txt`)

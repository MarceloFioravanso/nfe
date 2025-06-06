import tokenize
import io

def verificar_indentacao(arquivo):
    with open(arquivo, 'rb') as f:
        tokens = tokenize.tokenize(f.readline)
        for token in tokens:
            if token.type == tokenize.INDENT:
                print(f"INDENT encontrado na linha {token.start[0]}: {repr(token.string)}")
            elif token.type == tokenize.DEDENT:
                print(f"DEDENT encontrado na linha {token.start[0]}")
            elif token.type == tokenize.ERROR:
                print(f"ERRO na linha {token.start[0]}: {repr(token.string)}")

if __name__ == "__main__":
    verificar_indentacao('nfs_emissao_auto.py')

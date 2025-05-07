import os
from PIL import Image, ImageDraw, ImageFont
import sys

def gerar_imagem_com_coordenadas(imagem_path, output_path=None, grid_step=50):
    """
    Gera uma versão da imagem com uma grade de coordenadas sobreposta.
    Útil para identificar onde clicar em CAPTCHAs em ambientes sem interface gráfica.
    
    Args:
        imagem_path: Caminho para a imagem de entrada
        output_path: Caminho para salvar a imagem com coordenadas (opcional)
        grid_step: Espaçamento da grade em pixels
    """
    if not os.path.exists(imagem_path):
        print(f"Erro: A imagem {imagem_path} não foi encontrada.")
        return

    # Carrega a imagem
    try:
        imagem = Image.open(imagem_path)
        print(f"Imagem carregada: {imagem_path}")
        print(f"Dimensões: {imagem.size[0]}x{imagem.size[1]} pixels")
    except Exception as e:
        print(f"Erro ao abrir a imagem: {e}")
        return

    # Cria uma cópia da imagem para não modificar a original
    img_com_coordenadas = imagem.copy()
    
    # Prepara para desenhar na imagem
    draw = ImageDraw.Draw(img_com_coordenadas)
    
    # Tenta carregar uma fonte, se não conseguir usa o padrão
    try:
        # Tenta encontrar uma fonte no sistema
        font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except IOError:
        try:
            # Segunda tentativa com outra fonte comum
            font = ImageFont.truetype("Arial.ttf", 12)
        except IOError:
            # Se não encontrar, usa a fonte padrão
            font = ImageFont.load_default()
    
    # Desenha linhas horizontais e verticais em intervalos regulares
    largura, altura = imagem.size
    
    # Desenha linhas horizontais
    for y in range(0, altura, grid_step):
        draw.line([(0, y), (largura, y)], fill=(255, 0, 0), width=1)
        # Adiciona coordenada Y
        draw.text((5, y), str(y), fill=(255, 0, 0), font=font)
    
    # Desenha linhas verticais
    for x in range(0, largura, grid_step):
        draw.line([(x, 0), (x, altura)], fill=(255, 0, 0), width=1)
        # Adiciona coordenada X
        draw.text((x, 5), str(x), fill=(255, 0, 0), font=font)
    
    # Determina o nome do arquivo de saída
    if output_path is None:
        base, ext = os.path.splitext(imagem_path)
        output_path = f"{base}_com_coordenadas{ext}"
    
    # Salva a imagem com coordenadas
    img_com_coordenadas.save(output_path)
    print(f"Imagem com grade de coordenadas salva em: {output_path}")
    
    return output_path

def mostrar_pontos_interativos(imagem_path):
    """
    Permite ao usuário especificar pontos de clique manualmente usando coordenadas.
    Os pontos serão marcados na imagem e salvos em uma nova versão.
    """
    print("\nSelecione pontos para clicar na imagem:")
    print("Digite as coordenadas no formato 'x,y' ou 'fim' para terminar")
    
    pontos = []
    
    while True:
        entrada = input("\nDigite as coordenadas (x,y) ou 'fim' para terminar: ")
        
        if entrada.lower() == 'fim':
            break
        
        try:
            x, y = map(int, entrada.split(','))
            pontos.append((x, y))
            print(f"Ponto adicionado: ({x}, {y})")
        except ValueError:
            print("Formato inválido! Use 'x,y' (ex: 150,200)")
    
    if pontos:
        # Carrega a imagem e marca os pontos
        try:
            # Carrega a imagem com coordenadas se existir, senão a original
            base, ext = os.path.splitext(imagem_path)
            imagem_coords_path = f"{base}_com_coordenadas{ext}"
            
            if os.path.exists(imagem_coords_path):
                imagem = Image.open(imagem_coords_path)
            else:
                imagem = Image.open(imagem_path)
                
            draw = ImageDraw.Draw(imagem)
            
            # Marca cada ponto selecionado com um círculo
            for i, (x, y) in enumerate(pontos):
                raio = 10
                draw.ellipse([(x-raio, y-raio), (x+raio, y+raio)], outline=(0, 255, 0), width=2)
                draw.text((x+raio+5, y), f"Ponto {i+1}: ({x},{y})", fill=(0, 255, 0))
            
            # Salva a nova imagem
            output_path = f"{base}_com_pontos{ext}"
            imagem.save(output_path)
            print(f"\nImagem com pontos marcados salva em: {output_path}")
            
            # Retorna string formatada para uso no script CAPTCHA
            pontos_formatados = ' '.join([f"{x},{y}" for x, y in pontos])
            print(f"\nCoordenadas para usar no script de CAPTCHA:")
            print(pontos_formatados)
            print("\nCopie e cole esta string quando o script nfs_emissao.py solicitar as coordenadas.")
            
        except Exception as e:
            print(f"Erro ao processar a imagem com os pontos: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        imagem_path = sys.argv[1]
    else:
        # Se nenhuma imagem for especificada, tenta usar captcha_page.png
        imagem_path = "captcha_page.png"
        if not os.path.exists(imagem_path):
            imagem_path = input("Digite o caminho para a imagem do CAPTCHA: ")
    
    # Gera a imagem com grade de coordenadas
    gerar_imagem_com_coordenadas(imagem_path)
    
    # Permite ao usuário marcar pontos de clique
    mostrar_pontos_interativos(imagem_path)
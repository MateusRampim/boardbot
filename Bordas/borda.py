import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import io, filters


# Carregar a imagem (modificado para suportar cor)
imagem_cor = io.imread('image.jpg')  # Carrega imagem colorida
imagem = cv2.cvtColor(imagem_cor, cv2.COLOR_RGB2GRAY)  # Versão em tons de cinza

# Diferentes níveis de suavização (modificado)
suave_media = cv2.GaussianBlur(imagem, (5,5), 1.0)
suave_intermediaria = cv2.GaussianBlur(imagem, (5,5), sigmaX=1.2, sigmaY=1.0)  # Nova suavização
suave_personalizada = cv2.GaussianBlur(imagem, (5,5), sigmaX=1.5, sigmaY=0.5)

# Função para limpar ruído
def limpar_ruido(imagem):
    kernel = np.ones((3,3), np.uint8)
    imagem = cv2.morphologyEx(imagem, cv2.MORPH_CLOSE, kernel)
    imagem = cv2.morphologyEx(imagem, cv2.MORPH_OPEN, kernel)
    return imagem

def limpar_bordas(imagem):
    """Função para pós-processamento e limpeza das bordas"""
    # Remover ruídos pequenos
    kernel_small = np.ones((2,2), np.uint8)
    kernel_med = np.ones((3,3), np.uint8)
    
    # Sequência de operações morfológicas
    imagem = cv2.morphologyEx(imagem, cv2.MORPH_OPEN, kernel_small)  # Remove ruídos pequenos
    imagem = cv2.dilate(imagem, kernel_med, iterations=1)  # Engrossa bordas
    imagem = cv2.erode(imagem, kernel_small, iterations=1)  # Afina levemente
    imagem = cv2.medianBlur(imagem, 3)  # Suaviza as bordas
    
    return imagem

def detectar_linhas_conectadas(imagem):
    """Função para detectar linhas conectadas usando Hough Lines"""
    edges = cv2.Canny(imagem, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=50,
        minLineLength=50,
        maxLineGap=10
    )
    
    # Criar imagem em branco para desenhar as linhas
    resultado = np.zeros_like(imagem)
    
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(resultado, (x1, y1), (x2, y2), 255, 2)
    
    # Limpar e conectar linhas próximas
    kernel = np.ones((3,3), np.uint8)
    resultado = cv2.dilate(resultado, kernel, iterations=1)
    resultado = cv2.erode(resultado, kernel, iterations=1)
    
    return resultado

def aplicar_filtros(imagem_suavizada):
    # Sobel OpenCV com bordas mais grossas
    sobelx = cv2.Sobel(imagem_suavizada, cv2.CV_64F, 1, 0, ksize=5)  # aumentado ksize
    sobely = cv2.Sobel(imagem_suavizada, cv2.CV_64F, 0, 1, ksize=5)
    bordas_sobel = cv2.magnitude(sobelx, sobely)
    bordas_sobel = np.uint8(255 * (bordas_sobel / bordas_sobel.max()))
    _, bordas_sobel = cv2.threshold(bordas_sobel, 35, 255, cv2.THRESH_BINARY)  # limiar reduzido
    bordas_sobel = cv2.dilate(bordas_sobel, np.ones((3,3), np.uint8), iterations=1)  # dilatar bordas
    bordas_sobel = limpar_ruido(bordas_sobel)
    bordas_sobel = limpar_bordas(bordas_sobel)  # Nova etapa de limpeza
    bordas_sobel = 255 - bordas_sobel

    # Filtros skimage com bordas mais grossas
    bordas_sobel_sk = filters.sobel(imagem_suavizada)
    bordas_sobel_sk = (bordas_sobel_sk > 0.04).astype(np.uint8) * 255  # limiar reduzido
    bordas_sobel_sk = cv2.dilate(bordas_sobel_sk, np.ones((3,3), np.uint8), iterations=1)
    bordas_sobel_sk = limpar_ruido(bordas_sobel_sk)
    bordas_sobel_sk = limpar_bordas(bordas_sobel_sk)  # Nova etapa de limpeza
    bordas_sobel_sk = 255 - bordas_sobel_sk

    bordas_prewitt = filters.prewitt(imagem_suavizada)
    bordas_prewitt = (bordas_prewitt > 0.04).astype(np.uint8) * 255  # limiar reduzido
    bordas_prewitt = cv2.dilate(bordas_prewitt, np.ones((3,3), np.uint8), iterations=1)
    bordas_prewitt = limpar_ruido(bordas_prewitt)
    bordas_prewitt = limpar_bordas(bordas_prewitt)  # Nova etapa de limpeza
    bordas_prewitt = 255 - bordas_prewitt
    
    # Adicionar detecção de linhas conectadas
    linhas_conectadas = detectar_linhas_conectadas(imagem_suavizada)
    linhas_conectadas = limpar_bordas(linhas_conectadas)
    linhas_conectadas = 255 - linhas_conectadas
    
    return bordas_sobel, bordas_sobel_sk, bordas_prewitt, linhas_conectadas

def mostrar_resultados(img_original, img_cinza, titulo, resultados, num_figura):
    plt.figure(num_figura, figsize=(15, 12))
    
    plt.subplot(2, 3, 1)
    if len(img_original.shape) == 3:
        plt.imshow(img_original)
    else:
        plt.imshow(img_original, cmap='gray')
    plt.title(f'Imagem {titulo}')
    plt.axis('off')

    plt.subplot(2, 3, 2)
    plt.imshow(resultados[0], cmap='gray')
    plt.title('Sobel (OpenCV)')
    plt.axis('off')

    plt.subplot(2, 3, 3)
    plt.imshow(resultados[1], cmap='gray')
    plt.title('Sobel (skimage)')
    plt.axis('off')

    plt.subplot(2, 3, 4)
    plt.imshow(resultados[2], cmap='gray')
    plt.title('Prewitt')
    plt.axis('off')

    plt.subplot(2, 3, 5)
    plt.imshow(resultados[3], cmap='gray')
    plt.title('Linhas Conectadas')
    plt.axis('off')

    plt.suptitle(f'Detecção de Bordas - {titulo}')

# Processamento modificado
resultados_original = aplicar_filtros(imagem)
resultados_media = aplicar_filtros(suave_media)
resultados_inter = aplicar_filtros(suave_intermediaria)  # Novo processamento
resultados_pers = aplicar_filtros(suave_personalizada)

# Mostrar resultados modificados
mostrar_resultados(imagem_cor, imagem, "Original", resultados_original, 1)
mostrar_resultados(imagem_cor, suave_media, "Suavização Média (5x5, σ=1.0)", resultados_media, 2)
mostrar_resultados(imagem_cor, suave_intermediaria, "Suavização Intermediária (5x5, σx=1.2, σy=1.0)", resultados_inter, 3)
mostrar_resultados(imagem_cor, suave_personalizada, "Suavização Personalizada (5x5, σx=1.5, σy=0.5)", resultados_pers, 4)

# Mostrar todos os gráficos no final
plt.show()
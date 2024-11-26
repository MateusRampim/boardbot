import asyncio
import websockets.server
import base64
import cv2
import numpy as np
from flask import Flask, request, jsonify
from threading import Thread
import traceback
from flask_cors import CORS

async def handler(websocket):
    print("Cliente conectado")
    try:
        while True:
            await websocket.send("ok")
            await asyncio.sleep(5000)
    except websockets.exceptions.ConnectionClosed:
        print("Cliente desconectado")

app = Flask(__name__)
# Configurar CORS corretamente
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"]
    }
})

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        print("Headers recebidos:", dict(request.headers))
        print("Conteúdo do request.files:", request.files)
        print("Conteúdo do request.form:", request.form)
        
        if 'image' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400

        file = request.files['image']
        if not file:
            return jsonify({'error': 'Arquivo vazio'}), 400

        # Ler os bytes da imagem
        file_bytes = file.read()
        if not file_bytes:
            return jsonify({'error': 'Arquivo sem conteúdo'}), 400

        print(f"Bytes recebidos: {len(file_bytes)}")

        # Adicionar limite de tamanho
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_bytes) > max_size:
            return jsonify({'error': 'Arquivo muito grande'}), 413

        # Continua com o processamento da imagem
        npimg = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'error': 'Falha ao decodificar imagem'}), 400

        # Redimensionar imagens muito grandes
        max_dimension = 1920
        height, width = img.shape[:2]
        if height > max_dimension or width > max_dimension:
            scale = max_dimension / max(height, width)
            img = cv2.resize(img, None, fx=scale, fy=scale)

        # Pré-processamento
        # Converter para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Aplicar blur para reduzir ruídos
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detectar bordas com Canny (ajustando os limiares)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilatar as bordas para ficarem mais espessas
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Remover componentes pequenos (ruídos)
        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Criar máscara em branco
        mask = np.ones_like(edges) * 255
        
        # Desenhar apenas contornos grandes
        for contour in contours:
            if cv2.contourArea(contour) > 100:  # ajuste este valor conforme necessário
                cv2.drawContours(mask, [contour], -1, (0, 0, 0), 2)
        
        # O resto do código permanece igual
        _, buffer = cv2.imencode('.jpg', mask)
        processed_image = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            'processedImage': f'data:image/jpeg;base64,{processed_image}'
        })
    except Exception as e:
        print("Erro detalhado:")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def run_flask():
    # Alterando para aceitar conexões externas
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

async def main():
    # Configurando WebSocket para aceitar conexões externas
    async with websockets.server.serve(
        handler, 
        host="0.0.0.0",  # Aceita conexões de qualquer IP
        port=8777,
        ping_interval=None  # Desativa ping automático
    ):
        print("Servidor WebSocket iniciado em 0.0.0.0:8777")
        await asyncio.Future()

def run_websocket():
    asyncio.run(main())

if __name__ == '__main__':
    # Iniciar WebSocket em uma thread separada
    websocket_thread = Thread(target=run_websocket)
    websocket_thread.daemon = True  # Thread será encerrada quando a principal terminar
    websocket_thread.start()
    
    # Executar Flask na thread principal
    print("Iniciando servidor Flask...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
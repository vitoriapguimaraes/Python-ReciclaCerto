import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')

# Configura as APIs Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
Maps_API_KEY = os.getenv("Maps_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
if not Maps_API_KEY:
    print("Aviso: Maps_API_KEY não encontrada. A funcionalidade de mapas será limitada.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Carrega os dados dos pontos de reciclagem
PONTOS_RECICLAGEM = []
try:
    with open('data/pontos_reciclagem_sp.json', 'r', encoding='utf-8') as f:
        PONTOS_RECICLAGEM = json.load(f)
except FileNotFoundError:
    print("Aviso: arquivo 'pontos_reciclagem_sp.json' não encontrado. A busca por locais não funcionará.")
except json.JSONDecodeError:
    print("Erro: 'pontos_reciclagem_sp.json' contém JSON inválido.")

@app.route('/')
def index():
    return render_template('index.html', Maps_api_key=Maps_API_KEY)

@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    data = request.json
    item = data.get('item')

    if not item:
        return jsonify({"error": "Por favor, forneça um item para verificar."}), 400

    # Prompt mais robusto para o Gemini
    prompt = f"""
    Você é um assistente de reciclagem no Brasil. Sua tarefa é analisar o item fornecido e responder de forma concisa:
    1. Se o item é reciclável ou não no Brasil.
    2. Se reciclável, qual a categoria de material (ex: plástico, papel, metal, vidro, eletrônico, óleo, isopor, etc.).
    3. Uma breve instrução de como prepará-lo para reciclagem (ex: lavar e secar, descartar em ecoponto, etc.).
    4. Se não for reciclável pelo descarte comum, explique por que e sugira o que fazer (lixo comum, programas específicos).

    Responda no formato JSON. Se não souber, diga "Não sei".

    Exemplos de saída JSON:
    - Item: Garrafa PET
      Resposta: {{"reciclavel": true, "material": "plástico", "instrucao": "Lave e seque bem, descarte em ponto de coleta de plástico."}}
    - Item: Isopor
      Resposta: {{"reciclavel": false, "material": "isopor", "instrucao": "Isopor é difícil de reciclar e nem todos os locais aceitam. Verifique pontos de coleta específicos para isopor na sua região ou descarte no lixo comum."}}
    - Item: Bucha de banho (sintética)
      Resposta: {{"reciclavel": false, "material": "higiene pessoal", "instrucao": "Não, bucha de banho sintética não é reciclável. Descarte no lixo comum."}}
    - Item: Óleo de cozinha usado
      Resposta: {{"reciclavel": true, "material": "óleo", "instrucao": "Guarde em garrafas PET limpas e secas. Procure ecopontos ou programas de coleta específicos."}}
    - Item: Escova de dente
      Resposta: {{"reciclavel": false, "material": "higiene pessoal", "instrucao": "A maioria das escovas de dente não é reciclável no lixo comum. Algumas marcas têm programas de reciclagem específicos. Verifique com o fabricante."}}
    - Item: Pneu
      Resposta: {{"reciclavel": true, "material": "borracha", "instrucao": "Pneus são recicláveis em pontos de coleta específicos ou borracharias que participam de programas de descarte. Nunca descarte no lixo comum."}}

    Agora, para o item: {item}
    Resposta:
    """

    try:
        response = model.generate_content(prompt)
        gemini_response_text = response.candidates[0].content.parts[0].text
        
        # Tenta parsear a resposta como JSON
        try:
            gemini_json = json.loads(gemini_response_text)
            return jsonify(gemini_json)
        except json.JSONDecodeError:
            # Se não for JSON, trata como texto simples
            return jsonify({"reciclavel": "desconhecido", "instrucao": gemini_response_text}), 200

    except Exception as e:
        print(f"Erro ao chamar a API Gemini: {e}")
        return jsonify({"error": "Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde."}), 500


@app.route('/find_recycling_points', methods=['POST'])
def find_recycling_points():
    data = request.json
    material = data.get('material')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not material or not latitude or not longitude:
        return jsonify({"error": "Material, latitude e longitude são necessários."}), 400

    # Simples filtro por material e proximidade (distância euclidiana para MVP)
    # Em um projeto real, usaria uma biblioteca de geocodificação/cálculo de distância mais robusta
    pontos_encontrados = []
    for ponto in PONTOS_RECICLAGEM:
        if material.lower() in [m.lower() for m in ponto.get('materiais_aceitos', [])]:
            # Cálculo de distância simples (apenas para MVP)
            # sqrt((x2-x1)^2 + (y2-y1)^2)
            distancia = ((ponto['latitude'] - latitude)**2 + (ponto['longitude'] - longitude)**2)**0.5
            ponto_com_dist = ponto.copy()
            ponto_com_dist['distancia_aprox'] = distancia # km, de forma muito rudimentar
            pontos_encontrados.append(ponto_com_dist)
    
    # Ordena por distância
    pontos_encontrados.sort(key=lambda p: p.get('distancia_aprox', float('inf')))

    return jsonify({"pontos": pontos_encontrados})


if __name__ == '__main__':
    app.run(debug=True)
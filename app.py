import os
import json
import re
import math
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente. Certifique-se de que o arquivo .env está configurado corretamente.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.0-flash')

PONTOS_RECICLAGEM = []
try:
    with open('data/pontos_reciclagem_sp.json', 'r', encoding='utf-8') as f:
        PONTOS_RECICLAGEM = json.load(f)
    print(f"Sucesso ao carregar {len(PONTOS_RECICLAGEM)} pontos de reciclagem.")
except FileNotFoundError:
    print("Aviso: arquivo 'pontos_reciclagem_sp.json' não encontrado. A busca por locais de reciclagem não funcionará.")
    PONTOS_RECICLAGEM = []
except json.JSONDecodeError:
    print("Erro: 'pontos_reciclagem_sp.json' contém JSON inválido. Verifique a sintaxe do arquivo JSON.")
    PONTOS_RECICLAGEM = []

@app.route('/')
def index() -> str:
    return render_template('index.html')

def normalize_string(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = (text.replace("á", "a").replace("ã", "a").replace("â", "a")
                .replace("é", "e").replace("ê", "e").replace("í", "i")
                .replace("ó", "o").replace("ô", "o").replace("õ", "o")
                .replace("ú", "u").replace("ç", "c"))
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) * math.sin(d_lat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(d_lon / 2) * math.sin(d_lon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

@app.route('/ask_gemini', methods=['POST'])
def ask_gemini() -> json:
    data = request.json
    item = data.get('item')

    if not item:
        return jsonify({"error": "Por favor, forneça um item para verificar."}), 400

    prompt = f"""
    Você é um assistente de reciclagem no Brasil. Sua tarefa é analisar o item fornecido e responder de forma concisa:
    1. Se o item é reciclável ou não no Brasil.
    2. Se reciclável, qual a categoria de material (ex: plástico, papel, metal, vidro, eletrônico, óleo, isopor, orgânico, etc.). Forneça uma categoria genérica e comum no Brasil.
    3. Uma breve instrução de como prepará-lo para reciclagem (ex: lavar e secar, remover rótulos, descartar em ecoponto, etc.). Seja específico.
    4. Se não for reciclável pelo descarte comum, explique por que e sugira o que fazer (lixo comum, programas específicos).
    5. Se for um material muito específico ou que requer descarte especial (ex: medicamentos, lixo hospitalar, pilhas, óleo de cozinha, eletrônicos), adicione a instrução de "Procurar pontos de coleta específicos ou ecopontos".
    Responda EXCLUSIVAMENTE no formato JSON, sem nenhum texto adicional antes ou depois. Se não souber, diga "Não sei" e "reciclavel": "desconhecido".
    Exemplos de saída JSON:
    - Item: Garrafa PET
      Resposta: {{"reciclavel": true, "material": "plástico", "instrucao": "Lave e seque bem, amasse para ocupar menos espaço. Descarte em pontos de coleta de plástico ou lixeiras para recicláveis."}}
    - Item: Isopor
      Resposta: {{"reciclavel": true, "material": "isopor", "instrucao": "Nem todos os locais aceitam isopor. Se possível, quebre em pedaços menores. Procure pontos de coleta específicos para isopor na sua região, pois não é comum na coleta seletiva porta a porta."}}
    - Item: Bucha de banho (sintética)
      Resposta: {{"reciclavel": false, "material": "higiene pessoal", "instrucao": "Não, bucha de banho sintética não é reciclável no descarte comum. Descarte no lixo comum ou em programas de descarte de difícil reciclagem se houver."}}
    - Item: Óleo de cozinha usado
      Resposta: {{"reciclavel": true, "material": "óleo", "instrucao": "Não descarte no ralo! Guarde em garrafas PET limpas e secas. Procure ecopontos ou programas de coleta de óleo específicos na sua cidade."}}
    - Item: Escova de dente
      Resposta: {{"reciclavel": false, "material": "higiene pessoal", "instrucao": "A maioria das escovas de dente não é reciclável no lixo comum devido à mistura de materiais. Algumas marcas têm programas de reciclagem específicos. Verifique com o fabricante."}}
    - Item: Pneu
      Resposta: {{"reciclavel": true, "material": "borracha", "instrucao": "Pneus são recicláveis em pontos de coleta específicos ou borracharias que participam de programas de descarte. Nunca descarte no lixo comum. Podem ser usados para asfalto, quadras e outros produtos."}}
    - Item: Bateria de celular
      Resposta: {{"reciclavel": true, "material": "eletrônico", "instrucao": "Baterias de celular contêm metais pesados e não devem ser descartadas no lixo comum. Leve a pontos de coleta específicos para eletrônicos, lojas de eletrônicos ou ecopontos."}}
    - Item: Papel de pão engordurado
      Resposta: {{"reciclavel": false, "material": "papel", "instrucao": "Papéis com gordura ou restos de alimentos não são recicláveis, pois contaminam o processo. Descarte no lixo comum."}}
    Agora, para o item: {item}
    Resposta:
    """

    try:
        response = model.generate_content(prompt)
        gemini_response_text = ""
        if response.candidates and hasattr(response.candidates[0], 'content') and \
           hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts:
            gemini_response_text = response.candidates[0].content.parts[0].text
        json_start = gemini_response_text.find('{')
        json_end = gemini_response_text.rfind('}')
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_string = gemini_response_text[json_start : json_end + 1]
            try:
                gemini_json = json.loads(json_string)
            except json.JSONDecodeError:
                print(f"Erro ao parsear JSON do Gemini. String JSON: {json_string}")
                return jsonify({
                    "error": "Formato de resposta inesperado do Gemini. Tente novamente mais tarde.",
                    "raw_gemini_response": gemini_response_text
                }), 500
        else:
            print(f"Resposta do Gemini não contém JSON válido: {gemini_response_text}")
            return jsonify({
                "error": "Resposta do Gemini não contém formato JSON esperado.",
                "raw_gemini_response": gemini_response_text
            }), 500

        material_gemini = gemini_json.get("material", "").lower()
        locais_encontrados = []
        
        if material_gemini:
            for ponto in PONTOS_RECICLAGEM:
                materiais_aceitos_norm = [normalize_string(m) for m in ponto.get('materiais_aceitos', [])]
                if normalize_string(material_gemini) in materiais_aceitos_norm:
                    locais_encontrados.append(ponto)

        resultado = {
            "mensagem1": "",
            "mensagem2": "",
            "mensagem3": "",
            "status": "desconhecido",
            "gemini_raw": gemini_json,
            "locais": locais_encontrados
        }

        if gemini_json.get("reciclavel") is True and locais_encontrados:
            resultado["mensagem1"] = f"Há cooperativas que recolhem {item.lower()}, confira a mais perto de você."
            resultado["mensagem2"] = "Esse material é reciclável."
            resultado["mensagem3"] = f"Instruções para reciclar: {gemini_json.get('instrucao', 'N/A')}"
            resultado["status"] = "tem_local"
        elif gemini_json.get("reciclavel") is True and not locais_encontrados:
            resultado["mensagem1"] = f"Esse material é reciclável, mas não temos informações de locais que reciclam {item.lower()} na nossa base de dados."
            resultado["mensagem2"] = "Dicas do Gemini para você:"
            resultado["mensagem3"] = gemini_json.get('instrucao', 'N/A')
            resultado["status"] = "reciclavel_sem_local"
        elif gemini_json.get("reciclavel") is False:
            resultado["mensagem1"] = f"{item.capitalize()} NÃO é reciclável. É considerado um resíduo comum."
            resultado["mensagem2"] = "Orientação do Gemini para você:"
            resultado["mensagem3"] = gemini_json.get('instrucao', 'N/A')
            resultado["status"] = "nao_reciclavel"
        else:
            resultado["mensagem1"] = f"Não foi possível determinar para {item.lower()}. Tente novamente com outra descrição."
            resultado["mensagem2"] = "Verifique a informação ou tente novamente."
            resultado["status"] = "desconhecido"

        return jsonify(resultado)

    except Exception as e:
        print(f"Erro inesperado ao processar solicitação '/ask_gemini': {e}", exc_info=True)
        return jsonify({
            "error": f"Ocorreu um erro interno ao verificar o item. Por favor, tente novamente mais tarde. Detalhes: {str(e)}"
        }), 500

@app.route('/find_recycling_points', methods=['POST'])
def find_recycling_points() -> json:
    data = request.json
    material_from_frontend = data.get('material')
    user_latitude = data.get('latitude')
    user_longitude = data.get('longitude')

    if not material_from_frontend or user_latitude is None or user_longitude is None:
        return jsonify({"error": "Material, latitude e longitude são necessários para buscar pontos."}), 400

    pontos_filtrados_e_ordenados = []
    normalized_material_frontend = normalize_string(material_from_frontend)

    for ponto in PONTOS_RECICLAGEM:
        materiais_aceitos_norm = [normalize_string(m) for m in ponto.get('materiais_aceitos', [])]
        if normalized_material_frontend in materiais_aceitos_norm:
            ponto_latitude = ponto.get('latitude')
            ponto_longitude = ponto.get('longitude')
            if ponto_latitude is not None and ponto_longitude is not None:
                distancia_km = calculate_distance(user_latitude, user_longitude, 
                                                  ponto_latitude, ponto_longitude)
                ponto_com_dist = ponto.copy()
                ponto_com_dist['distancia_km'] = round(distancia_km, 2)
                pontos_filtrados_e_ordenados.append(ponto_com_dist)

    pontos_filtrados_e_ordenados.sort(key=lambda p: p.get('distancia_km', float('inf')))

    return jsonify({"pontos": pontos_filtrados_e_ordenados})

if __name__ == '__main__':
    app.run(debug=True)
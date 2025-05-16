import os
import json
import re
import math # Importa o módulo math para cálculos matemáticos

import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__, static_folder='static')

# --- Configuração da API Gemini ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente. "
                     "Certifique-se de que o arquivo .env está configurado corretamente.")

genai.configure(api_key=GEMINI_API_KEY)
# Utiliza o modelo Gemini 2.0 Flash para respostas mais rápidas
model = genai.GenerativeModel('models/gemini-2.0-flash')

# --- Carregamento dos Dados de Pontos de Reciclagem ---
PONTOS_RECICLAGEM = []
try:
    with open('data/pontos_reciclagem_sp.json', 'r', encoding='utf-8') as f:
        PONTOS_RECICLAGEM = json.load(f)
    print(f"Sucesso ao carregar {len(PONTOS_RECICLAGEM)} pontos de reciclagem.")
except FileNotFoundError:
    print("Aviso: arquivo 'pontos_reciclagem_sp.json' não encontrado. "
          "A busca por locais de reciclagem não funcionará.")
    PONTOS_RECICLAGEM = []
except json.JSONDecodeError:
    print("Erro: 'pontos_reciclagem_sp.json' contém JSON inválido. "
          "Verifique a sintaxe do arquivo JSON.")
    PONTOS_RECICLAGEM = [] # Garante que a lista esteja vazia em caso de erro

# --- Rotas da Aplicação ---

@app.route('/')
def index() -> str:
    """Renderiza a página principal da aplicação."""
    return render_template('index.html')

def normalize_string(text: str) -> str:
    """
    Normaliza uma string removendo acentos e caracteres especiais,
    e convertendo para minúsculas.
    Útil para comparações case-insensitive e sem acentos.
    """
    if not text:
        return ""
    # Transforma para minúsculas
    text = text.lower()
    # Remove acentos
    text = (text.replace("á", "a").replace("ã", "a").replace("â", "a")
                .replace("é", "e").replace("ê", "e").replace("í", "i")
                .replace("ó", "o").replace("ô", "o").replace("õ", "o")
                .replace("ú", "u").replace("ç", "c"))
    # Remove caracteres não alfanuméricos (mantém apenas letras, números e espaços)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula a distância aproximada entre dois pontos de coordenadas (latitude, longitude) em quilômetros.
    Usa a fórmula de Haversine simplificada para pequenas distâncias.
    Para precisão exata em longas distâncias, uma biblioteca geográfica seria ideal.
    """
    R = 6371 # Raio da Terra em quilômetros

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
    """
    Endpoint para consultar o modelo Gemini sobre a reciclagem de um item.
    Retorna informações sobre se o item é reciclável, seu material e instruções.
    """
    data = request.json
    item = data.get('item')

    if not item:
        return jsonify({"error": "Por favor, forneça um item para verificar."}), 400

    # O prompt instrui o Gemini a responder EXCLUSIVAMENTE em formato JSON.
    # Inclui exemplos para guiar a resposta.
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
        # Extrai o texto da resposta do Gemini de forma segura
        if response.candidates and hasattr(response.candidates[0], 'content') and \
           hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts:
            gemini_response_text = response.candidates[0].content.parts[0].text

        # Tenta encontrar e extrair o JSON da string bruta da resposta do Gemini.
        # Isso lida com casos onde o Gemini pode adicionar texto extra (ex: ```json\n{...}\n```).
        json_start = gemini_response_text.find('{')
        json_end = gemini_response_text.rfind('}')
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_string = gemini_response_text[json_start : json_end + 1]
            try:
                gemini_json = json.loads(json_string)
            except json.JSONDecodeError:
                # Se o JSON encontrado ainda for inválido, registra o erro e retorna.
                print(f"Erro ao parsear JSON do Gemini. String JSON: {json_string}")
                return jsonify({
                    "error": "Formato de resposta inesperado do Gemini. Tente novamente mais tarde.",
                    "raw_gemini_response": gemini_response_text
                }), 500
        else:
            # Se nenhum JSON válido for encontrado na resposta do Gemini, registra e retorna.
            print(f"Resposta do Gemini não contém JSON válido: {gemini_response_text}")
            return jsonify({
                "error": "Resposta do Gemini não contém formato JSON esperado.",
                "raw_gemini_response": gemini_response_text
            }), 500

        # --- Lógica de Busca e Resposta Customizada ---
        material_gemini = gemini_json.get("material", "").lower()
        locais_encontrados = []
        
        if material_gemini: # Só busca locais se o Gemini identificar um material
            for ponto in PONTOS_RECICLAGEM:
                # Normaliza os materiais aceitos pelo ponto para comparação
                materiais_aceitos_norm = [normalize_string(m) for m in ponto.get('materiais_aceitos', [])]
                if normalize_string(material_gemini) in materiais_aceitos_norm:
                    locais_encontrados.append(ponto)

        resultado = {
            "mensagem1": "", # Mensagem sobre cooperativas/locais
            "mensagem2": "", # Mensagem principal de reciclagem
            "mensagem3": "", # Instruções de preparo
            "status": "desconhecido", # Status para o frontend (tem_local, reciclavel_sem_local, nao_reciclavel, desconhecido)
            "gemini_raw": gemini_json, # Dados brutos do Gemini para debug/uso no frontend
            "locais": locais_encontrados # Lista de locais encontrados
        }

        # Condição 1: Item é reciclável E há locais na base de dados
        if gemini_json.get("reciclavel") is True and locais_encontrados:
            resultado["mensagem1"] = f"Há cooperativas que recolhem {item.lower()}, confira a mais perto de você."
            resultado["mensagem2"] = "Esse material é reciclável."
            resultado["mensagem3"] = f"Instruções para reciclar: {gemini_json.get('instrucao', 'N/A')}"
            resultado["status"] = "tem_local"

        # Condição 2: Item é reciclável, mas NÃO há locais na base de dados
        elif gemini_json.get("reciclavel") is True and not locais_encontrados:
            resultado["mensagem1"] = f"Esse material é reciclável, mas não temos informações de locais que reciclam {item.lower()} na nossa base de dados."
            resultado["mensagem2"] = "Dicas do Gemini para você:"
            resultado["mensagem3"] = gemini_json.get('instrucao', 'N/A')
            resultado["status"] = "reciclavel_sem_local"

        # Condição 3: Item NÃO é reciclável
        elif gemini_json.get("reciclavel") is False:
            resultado["mensagem1"] = f"{item.capitalize()} NÃO é reciclável. É considerado um resíduo comum."
            resultado["mensagem2"] = "Orientação do Gemini para você:"
            resultado["mensagem3"] = gemini_json.get('instrucao', 'N/A')
            resultado["status"] = "nao_reciclavel"

        # Condição 4: Gemini não soube determinar a reciclabilidade
        else:
            resultado["mensagem1"] = f"Não foi possível determinar para {item.lower()}. Tente novamente com outra descrição."
            resultado["mensagem2"] = "Verifique a informação ou tente novamente."
            # resultado["mensagem3"] permanece vazio
            resultado["status"] = "desconhecido"

        return jsonify(resultado)

    except Exception as e:
        # Captura e loga quaisquer outros erros inesperados no processo
        print(f"Erro inesperado ao processar solicitação '/ask_gemini': {e}", exc_info=True)
        return jsonify({
            "error": f"Ocorreu um erro interno ao verificar o item. Por favor, tente novamente mais tarde. Detalhes: {str(e)}"
        }), 500

@app.route('/find_recycling_points', methods=['POST'])
def find_recycling_points() -> json:
    """
    Endpoint para buscar pontos de reciclagem com base no material e coordenadas.
    Retorna uma lista de pontos de coleta próximos que aceitam o material especificado,
    ordenados pela distância.
    """
    data = request.json
    material_from_frontend = data.get('material')
    user_latitude = data.get('latitude')
    user_longitude = data.get('longitude')

    if not material_from_frontend or user_latitude is None or user_longitude is None:
        return jsonify({"error": "Material, latitude e longitude são necessários para buscar pontos."}), 400

    pontos_filtrados_e_ordenados = []
    normalized_material_frontend = normalize_string(material_from_frontend)

    for ponto in PONTOS_RECICLAGEM:
        # Normaliza a lista de materiais aceitos por cada ponto para comparação
        materiais_aceitos_norm = [normalize_string(m) for m in ponto.get('materiais_aceitos', [])]

        if normalized_material_frontend in materiais_aceitos_norm:
            ponto_latitude = ponto.get('latitude')
            ponto_longitude = ponto.get('longitude')

            if ponto_latitude is not None and ponto_longitude is not None:
                # Calcula a distância em km usando a função auxiliar
                distancia_km = calculate_distance(user_latitude, user_longitude, 
                                                  ponto_latitude, ponto_longitude)
                
                ponto_com_dist = ponto.copy()
                ponto_com_dist['distancia_km'] = round(distancia_km, 2) # Arredonda para 2 casas decimais
                pontos_filtrados_e_ordenados.append(ponto_com_dist)

    # Ordena os pontos pela distância calculada em km
    pontos_filtrados_e_ordenados.sort(key=lambda p: p.get('distancia_km', float('inf')))

    return jsonify({"pontos": pontos_filtrados_e_ordenados})

# --- Execução da Aplicação ---
if __name__ == '__main__':
    # 'debug=True' é útil para desenvolvimento (recarga automática, mensagens de erro detalhadas)
    # Mas deve ser False em produção por motivos de segurança e performance.
    app.run(debug=True)
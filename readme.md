# ReciclaCerto

> Aplicação web que simplifica a reciclagem no dia a dia, conectando o usuário a informações essenciais sobre descarte correto de resíduos e pontos de coleta próximos, utilizando Inteligência Artificial e mapas interativos.

<a href="https://projetoreciclacerto.onrender.com/"><img src="https://img.shields.io/badge/-ReciclaCerto-228B22?style=for-the-badge" alt="ReciclaCerto"></a>

![Demonstração do sistema](https://github.com/vitoriapguimaraes/projetoReciclaCerto/blob/main/results/display.gif)

## Funcionalidades Principais

- Consulta de itens: Descubra se um material é reciclável e como descartá-lo corretamente, com auxílio de IA (Google Gemini API).
- Busca de pontos de coleta: Encontre locais próximos que aceitam o material informado, com visualização em mapa (OpenStreetMap + Leaflet.js).
- Formulário de cadastro de associações (esqueleto): Indica futuras funcionalidades para cooperativas e associações de reciclagem.

## Tecnologias Utilizadas

- Python
- Flask
- Google Gemini API
- python-dotenv
- HTML5, CSS3, JavaScript
- Leaflet.js
- OpenStreetMap (OSM)
- Nominatim

## Como Executar

1. Clone o repositório:
2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv
   # No Windows:
   .\venv\Scripts\activate
   # No Linux/macOS:
   source venv/bin/activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure o arquivo `.env` na raiz do projeto com sua chave Gemini:

   ```env
   GEMINI_API_KEY="SUA_CHAVE_API_DO_GEMINI_AQUI"
   ```

5. Execute o aplicativo Flask:

   ```bash
   python app.py
   ```

6. Acesse no navegador: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Como Usar

- Digite o nome de um item (ex: "garrafa PET", "isopor") para saber se é reciclável e como descartar.
- Para itens recicláveis, informe sua localização para visualizar pontos de coleta próximos no mapa.
- Utilize o formulário de cadastro para simular o registro de uma associação (funcionalidade em desenvolvimento).

## Estrutura de Diretórios

```
projetoReciclaCerto/
├── .env                            # Variáveis de ambiente (API Keys)
├── app.py                          # Backend Flask
├── static/
│   ├── style.css                   # Estilização CSS
│   └── script.js                   # Lógica JavaScript do frontend
├── templates/
│   └── index.html                  # Página web principal
├── data/
│   └── pontos_reciclagem_sp.json   # Base de dados inicial (mock) de pontos de coleta para SP
├── requirements.txt                # Dependências do projeto
├── results/                        # Prints e gifs do sistema
└── README.md                       # Documentação do projeto
```

## Status

✅ Concluído

> Veja as [issues abertas](https://github.com/vitoriapguimaraes/projetoReciclaCerto/issues) para sugestões de melhorias e próximos passos.

## Mais Sobre Mim

Acesse os arquivos disponíveis na [Pasta Documentos](https://github.com/vitoriapguimaraes/vitoriapguimaraes/tree/main/DOCUMENTOS) para mais informações sobre minhas qualificações e certificações.

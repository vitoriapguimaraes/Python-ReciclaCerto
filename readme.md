# ReciclaCerto: Seu Guia Rápido para uma Reciclagem Consciente

> Uma aplicação web que simplifica a reciclagem no dia a dia, conectando o usuário a informações essenciais sobre descarte correto de resíduos e pontos de coleta próximos, utilizando Inteligência Artificial e mapas interativos.

A iniciativa ReciclaCerto nasceu da necessidade de tornar a reciclagem mais acessível e prática. Muitas pessoas não sabem exatamente o que pode ser reciclado ou onde descartar corretamente cada material. O ReciclaCerto resolve esse problema ao informar, de forma rápida e intuitiva, se um item é reciclável e onde descartá-lo, promovendo impacto positivo no meio ambiente.

<a href="https://projetoreciclacerto.onrender.com/"><img src="https://img.shields.io/badge/-ReciclaCerto-228B22?style=for-the-badge" alt="ReciclaCerto"></a>

Durante a Imersão IA da Alura, encarei o desafio de desenvolver este projeto em tempo limitado. Para isso, explorei o poder da inteligência artificial, que me ajudou a estruturar o site, permitindo-me focar nas implementações futuras. Compartilho aqui a 'versão zero' desse trabalho, que serve como uma reflexão sobre como a IA pode simplificar e acelerar até as tarefas mais banais, abrindo um universo de possibilidades onde apenas nossa criatividade pode nos deter.

![Tela do sistema](https://github.com/vitoriapguimaraes/projetoReciclaCerto/blob/main/results/display.gif)

### Versão 'zero'
![Tela do sistema](https://github.com/vitoriapguimaraes/projetoReciclaCerto/blob/main/results/display-v1.gif)

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

   ```bash
   git clone https://github.com/seu-usuario/reciclacerto.git
   cd reciclacerto
   ```

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

🚧 Em desenvolvimento

> Melhorias planejadas:
> - Design responsivo para mobile
> - Integração avançada de mapas (rotas, detalhes dos pontos)
> - Banco de dados persistente para cooperativas e ecopontos
> - Cadastro e gerenciamento de associações/cooperativas
> - Parcerias com organizações nacionais de reciclagem

## Mais sobre mim

Acesse os arquivos disponíveis na [Pasta Documentos](https://github.com/vitoriapguimaraes/vitoriapguimaraes/tree/main/DOCUMENTOS) para mais informações sobre minhas qualificações e certificações.

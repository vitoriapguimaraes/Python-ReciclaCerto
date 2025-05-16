let currentMaterial = null; // Guarda o material retornado pelo Gemini (ex: "plástico")
let currentItem = null; // Guarda o último item pesquisado pelo usuário (ex: "Garrafa PET")
// Indica se há locais disponíveis no JSON para o material atual
// (determinado pelo backend)
let currentLocalsAvailable = false;

/**
 * Função assíncrona para verificar um item com o modelo Gemini.
 * Exibe as informações de reciclagem e atualiza o estado da aplicação.
 */
async function verificarItem() {
  const itemInput = document.getElementById("itemInput");
  const geminiResultDiv = document.getElementById("geminiResult");
  // Sempre esconde o resultado antes de processar
  geminiResultDiv.style.display = "none";
  const item = itemInput.value.trim();

  if (!item) {
    geminiResultDiv.innerHTML =
      '<div class="result-box error">Por favor, digite um item.</div>';
    geminiResultDiv.style.display = "block";
    return;
  }

  geminiResultDiv.innerHTML =
    '<div class="result-box loading">Verificando com o Gemini...</div>';
  geminiResultDiv.style.display = "block";

  // Reseta estados para uma nova busca
  currentMaterial = null;
  currentItem = item;
  currentLocalsAvailable = false;

  // Limpa resultados de localização anteriores
  document.getElementById("locationResult").innerHTML = "";

  try {
    const response = await fetch("/ask_gemini", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ item: item }),
    });

    const data = await response.json();

    if (response.ok) {
      let htmlContent = "";
      // Usa as mensagens personalizadas do backend para preencher as "boxes"
      if (data.mensagem2) {
        // Mensagem principal de reciclagem
        htmlContent += `<div class="result-box-reciclavel">${data.mensagem2}</div>`;
      }
      if (data.mensagem1) {
        // Mensagem sobre cooperativas/locais
        htmlContent += `<div class="result-box-coleta">${data.mensagem1}</div>`;
      }
      if (data.mensagem3) {
        // Instruções de preparo
        htmlContent += `<div class="result-box-instrucao">${data.mensagem3}</div>`;
      }

      geminiResultDiv.innerHTML = htmlContent;
      geminiResultDiv.style.display = "block";

      // Atualiza variáveis globais com base na resposta do backend
      currentMaterial = data.gemini_raw?.material || item; // Pega o material ou o item original
      currentLocalsAvailable = data.status === "tem_local"; // True se o backend indicou locais
    } else {
      // Tratamento de erro quando a resposta do servidor não é ok (e.g., 500 INTERNAL SERVER ERROR)
      geminiResultDiv.innerHTML = `<div class="result-box error">Erro: ${
        data.error || "Ocorreu um erro desconhecido."
      }</div>`;
      geminiResultDiv.style.display = "block";
    }
  } catch (error) {
    // Tratamento de erro de rede ou falha na requisição
    console.error("Erro na requisição Gemini:", error);
    geminiResultDiv.innerHTML =
      '<div class="result-box error">Não foi possível conectar ao servidor. Verifique sua conexão ou tente novamente.</div>';
    geminiResultDiv.style.display = "block";
  }
}

/**
 * Função assíncrona para buscar pontos de coleta próximos.
 * Pode usar a geolocalização do navegador ou um endereço digitado.
 * @param {boolean} useAddressInput - Se true, usa o valor do input de endereço; caso contrário, usa a geolocalização.
 */
async function buscarLocalizacao(useAddressInput = false) {
  const locationInput = document.getElementById("locationInput");
  const locationResultDiv = document.getElementById("locationResult");

  // Sempre esconde o resultado antes de processar
  locationResultDiv.style.display = "none";

  // Verifica se há material ou item para buscar
  if (!currentMaterial && !currentItem) {
    locationResultDiv.innerHTML =
      '<div class="result-box error">Primeiro, verifique um item para saber o tipo de material!</div>';
    locationResultDiv.style.display = "block";
    return;
  }

  // Se o backend informou que não há locais específicos para este material,
  // exibe a mensagem apropriada e não tenta buscar locais.
  if (!currentLocalsAvailable) {
    locationResultDiv.innerHTML = `<div class="result-box info">Não temos cooperativas cadastradas que aceitam <span class="material-info">${
      currentItem || currentMaterial
    }</span> na nossa base de dados.</div>`;
    locationResultDiv.style.display = "block";
    return;
  }

  locationResultDiv.innerHTML =
    '<div class="result-box loading">Buscando pontos de coleta...</div>';
  locationResultDiv.style.display = "block";

  let latitude, longitude;
  let userLocationFound = false;

  if (useAddressInput) {
    const address = locationInput.value.trim();
    if (!address) {
      locationResultDiv.innerHTML =
        '<div class="result-box error">Por favor, digite um endereço para buscar.</div>';
      return;
    }
    try {
      const geocodingResponse = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
          address
        )}&limit=1`
      );
      const geocodingData = await geocodingResponse.json();

      if (geocodingData && geocodingData.length > 0) {
        latitude = parseFloat(geocodingData[0].lat);
        longitude = parseFloat(geocodingData[0].lon);
        userLocationFound = true;
      } else {
        locationResultDiv.innerHTML =
          '<div class="result-box error">Endereço não encontrado. Tente novamente.</div>';
        return;
      }
    } catch (error) {
      console.error("Erro na geocodificação com Nominatim:", error);
      locationResultDiv.innerHTML =
        '<div class="result-box error">Erro ao obter coordenadas do endereço. (Limite de Nominatim atingido?)</div>';
      return;
    }
  } else {
    if (navigator.geolocation) {
      try {
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 5000,
            maximumAge: 0,
          });
        });
        latitude = position.coords.latitude;
        longitude = position.coords.longitude;
        userLocationFound = true;
      } catch (error) {
        console.error("Erro ao obter localização atual:", error);
        locationResultDiv.innerHTML =
          '<div class="result-box error">Não foi possível obter sua localização atual. Digite um endereço ou verifique as permissões do navegador.</div>';
        return;
      }
    } else {
      locationResultDiv.innerHTML =
        '<div class="result-box error">Geolocalização não é suportada pelo seu navegador. Por favor, digite um endereço.</div>';
      return;
    }
  }

  if (!userLocationFound) {
    locationResultDiv.innerHTML =
      '<div class="result-box error">Não foi possível determinar sua localização para buscar pontos de coleta.</div>';
    return;
  }

  try {
    const response = await fetch("/find_recycling_points", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        material: currentMaterial,
        latitude: latitude,
        longitude: longitude,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      if (data.pontos && data.pontos.length > 0) {
        let listHtml =
          `<div class="result-box"><b>Pontos de coleta próximos que aceitam <span class="material-info">${
            currentMaterial || currentItem
          }</span>:</b></div>` + '<ul class="location-list">';

        // Exibe os pontos de coleta encontrados
        data.pontos.forEach((ponto) => {
          // Adiciona a distância se ela existir no objeto do ponto
          const distancia = ponto.distancia_km
            ? ` (${ponto.distancia_km} km)`
            : "";
          listHtml += `<li>
                                    <span>${ponto.nome}${distancia}</span>
                                    <p>${ponto.endereco}</p>
                                    <a href="https://www.openstreetmap.org/directions?engine=osrm_car&route=${latitude}%2C${longitude}%3B${ponto.latitude}%2C${ponto.longitude}" target="_blank">Rotas no OSM</a>
                                </li>`;
        });
        listHtml += "</ul>";
        locationResultDiv.innerHTML = listHtml;
        locationResultDiv.style.display = "block";
      } else {
        locationResultDiv.innerHTML = `<div class="result-box info">Nenhum ponto de coleta encontrado para <span class="material-info">${
          currentMaterial || currentItem
        }</span> na sua região em nossa base de dados.</div>`;
        locationResultDiv.style.display = "block";
      }
    } else {
      locationResultDiv.innerHTML = `<div class="result-box error">Erro ao buscar pontos: ${
        data.error || "Ocorreu um erro desconhecido."
      }</div>`;
      locationResultDiv.style.display = "block";
    }
  } catch (error) {
    console.error("Erro na requisição de pontos de coleta:", error);
    locationResultDiv.innerHTML =
      '<div class="result-box error">Não foi possível conectar ao servidor para buscar pontos de coleta.</div>';
    locationResultDiv.style.display = "block";
  }
}

// Event Listener para o formulário de associação (funcionalidade em desenvolvimento)
document
  .getElementById("associationForm")
  .addEventListener("submit", function (event) {
    event.preventDefault(); // Impede o envio padrão do formulário
    alert(
      "Obrigado! A funcionalidade de cadastro de associações está em desenvolvimento. Seus dados não foram enviados. Continue acompanhando!"
    );
    this.reset(); // Limpa o formulário
  });

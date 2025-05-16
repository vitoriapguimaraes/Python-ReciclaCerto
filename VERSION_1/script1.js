// static/script.js
let map; // Variável global para o mapa do Google Maps
let currentMaterial = null; // Para guardar o material retornado pelo Gemini

function initMap() {
  // Inicializa o mapa centralizado em São Paulo (ou outra cidade padrão)
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: -23.55052, lng: -46.633309 }, // Centro de SP
    zoom: 10,
  });
}

async function verificarItem() {
  const itemInput = document.getElementById("itemInput");
  const geminiResultDiv = document.getElementById("geminiResult");
  const item = itemInput.value.trim();

  if (!item) {
    geminiResultDiv.innerHTML =
      '<span class="error">Por favor, digite um item.</span>';
    return;
  }

  geminiResultDiv.innerHTML =
    '<span class="loading">Verificando com o Gemini...</span>';
  currentMaterial = null; // Reseta o material ao verificar um novo item

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
      if (data.reciclavel === true) {
        htmlContent = `<p><span class="material-info">Sim, ${item} é reciclável!</span></p>`;
        htmlContent += `<p>Material: <strong>${data.material}</strong></p>`;
        htmlContent += `<p class="instrucao">Instruções: ${data.instrucao}</p>`;
        currentMaterial = data.material; // Guarda o material para a busca de locais
      } else if (data.reciclavel === false) {
        htmlContent = `<p><span class="error">Não, ${item} geralmente NÃO é reciclável no descarte comum.</span></p>`;
        htmlContent += `<p class="instrucao">${data.instrucao}</p>`;
      } else {
        // "desconhecido" ou formato inesperado
        htmlContent = `<p>Não foi possível determinar para ${item}.</p>`;
        htmlContent += `<p class="instrucao">${
          data.instrucao || "Tente novamente com outra descrição."
        }</p>`;
      }
      geminiResultDiv.innerHTML = htmlContent;
    } else {
      geminiResultDiv.innerHTML = `<span class="error">Erro: ${
        data.error || "Ocorreu um erro desconhecido."
      }</span>`;
    }
  } catch (error) {
    console.error("Erro na requisição Gemini:", error);
    geminiResultDiv.innerHTML =
      '<span class="error">Não foi possível conectar ao servidor. Verifique sua conexão ou tente novamente.</span>';
  }
}

async function buscarLocalizacao(useAddressInput = false) {
  const locationInput = document.getElementById("locationInput");
  const locationResultDiv = document.getElementById("locationResult");
  const mapDiv = document.getElementById("map");

  if (!currentMaterial) {
    locationResultDiv.innerHTML =
      '<span class="error">Primeiro, verifique um item para saber o tipo de material!</span>';
    return;
  }

  locationResultDiv.innerHTML =
    '<span class="loading">Buscando pontos de coleta...</span>';
  mapDiv.style.display = "none"; // Esconde o mapa enquanto busca

  let latitude, longitude;

  if (useAddressInput) {
    const address = locationInput.value.trim();
    if (!address) {
      locationResultDiv.innerHTML =
        '<span class="error">Por favor, digite um endereço para buscar.</span>';
      return;
    }
    // Usar a API do Google Maps Geocoding para converter endereço em lat/lng
    try {
      const geocoder = new google.maps.Geocoder();
      const response = await geocoder.geocode({ address: address });
      if (response.results && response.results.length > 0) {
        latitude = response.results[0].geometry.location.lat();
        longitude = response.results[0].geometry.location.lng();
      } else {
        locationResultDiv.innerHTML =
          '<span class="error">Endereço não encontrado. Tente novamente.</span>';
        return;
      }
    } catch (error) {
      console.error("Erro na geocodificação:", error);
      locationResultDiv.innerHTML =
        '<span class="error">Erro ao obter coordenadas do endereço.</span>';
      return;
    }
  } else {
    // Tentar obter a localização atual do navegador
    if (navigator.geolocation) {
      try {
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject);
        });
        latitude = position.coords.latitude;
        longitude = position.coords.longitude;
      } catch (error) {
        console.error("Erro ao obter localização atual:", error);
        locationResultDiv.innerHTML =
          '<span class="error">Não foi possível obter sua localização atual. Digite um endereço ou verifique as permissões do navegador.</span>';
        return;
      }
    } else {
      locationResultDiv.innerHTML =
        '<span class="error">Geolocalização não é suportada pelo seu navegador. Por favor, digite um endereço.</span>';
      return;
    }
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
          "<p>Pontos de coleta próximos que aceitam " +
          currentMaterial +
          ':</p><ul class="location-list">';
        data.pontos.forEach((ponto) => {
          listHtml += `<li>
                        <span>${ponto.nome}</span>
                        <p>${ponto.endereco}</p>
                        <a href="https://www.google.com/maps/search/?api=1&query=${ponto.latitude},${ponto.longitude}" target="_blank">Ver no Mapa</a>
                    </li>`;
        });
        listHtml += "</ul>";
        locationResultDiv.innerHTML = listHtml;

        // Atualiza o mapa
        mapDiv.style.display = "block";
        map.setCenter({ lat: latitude, lng: longitude });
        map.setZoom(12); // Ajusta o zoom para a área do usuário

        // Adiciona marcadores para os pontos encontrados
        data.pontos.forEach((ponto) => {
          new google.maps.Marker({
            position: { lat: ponto.latitude, lng: ponto.longitude },
            map: map,
            title: ponto.nome,
          });
        });
      } else {
        locationResultDiv.innerHTML =
          '<span class="info">Nenhum ponto de coleta encontrado para ' +
          currentMaterial +
          " na sua região.</span>";
      }
    } else {
      locationResultDiv.innerHTML = `<span class="error">Erro ao buscar pontos: ${
        data.error || "Ocorreu um erro desconhecido."
      }</span>`;
    }
  } catch (error) {
    console.error("Erro na requisição de pontos de coleta:", error);
    locationResultDiv.innerHTML =
      '<span class="error">Não foi possível conectar ao servidor para buscar pontos de coleta.</span>';
  }
}

// Placeholder para o formulário de associação (não implementado no backend do MVP)
document
  .getElementById("associationForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();
    alert(
      "Obrigado! A funcionalidade de cadastro de associações está em desenvolvimento. Seus dados não foram enviados. Continue acompanhando!"
    );
    // Aqui no futuro você enviaria os dados para um endpoint no Flask que salva em um banco de dados
    this.reset();
  });

// Garante que o mapa seja inicializado se a API do Google Maps for carregada antes da página.
window.onload = function () {
  if (typeof google === "object" && typeof google.maps === "object") {
    initMap();
  }
};

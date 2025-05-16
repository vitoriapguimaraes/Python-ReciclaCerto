let currentMaterial = null;
let currentItem = null;
let currentLocalsAvailable = false;
async function verificarItem() {
  const itemInput = document.getElementById("itemInput");
  const geminiResultDiv = document.getElementById("geminiResult");
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
  currentMaterial = null;
  currentItem = item;
  currentLocalsAvailable = false;
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
      if (data.mensagem2) {
        htmlContent += `<div class="result-box-reciclavel">${data.mensagem2}</div>`;
      }
      if (data.mensagem1) {
        htmlContent += `<div class="result-box-coleta">${data.mensagem1}</div>`;
      }
      if (data.mensagem3) {
        htmlContent += `<div class="result-box-instrucao">${data.mensagem3}</div>`;
      }
      geminiResultDiv.innerHTML = htmlContent;
      geminiResultDiv.style.display = "block";
      currentMaterial = data.gemini_raw?.material || item;
      currentLocalsAvailable = data.status === "tem_local";
    } else {
      geminiResultDiv.innerHTML = `<div class="result-box error">Erro: ${
        data.error || "Ocorreu um erro desconhecido."
      }</div>`;
      geminiResultDiv.style.display = "block";
    }
  } catch (error) {
    console.error("Erro na requisição Gemini:", error);
    geminiResultDiv.innerHTML =
      '<div class="result-box error">Não foi possível conectar ao servidor. Verifique sua conexão ou tente novamente.</div>';
    geminiResultDiv.style.display = "block";
  }
}
async function buscarLocalizacao(useAddressInput = false) {
  const locationInput = document.getElementById("locationInput");
  const locationResultDiv = document.getElementById("locationResult");
  locationResultDiv.style.display = "none";
  if (!currentMaterial && !currentItem) {
    locationResultDiv.innerHTML =
      '<div class="result-box error">Primeiro, verifique um item para saber o tipo de material!</div>';
    locationResultDiv.style.display = "block";
    return;
  }
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
        data.pontos.forEach((ponto) => {
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
document
  .getElementById("associationForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();
    alert(
      "Obrigado! A funcionalidade de cadastro de associações está em desenvolvimento. Seus dados não foram enviados. Continue acompanhando!"
    );
    this.reset();
  });

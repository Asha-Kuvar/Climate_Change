// static/js/scripts.js
// Shared functions
// function showLoading(elementId) {
//     document.getElementById(elementId).style.display = 'block';
// }

// function hideLoading(elementId) {
//     document.getElementById(elementId).style.display = 'none';
// }

// function toggleTheme() {
//     const body = document.body;
//     const isDark = body.classList.contains('dark-theme');
//     if (isDark) {
//         body.classList.remove('dark-theme');
//         body.classList.add('light-theme');
//         localStorage.setItem('theme', 'light');
//     } else {
//         body.classList.remove('light-theme');
//         body.classList.add('dark-theme');
//         localStorage.setItem('theme', 'dark');
//     }
//     updateMapTileLayer();
//     ['chart1', 'chart2', 'chart3'].forEach(id => {
//         const chart = Chart.getChart(id);
//         if (chart) {
//             chart.options.plugins.legend.labels.color = document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0';
//             chart.options.scales.x.title.color = document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0';
//             chart.options.scales.y.title.color = document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0';
//             chart.update();
//         }
//     });
// }

// function initTheme() {
//     const preferredTheme = localStorage.getItem('theme') || 'dark';
//     document.body.classList.add(`${preferredTheme}-theme`);
//     updateMapTileLayer();
// }

// // Chatbot functions
// function addUserMessage(message) {
//     const messages = document.getElementById('chatbot-messages');
//     const div = document.createElement('div');
//     div.className = 'chatbot-message user-message';
//     div.textContent = message;
//     messages.appendChild(div);
//     messages.scrollTop = messages.scrollHeight;
// }

// function addBotMessage(message) {
//     const messages = document.getElementById('chatbot-messages');
//     const div = document.createElement('div');
//     div.className = 'chatbot-message bot-message';
//     div.textContent = message;
//     messages.appendChild(div);
//     messages.scrollTop = messages.scrollHeight;
// }

// async function sendMessage() {
//     const input = document.getElementById('chatbot-message');
//     const message = input.value.trim();
//     if (!message) return;

//     addUserMessage(message);
//     input.value = '';

//     try {
//         const response = await fetch('/api/chat', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ message })
//         });
//         const data = await response.json();
//         if (data.error) {
//             addBotMessage('Sorry, something went wrong. Try again!');
//         } else {
//             addBotMessage(data.response);
//         }
//     } catch (error) {
//         console.error('Chatbot error:', error);
//         addBotMessage('Oops, I couldn\'t process that. Please try again.');
//     }
// }

// // Map initialization (for home page)
// let map, geoJsonLayer, climateData = {};
// function initMap() {
//     map = L.map('map').setView([20, 0], 2);
//     const darkTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
//         attribution: '© OpenStreetMap contributors'
//     });
//     const lightTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
//         attribution: '© OpenStreetMap contributors'
//     });
//     let currentTileLayer = document.body.classList.contains('light-theme') ? lightTileLayer : darkTileLayer;
//     currentTileLayer.addTo(map);

//     fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
//         .then(response => response.json())
//         .then(geojsonData => {
//             geoJsonLayer = L.geoJson(geojsonData, {
//                 style: function (feature) {
//                     const country = feature.properties.name;
//                     const data = climateData[country] || { temperature: 25, co2: 415, deforestation: 10 };
//                     const score = calculateClimateScore(data.temperature, data.co2, data.deforestation);
//                     return {
//                         fillColor: getColor(score),
//                         weight: 1,
//                         opacity: 1,
//                         color: 'white',
//                         fillOpacity: 0.7
//                     };
//                 },
//                 onEachFeature: function (feature, layer) {
//                     const country = feature.properties.name;
//                     layer.on('click', async () => {
//                         const data = await fetchClimateDataForCountry(country);
//                         climateData[country] = data;
//                         const score = calculateClimateScore(data.temperature, data.co2, data.deforestation);
//                         layer.setStyle({ fillColor: getColor(score) });

//                         document.getElementById("temperature").textContent = `${data.temperature}°C`;
//                         document.getElementById("co2Emissions").textContent = `${data.co2} ppm`;
//                         document.getElementById("deforestationRate").textContent = `${data.deforestation}%`;
//                         document.getElementById("location").textContent = country;

//                         fetchTemperatureData(country);
//                         fetchCO2EmissionsData(country);
//                         fetchDeforestationData(country);

//                         layer.bindPopup(
//                             `<b>${country}</b><br>` +
//                             `Temp: ${data.temperature}°C<br>` +
//                             `CO₂: ${data.co2} ppm<br>` +
//                             `Deforestation: ${data.deforestation}%<br>` +
//                             `Climate Score: ${score.toFixed(1)}`
//                         ).openPopup();

//                         const countryData = await (await fetch(`https://restcountries.com/v3.1/name/${encodeURIComponent(country)}`)).json();
//                         if (countryData && countryData[0]?.latlng) {
//                             const [lat, lon] = countryData[0].latlng;
//                             map.setView([lat, lon], 5);
//                             map.eachLayer(layer => { if (layer instanceof L.Marker) map.removeLayer(layer); });
//                             L.marker([lat, lon]).addTo(map)
//                                 .bindPopup(
//                                     `<b>${country}</b><br>` +
//                                     `Temp: ${data.temperature}°C<br>` +
//                                     `CO₂: ${data.co2} ppm<br>` +
//                                     `Deforestation: ${data.deforestation}%<br>` +
//                                     `Climate Score: ${score.toFixed(1)}`
//                                 ).openPopup();
//                         }
//                     });
//                 }
//             }).addTo(map);
//             addMapLegend();
//         })
//         .catch(error => console.error("Error loading GeoJSON:", error));
// }

// Include other shared functions: fetchClimateDataForCountry, calculateClimateScore, getColor, etc.
// (Copy relevant functions from original index.html script)
// Map initialization with theme-aware tile layers
var map = L.map('map').setView([20, 0], 2);
const darkTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors'
});
const lightTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors'
});
let currentTileLayer = darkTileLayer;
currentTileLayer.addTo(map);

let geoJsonLayer;
let climateData = {};

function updateMapTileLayer() {
    const isLightTheme = document.body.classList.contains('light-theme');
    if (currentTileLayer) map.removeLayer(currentTileLayer);
    currentTileLayer = isLightTheme ? lightTileLayer : darkTileLayer;
    currentTileLayer.addTo(map);
}

async function fetchClimateDataForCountry(country) {
    showLoading('mapLoading');
    try {
        const [tempRes, co2Res, countryInfoRes] = await Promise.all([
            fetch(`/api/current_temperature?country=${encodeURIComponent(country)}`),
            fetch(`/api/co2?country=${encodeURIComponent(country)}`),
            fetch(`/api/country_info?country=${encodeURIComponent(country)}`)
        ]);
        const tempData = await tempRes.json();
        const co2Data = await co2Res.json();
        const countryInfo = await countryInfoRes.json();
        const temperature = tempData.error ? 25 : tempData.temperature;
        const co2 = co2Data.error ? 415 : co2Data.co2_level;
        const deforestation = countryInfo.error || !countryInfo.deforestation_rate ? 10 : countryInfo.deforestation_rate;
        return { temperature, co2, deforestation };
    } catch (error) {
        console.error(`Error fetching data for ${country}:`, error);
        return { temperature: 25, co2: 415, deforestation: 10 };
    } finally {
        hideLoading('mapLoading');
    }
}

function calculateClimateScore(temp, co2, deforest) {
    const tempNorm = Math.min((temp + 20) / 60, 1) * 100;
    const co2Norm = Math.min((co2 - 300) / 200, 1) * 100;
    const deforestNorm = Math.min(deforest / 50, 1) * 100;
    return (tempNorm * 0.4 + co2Norm * 0.4 + deforestNorm * 0.2);
}

function getColor(score) {
    const isDark = document.body.classList.contains('dark-theme');
    if (isDark) {
        return score > 80 ? '#800026' :
            score > 60 ? '#BD0026' :
                score > 40 ? '#E31A1C' :
                    score > 20 ? '#FC4E2A' :
                        '#FFEDA0';
    } else {
        return score > 80 ? '#d7191c' :
            score > 60 ? '#fdae61' :
                score > 40 ? '#cccc80' :
                    score > 20 ? '#abd9e9' :
                        '#2c7bb6';
    }
}

fetch('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json')
    .then(response => response.json())
    .then(geojsonData => {
        geoJsonLayer = L.geoJson(geojsonData, {
            style: function (feature) {
                const country = feature.properties.name;
                const data = climateData[country] || { temperature: 25, co2: 415, deforestation: 10 };
                const score = calculateClimateScore(data.temperature, data.co2, data.deforestation);
                return {
                    fillColor: getColor(score),
                    weight: 1,
                    opacity: 1,
                    color: 'white',
                    fillOpacity: 0.7
                };
            },
            onEachFeature: function (feature, layer) {
                const country = feature.properties.name;
                layer.on('click', async () => {
                    const data = await fetchClimateDataForCountry(country);
                    climateData[country] = data;
                    const score = calculateClimateScore(data.temperature, data.co2, data.deforestation);
                    layer.setStyle({ fillColor: getColor(score) });

                    document.getElementById("temperature").textContent = `${data.temperature}°C`;
                    document.getElementById("co2Emissions").textContent = `${data.co2} ppm`;
                    document.getElementById("deforestationRate").textContent = `${data.deforestation}%`;
                    document.getElementById("location").textContent = country;

                    fetchTemperatureData(country);
                    fetchCO2EmissionsData(country);
                    fetchDeforestationData(country);

                    layer.bindPopup(
                        `<b>${country}</b><br>` +
                        `Temp: ${data.temperature}°C<br>` +
                        `CO₂: ${data.co2} ppm<br>` +
                        `Deforestation: ${data.deforestation}%<br>` +
                        `Climate Score: ${score.toFixed(1)}`
                    ).openPopup();

                    const countryData = await (await fetch(`https://restcountries.com/v3.1/name/${encodeURIComponent(country)}`)).json();
                    if (countryData && countryData[0]?.latlng) {
                        const [lat, lon] = countryData[0].latlng;
                        map.setView([lat, lon], 5);
                        map.eachLayer(layer => { if (layer instanceof L.Marker) map.removeLayer(layer); });
                        L.marker([lat, lon]).addTo(map)
                            .bindPopup(
                                `<b>${country}</b><br>` +
                                `Temp: ${data.temperature}°C<br>` +
                                `CO₂: ${data.co2} ppm<br>` +
                                `Deforestation: ${data.deforestation}%<br>` +
                                `Climate Score: ${score.toFixed(1)}`
                            ).openPopup();
                    }
                });
            }
        }).addTo(map);
    })
    .catch(error => console.error("Error loading GeoJSON:", error));

async function fetchCountryInfo(countryName) {
    showLoading('mapLoading');
    try {
        const tempResponse = await fetch(`/api/current_temperature?country=${encodeURIComponent(countryName)}`);
        const tempData = await tempResponse.json();
        const CO2Response = await fetch(`/api/co2?country=${encodeURIComponent(countryName)}`);
        const CO2 = await CO2Response.json();
        const deforestationResponse = await fetch(`/api/deforestations?country=${encodeURIComponent(countryName)}`);
        const deforestation = await deforestationResponse.json();

        document.getElementById("temperature").textContent = tempData.error ? "N/A" : `${tempData.temperature}°C`;
        document.getElementById("co2Emissions").textContent = CO2.error ? "N/A" : `${CO2.co2_level}ppm`;
        document.getElementById("deforestationRate").textContent = deforestation.error ? "N/A" : `${deforestation.deforestation_rate}%`;
        document.getElementById("location").textContent = countryName;

        fetchTemperatureData(countryName);
        fetchCO2EmissionsData(countryName);
        fetchDeforestationData(countryName);

        const countryData = await (await fetch(`https://restcountries.com/v3.1/name/${encodeURIComponent(countryName)}`)).json();
        if (countryData && countryData[0]?.latlng) {
            const [lat, lon] = countryData[0].latlng;
            map.setView([lat, lon], 5);
            map.eachLayer(layer => { if (layer instanceof L.Marker) map.removeLayer(layer); });
            L.marker([lat, lon]).addTo(map)
                .bindPopup(`<b>${countryName}</b><br>${tempData.temperature || "N/A"}°C`)
                .openPopup();

            climateData[countryName] = await fetchClimateDataForCountry(countryName);
            geoJsonLayer.eachLayer(layer => {
                if (layer.feature.properties.name === countryName) {
                    const score = calculateClimateScore(
                        climateData[countryName].temperature,
                        climateData[countryName].co2,
                        climateData[countryName].deforestation
                    );
                    layer.setStyle({ fillColor: getColor(score) });
                }
            });
        }
    } catch (error) {
        console.error("Error in fetchCountryInfo:", error);
        document.getElementById("location").textContent = "Error loading location";
    } finally {
        hideLoading('mapLoading');
    }
}

document.getElementById("updateLocation").addEventListener("click", function () {
    const selectedCountry = document.getElementById("countrySelect").value;
    if (selectedCountry) {
        fetchCountryInfo(selectedCountry);
        bootstrap.Modal.getInstance(document.getElementById("locationModal")).hide();
    }
});

document.getElementById("refreshData").addEventListener("click", () => fetchCountryInfo(document.getElementById("location").textContent));

document.addEventListener("DOMContentLoaded", function () {
    fetchCountryInfo("India");
});

fetch("https://restcountries.com/v3.1/all")
    .then(res => res.json())
    .then(data => {
        let countrySelect = document.getElementById("countrySelect");
        let predictionCountrySelect = document.getElementById("predictionCountry");
        countrySelect.innerHTML = "";
        predictionCountrySelect.innerHTML = "";
        data.sort((a, b) => a.name.common.localeCompare(b.name.common));
        data.forEach(country => {
            let option = document.createElement("option");
            option.value = country.name.common;
            option.textContent = country.name.common;
            countrySelect.appendChild(option.cloneNode(true));
            predictionCountrySelect.appendChild(option.cloneNode(true));
        });

        const countrySearch = document.getElementById("countrySearch");
        countrySearch.addEventListener("input", function () {
            const searchTerm = this.value.toLowerCase();
            const filteredCountries = data.filter(c => c.name.common.toLowerCase().includes(searchTerm));
            countrySelect.innerHTML = "";
            filteredCountries.forEach(c => {
                let option = document.createElement("option");
                option.value = c.name.common;
                option.textContent = c.name.common;
                countrySelect.appendChild(option);
            });
        });
    });

function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                try {
                    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`);
                    const data = await response.json();
                    const country = data.address?.country || "India";
                    console.log(`User location detected: ${country}`);
                    await fetchCountryInfo(country);
                } catch (error) {
                    console.error("Error fetching country from coordinates:", error);
                    await fetchCountryInfo("India");
                }
            },
            (error) => {
                console.error("Geolocation error:", error.message);
                fetchCountryInfo("India");
            }
        );
    } else {
        console.error("Geolocation not supported by this browser.");
        fetchCountryInfo("India");
    }
}

async function fetchTemperatureData(country) {
    try {
        const response = await fetch(`/api/temperature?country=${encodeURIComponent(country)}`);
        const tempData = await response.json();
        if (!tempData.length) return;

        const labels = tempData.map(d => d.year.toString());
        const avgTemps = tempData.map(d => d.avg_temperature);

        const existingChart = Chart.getChart("chart1");
        if (existingChart) existingChart.destroy();

        new Chart(document.getElementById("chart1"), {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: `Avg Temperature in ${country} (°C)`,
                    data: avgTemps,
                    borderColor: "red",
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { type: 'linear', ticks: { stepSize: 2, callback: value => Number(value).toFixed(0) } },
                    y: { beginAtZero: false }
                },
                plugins: {
                    legend: { labels: { color: document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0' } },
                    tooltip: { mode: 'index', intersect: false }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching temperature data:", error);
    }
}

async function fetchCO2EmissionsData(country) {
    try {
        const response = await fetch(`/api/co2-emissions?country=${encodeURIComponent(country)}`);
        const co2Data = await response.json();
        if (!co2Data.length) return;

        const labels = co2Data.map(d => d.year.toString());
        const emissions = co2Data.map(d => d.co2_emissions);

        const existingChart = Chart.getChart("chart2");
        if (existingChart) existingChart.destroy();

        new Chart(document.getElementById("chart2"), {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: `CO₂ Emissions in ${country} (ppm)`,
                    data: emissions,
                    borderColor: "blue",
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { type: 'linear', ticks: { stepSize: 2, callback: value => Number(value).toFixed(0) } },
                    y: { beginAtZero: false }
                },
                plugins: {
                    legend: { labels: { color: document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0' } },
                    tooltip: { mode: 'index', intersect: false }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching CO₂ emissions data:", error);
    }
}

async function fetchDeforestationData(country) {
    try {
        const response = await fetch(`/api/deforestation?country=${encodeURIComponent(country)}`);
        const deforestationData = await response.json();
        if (!deforestationData.length) return;

        const existingChart = Chart.getChart("chart3");
        if (existingChart) existingChart.destroy();

        new Chart(document.getElementById("chart3"), {
            type: 'scatter',
            data: {
                datasets: [{
                    label: `Deforestation vs Temperature Rise (${country})`,
                    data: deforestationData.map(d => ({ x: d.deforestation_rate, y: d.avg_temperature })),
                    backgroundColor: "green",
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { title: { display: true, text: "Forests Lost (%)", color: document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0' } },
                    y: { title: { display: true, text: "Temperature Rise (°C)", color: document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0' } }
                },
                plugins: {
                    legend: { labels: { color: document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0' } }
                }
            }
        });
    } catch (error) {
        console.error("Error fetching deforestation data:", error);
    }
}

document.getElementById("simulationForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const temperatureChange = parseFloat(document.getElementById("temperatureChange").value) || 0;
    const co2Level = parseFloat(document.getElementById("co2Level").value) || 400;
    const deforestationChange = parseFloat(document.getElementById("deforestationChange").value) || 0;

    showLoading('mapLoading');
    try {
        const response = await fetch('/api/predicts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ temperatureChange, co2Level, deforestationChange })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        if (data.error) throw new Error(data.error);

        document.getElementById("predictTemperature").textContent = `${data.predict_temperature_c || '-'}°C`;
        document.getElementById("predictCO2").textContent = `${data.predict_co2_emissions_mmt || '-'} ppm`;
        document.getElementById("predictDeforestation").textContent = `${data.predict_deforestation_rate_percent || '-'}%`;
    } catch (error) {
        console.error("Simulation Error:", error);
        alert("Failed to simulate impact: " + error.message);
        document.getElementById("predictTemperature").textContent = "-";
        document.getElementById("predictCO2").textContent = "-";
        document.getElementById("predictDeforestation").textContent = "-";
    } finally {
        hideLoading('mapLoading');
    }
});

document.getElementById("predictionForm").addEventListener("submit", function (event) {
    event.preventDefault();
    const country = document.getElementById("predictionCountry").value;
    const year = document.getElementById("predictionYear").value;

    if (!country || !year) {
        alert("Please select a country and enter a year.");
        return;
    }

    showLoading('mapLoading');
    fetch(`/api/predict?country=${encodeURIComponent(country)}&year=${year}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) alert(data.error);
            else {
                document.getElementById("predictedTemperature").textContent = `${data.predicted_temperature_c}°C`;
                document.getElementById("predictedCO2").textContent = `${data.predicted_co2_emissions_mmt} ppm`;
                document.getElementById("predictedDeforestation").textContent = `${data.predicted_deforestation_rate_percent}%`;
            }
        })
        .catch(error => console.error("Error fetching prediction data:", error))
        .finally(() => hideLoading('mapLoading'));
});

document.getElementById("generateReportBtn").addEventListener("click", function () {
    const currentCountry = document.getElementById("location").textContent;
    if (!currentCountry || currentCountry === "Loading...") {
        alert("Please select a country first");
        return;
    }

    showLoading('mapLoading');
    fetch(`/api/generate-report?country=${encodeURIComponent(currentCountry)}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/pdf'
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentCountry}_climate_report.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error generating report:', error);
            alert('Failed to generate report. Please check the console for details or try again.');
        })
        .finally(() => hideLoading('mapLoading'));
});

document.getElementById("contactForm").addEventListener("submit", function (event) {
    event.preventDefault();
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const mobile = document.getElementById("mobile").value;
    const message = document.getElementById("message").value;

    showLoading('mapLoading');
    fetch('/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, mobile, message })
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert("Message sent successfully!");
                document.getElementById("contactForm").reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById("contactModal"));
                modal.hide();
            }
        })
        .catch(error => console.error("Error submitting contact form:", error))
        .finally(() => hideLoading('mapLoading'));
});

fetch("https://restcountries.com/v3.1/all")
    .then(res => res.json())
    .then(data => {
        let countrySelect = document.getElementById("countrySelect");
        let predictionCountrySelect = document.getElementById("predictionCountry");
        countrySelect.innerHTML = "";
        predictionCountrySelect.innerHTML = "";
        data.sort((a, b) => a.name.common.localeCompare(b.name.common));
        data.forEach(country => {
            let option = document.createElement("option");
            option.value = country.name.common;
            option.textContent = country.name.common;
            countrySelect.appendChild(option.cloneNode(true));
            predictionCountrySelect.appendChild(option.cloneNode(true));
        });
    })
    .catch(error => console.error("Error loading countries:", error));

function addMapLegend() {
    const legend = L.control({ position: 'bottomright' });

    legend.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'legend');
        const grades = [0, 20, 40, 60, 80];
        const labels = [];

        div.innerHTML = '<h4>Climate Risk Score</h4>';

        for (let i = 0; i < grades.length; i++) {
            div.innerHTML +=
                '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
                grades[i] + (grades[i + 1] ? '–' + grades[i + 1] + '<br>' : '+');
        }

        return div;
    };

    legend.addTo(map);
}

function toggleTheme() {
    const body = document.body;
    const isDark = body.classList.contains('dark-theme');

    if (isDark) {
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
    }
    updateMapTileLayer();
    ['chart1', 'chart2', 'chart3'].forEach(id => {
        const chart = Chart.getChart(id);
        if (chart) {
            chart.options.plugins.legend.labels.color = document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0';
            chart.options.scales.x.title.color = document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0';
            chart.options.scales.y.title.color = document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0';
            chart.update();
        }
    });
}

function initTheme() {
    const preferredTheme = localStorage.getItem('theme') || 'dark';
    document.body.classList.add(`${preferredTheme}-theme`);
    updateMapTileLayer();
}

function showLoading(elementId) {
    document.getElementById(elementId).style.display = 'block';
}

function hideLoading(elementId) {
    document.getElementById(elementId).style.display = 'none';
}

let compareMode = false;
let comparedCountries = [];

document.getElementById('compareMode').addEventListener('change', function (e) {
    compareMode = e.target.checked;
    if (compareMode) {
        document.body.classList.add('compare-mode');
        initCompareMode();
    } else {
        document.body.classList.remove('compare-mode');
        exitCompareMode();
    }
});

function initCompareMode() {
    map.on('click', async function (e) {
        const country = await getCountryFromCoordinates(e.latlng);
        if (country && !comparedCountries.includes(country)) {
            comparedCountries.push(country);
            updateCompareView();
        }
    });

    const compareUI = document.createElement('div');
    compareUI.id = 'compareUI';
    compareUI.style.position = 'absolute';
    compareUI.style.top = '10px';
    compareUI.style.right = '10px';
    compareUI.style.zIndex = '1000';
    compareUI.style.padding = '15px';
    compareUI.style.borderRadius = '10px';
    document.getElementById('map').appendChild(compareUI);

    updateCompareView();
}

function exitCompareMode() {
    comparedCountries = [];
    map.off('click');
    const compareUI = document.getElementById('compareUI');
    if (compareUI) compareUI.remove();
}

async function updateCompareView() {
    const compareUI = document.getElementById('compareUI');
    if (!compareUI) return;

    if (comparedCountries.length === 0) {
        compareUI.innerHTML = '<p>Click on countries to compare</p>';
        return;
    }

    compareUI.innerHTML = '<h5>Comparing Countries:</h5><ul>';
    comparedCountries.forEach(country => {
        const li = document.createElement('li');
        li.textContent = country;
        compareUI.appendChild(li);
    });
    compareUI.innerHTML += '</ul>';

    const compareBtn = document.createElement('button');
    compareBtn.textContent = 'Compare Data';
    compareBtn.className = 'btn btn-sm btn-primary mt-2';
    compareBtn.onclick = fetchComparisonData;
    compareUI.appendChild(compareBtn);
}

async function fetchComparisonData() {
    if (comparedCountries.length < 2) {
        alert('Please select at least 2 countries to compare');
        return;
    }

    showLoading('mapLoading');
    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ countries: comparedCountries })
        });

        const data = await response.json();
        displayComparisonResults(data);
    } catch (error) {
        console.error('Comparison error:', error);
        alert('Failed to fetch comparison data');
    } finally {
        hideLoading('mapLoading');
    }
}

function displayComparisonResults(data) {
    let modal = document.getElementById('compareModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'compareModal';
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title text-dark">Country Comparison</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" id="compareResults"></div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    const resultsContainer = document.getElementById('compareResults');
    resultsContainer.innerHTML = '';

    const table = document.createElement('table');
    table.className = 'table table-striped';

    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Country</th>
            <th>Temperature (°C)</th>
            <th>CO₂ (ppm)</th>
            <th>Deforestation (%)</th>
        </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    data.forEach(country => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${country.country}</td>
            <td>${country.temperature || "N/A"}</td>
            <td>${country.co2 || "415"}</td>
            <td>${country.deforestation || "10"}</td>
        `;
        tbody.appendChild(row);
    });
    table.appendChild(tbody);

    const chartCanvas = document.createElement('canvas');
    chartCanvas.id = 'compareChart';
    resultsContainer.appendChild(table);
    resultsContainer.appendChild(chartCanvas);

    new Chart(document.getElementById('compareChart'), {
        type: 'bar',
        data: {
            labels: data.map(d => d.country),
            datasets: [{
                label: 'Temperature (°C)',
                data: data.map(d => d.temperature || 0),
                backgroundColor: 'rgba(255, 99, 132, 0.5)'
            }, {
                label: 'CO₂ (ppm)',
                data: data.map(d => d.co2 || 0),
                backgroundColor: 'rgba(54, 162, 235, 0.5)'
            }, {
                label: 'Deforestation (%)',
                data: data.map(d => d.deforestation || 0),
                backgroundColor: 'rgba(75, 192, 192, 0.5)'
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { labels: { color: document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0' } }
            }
        }
    });

    new bootstrap.Modal(modal).show();
}

async function getCountryFromCoordinates(latlng) {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latlng.lat}&lon=${latlng.lng}&format=json`);
        const data = await response.json();
        return data.address?.country;
    } catch (error) {
        console.error('Geocoding error:', error);
        return null;
    }
}

function prepareMapForPrint(country) {
    const currentCenter = map.getCenter();
    const currentZoom = map.getZoom();

    if (climateData[country] && climateData[country].latlng) {
        map.setView(climateData[country].latlng, 6);

        let countryBounds;
        geoJsonLayer.eachLayer(layer => {
            if (layer.feature.properties.name === country) {
                countryBounds = layer.getBounds();
            }
        });

        if (countryBounds) {
            const countryCenter = countryBounds.getCenter();
            const countrySize = countryBounds.getSize();
            const padding = Math.max(countrySize.lat, countrySize.lng) * 1.5;
            const bounds = L.latLngBounds(
                [countryCenter.lat - padding, countryCenter.lng - padding],
                [countryCenter.lat + padding, countryCenter.lng + padding]
            );
            map.fitBounds(bounds);
        }

        const printContainer = document.createElement('div');
        printContainer.className = 'print-container';
        printContainer.innerHTML = `
            <h3 class="print-title">Climate Data Report</h3>
            <h4 class="country-title">Selected Country: <span>${country}</span></h4>
        `;
        document.getElementById('map').before(printContainer);

        geoJsonLayer.eachLayer(layer => {
            if (layer.feature.properties.name === country) {
                layer.setStyle({
                    weight: 4,
                    color: '#FF0000',
                    fillColor: '#FF0000',
                    fillOpacity: 0.3
                });
                layer.bringToFront();

                const center = layer.getBounds().getCenter();
                L.marker(center, {
                    icon: L.divIcon({
                        className: 'print-marker',
                        html: `<div>${country}</div>`,
                        iconSize: [120, 40]
                    }),
                    zIndexOffset: 1000
                }).addTo(map);
            }
        });

        setTimeout(() => {
            window.print();
            map.setView(currentCenter, currentZoom);
            document.querySelector('.print-container')?.remove();
            geoJsonLayer.resetStyle();
            map.eachLayer(layer => {
                if (layer instanceof L.Marker && layer.options.icon?.options?.className === 'print-marker') {
                    map.removeLayer(layer);
                }
            });
        }, 2000);
    }
}

// Chatbot functionality
document.getElementById('chatbot-toggle').addEventListener('click', function () {
    const chatbotWindow = document.getElementById('chatbot-window');
    chatbotWindow.style.display = chatbotWindow.style.display === 'block' ? 'none' : 'block';
    if (chatbotWindow.style.display === 'block') {
        document.getElementById('chatbot-message').focus();
        if (!document.querySelector('#chatbot-messages .chatbot-message')) {
            addBotMessage('Hi! I\'m ClimateBot. Ask me about climate data, predictions, or how to use the dashboard!');
        }
    }
});

document.getElementById('chatbot-send').addEventListener('click', sendMessage);
document.getElementById('chatbot-message').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') sendMessage();
});

function addUserMessage(message) {
    const messages = document.getElementById('chatbot-messages');
    const div = document.createElement('div');
    div.className = 'chatbot-message user-message';
    div.textContent = message;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

function addBotMessage(message) {
    const messages = document.getElementById('chatbot-messages');
    const div = document.createElement('div');
    div.className = 'chatbot-message bot-message';
    div.textContent = message;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('chatbot-message');
    const message = input.value.trim();
    if (!message) return;

    addUserMessage(message);
    input.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        if (data.error) {
            addBotMessage('Sorry, something went wrong. Try again!');
        } else {
            addBotMessage(data.response);
        }
    } catch (error) {
        console.error('Chatbot error:', error);
        addBotMessage('Oops, I couldn\'t process that. Please try again.');
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    addMapLegend();
    getUserLocation();

    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function () {
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) firstInput.focus();
            modal.querySelectorAll('input, select, textarea, button, .btn-close').forEach(el => {
                el.style.pointerEvents = 'auto';
                el.style.zIndex = '1070';
            });
        });
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            }
        });
        modal.querySelector('.modal-content').addEventListener('click', (e) => e.stopPropagation());
    });
});

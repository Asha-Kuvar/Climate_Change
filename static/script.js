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
             fetch(`/api/deforestations?country=${encodeURIComponent(country)}`)
             // fetch(`/api/country_info?country=${encodeURIComponent(country)}`)
         ]);
         const tempData = await tempRes.json();
         const co2Data = await co2Res.json();
         const countryInfo = await countryInfoRes.json();
         const temperature = tempData.error ? 25 : tempData.temperature;
         const co2 = co2Data.error ? 415 : co2Data.co2_level;
         const deforestation = countryInfo.error ? 10 : countryInfo.deforestation_rate;
         // const deforestation = countryInfo.error || !countryInfo.deforestation_rate ? 10 : countryInfo.deforestation_rate;
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

 // NEW

 function debounce(func, wait) {
     let timeout;
     return function (...args) {
         clearTimeout(timeout);
         timeout = setTimeout(() => func.apply(this, args), wait);
     };
 }

 function validateInput(input, min, max, errorElementId, fieldName) {
     const value = parseFloat(input.value);
     const errorElement = document.getElementById(errorElementId);
     if (isNaN(value) || value < min || value > max) {
         input.classList.add('is-invalid');
         errorElement.textContent = `${fieldName} must be between ${min} and ${max}.`;
         return false;
     } else {
         input.classList.remove('is-invalid');
         errorElement.textContent = '';
         return true;
     }
 }

 function showLoading(elementId) {
     document.getElementById(elementId).style.display = 'block';
 }

 function hideLoading(elementId) {
     document.getElementById(elementId).style.display = 'none';
 }

 function renderSimulationChart(temp, co2, def) {
     const ctx = document.getElementById('simulationChart').getContext('2d');
     const chart = Chart.getChart('simulationChart');
     if (chart) chart.destroy();
     new Chart(ctx, {
         type: 'bar',
         data: {
             labels: ['Temperature (°C)', 'CO₂ (ppm)', 'Deforestation (%)'],
             datasets: [{
                 label: 'Simulated Values',
                 data: [temp, co2, def],
                 backgroundColor: ['#ff6384', '#36a2eb', '#4bc0c0'],
                 borderColor: ['#ff6384', '#36a2eb', '#4bc0c0'],
                 borderWidth: 1
             }]
         },
         options: {
             responsive: true,
             scales: {
                 y: { beginAtZero: true }
             },
             plugins: {
                 legend: { display: false },
                 title: {
                     display: true,
                     text: 'Simulation Results'
                 }
             }
         }
     });
 }

 function updateResults(data) {
     const elements = [
         { id: 'predictTemperature', key: 'predict_temperature_c', unit: '°C' },
         { id: 'predictCO2', key: 'predict_co2_emissions_mmt', unit: 'ppm' },
         { id: 'predictDeforestation', key: 'predict_deforestation_rate_percent', unit: '%' }
     ];
     elements.forEach(el => {
         const element = document.getElementById(el.id);
         element.classList.remove('updated');
         element.classList.add('simulation-result');
         setTimeout(() => {
             element.textContent = `${data[el.key]} ${el.unit}`;
             element.classList.add('updated');
         }, 100);
     });
 }

 async function populateCountries() {
     try {
         const response = await fetch('/api/countries');
         const data = await response.json();
         if (!data.error) {
             const select = document.getElementById('country');
             data.countries.forEach(country => {
                 const option = document.createElement('option');
                 option.value = country;
                 option.textContent = country;
                 select.appendChild(option);
             });
         } else {
             console.error('Failed to load countries:', data.error);
         }
     } catch (error) {
         console.error('Failed to load countries:', error);
     }
 }

 async function previewSimulation() {
     const temperatureChange = parseFloat(document.getElementById('temperatureChange').value) || 0;
     const co2Level = parseFloat(document.getElementById('co2Level').value) || 400;
     const deforestationChange = parseFloat(document.getElementById('deforestationChange').value) || 0;
     const country = document.getElementById('country').value;
     const year = parseInt(document.getElementById('year').value) || 2025;

     const isTempValid = validateInput(document.getElementById('tempValue'), -10, 10, 'tempError', 'Temperature change');
     const isCO2Valid = validateInput(document.getElementById('co2Value'), 300, 600, 'co2Error', 'CO₂ level');
     const isDefValid = validateInput(document.getElementById('defValue'), -50, 50, 'defError', 'Deforestation change');
     const isYearValid = validateInput(document.getElementById('year'), 2020, 2100, 'yearError', 'Year');

     if (!isTempValid || !isCO2Valid || !isDefValid || !isYearValid) return;

     showLoading('mapLoading');
     try {
         const response = await fetch('/api/predicts', {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({ temperatureChange, co2Level, deforestationChange, country, year })
         });
         const data = await response.json();
         if (!data.error) {
             updateResults(data);
             renderSimulationChart(
                 data.predict_temperature_c,
                 data.predict_co2_emissions_mmt,
                 data.predict_deforestation_rate_percent
             );
             document.getElementById('formError').style.display = 'none';
         } else {
             document.getElementById('formError').textContent = data.error;
             document.getElementById('formError').style.display = 'block';
         }
     } catch (error) {
         document.getElementById('formError').textContent = 'Failed to simulate impact. Please try again.';
         document.getElementById('formError').style.display = 'block';
     } finally {
         hideLoading('mapLoading');
     }
 }

 document.getElementById('simulationForm').addEventListener('submit', async function (event) {
     event.preventDefault();
     await previewSimulation();
 });

 document.getElementById('resetSimulation').addEventListener('click', () => {
     document.getElementById('simulationForm').reset();
     document.getElementById('temperatureChange').value = 0;
     document.getElementById('co2Level').value = 400;
     document.getElementById('deforestationChange').value = 0;
     document.getElementById('year').value = 2025;
     document.getElementById('predictTemperature').textContent = '-';
     document.getElementById('predictCO2').textContent = '-';
     document.getElementById('predictDeforestation').textContent = '-';
     document.getElementById('formError').style.display = 'none';
     const chart = Chart.getChart('simulationChart');
     if (chart) chart.destroy();
 });

 document.getElementById('temperatureChange').addEventListener('input', debounce(previewSimulation, 500));
 document.getElementById('co2Level').addEventListener('input', debounce(previewSimulation, 500));
 document.getElementById('deforestationChange').addEventListener('input', debounce(previewSimulation, 500));
 document.getElementById('year').addEventListener('input', debounce(previewSimulation, 500));
 document.getElementById('country').addEventListener('change', debounce(previewSimulation, 500));

 document.getElementById('tempValue').addEventListener('input', () => {
     validateInput(document.getElementById('tempValue'), -10, 10, 'tempError', 'Temperature change');
 });
 document.getElementById('co2Value').addEventListener('input', () => {
     validateInput(document.getElementById('co2Value'), 300, 600, 'co2Error', 'CO₂ level');
 });
 document.getElementById('defValue').addEventListener('input', () => {
     validateInput(document.getElementById('defValue'), -50, 50, 'defError', 'Deforestation change');
 });
 document.getElementById('year').addEventListener('input', () => {
     validateInput(document.getElementById('year'), 2020, 2100, 'yearError', 'Year');
 });

 document.getElementById('simulationForm').addEventListener('keypress', function (e) {
     if (e.key === 'Enter') {
         e.preventDefault();
         document.querySelector('#simulationForm button[type="submit"]').click();
     }
 });

 document.addEventListener('DOMContentLoaded', populateCountries);

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
     if (confirm(`Generate a climate report for ${currentCountry}?`)) {
         showLoading('mapLoading');
         fetch(`/api/generate-report?country=${encodeURIComponent(currentCountry)}`, {
             method: 'GET',
             headers: { 'Accept': 'application/pdf' }
         })
             .then(response => {
                 if (!response.ok) {
                     return response.json().then(error => { throw new Error(error.error); });
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
                 alert(`Failed to generate report: ${error.message}`);
             })
             .finally(() => hideLoading('mapLoading'));
     }
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
             <td>${country.co2 || "N/A"}</td>
             <td>${country.deforestation || "0"}</td>
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

 // Initialize chatbot and visualization
 $(document).ready(function () {
     // Toggle chatbot window
     $('#chatbot-toggle').click(function () {
         $('#chatbot-window').toggle();
         if ($('#chatbot-window').is(':visible')) {
             const welcomeMessage = "Welcome to the Climate Change Impacts Visualizer Chatbot! Ask me about temperature trends, CO2 emissions, deforestation, or climate predictions.";
             $('#chatbot-messages').append(
                 $('<div>').addClass('assistant-message').text(welcomeMessage)
             );
             $('#chatbot-messages').scrollTop($('#chatbot-messages')[0].scrollHeight);
         }
     });

     // Send message on Enter key
     $('#chatbot-message').keypress(function (e) {
         if (e.which === 13) {
             sendChat();
         }
     });

     // Initialize visualization
     renderCorrelationPlot('India');
 });

 function sendChat() {
     const message = $('#chatbot-message').val().trim();
     if (!message) {
         return; // Skip empty messages
     }

     // Add user message
     $('#chatbot-messages').append(
         $('<div>').addClass('user-message').text(message)
     );
     $('#chatbot-messages').scrollTop($('#chatbot-messages')[0].scrollHeight);

     // Send AJAX request
     $.ajax({
         url: '/chat',
         type: 'POST',
         contentType: 'application/json',
         data: JSON.stringify({ message: message }),
         success: function (response) {
             const reply = response.error || response.reply;
             $('#chatbot-messages').append(
                 $('<div>').addClass('assistant-message').text(reply)
             );
             $('#chatbot-message').val('');
             $('#chatbot-messages').scrollTop($('#chatbot-messages')[0].scrollHeight);
         },
         error: function (xhr, status, error) {
             $('#chatbot-messages').append(
                 $('<div>').addClass('assistant-message').text('Error: Unable to connect to chatbot')
             );
             $('#chatbot-messages').scrollTop($('#chatbot-messages')[0].scrollHeight);
         }
     });
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

 // Initialize Leaflet map
 let map;
 function initMap() {
     map = L.map('deforestationMap').setView([20.5937, 78.9629], 5); // Center on India
     L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
         attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
     }).addTo(map);
 }

 // Populate country dropdown
 async function populateDeforestationCountries() {
     try {
         const response = await fetch('/api/countries');
         const data = await response.json();
         if (!data.error) {
             const select = document.getElementById('defCountry');
             data.countries.forEach(country => {
                 const option = document.createElement('option');
                 option.value = country;
                 option.textContent = country;
                 select.appendChild(option);
             });
         } else {
             console.error('Error loading countries:', data.error);
         }
     } catch (error) {
         console.error('Error loading countries:', error);
     }
 }

 // Pre-fill bounding box for India
 document.getElementById('defCountry').addEventListener('change', function () {
     const country = this.value;
     const minLonInput = document.getElementById('minLon');
     const minLatInput = document.getElementById('minLat');
     const maxLonInput = document.getElementById('maxLon');
     const maxLatInput = document.getElementById('maxLat');

     if (country === 'India') {
         minLonInput.value = 68.1;
         minLatInput.value = 6.7;
         maxLonInput.value = 97.4;
         maxLatInput.value = 35.5;
     } else {
         minLonInput.value = '';
         minLatInput.value = '';
         maxLonInput.value = '';
         maxLatInput.value = '';
     }
 });

 // Handle form submission
 document.getElementById('deforestationForm').addEventListener('submit', async function (event) {
     event.preventDefault();
     const country = document.getElementById('defCountry').value;
     const startYear = parseInt(document.getElementById('startYear').value);
     const endYear = parseInt(document.getElementById('endYear').value);
     const minLon = parseFloat(document.getElementById('minLon').value) || undefined;
     const minLat = parseFloat(document.getElementById('minLat').value) || undefined;
     const maxLon = parseFloat(document.getElementById('maxLon').value) || undefined;
     const maxLat = parseFloat(document.getElementById('maxLat').value) || undefined;

     // Validate years
     const currentYear = new Date().getFullYear();
     if (startYear < 2015 || endYear > currentYear || startYear >= endYear) {
         document.getElementById('defFormError').textContent = 'Invalid year range (2015-current, start < end)';
         document.getElementById('defFormError').style.display = 'block';
         return;
     }

     document.getElementById('mapLoading').style.display = 'block';
     try {
         const response = await fetch('/api/deforestation_tracker', {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({ country, startYear, endYear, minLon, minLat, maxLon, maxLat })
         });
         const data = await response.json();
         if (data.error) {
             document.getElementById('defFormError').textContent = data.error;
             document.getElementById('defFormError').style.display = 'block';
         } else {
             document.getElementById('defFormError').style.display = 'none';

             // Update Chart.js chart
             const chart = Chart.getChart('deforestationChart');
             if (chart) chart.destroy();
             new Chart(document.getElementById('deforestationChart'), {
                 type: 'line',
                 data: {
                     labels: data.ndvi_trends.map(t => t.year),
                     datasets: [{
                         label: `Mean NDVI for ${country}`,
                         data: data.ndvi_trends.map(t => t.ndvi),
                         borderColor: 'green',
                         fill: false,
                         tension: 0.4
                     }]
                 },
                 options: {
                     responsive: true,
                     scales: {
                         x: { title: { display: true, text: 'Year' } },
                         y: { title: { display: true, text: 'Mean NDVI' }, min: 0, max: 1 }
                     },
                     plugins: {
                         legend: { labels: { color: document.body.classList.contains('light-theme') ? '#2a2a2a' : '#e0e0e0' } }
                     }
                 }
             });

             // Update Leaflet map with NDVI rasters
             map.eachLayer(layer => {
                 if (layer instanceof L.ImageOverlay) map.removeLayer(layer);
             });
             data.rasters.forEach(raster => {
                 L.imageOverlay(raster.url, raster.bounds, { opacity: 0.7 }).addTo(map);
             });
             map.fitBounds([[minLat || 6.7, minLon || 68.1], [maxLat || 35.5, maxLon || 97.4]]);
         }
     } catch (error) {
         document.getElementById('defFormError').textContent = 'Failed to track deforestation. Please try again.';
         document.getElementById('defFormError').style.display = 'block';
     } finally {
         document.getElementById('mapLoading').style.display = 'none';
     }
 });

 // Reset form
 document.getElementById('resetDeforestation').addEventListener('click', () => {
     document.getElementById('deforestationForm').reset();
     document.getElementById('startYear').value = 2015;
     document.getElementById('endYear').value = 2020;
     document.getElementById('defFormError').style.display = 'none';
     const chart = Chart.getChart('deforestationChart');
     if (chart) chart.destroy();
     map.eachLayer(layer => {
         if (layer instanceof L.ImageOverlay) map.removeLayer(layer);
     });
 });

 // Initialize on page load
 document.addEventListener('DOMContentLoaded', () => {
     initMap();
     populateDeforestationCountries();
 });
export async function drawTemperatureChart(country) {
    const response = await fetch(`/api/temperature?country=${encodeURIComponent(country)}`);
    const data = await response.json();
    const svg = d3.select("#chart1").html("").append("svg").attr("width", 400).attr("height", 300);
    const margin = { top: 20, right: 20, bottom: 30, left: 50 };
    const width = 400 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain(d3.extent(data, d => d.year)).range([0, width]);
    const y = d3.scaleLinear().domain(d3.extent(data, d => d.avg_temperature)).range([height, 0]);

    g.append("g").attr("transform", `translate(0,${height})`).call(d3.axisBottom(x).tickFormat(d3.format("d")));
    g.append("g").call(d3.axisLeft(y));

    g.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "red")
        .attr("stroke-width", 2)
        .attr("d", d3.line().x(d => x(d.year)).y(d => y(d.avg_temperature)));

    g.selectAll("circle")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", d => x(d.year))
        .attr("cy", d => y(d.avg_temperature))
        .attr("r", 5)
        .attr("fill", "red")
        .on("mouseover", (event, d) => {
            d3.select("#tooltip")
                .style("visibility", "visible")
                .style("left", `${event.pageX + 10}px`)
                .style("top", `${event.pageY - 10}px`)
                .text(`Year: ${d.year}, Temp: ${d.avg_temperature}°C`);
        })
        .on("mouseout", () => d3.select("#tooltip").style("visibility", "hidden"));
}

export async function drawCorrelationChart(country) {
    const response = await fetch(`/api/correlation?country=${encodeURIComponent(country)}`);
    const corrData = await response.json();
    const dataResponse = await fetch(`/api/temperature?country=${encodeURIComponent(country)}`);
    const data = await dataResponse.json();
    const svg = d3.select("#chart2").html("").append("svg").attr("width", 400).attr("height", 300);
    const margin = { top: 20, right: 20, bottom: 30, left: 50 };
    const width = 400 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain(d3.extent(data, d => d.avg_temperature)).range([0, width]);
    const y = d3.scaleLinear().domain(d3.extent(data, d => d.deforestation_rate)).range([height, 0]);

    g.append("g").attr("transform", `translate(0,${height})`).call(d3.axisBottom(x));
    g.append("g").call(d3.axisLeft(y));

    g.selectAll("circle")
        .data(data)
        .enter()
        .append("circle")
        .attr("cx", d => x(d.avg_temperature))
        .attr("cy", d => y(d.deforestation_rate))
        .attr("r", 5)
        .attr("fill", "blue");

    g.append("text")
        .attr("x", width / 2)
        .attr("y", 0)
        .attr("text-anchor", "middle")
        .text(`Correlation: ${corrData.correlation.toFixed(2)}`);
}
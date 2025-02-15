const accessToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhcGkuZnllcnMuaW4iLCJpYXQiOjE3MzkyNDk3OTEsImV4cCI6MTczOTMyMDIzMSwibmJmIjoxNzM5MjQ5NzkxLCJhdWQiOlsieDowIiwieDoxIiwieDoyIiwiZDoxIiwiZDoyIiwieDoxIiwieDowIl0sInN1YiI6ImFjY2Vzc190b2tlbiIsImF0X2hhc2giOiJnQUFBQUFCbnF0aF9TVGl3TEYtNFBzeUJCYTNxMmp1Q2hPRUdVWHpQNG9tOVNWOXQ1ZkpvaGZ5eHltR1hyOEc5UDc3dkJGYlV3UHpmNUxfQjVQdm15Um45M21OX19wOGlzT2lVR29mNlRobDEzZlc5MGZScXRuTT0iLCJkaXNwbGF5X25hbWUiOiJCQUtBUkUgUkFNQUNIQU5EUkEgUkFPIEdFRVRIQSIsIm9tcyI6IksxIiwiaHNtX2tleSI6IjI5Yzg1NGYwYTJmMDAyNDJjNjUxZjQzM2VlODI1ZGYyNTUxNWNmY2JhNjg1MjMwMDE1NTVmYmYyIiwiaXNEZHBpRW5hYmxlZCI6Ik4iLCJpc010ZkVuYWJsZWQiOiJOIiwiZnlfaWQiOiJYQjEwMTE2IiwiYXBwVHlwZSI6MTAwLCJwb2FfZmxhZyI6Ik4ifQ.Fu2Idof1P9MVEI4AUqKj64OaQiksfenUatjzHQeybwM";




const chartProperties = {
  timeScale: {
    timeVisible: true,
    secondsVisible: false,
    fixLeftEdge: true,
    borderVisible: false,
  },
  crosshair: {
    mode: LightweightCharts.CrosshairMode.None, // Disables the crosshair lines
    vertLine: {
      visible: true, // Hides the vertical line
      labelVisible: true, // Hides the vertical line labelnod
    },
    horzLine: {
      visible: true, // Hides the horizontal line
      labelVisible: true, // Hides the horizontal line label
    },
  },
};
const domElement = document.getElementById("tvchart");
const chart = LightweightCharts.createChart(domElement, {
  width: domElement.clientWidth,
  height: domElement.clientHeight,
});

console.log("Chart object:", chart);
// const candleSeries = chart.addCandlestickSeries();
const hoverInfo = document.getElementById("hover-info");
const spinner = document.getElementById("spinner");

let currentOHLC = {};
// Function to resize the chart
function resizeChart() {
  chart.resize(domElement.clientWidth, domElement.clientHeight);
}

// Resize the chart initially
resizeChart();

// Use ResizeObserver to detect size changes
const resizeObserver = new ResizeObserver(() => {
  resizeChart();
});

// Start observing the container
resizeObserver.observe(domElement);

// Optionally: Handle window resize event as a fallback
window.addEventListener("resize", resizeChart);

// Helper function to parse date-time string to Unix timestamp in seconds
function parseDateTimeToUnix(dateTime) {
  const [datePart, timePart] = dateTime.split(" ");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute, second] = timePart.split(":").map(Number);
  const date = new Date(year, month - 1, day, hour, minute, second);
  const offset = 5 * 60 * 60 * 1000 + 30 * 60 * 1000;
  const newDate = new Date(date.getTime() + offset);
  return Math.floor(newDate.getTime() / 1000);
}

function showSpinner() {
  spinner.style.display = "block";
}

function hideSpinner() {
  spinner.style.display = "none";
}
// Function to fetch and process data from backend
const candleSeries = chart.addCandlestickSeries({
  upColor: "#26a69a",
  downColor: "#ef5350",
  borderVisible: true,
  wickVisible: true,
  scaleMargins: {
    top: 0.2,
    bottom: 0.3, // Increase bottom margin to separate from volume bars
  },
});

const volumeSeries = chart.addHistogramSeries({
  color: "#90caf9",
  priceFormat: {
    type: "volume",
  },
  priceScaleId: "volume", // Use a separate price scale for volume
  scaleMargins: {
    top: 0,
    bottom: 0,
  },
});

chart.priceScale("volume").applyOptions({
  scaleMargins: {
    top: 0.8, // Increase top margin to separate from candlesticks
    bottom: 0,
  },
});

async function fetchData(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/stock-data?symbol=${symbol}&interval=${interval}`
    );
    const data = await response.json();

    // Process candlestick data
    const cdata = data.map((d) => ({
      time: parseDateTimeToUnix(d.Date),
      open: parseFloat(d.Open),
      high: parseFloat(d.High),
      low: parseFloat(d.Low),
      close: parseFloat(d.Close),
    }));

    // Log candlestick data for debugging
    console.log("Candlestick Data:", cdata);

    // Set candlestick data to the chart
    candleSeries.setData(cdata);
    // Check if volume data is present
    if (data.some((d) => d.Volume !== undefined && d.Volume !== null)) {
      const volumeData = data
        .map((d) => ({
          time: parseDateTimeToUnix(d.Date),
          value: d.Volume !== undefined ? parseFloat(d.Volume) : 0,
          color: d.Close >= d.Open ? "#66cdaa" : "#f4a6a6",
        }))
        .filter((d) => d.value > 0); // Exclude volume data with value 0

      // Check if filtered volume data exists
      if (volumeData.length > 0) {
        // Log filtered volume data
        console.log("Filtered Volume Data:", volumeData);

        // Set filtered volume data to the chart
        volumeSeries.setData(volumeData);
      } else {
        console.warn("Filtered volume data is empty. Nothing to draw.");
      }
    } else {
      console.warn("Volume data is not available for this stock.");
    }

    hideSpinner();

    // Ensure the refresh happens only after data has been loaded
    triggerRefresh();

    return cdata[cdata.length - 1];
  } catch (error) {
    console.error("Error fetching data:", error);
    hideSpinner();
  }
}


// Function to trigger the refresh
function triggerRefresh() {
  const refreshButton = document.getElementById("refresh-button");
  if (refreshButton) {
    refreshButton.click(); // Simulate a click on the refresh button
    // console.log("Refresh button clicked");
  }
}

async function selectStock(row) {
  // Clear the selected class from previous stock
  var rows = document.getElementsByClassName("stock-row");
  for (var i = 0; i < rows.length; i++) {
    rows[i].classList.remove("selected");
  }

  volumeSeries.setData([]); // Clear volume data when changing stocks


  // Set the selected stock row
  row.classList.add("selected");
  var stockName = row.getElementsByTagName("td")[0].innerText;
  document.getElementById("selected-stock").textContent = stockName;

  // Clear the selected pattern options when stock changes
  const options = document.querySelectorAll(".option");
  options.forEach((option) => {
    option.classList.remove("selected");
  });

  // Get values from the selected row, handle missing data
  const lastPrice = row.querySelector(".last-price")
    ? row.querySelector(".last-price").innerText
    : "--";
  const change = row.querySelector(".change")
    ? row.querySelector(".change").innerText
    : "--";
  const changePercentage = row.querySelector(".change-percentage")
    ? row.querySelector(".change-percentage").innerText
    : "--";

  // Update the display area with the selected stock's information
  document.getElementById("last-price").textContent = lastPrice;
  document.getElementById("change").textContent = change;
  document.getElementById("change-percentage").textContent = changePercentage;

  selectedOptions = [];

  // Reset the parallel channel button appearance
  const parallelChannelBtn = document.getElementById("parallel-channel-btn");
  parallelChannelBtn.classList.remove("active"); // Remove 'active' class

  // Unsubscribe from the live data of the previous stock
  const symbol = row.getAttribute("data-symbol");
  skt.unsubscribe([symbol], false, 1); // Unsubscribe previous stock live data

  // // Fetch data for the selected stock
  const interval = document.getElementById("interval-select").value;

  // Fetch data for the selected stock and interval
  const lastCandle = await fetchData(symbol, interval); // One call to fetchData

  // Check if lastCandle exists and stock data is fetched properly
  if (lastCandle) {
    // Remove all previous chart series (patterns) for the old stock

    clearAllPatterns(); // Clear all patterns
    // Clear all previous OHLC data
    currentOHLC = {}; // Ensure old OHLC data is reset for the new stock

    // Store the latest OHLC data for the current stock
    currentOHLC[lastCandle.time] = lastCandle;
    console.log(currentOHLC[lastCandle.time]);
    console.log(lastCandle);

    // Update the subscription for live data
    skt.subscribe([symbol], false, 1);
  } else {
    console.error("Error fetching stock data. No last candle found.");
  }
  // Ensure no patterns are drawn after stock change, until user reselects them
}

function clearAllPatterns() {
  srLineSeries.forEach((series) => chart.removeSeries(series));
  srLineSeries = [];
  trendlineSeries.forEach((series) => chart.removeSeries(series));
  trendlineSeries = [];
  angleMarkers.forEach((marker) => chart.removeSeries(marker));
  angleMarkers = [];
  parallelChannelSeries.forEach((series) => chart.removeSeries(series));
  parallelChannelSeries = [];
  morningStarMarkers.forEach((series) => chart.removeSeries(series));
  morningStarMarkers = [];
  eveningStarMarkers.forEach((series) => chart.removeSeries(series));
  eveningStarMarkers = [];
  triangleSeries.forEach((series) => chart.removeSeries(series));
  triangleSeries = [];
  angleeMarkers.forEach((series) => chart.removeSeries(series));
  angleeMarkers = [];
  ibars.forEach((series) => chart.removeSeries(series));
  ibars = [];
  vShapes.forEach((series) => chart.removeSeries(series));
  vShapes = [];
  headAndShoulders.forEach((series) => chart.removeSeries(series));
  headAndShoulders = [];
  doubleTops.forEach((series) => chart.removeSeries(series));
  doubleTops = [];
  doubleBottoms.forEach((series) => chart.removeSeries(series));
  doubleBottoms = [];
  cupAndHandle.forEach((series) => chart.removeSeries(series));
  cupAndHandle = [];
  zones.forEach((series) => chart.removeSeries(series));
  zones = [];
  zoneLabels.forEach((series) => chart.removeSeries(series));
  zoneLabels = [];
  Object.values(emaSeries).forEach((series) => chart.removeSeries(series));
  emaSeries = {};
  darvasBoxes.forEach((series) => chart.removeSeries(series));
  darvasBoxes = [];
  bollingerBandsSeries.forEach((series) => chart.removeSeries(series));
  bollingerBandsSeries = [];
  consecutiveGreenMarkers.forEach((marker) => chart.removeSeries(marker));
  consecutiveRedMarkers.forEach((marker) => chart.removeSeries(marker));
  consecutiveGreenMarkers = [];
  consecutiveRedMarkers = [];
  donchianChannelSeries.forEach((series) => chart.removeSeries(series));
  donchianChannelSeries = [];
}

let emaSeries = {}; // To track EMA lines
let isEmaLoaded = false; // To track whether EMA is loaded

// Fetch and draw EMA data
async function fetchAndDrawEma(symbol, interval) {
  showSpinner();
  try {
    const periodsInput = document.getElementById("ema-periods").value;
    const periods = periodsInput
      .split(",")
      .map(Number)
      .filter((n) => !isNaN(n) && n > 0);

    if (periods.length === 0) {
      alert("Please enter valid EMA periods.");
      hideSpinner();
      return;
    }

    const periodsParam = periods.join(",");
    const response = await fetch(
      `/ema-series?symbol=${symbol}&interval=${interval}&periods=${periodsParam}`
    );
    const emaData = await response.json();

    // Clear existing EMA series
    Object.values(emaSeries).forEach((series) => chart.removeSeries(series));
    emaSeries = {}; // Reset emaSeries

    const colors = ["blue", "green", "red", "purple", "orange", "yellow"];
    const shiftAmount = 1 * 335; // Adjust shift as needed

    periods.forEach((period, index) => {
      const emaKey = `EMA${period}`;
      const emaPlotData = emaData.map((point) => ({
        time: Math.floor(new Date(point.Date).getTime() / 1000) - shiftAmount,
        value: point[emaKey],
      }));

      emaSeries[emaKey] = chart.addLineSeries({
        color: colors[index % colors.length],
        lineWidth: 1,
        lastValueVisible: false,
        priceLineVisible: false,
      });

      emaSeries[emaKey].setData(emaPlotData);
    });

    // Disable the dropdown after loading EMA
    document.getElementById("ema-dropdown").style.display = "none";
    isEmaLoaded = true;

    hideSpinner();
  } catch (error) {
    console.error("Error fetching EMA data:", error);
    hideSpinner();
  }
}

// Toggle dropdown visibility and handle reset
function toggleDropdown() {
  const emaDropdown = document.getElementById("ema-dropdown");
  const emaButton = document.getElementById("submitema"); // Reference to the button

  if (isEmaLoaded) {
    // Remove EMA lines and reset state
    Object.values(emaSeries).forEach((series) => chart.removeSeries(series));
    emaSeries = {};
    isEmaLoaded = false;

    emaButton.classList.remove("active");

    // alert("Previous EMA lines have been removed.");
  } else {
    // Toggle dropdown visibility
    if (
      emaDropdown.style.display === "none" ||
      emaDropdown.style.display === ""
    ) {
      emaDropdown.style.display = "block";
    } else {
      emaDropdown.style.display = "none";
    }
    // Ensure button enters active state only when EMA is loaded
    emaButton.classList.add("active");
  }
}

handlePatternButtonClick("submitema", fetchAndDrawEma);

let srLineSeries = [];

async function fetchAndDrawSupportResistance(
  symbol,
  interval,
  isDefault = true
) {
  showSpinner();
  try {
    const nsr = document.getElementById("num-sr-lines").value;
    const startDateInput = document.getElementById("sr-date");
    let startDate = startDateInput.value;
    const errorMsgElement = document.getElementById("sr-error-msg");
    const groupSize = 1400;

    errorMsgElement.textContent = "";

    if (startDate) {
      const enteredDate = new Date(startDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      if (enteredDate > today) {
        errorMsgElement.textContent = "Enter a valid date.";
        hideSpinner();
        return;
      }
    }

    let response;
    if (isDefault) {
      response = await fetch(
        `/support-resistance?symbol=${symbol}&interval=${interval}&nsr=${nsr}&group_size=${groupSize}`
      );
    } else {
      if (startDate) {
        response = await fetch(
          `/support-resistance?symbol=${symbol}&interval=${interval}&nsr=${nsr}&start_date=${startDate}`
        );
      } else {
        response = await fetch(
          `/support-resistance?symbol=${symbol}&interval=${interval}&nsr=${nsr}&group_size=${groupSize}`
        );
      }
    }

    if (!response.ok) {
      throw new Error("Failed to fetch SR lines");
    }

    const srGroups = await response.json();

    srLineSeries.forEach((series) => chart.removeSeries(series));
    srLineSeries = [];

    const color = !isDefault && startDate ? "black" : null;

    srGroups.forEach((group, index) => {
      const groupColor = color || ["black", "blue", "green"][index % 3];
      const { start_date, end_date, sr_lines } = group;

      const startTime = parseDateTimeToUnix(start_date);
      const endTime = parseDateTimeToUnix(end_date) || Date.now();

      sr_lines.forEach((level) => {
        const horizontalLineData = [
          { time: startTime, value: level },
          { time: endTime, value: level },
        ];

        const lineSeries = chart.addLineSeries({
          color: groupColor,
          lineWidth: 1,
          priceLineVisible: false,
        });

        lineSeries.setData(horizontalLineData);
        srLineSeries.push(lineSeries);
      });
    });

    hideSpinner();
  } catch (error) {
    console.error(error);
    hideSpinner();
    document.getElementById("sr-error-msg").textContent =
      "Error fetching SR lines.";
  }
}

// Helper function to parse datetime string to Unix timestamp
let trendlineSeries = [];
let angleMarkers = [];
let parallelChannelSeries = [];
let trendlinesVisible = false; // Flag for trendlines
let parallelChannelsVisible = false; // Flag for parallel channels

async function fetchAndDrawTrendLines(symbol, interval, mode) {
  showSpinner();
  try {
    const response = await fetch(
      `/trend-lines?symbol=${symbol}&interval=${interval}&mode=${mode}`
    );
    const lineData = await response.json();

    console.log(`Received ${mode} data:`, lineData);

    // Determine whether we're drawing trendlines or parallel channels
    const isTrendLines = mode === "trend_lines";

    // Clear existing lines
    if (isTrendLines) {
      trendlineSeries.forEach((series) => chart.removeSeries(series));
      angleMarkers.forEach((marker) => chart.removeSeries(marker));
      trendlineSeries = [];
      angleMarkers = [];
    } else {
      parallelChannelSeries.forEach((series) => chart.removeSeries(series));
      parallelChannelSeries = [];
      angleMarkers.forEach((marker) => chart.removeSeries(marker));

      angleMarkers = [];
    }

    lineData.forEach((line, index) => {
      let [x0, y0, x1, y1, colorCode, angle] = line;
      let x0Unix = parseDateTimeToUnix(x0);
      let x1Unix = parseDateTimeToUnix(x1);

      if (x0Unix === null || x1Unix === null) {
        console.error(`Invalid date conversion for line ${index}:`, line);
        return;
      }

      const linecolor = colorCode === 1 ? "green" : "red";

      // Ensure x0 is always the earlier time
      if (x0Unix > x1Unix) {
        [x0Unix, x1Unix] = [x1Unix, x0Unix];
        [y0, y1] = [y1, y0];
      }

      try {
        const lineSeries = chart.addLineSeries({
          color: linecolor,
          lineWidth: 1,
          priceLineVisible: false,
        });

        lineSeries.setData([
          { time: x0Unix, value: parseFloat(y0) },
          { time: x1Unix, value: parseFloat(y1) },
        ]);

        if (isTrendLines) {
          trendlineSeries.push(lineSeries);
          console.log(`Added trendline series for line ${index}`);

          // Add angle marker for trendlines
          const midTime = Math.floor((x0Unix + x1Unix) / 2);
          const midPrice = (parseFloat(y0) + parseFloat(y1)) / 2;

          const angleMarker = chart.addLineSeries({
            color: linecolor,
            lineWidth: 0,
            lastValueVisible: false,
            priceLineVisible: false,
          });

          angleMarker.setData([{ time: midTime, value: midPrice }]);
          angleMarker.setMarkers([
            {
              time: midTime,
              position: "inBar",
              color: linecolor,
              shape: "circle",
              text: `${angle.toFixed(2)}°`,
            },
          ]);
          angleMarkers.push(angleMarker);
          console.log(`Added angle marker for line ${index}`);
        } else {
          parallelChannelSeries.push(lineSeries);
          console.log(`Added parallel channel series for line ${index}`);

          // Add angle marker for parallel channels
          const midTime = Math.floor((x0Unix + x1Unix) / 2);
          const midPrice = (parseFloat(y0) + parseFloat(y1)) / 2;

          const angleMarker = chart.addLineSeries({
            color: linecolor,
            lineWidth: 0,
            lastValueVisible: false,
            priceLineVisible: false,
          });

          angleMarker.setData([{ time: midTime, value: midPrice }]);
          angleMarker.setMarkers([
            {
              time: midTime,
              position: "inBar",
              color: linecolor,
              shape: "circle",
              text: `${angle.toFixed(2)}°`,
            },
          ]);
          angleMarkers.push(angleMarker);
          console.log(`Added angle marker for parallel channel ${index}`);
        }
      } catch (error) {
        console.error(`Error adding series for line ${index}:`, error);
      }
    });

    hideSpinner();
  } catch (error) {
    console.error(`Error fetching or processing ${mode}:`, error);
    hideSpinner();
  }
}

// Toggle function for both trendlines and parallel channels
// Toggle function for both trendlines and parallel channels
function toggleLines(mode) {
  const selectedRow = document.querySelector(".stock-row.selected");
  if (selectedRow) {
    const symbol = selectedRow.getAttribute("data-symbol");
    const interval = document.getElementById("interval-select").value;

    if (mode === "trend_lines") {
      if (!trendlinesVisible) {
        // Disable parallel channels if they are currently visible
        if (parallelChannelsVisible) {
          parallelChannelSeries.forEach((series) => chart.removeSeries(series));
          parallelChannelSeries = [];
          parallelChannelsVisible = false;
          console.log("Parallel channels removed");
        }

        // Fetch and draw trendlines
        fetchAndDrawTrendLines(symbol, interval, mode);
        trendlinesVisible = true;
      } else {
        // Remove trendlines if they are currently visible
        trendlineSeries.forEach((series) => chart.removeSeries(series));
        angleMarkers.forEach((marker) => chart.removeSeries(marker));
        trendlineSeries = [];
        angleMarkers = [];
        trendlinesVisible = false;
        console.log("Trendlines removed");
      }
    } else if (mode === "parallel_channels") {
      if (!parallelChannelsVisible) {
        // Disable trendlines if they are currently visible
        if (trendlinesVisible) {
          trendlineSeries.forEach((series) => chart.removeSeries(series));
          angleMarkers.forEach((marker) => chart.removeSeries(marker));
          trendlineSeries = [];
          angleMarkers = [];
          trendlinesVisible = false;
          console.log("Trendlines removed");
        }

        // Fetch and draw parallel channels
        fetchAndDrawTrendLines(symbol, interval, mode);
        parallelChannelsVisible = true;
      } else {
        // Remove parallel channels if they are currently visible
        parallelChannelSeries.forEach((series) => chart.removeSeries(series));
        parallelChannelSeries = [];
        angleMarkers.forEach((marker) => chart.removeSeries(marker)); // Clear angle markers for parallel channels

        angleMarkers = [];
        parallelChannelsVisible = false;
        console.log("Parallel channels removed");
      }
    }
  }
}

// Event listeners for trendlines and parallel channels
document.getElementById("trlines-btn").addEventListener("click", function () {
  // Toggle the active state for the clicked button
  this.classList.toggle("active");

  // Remove active state from the other button
  document.getElementById("parallel-channel-btn").classList.remove("active");

  // Call your existing function
  toggleLines("trend_lines");
});

document
  .getElementById("parallel-channel-btn")
  .addEventListener("click", function () {
    // Toggle the active state for the clicked button
    this.classList.toggle("active");

    // Remove active state from the other button
    document.getElementById("trlines-btn").classList.remove("active");

    // Call your existing function
    toggleLines("parallel_channels");
  });

let ibars = [];

// Fetch and draw consecutive inside bars
async function fetchAndDrawIbars(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/inside-bars?symbol=${symbol}&interval=${interval}`
    );
    const ibarsData = await response.json();

    // Clear existing inside bar series
    ibars.forEach((series) => chart.removeSeries(series));
    ibars = [];

    ibarsData.forEach((line) => {
      let { x0, y0, x1, y1 } = line;

      let x0Unix = parseDateTimeToUnix(x0);
      let x1Unix = parseDateTimeToUnix(x1);

      if (x0Unix === null || x1Unix === null) {
        console.error("Invalid date conversion for:", line);
        return;
      }

      // Ensure (x0, y0) is to the left of (x1, y1)
      if (x0Unix > x1Unix) {
        [x0Unix, x1Unix] = [x1Unix, x0Unix];
        [y0, y1] = [y1, y0];
      }

      // Define the rectangle series using LineSeries
      const rectangleSeries = chart.addLineSeries({
        color: "rgba(0, 150, 136, 0.6)", // Semi-transparent color
        lineWidth: 2,
        priceLineVisible: false,
      });

      // Draw rectangle using four lines
      const rectangleData = [
        { time: x0Unix, value: y0 }, // Bottom left
        { time: x1Unix, value: y0 }, // Bottom right
        { time: x1Unix, value: y1 }, // Top right
        { time: x0Unix, value: y1 }, // Top left
        { time: x0Unix, value: y0 }, // Close the rectangle
      ];

      rectangleSeries.setData(rectangleData);

      ibars.push(rectangleSeries);
    });

    hideSpinner();
  } catch (error) {
    console.error("Error:", error);
    hideSpinner();
  }
}

let vShapes = [];

// Fetch and draw V-shape patterns
async function fetchAndDrawVShapes(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/v-shape-patterns?symbol=${symbol}&interval=${interval}`
    );
    const vShapesData = await response.json();

    // Clear existing V-shape series
    vShapes.forEach((series) => chart.removeSeries(series));
    vShapes = [];

    vShapesData.forEach((shape) => {
      const { x0, y0, x1, y1, x2, y2 } = shape;

      const x0Unix = parseDateTimeToUnix(x0);
      const x1Unix = parseDateTimeToUnix(x1);
      const x2Unix = parseDateTimeToUnix(x2);

      if (x0Unix === null || x1Unix === null || x2Unix === null) {
        console.error("Invalid date conversion for:", shape);
        return;
      }

      // Define the line series for the V-shape pattern
      const vShapeSeries = chart.addLineSeries({
        color: "blue",
        lineWidth: 2,
        priceLineVisible: false,
      });

      // Draw V-shape using three lines
      const vShapeData = [
        { time: x0Unix, value: y0 },
        { time: x1Unix, value: y1 },
        { time: x2Unix, value: y2 },
      ];

      vShapeSeries.setData(vShapeData);

      vShapes.push(vShapeSeries);
    });

    hideSpinner();
  } catch (error) {
    console.error("Error:", error);
    hideSpinner();
  }
}

let bollingerBandsSeries = [];
let isBollingerBandsActive = false;

async function fetchAndDrawBollingerBands(symbol, interval) {
  // Toggle state
  isBollingerBandsActive = !isBollingerBandsActive;

  if (isBollingerBandsActive) {
    // First click: Fetch and draw Bollinger Bands
    showSpinner();
    try {
      const response = await fetch(
        `/Bollinger_bands?symbol=${symbol}&interval=${interval}`
      );
      const bollingerData = await response.json();

      // Clear existing Bollinger Bands series (if any)
      bollingerBandsSeries.forEach((series) => chart.removeSeries(series));
      bollingerBandsSeries = [];

      // Create series for Middle, Upper, and Lower Bands
      const middleBandSeries = chart.addLineSeries({
        color: "green",
        lineWidth: 1,
        priceLineVisible: false,
      });

      const upperBandSeries = chart.addLineSeries({
        color: "rgba(255, 0, 0, 0.5)",
        lineWidth: 1,
        priceLineVisible: false,
      });

      const lowerBandSeries = chart.addLineSeries({
        color: "rgba(0, 0, 255, 0.5)",
        lineWidth: 1,
        priceLineVisible: false,
      });

      // Convert data to chart format
      const middleBandData = bollingerData.map((d) => ({
        time: parseDateTimeToUnix(d.Date),
        value: d.Middle_Band,
      }));

      const upperBandData = bollingerData.map((d) => ({
        time: parseDateTimeToUnix(d.Date),
        value: d.Upper_Band,
      }));

      const lowerBandData = bollingerData.map((d) => ({
        time: parseDateTimeToUnix(d.Date),
        value: d.Lower_Band,
      }));

      // Set data for each series
      middleBandSeries.setData(middleBandData);
      upperBandSeries.setData(upperBandData);
      lowerBandSeries.setData(lowerBandData);

      // Store series for potential later removal
      bollingerBandsSeries.push(
        middleBandSeries,
        upperBandSeries,
        lowerBandSeries
      );

      console.log("Bollinger Bands activated and displayed on chart.");
      hideSpinner();
    } catch (error) {
      console.error("Error fetching Bollinger Bands:", error);
      hideSpinner();
      isBollingerBandsActive = false; // Reset state if fetch fails
    }
  } else {
    // Second click: Remove Bollinger Bands from the chart
    bollingerBandsSeries.forEach((series) => {
      try {
        chart.removeSeries(series);
      } catch (error) {
        console.error("Error removing series:", error);
      }
    });

    // Explicitly clear the array
    bollingerBandsSeries = [];

    console.log("Bollinger Bands deactivated and removed from chart.");
  }
}

// Attach the function to the button
handlePatternButtonClick("bolingerbandButton", fetchAndDrawBollingerBands);

let tripleTopShapes = [];

// Fetch and draw Triple Top/Bottom patterns
async function fetchAndDrawTripleTops(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/tripletops?symbol=${symbol}&interval=${interval}`
    );
    const tripleTopsData = await response.json();

    // Clear existing Triple Top series
    tripleTopShapes.forEach((series) => chart.removeSeries(series));
    tripleTopShapes = [];

    tripleTopsData.forEach((pattern) => {
      const { x0, y0, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6 } =
        pattern;

      // Convert dates to Unix timestamps
      const x0Unix = parseDateTimeToUnix(x0);
      const x1Unix = parseDateTimeToUnix(x1);
      const x2Unix = parseDateTimeToUnix(x2);
      const x3Unix = parseDateTimeToUnix(x3);
      const x4Unix = parseDateTimeToUnix(x4);
      const x5Unix = parseDateTimeToUnix(x5);
      const x6Unix = parseDateTimeToUnix(x6);

      if (
        [x0Unix, x1Unix, x2Unix, x3Unix, x4Unix, x5Unix, x6Unix].includes(null)
      ) {
        console.error("Invalid date conversion for:", pattern);
        return;
      }

      // Define line series for each segment in the Triple Top pattern
      const tripleTopSeries = chart.addLineSeries({
        color: "red",
        lineWidth: 2,
        priceLineVisible: false,
      });

      // Draw Triple Top pattern using multiple line segments
      const tripleTopData = [
        { time: x0Unix, value: y0 },
        { time: x1Unix, value: y1 },
        { time: x2Unix, value: y2 },
        { time: x3Unix, value: y3 },
        { time: x4Unix, value: y4 },
        { time: x5Unix, value: y5 },
        { time: x6Unix, value: y6 },
      ];

      tripleTopSeries.setData(tripleTopData);
      tripleTopShapes.push(tripleTopSeries);
    });

    hideSpinner();
  } catch (error) {
    console.error("Error:", error);
    hideSpinner();
  }
}

handlePatternButtonClick("triple-tops-btn", fetchAndDrawTripleTops);

let darvasBoxes = [];

async function fetchAndDrawDarvasBoxes(symbol, interval) {
  showSpinner();
  try {
    // Fetch Darvas box data
    const response = await fetch(
      `/darvas-box?symbol=${symbol}&interval=${interval}`
    );
    const darvasBoxData = await response.json();

    // Clear existing boxes
    darvasBoxes.forEach((series) => chart.removeSeries(series));
    darvasBoxes = [];

    // Draw Darvas boxes
    darvasBoxData.forEach((box) => {
      const { x0, x1, y0, y1 } = box;

      let startUnix = parseDateTimeToUnix(x0);
      let endUnix = parseDateTimeToUnix(x1);

      if (startUnix === null || endUnix === null) {
        console.error("Invalid date conversion for Darvas box:", box);
        return;
      }

      // Create top line
      const topLine = chart.addLineSeries({
        color: "rgba(75, 192, 192, 0.6)", // Semi-transparent teal color
        lineWidth: 2,
        priceLineVisible: false,
      });

      // Create bottom line
      const bottomLine = chart.addLineSeries({
        color: "rgba(75, 192, 192, 0.6)",
        lineWidth: 2,
        priceLineVisible: false,
      });

      // Create left vertical line
      const leftLine = chart.addLineSeries({
        color: "rgba(75, 192, 192, 0.6)",
        lineWidth: 2,
        priceLineVisible: false,
      });

      // Create right vertical line
      const rightLine = chart.addLineSeries({
        color: "rgba(75, 192, 192, 0.6)",
        lineWidth: 2,
        priceLineVisible: false,
      });

      // Set data for horizontal lines (top and bottom)
      const topData = [
        { time: startUnix, value: y1 },
        { time: endUnix, value: y1 },
      ];
      topLine.setData(topData);

      const bottomData = [
        { time: startUnix, value: y0 },
        { time: endUnix, value: y0 },
      ];
      bottomLine.setData(bottomData);

      // Set data for vertical lines (left and right)
      const leftData = [
        { time: startUnix, value: y0 },
        { time: startUnix, value: y1 },
      ];
      leftLine.setData(leftData);

      const rightData = [
        { time: endUnix, value: y0 },
        { time: endUnix, value: y1 },
      ];
      rightLine.setData(rightData);

      // Store all lines for the box
      darvasBoxes.push(topLine);
      darvasBoxes.push(bottomLine);
      darvasBoxes.push(leftLine);
      darvasBoxes.push(rightLine);
    });

    // Make the boxes adjustable
    makeLineAdjustable(chart, darvasBoxes);
    hideSpinner();
  } catch (error) {
    console.error("Error fetching/drawing Darvas boxes:", error);
    hideSpinner();
  }
}
function makeLineAdjustable(chart, lines) {
  let isDragging = false;
  let selectedLine = null;
  let initialY = null;

  chart.subscribeClick((param) => {
    if (!param.point) return;

    const price = param.point.y;
    const time = param.time;

    lines.forEach((line) => {
      const lineData = line.getData();
      lineData.forEach((point) => {
        if (Math.abs(point.value - price) < 5) {
          selectedLine = line;
          initialY = price;
          isDragging = true;
        }
      });
    });
  });

  chart.subscribeCustomPriceLineDrag((param) => {
    if (isDragging && selectedLine) {
      const newY = param.price;
      const deltaY = newY - initialY;

      const lineData = selectedLine.getData();
      const updatedData = lineData.map((point) => ({
        time: point.time,
        value: point.value + deltaY,
      }));

      selectedLine.setData(updatedData);
      initialY = newY;
    }
  });

  chart.subscribeCrosshairMove(() => {
    if (!isDragging) {
      selectedLine = null;
    }
  });
}

function makeLinesAdjustable(chart, lineSeriesArray) {
  lineSeriesArray.forEach((lineSeries) => {
    const data = lineSeries.data();

    data.forEach((point, pointIndex) => {
      // Marker for user to click on to adjust points
      const marker = {
        time: point.time,
        position: "inBar",
        color: "blue",
        shape: "circle",
        size: 1,
      };

      // Set markers on the line points
      lineSeries.setMarkers([marker]);

      // Listen for click events on the chart
      chart.subscribeClick((param) => {
        // Check if user clicked near a point (within a certain threshold)
        if (
          Math.abs(param.time - point.time) < 300000 && // Within 5 minutes of the point
          Math.abs(param.price - point.value) <
            chart.priceScale().height() * 0.01 // Within 1% of the price scale height
        ) {
          let isDragging = true;

          // Handle the mouse movement when dragging
          const mouseMoveHandler = (e) => {
            if (isDragging) {
              // Convert mouse coordinates to time and price
              const price = chart
                .priceScale()
                .coordinateToPrice(e.clientY, chart.priceScale().id());
              const logical = chart.timeScale().coordinateToLogical(e.clientX);
              const time = chart.timeScale().logicalToCoordinate(logical);

              // Update the dragged point's position
              data[pointIndex] = { time: time, value: price };
              lineSeries.setData(data);

              // If dragging the last point, don't update the next one
              if (pointIndex < data.length - 1) {
                data[pointIndex + 1].time = time;
              }

              // If dragging the first point, don't update the previous one
              if (pointIndex > 0) {
                data[pointIndex - 1].time = time;
              }

              lineSeries.setData(data);
            }
          };

          // Stop dragging when the mouse is released
          const mouseUpHandler = () => {
            isDragging = false;
            document.removeEventListener("mousemove", mouseMoveHandler);
            document.removeEventListener("mouseup", mouseUpHandler);
          };

          // Add event listeners for dragging and releasing
          document.addEventListener("mousemove", mouseMoveHandler);
          document.addEventListener("mouseup", mouseUpHandler);
        }
      });
    });
  });
}

let doubleTops = [];
let doubleBottoms = [];

// Unified function to fetch and draw both double tops and double bottoms
async function fetchAndDrawPatterns(symbol, interval) {
  showSpinner();
  try {
    // Fetch data for both patterns simultaneously
    const [doubleTopsResponse, doubleBottomsResponse] = await Promise.all([
      fetch(`/double-top?symbol=${symbol}&interval=${interval}`),
      fetch(`/double-bottoms?symbol=${symbol}&interval=${interval}`),
    ]);

    // Parse the responses
    const doubleTopsData = await doubleTopsResponse.json();
    const doubleBottomsData = await doubleBottomsResponse.json();

    // Clear existing series for both patterns
    doubleTops.forEach((series) => chart.removeSeries(series));
    doubleTops = [];
    doubleBottoms.forEach((series) => chart.removeSeries(series));
    doubleBottoms = [];

    // Draw double tops
    doubleTopsData.forEach((line) => {
      const { x0, y0, x1, y1, x2, y2, x3, y3, x4, y4 } = line;

      let x0Unix = parseDateTimeToUnix(x0);
      let x1Unix = parseDateTimeToUnix(x1);
      let x2Unix = parseDateTimeToUnix(x2);
      let x3Unix = parseDateTimeToUnix(x3);
      let x4Unix = parseDateTimeToUnix(x4);

      if (
        x0Unix === null ||
        x1Unix === null ||
        x2Unix === null ||
        x3Unix === null ||
        x4Unix === null
      ) {
        console.error("Invalid date conversion for double tops:", line);
        return;
      }

      const doubleTopSeries = chart.addLineSeries({
        color: "rgba(0, 0, 255, 0.6)", // Semi-transparent blue color for double top
        lineWidth: 2,
        priceLineVisible: false,
      });

      const doubleTopData = [
        { time: x0Unix, value: y0 },
        { time: x1Unix, value: y1 },
        { time: x2Unix, value: y2 },
        { time: x3Unix, value: y3 },
        { time: x4Unix, value: y4 },
      ];

      doubleTopSeries.setData(doubleTopData);
      doubleTops.push(doubleTopSeries);
    });

    // Draw double bottoms
    doubleBottomsData.forEach((line) => {
      const { x0, y0, x1, y1, x2, y2, x3, y3, x4, y4 } = line;

      let x0Unix = parseDateTimeToUnix(x0);
      let x1Unix = parseDateTimeToUnix(x1);
      let x2Unix = parseDateTimeToUnix(x2);
      let x3Unix = parseDateTimeToUnix(x3);
      let x4Unix = parseDateTimeToUnix(x4);

      if (
        x0Unix === null ||
        x1Unix === null ||
        x2Unix === null ||
        x3Unix === null ||
        x4Unix === null
      ) {
        console.error("Invalid date conversion for double bottoms:", line);
        return;
      }

      const doubleBottomSeries = chart.addLineSeries({
        color: "rgba(0, 0, 0, 0.6)", // Semi-transparent black color for double bottom
        lineWidth: 2,
        priceLineVisible: false,
      });

      const doubleBottomData = [
        { time: x0Unix, value: y0 },
        { time: x1Unix, value: y1 },
        { time: x2Unix, value: y2 },
        { time: x3Unix, value: y3 },
        { time: x4Unix, value: y4 },
      ];

      doubleBottomSeries.setData(doubleBottomData);
      doubleBottoms.push(doubleBottomSeries);
    });

    // After drawing the patterns, make them adjustable
    makeLinesAdjustable(chart, doubleTops);
    makeLinesAdjustable(chart, doubleBottoms);
    hideSpinner();
  } catch (error) {
    console.error("Error fetching/drawing patterns:", error);
    hideSpinner();
  }
} // Initial arrays for storing pattern series
// // Event Listeners for the buttons
document.getElementById("mw-hns-vshape").addEventListener("click", function () {
  const extraOptions = document.getElementById("extra-options");
  extraOptions.classList.toggle("show"); // Toggle the 'show' class
});

let activeButton = null; // Track currently active button

// Function to handle pattern button clicks
function handlePatternButtonClick(buttonId, fetchFunction) {
  document
    .getElementById(buttonId)
    .addEventListener("click", async function (e) {
      const button = e.target;
      const selectedRow = document.querySelector(".stock-row.selected");

      if (selectedRow) {
        const symbol = selectedRow.getAttribute("data-symbol");
        const interval = document.getElementById("interval-select").value;

        // If clicking the same button that's already active
        if (activeButton === button) {
          // Deactivate the button and clear patterns
          button.style.backgroundColor = "";
          button.style.color = "";
          activeButton = null;
          doubleTops.forEach((series) => chart.removeSeries(series));
          doubleTops = [];
          doubleBottoms.forEach((series) => chart.removeSeries(series));
          doubleBottoms = [];
          headAndShoulders.forEach((series) => chart.removeSeries(series));
          headAndShoulders = [];
          ibars.forEach((series) => chart.removeSeries(series));
          ibars = [];
          bollingerBandsSeries.forEach((series) => chart.removeSeries(series));
          bollingerBandsSeries = [];
          Object.values(emaSeries).forEach((series) =>
            chart.removeSeries(series)
          );
          emaSeries = {};

          vShapes.forEach((series) => chart.removeSeries(series));
          vShapes = [];

          darvasBoxes.forEach((series) => chart.removeSeries(series));
          darvasBoxes = [];

          // vcpPatterns.forEach((series) => chart.removeSeries(series));
          // vcpPatterns = [];

          cupAndHandle.forEach((series) => chart.removeSeries(series));
          cupAndHandle = [];

          zones.forEach((series) => chart.removeSeries(series));
          zones = [];
          zoneLabels.forEach((series) => chart.removeSeries(series));
          zoneLabels = [];

          morningStarMarkers.forEach((series) => chart.removeSeries(series));
          morningStarMarkers = [];
          eveningStarMarkers.forEach((series) => chart.removeSeries(series));
          eveningStarMarkers = [];
          donchianChannelSeries.forEach((series) => chart.removeSeries(series));
          donchianChannelSeries = [];
          consecutiveGreenMarkers.forEach((marker) =>
            chart.removeSeries(marker)
          );
          consecutiveRedMarkers.forEach((marker) => chart.removeSeries(marker));
          consecutiveGreenMarkers = [];
          consecutiveRedMarkers = [];
          // Clear your patterns here
          // Example: clearPatterns();
        } else {
          // Reset previous active button if exists
          if (activeButton) {
            activeButton.style.backgroundColor = "hsl(228, 67%, 73%)";
            activeButton.style.color = "";
          }

          // Activate new button
          button.style.backgroundColor = "hsl(228, 67%, 73%)";

          activeButton = button;

          // Fetch and draw new patterns
          await fetchFunction(symbol, interval);
        }
      }
    });
}

document.head.appendChild(style);

// Attach event listeners for both buttons
handlePatternButtonClick("double-tops-btn", fetchAndDrawPatterns);
handlePatternButtonClick("triple-tops-btn", fetchAndDrawVShapes);
handlePatternButtonClick("hns-btn", fetchAndDrawHeadAndShoulders);
handlePatternButtonClick("vshape-btn", fetchAndDrawVShapes);

function handlePatternButtoncupandibar(buttonIdd, fetchFunc) {
  document.getElementById(buttonIdd).addEventListener("click", function () {
    const selectedRow = document.querySelector(".stock-row.selected");
    if (selectedRow) {
      const symbol = selectedRow.getAttribute("data-symbol");
      const interval = document.getElementById("interval-select").value;
      fetchFunc(symbol, interval);
    }
  });
}

// Attach event listeners for both buttons
handlePatternButtonClick("inside-bars", fetchAndDrawIbars);
handlePatternButtonClick("cup-handle", fetchAndDrawCupAndHandle);
handlePatternButtonClick("boxx", fetchAndDrawDarvasBoxes);
// handlePatternButtonClick("vcp", fetchAndDrawVCP);

// Updated zones array and fetch function
let zones = []; // Track each zone's series
let zoneLabels = []; // Track zone label markers

async function fetchAndDrawZones(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/zonespattern?symbol=${symbol}&interval=${interval}`
    );
    const zonesData = await response.json();

    // Clear existing zones and labels
    zones.forEach((series) => chart.removeSeries(series));
    zoneLabels.forEach((label) => chart.removeSeries(label));
    zones = [];
    zoneLabels = [];

    // Group coordinates by day and zone
    const groupedZones = zonesData.reduce((acc, coord) => {
      const key = `${coord.day}-${coord.zone}`;
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(coord);
      return acc;
    }, {});

    // Process each zone box
    Object.values(groupedZones).forEach((zoneCoords) => {
      // Find the top horizontal line coordinates
      const topLine = zoneCoords.find(
        (coord) =>
          coord.type === "horizontal_line" &&
          coord.y0 === Math.max(...zoneCoords.map((c) => c.y0))
      );

      if (!topLine) return;

      // Draw the box lines
      zoneCoords.forEach((coord) => {
        const zoneSeries = chart.addLineSeries({
          color: coord.category >= 4 ? "red" : "blue",
          lineWidth: 2,
          priceLineVisible: false,
        });

        zoneSeries.setData([
          { time: parseDateTimeToUnix(coord.x0), value: coord.y0 },
          { time: parseDateTimeToUnix(coord.x1), value: coord.y1 },
        ]);

        zones.push(zoneSeries);
      });

      // Add label marker series
      const labelSeries = chart.addLineSeries({
        color: topLine.category >= 4 ? "red" : "blue",
        lineWidth: 0,
        lastValueVisible: false,
        priceLineVisible: false,
      });

      // Calculate middle point of top line for label placement
      const midTime = Math.floor(
        (parseDateTimeToUnix(topLine.x0) + parseDateTimeToUnix(topLine.x1)) / 2
      );

      // Create label text with zone name and category
      const volatilityMap = {
        5: "Highly Volatile",
        4: "Good Moves",
        3: "Average Moves",
        2: "Small Moves",
        1: "Very Small Moves",
      };

      const labelText = `${topLine.zone.toUpperCase()} - ${
        volatilityMap[topLine.category]
      }`;

      // Add single data point for marker position
      labelSeries.setData([{ time: midTime, value: topLine.y0 }]);

      // Add marker with label
      labelSeries.setMarkers([
        {
          time: midTime,
          position: "aboveBar",
          color: topLine.category >= 4 ? "red" : "blue",
          shape: "square",
          text: labelText,
        },
      ]);

      zoneLabels.push(labelSeries);
    });

    hideSpinner();
  } catch (error) {
    console.error("Error:", error);
    hideSpinner();
  }
}

handlePatternButtonClick("volatilityButton", fetchAndDrawZones);

let donchianChannelSeries = [];

async function fetchAndDrawDonchianChannel(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/Donchian_channel?symbol=${symbol}&interval=${interval}`
    );
    const donchianData = await response.json();

    // Clear existing Donchian Channel series
    donchianChannelSeries.forEach((series) => chart.removeSeries(series));
    donchianChannelSeries = [];

    // Create series for Middle, Upper, and Lower Bands
    const middleBandSeries = chart.addLineSeries({
      color: "green",
      lineWidth: 1,
      priceLineVisible: false,
    });

    const upperBandSeries = chart.addLineSeries({
      color: "rgba(255, 0, 0, 0.5)",
      lineWidth: 1,
      priceLineVisible: false,
    });

    const lowerBandSeries = chart.addLineSeries({
      color: "rgba(0, 0, 255, 0.5)",
      lineWidth: 1,
      priceLineVisible: false,
    });

    // Convert data to chart format
    const middleBandData = donchianData.map((d) => ({
      time: parseDateTimeToUnix(d.Date),
      value: d.Middle_Band,
    }));

    const upperBandData = donchianData.map((d) => ({
      time: parseDateTimeToUnix(d.Date),
      value: d.Upper_Band,
    }));

    const lowerBandData = donchianData.map((d) => ({
      time: parseDateTimeToUnix(d.Date),
      value: d.Lower_Band,
    }));

    // Set data for each series
    middleBandSeries.setData(middleBandData);
    upperBandSeries.setData(upperBandData);
    lowerBandSeries.setData(lowerBandData);

    // Store series for potential later removal
    donchianChannelSeries.push(
      middleBandSeries,
      upperBandSeries,
      lowerBandSeries
    );

    hideSpinner();
  } catch (error) {
    console.error("Error fetching Donchian Channel:", error);
    hideSpinner();
  }
}
handlePatternButtonClick("dc", fetchAndDrawDonchianChannel);

let headAndShoulders = [];

// Fetch and draw head-and-shoulders patterns
async function fetchAndDrawHeadAndShoulders(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/head-and-shoulders?symbol=${symbol}&interval=${interval}`
    );
    const headAndShouldersData = await response.json();

    // Clear existing head-and-shoulders series
    headAndShoulders.forEach((series) => chart.removeSeries(series));
    headAndShoulders = [];

    headAndShouldersData.forEach((pattern) => {
      let patternData = pattern.map((point) => ({
        time: parseDateTimeToUnix(point.x),
        value: point.y,
      }));

      // Define the line series for the head-and-shoulders pattern
      const headAndShouldersSeries = chart.addLineSeries({
        color: "blue",
        lineWidth: 2,
        priceLineVisible: false,
      });

      headAndShouldersSeries.setData(patternData);

      headAndShoulders.push(headAndShouldersSeries);
    });

    hideSpinner();
  } catch (error) {
    console.error("Error:", error);
    hideSpinner();
  }
}
let morningStarMarkers = [];
let eveningStarMarkers = [];

async function fetchAndDrawMorningEveningStar(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/morning_evening_star?symbol=${symbol}&interval=${interval}`
    );
    const patternData = await response.json();

    const { morning_star: morningStarData, evening_star: eveningStarData } =
      patternData;

    console.log("Received candlestick pattern data:", patternData);

    // Clear existing markers
    morningStarMarkers.forEach((marker) => chart.removeSeries(marker));
    eveningStarMarkers.forEach((marker) => chart.removeSeries(marker));
    morningStarMarkers = [];
    eveningStarMarkers = [];

    // Add Morning Star markers
    morningStarData.forEach((pattern, index) => {
      const time = parseDateTimeToUnix(pattern.date);

      if (time === null) {
        console.error(
          `Invalid date conversion for morning star'${index}:`,
          pattern
        );
        return;
      }

      const marker = chart.addLineSeries({
        color: "green",
        lineWidth: 0,
        lastValueVisible: false,
        priceLineVisible: false,
      });

      marker.setData([{ time, value: parseFloat(pattern.value) }]);

      marker.setMarkers([
        {
          time,
          position: "belowBar",
          color: "green",
          shape: "arrowUp",
          text: "Morning Star",
        },
      ]);

      morningStarMarkers.push(marker);
    });

    // Add Evening Star markers
    eveningStarData.forEach((pattern, index) => {
      const time = parseDateTimeToUnix(pattern.date);

      if (time === null) {
        console.error(
          `Invalid date conversion for evening star ${index}:`,
          pattern
        );
        return;
      }

      const marker = chart.addLineSeries({
        color: "red",
        lineWidth: 0,
        lastValueVisible: false,
        priceLineVisible: false,
      });

      marker.setData([{ time, value: parseFloat(pattern.value) }]);

      marker.setMarkers([
        {
          time,
          position: "aboveBar",
          color: "red",
          shape: "arrowDown",
          text: "Evening Star",
        },
      ]);

      eveningStarMarkers.push(marker);
    });

    hideSpinner();
  } catch (error) {
    console.error("Error fetching or processing candlestick patterns:", error);
    hideSpinner();
  }
}

function parseDateTimeToUnix(dateTime) {
  try {
    const date = new Date(dateTime);
    const offset = 5 * 60 * 60 * 1000 + 30 * 60 * 1000; // 5:30 hour offset
    const newDate = new Date(date.getTime() + offset);

    return Math.floor(newDate.getTime() / 1000);
  } catch (error) {
    console.error("Error parsing date-time:", error);
    return null;
  }
}

// Attach the function to pattern button click
handlePatternButtonClick("morn-even", fetchAndDrawMorningEveningStar);

let consecutiveGreenMarkers = [];
let consecutiveRedMarkers = [];

async function fetchAndDrawConsecutiveCandlePatterns(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/consecutive_candles?symbol=${symbol}&interval=${interval}`
    );
    const patternData = await response.json();

    const {
      consecutive_green_candles: greenCandleData,
      consecutive_red_candles: redCandleData,
    } = patternData;

    console.log("Received consecutive candle pattern data:", patternData);

    // Clear existing markers
    consecutiveGreenMarkers.forEach((marker) => chart.removeSeries(marker));
    consecutiveRedMarkers.forEach((marker) => chart.removeSeries(marker));
    consecutiveGreenMarkers = [];
    consecutiveRedMarkers = [];

    // Add Consecutive Green Candle markers
    greenCandleData.forEach((pattern, index) => {
      const lastDate = pattern.dates[pattern.dates.length - 1];
      const time = parseDateTimeToUnix(lastDate);

      if (time === null) {
        console.error(
          `Invalid date conversion for consecutive green candle ${index}:`,
          pattern
        );
        return;
      }

      // Robust value parsing
      let lastCandleClose = parseFloat(pattern.value);
      if (isNaN(lastCandleClose)) {
        console.error(
          `Invalid numeric value for consecutive green candle ${index}:`,
          pattern.value
        );
        return;
      }

      const marker = chart.addLineSeries({
        color: "green",
        lineWidth: 0,
        lastValueVisible: false,
        priceLineVisible: false,
      });

      marker.setData([{ time, value: lastCandleClose }]);
      marker.setMarkers([
        {
          time,
          position: "belowBar",
          color: "green",
          shape: "arrowUp",
          text: "4+ Green Candles",
        },
      ]);

      consecutiveGreenMarkers.push(marker);
    });

    // Add Consecutive Red Candle markers
    redCandleData.forEach((pattern, index) => {
      const lastDate = pattern.dates[pattern.dates.length - 1];
      const time = parseDateTimeToUnix(lastDate);

      if (time === null) {
        console.error(
          `Invalid date conversion for consecutive red candle ${index}:`,
          pattern
        );
        return;
      }

      // Robust value parsing
      let lastCandleClose = parseFloat(pattern.value);
      if (isNaN(lastCandleClose)) {
        console.error(
          `Invalid numeric value for consecutive red candle ${index}:`,
          pattern.value
        );
        return;
      }

      const marker = chart.addLineSeries({
        color: "red",
        lineWidth: 0,
        lastValueVisible: false,
        priceLineVisible: false,
      });

      marker.setData([{ time, value: lastCandleClose }]);
      marker.setMarkers([
        {
          time,
          position: "aboveBar",
          color: "red",
          shape: "arrowDown",
          text: "4+ Red Candles",
        },
      ]);

      consecutiveRedMarkers.push(marker);
    });

    hideSpinner();
  } catch (error) {
    console.error(
      "Error fetching or processing consecutive candle patterns:",
      error
    );
    hideSpinner();
  }
}

function parseDateTimeToUnix(dateTime) {
  try {
    const date = new Date(dateTime);
    const offset = 5 * 60 * 60 * 1000 + 30 * 60 * 1000; // 5:30 hour offset
    const newDate = new Date(date.getTime() + offset);

    return Math.floor(newDate.getTime() / 1000);
  } catch (error) {
    console.error("Error parsing date-time:", error);
    return null;
  }
}

// Attach the function to pattern button click
handlePatternButtonClick(
  "consecutivecandlesButton",
  fetchAndDrawConsecutiveCandlePatterns
);

let triangleSeries = [];
let angleeMarkers = [];
let triangleVisible = false;

async function fetchAndDrawTriangle(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/triangle?symbol=${symbol}&interval=${interval}&mode=triangle`
    );
    const lineData = await response.json();

    console.log("Received triangle data:", lineData);

    // Clear existing triangles and markers
    triangleSeries.forEach((series) => chart.removeSeries(series));
    angleeMarkers.forEach((marker) => chart.removeSeries(marker));
    triangleSeries = [];
    angleeMarkers = [];

    lineData.forEach((line, index) => {
      // Destructure with more logging
      let [x0, y0, x1, y1, colorCode, angle] = line;
      console.log(`Line ${index} details:`, {
        x0,
        y0,
        x1,
        y1,
        colorCode,
        angle,
      });

      let x0Unix = parseDateTimeToUnix(x0);
      let x1Unix = parseDateTimeToUnix(x1);

      if (x0Unix === null || x1Unix === null) {
        console.error(`Invalid date conversion for line ${index}:`, line);
        return;
      }

      const linecolor = colorCode === 1 ? "green" : "red";

      // Ensure x0 is always the earlier time
      if (x0Unix > x1Unix) {
        [x0Unix, x1Unix] = [x1Unix, x0Unix];
        [y0, y1] = [y1, y0];
      }

      try {
        const lineSeries = chart.addLineSeries({
          color: linecolor,
          lineWidth: 1,
          priceLineVisible: false,
        });

        lineSeries.setData([
          { time: x0Unix, value: parseFloat(y0) },
          { time: x1Unix, value: parseFloat(y1) },
        ]);

        triangleSeries.push(lineSeries);

        // Angle marker creation with enhanced logging
        const midTime = Math.floor((x0Unix + x1Unix) / 2);
        const midPrice = (parseFloat(y0) + parseFloat(y1)) / 2;

        console.log(`Angle marker details:`, {
          midTime,
          midPrice,
          angle: angle !== undefined ? angle.toFixed(2) : "UNDEFINED",
        });

        const angleeMarker = chart.addLineSeries({
          color: linecolor,
          lineWidth: 0,
          lastValueVisible: false,
          priceLineVisible: false,
        });

        angleeMarker.setData([{ time: midTime, value: midPrice }]);

        // Only add marker if angle is defined and valid
        if (angle !== undefined && !isNaN(angle)) {
          angleeMarker.setMarkers([
            {
              time: midTime,
              position: "inBar",
              color: linecolor,
              shape: "circle",
              text: `${angle.toFixed(2)}°`,
            },
          ]);
        } else {
          console.warn(`No valid angle for line ${index}`);
        }

        angleeMarkers.push(angleeMarker);
      } catch (error) {
        console.error(`Error adding series for line ${index}:`, error);
      }
    });

    hideSpinner();
  } catch (error) {
    console.error("Error fetching or processing triangles:", error);
    hideSpinner();
  }
}

handlePatternButtonClick("triangles-btn", fetchAndDrawTriangle);

let cupAndHandle = [];

// Fetch and draw cup-and-handle patterns
async function fetchAndDrawCupAndHandle(symbol, interval) {
  showSpinner();
  try {
    const response = await fetch(
      `/cup-and-handle?symbol=${symbol}&interval=${interval}`
    );
    const cupAndHandleData = await response.json();

    // Clear existing cup-and-handle series
    cupAndHandle.forEach((series) => chart.removeSeries(series));
    cupAndHandle = [];

    cupAndHandleData.forEach((pattern) => {
      // Draw the left side of the cup from start to vertex
      let leftCupSeries = chart.addLineSeries({
        color: "purple",
        lineWidth: 2,
        priceLineVisible: false,
      });

      let leftCupData = [
        {
          time: parseDateTimeToUnix(pattern.start_date),
          value: pattern.start_price,
        },
        {
          time: parseDateTimeToUnix(pattern.vertex_date),
          value: pattern.vertex_price,
        },
      ];

      leftCupSeries.setData(leftCupData);
      cupAndHandle.push(leftCupSeries);

      // Draw the right side of the cup from vertex to end
      let rightCupSeries = chart.addLineSeries({
        color: "purple",
        lineWidth: 2,
        priceLineVisible: false,
      });

      let rightCupData = [
        {
          time: parseDateTimeToUnix(pattern.vertex_date),
          value: pattern.vertex_price,
        },
        {
          time: parseDateTimeToUnix(pattern.end_date),
          value: pattern.end_price,
        },
      ];

      rightCupSeries.setData(rightCupData);
      cupAndHandle.push(rightCupSeries);

      // Draw the handle part from end to handle end
      let handleSeries = chart.addLineSeries({
        color: "red",
        lineWidth: 2,
        priceLineVisible: false,
      });

      let handleData = [
        {
          time: parseDateTimeToUnix(pattern.end_date),
          value: pattern.end_price,
        },
        {
          time: parseDateTimeToUnix(pattern.handle_end_date),
          value: pattern.handle_end_price,
        },
      ];

      handleSeries.setData(handleData);
      cupAndHandle.push(handleSeries);
    });

    hideSpinner();
  } catch (error) {
    console.error("Error:", error);
    hideSpinner();
  }
}

// Update the change event listener for the interval select
document
  .getElementById("interval-select")
  .addEventListener("change", async (event) => {
    const interval = event.target.value;

    // Find the selected stock row
    const selectedRow = document.querySelector(".stock-row.selected");
    
    clearAllPatterns(); // Clear all patterns


    if (selectedRow) {
      const symbol = selectedRow.getAttribute("data-symbol");
      fetchData(symbol, interval);
      const lastCandle = await fetchData(symbol, interval);
      if (lastCandle) {
        currentOHLC[lastCandle.time] = lastCandle;
        console.log(currentOHLC[lastCandle.time]);
        console.log(lastCandle);
      }
      

      if (selectedOptions.includes("sup-res")) {
        await fetchAndDrawSupportResistance(symbol, interval);
      }
      if (selectedOptions.includes("trlines")) {
        await fetchAndDrawTrendLines(symbol, interval);
      }
      if (selectedOptions.includes("parallel_channels")) {
        await fetchAndDrawTrendLines(symbol, interval);
      }
      if (selectedOptions.includes("ibarss")) {
        await fetchAndDrawIbars(symbol, interval);
      }
      if (selectedOptions.includes("vshape")) {
        await fetchAndDrawVShapes(symbol, interval);
      }
      if (selectedOptions.includes("head-and-shoulders")) {
        await fetchAndDrawHeadAndShoulders(symbol, interval);
      }
      if (selectedOptions.includes("double-tops")) {
        await fetchAndDrawPatterns(symbol, interval);
      }
      if (selectedOptions.includes("cupandhandle")) {
        await fetchAndDrawCupAndHandle(symbol, interval);
      }
      if (selectedOptions.includes("ema")) {
        await fetchAndDrawEma(symbol, interval);
      }
      if (selectedOptions.includes("boxx")) {
        await fetchAndDrawDarvasBoxes(symbol, interval);
      }
      if (selectedOptions.includes("vcp")) {
        await fetchAndDrawVCP(symbol, interval);
      }
      if (selectedOptions.includes("dc")) {
        await fetchAndDrawDonchianChannel(symbol, interval);
      }
    }
  });

// Search Button

document.addEventListener("DOMContentLoaded", () => {
  console.time("DOMContentLoaded Execution Time for search button/SR zones/Full Screen "); // Start measuring DOMContentLoaded execution time

  const searchButton = document.getElementById("search-button");
  const addButton = document.getElementById("add-button");
  const searchPopup = document.getElementById("search-popup");
  const closeButton = document.querySelector(".close-button");
  const searchResults = document.getElementById("search-results");
  const searchInput = document.getElementById("search-input"); // Assuming you have a search input field
  let rows = document.querySelectorAll(".stock-row");
  let stocksData = []; // To store all fetched stocks

  // Event listener for the "+" button
  addButton.addEventListener("click", () => {
    console.log("Plus button clicked"); // Test log to ensure the button works
    searchPopup.style.display = "block"; // Display the search popup when the "+" button is clicked
    fetchStocks(); // Fetch the stock list to display in the search popup
  });

  // Show search popup on button click
  searchButton.addEventListener("click", () => {
    searchPopup.style.display = "block";
    fetchStocks();
  });

  // Close search popup on button click
  closeButton.addEventListener("click", () => {
    searchPopup.style.display = "none";
  });

  // Close the popup when clicking outside of it
  window.addEventListener("click", (event) => {
    if (event.target == searchPopup) {
      searchPopup.style.display = "none";
    }
  });

  function fetchStocks() {
    fetch("/get_50_stocks") // Adjust the endpoint URL as necessary
      .then((response) => response.json())
      .then((data) => {
        // console.log(data); // Log fetched data to verify it's correct
        stocksData = data; // Store the fetched stocks
        displayStocks(stocksData); // Initially display all stocks
      })
      .catch((error) => {
        console.error("Error fetching stocks:", error);
      });
  }

  // Event listener for the search input
  searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    console.log("User input:", query); // Log the user input to ensure it's being captured

    const filteredStocks = stocksData.filter((stock) => {
      // Normalize the stock value as done when displaying it
      let stockName = stock
        .replace("NSE:", "")
        .replace("BSE:", "")
        .replace("-INDEX", "")
        .replace("MCX:", "")
        .replace("-EQ", "")
        .replace(/"/g, "")
        .replace(/,/g, "");
      return stockName.toLowerCase().startsWith(query); // Compare the cleaned-up stock name
    });

    console.log("Filtered stocks:", filteredStocks); // Log the filtered stocks
    displayStocks(filteredStocks); // Display filtered stocks
  });

  // Display stocks in the search popup
  function displayStocks(stocks) {
    // console.log("Stocks to display:", stocks); // Log the stocks that are to be displayed
    searchResults.innerHTML = "";
    const existingSymbols = new Set(
      Array.from(rows).map((row) => row.getAttribute("data-symbol"))
    );

    stocks.forEach((stock) => {
      // Remove 'NSE:' prefix and '-INDEX' or '-EQ' suffix from the stock value
      let stockName = stock
        .replace("NSE:", "")
        .replace("BSE:", "")
        .replace("-INDEX", "")
        .replace("MCX:", "")
        .replace("-EQ", "")
        .replace(/"/g, "")
        .replace(/,/g, "");

      const stockItem = document.createElement("div");
      stockItem.classList.add("stock-item");
      stockItem.setAttribute("data-symbol", stock); // Use stock directly

      // Determine the button symbol based on whether the stock is already in the table
      let buttonSymbol = existingSymbols.has(stock) ? "🗑" : "+"; // Check existing symbols
      let buttonClass = existingSymbols.has(stock)
        ? "remove-stock-button"
        : "add-stock-button";

      stockItem.innerHTML = `
        <span>${stockName}</span>
        <button class="${buttonClass}">${buttonSymbol}</button>
      `;

      searchResults.appendChild(stockItem);

      const actionButton = stockItem.querySelector(`.${buttonClass}`);
      actionButton.addEventListener("click", () => {
        if (buttonSymbol === "+") {
          addStockToTable(stock);
          // Update button symbol and class
          buttonSymbol = "🗑";
          actionButton.textContent = buttonSymbol;
          actionButton.className = "remove-stock-button";
        } else {
          removeStockFromTable(stock);
          // Update button symbol and class
          buttonSymbol = "+";
          actionButton.textContent = buttonSymbol;
          actionButton.className = "add-stock-button";
        }
      });
    });
  }

  function removeStockFromTable(stock) {
    rows.forEach((row) => {
      if (row.getAttribute("data-symbol") === stock) {
        row.remove(); // Remove the stock row
      }
    });
    rows = document.querySelectorAll(".stock-row");
  }

  // Add stock to the stock table
  function addStockToTable(stock) {
    const tableBody = document.querySelector("#stock-table tbody");
    const newRow = document.createElement("tr");
    newRow.classList.add("stock-row");
    newRow.setAttribute("data-symbol", stock);
    newRow.setAttribute("onclick", "selectStock(this)");

    // Apply formatting to the stock name
    let stockName = stock
      .replace("NSE:", "")
      .replace("BSE:", "")
      .replace("-INDEX", "")
      .replace("MCX:", "")
      .replace("-EQ", "")
      .replace(/"/g, "")
      .replace(/,/g, "");

    // Add the formatted stock name to the row
    newRow.innerHTML = `
    <td>${stockName}</td>
    
    <td><button class="delete-button" aria-label="Delete stock">🗑️</button></td>
  `;

    tableBody.appendChild(newRow);

    // Add event listener for the delete button
    newRow
      .querySelector(".delete-button")
      .addEventListener("click", (event) => {
        event.stopPropagation(); // Prevents the row click event from firing
        deleteRow(newRow);
      });

    rows = document.querySelectorAll(".stock-row");
    console.log(rows);
  }

  function deleteRow(row) {
    row.remove();
    // Optionally, handle backend deletion if needed
  }

  //SR zone DOM starts hear

  const srZonesButton = document.getElementById("srzones");
  const srZonesContent = document.getElementById("srzones-content");
  const defaultSrZones = document.getElementById("default-srzones");
  const customSrZones = document.getElementById("custom-srzones");
  const customContent = document.getElementById("custom-srzones-content");
  const srDateInput = document.getElementById("sr-date");
  const numSrLinesInput = document.getElementById("num-sr-lines");

  let isDefaultMode = true;
  let isDefaultVisible = false;
  let isCustomVisible = false;

  function clearAllLines() {
    srLineSeries.forEach((series) => chart.removeSeries(series));
    srLineSeries = [];
  }

  function toggleButtonColor(button, isActive) {
    if (isActive) {
      button.classList.add("active-button");
    } else {
      button.classList.remove("active-button");
    }
  }

  srZonesButton.addEventListener("click", () => {
    // Toggle the visibility of the dropdown content
    const isDropdownVisible = srZonesContent.style.display === "block";
    srZonesContent.style.display = isDropdownVisible ? "none" : "block";
    customContent.style.display = "none"; // Ensure custom content is hidden
  });

  defaultSrZones.addEventListener("click", () => {
    // Close dropdown regardless of whether enabling or disabling
    srZonesContent.style.display = "none";

    if (isDefaultVisible) {
      clearAllLines();
      isDefaultVisible = false;
      toggleButtonColor(defaultSrZones, false);
    } else {
      isDefaultMode = true;
      customContent.style.display = "none";
      const selectedRow = document.querySelector(".stock-row.selected");
      if (selectedRow) {
        const symbol = selectedRow.getAttribute("data-symbol");
        const interval = document.getElementById("interval-select").value;
        fetchAndDrawSupportResistance(symbol, interval, true);
      }
      isDefaultVisible = true;
      isCustomVisible = false;
      toggleButtonColor(defaultSrZones, true);
      toggleButtonColor(customSrZones, false);
    }
  });

  customSrZones.addEventListener("click", () => {
    if (isCustomVisible) {
      clearAllLines();
      customContent.style.display = "none";
      isCustomVisible = false;
      toggleButtonColor(customSrZones, false);

      // Disable dropdown when deselecting custom SR zones
      srZonesContent.style.display = "none";
    } else {
      isDefaultMode = false;
      customContent.style.display = "block";
      clearAllLines(); // Clear any existing lines when switching to custom
      isCustomVisible = true;
      isDefaultVisible = false;
      toggleButtonColor(customSrZones, true);
      toggleButtonColor(defaultSrZones, false);
    }
  });

  srDateInput.addEventListener("change", () => {
    // Only load data if both date and number of lines are provided
    if (!isDefaultMode && srDateInput.value && numSrLinesInput.value) {
      const selectedRow = document.querySelector(".stock-row.selected");
      if (selectedRow) {
        const symbol = selectedRow.getAttribute("data-symbol");
        const interval = document.getElementById("interval-select").value;

        // Load custom SR data
        fetchAndDrawSupportResistance(symbol, interval, false);

        // Close the dropdown only after data is loaded
        srZonesContent.style.display = "none";
      }
    }
  });

  numSrLinesInput.addEventListener("input", () => {
    // Reset data if either input is incomplete
    if (!isDefaultMode && (!srDateInput.value || !numSrLinesInput.value)) {
      clearAllLines();
    }
  });

  

  document.addEventListener("click", (event) => {
    if (
      !event.target.closest(".dropdown") &&
      !event.target.closest("#srzones") &&
      !event.target.closest("#srzones-content")
    ) {
      srZonesContent.style.display = "none";
    }
  });



  // Full screan DOM starts hear
  
  const fullscreenButton = document.getElementById("fullscreen-button");
  const mainContainer = document.getElementById("main-container");
  const tvChart = document.getElementById("tvchart");

  let isFullscreen = false; // Track fullscreen state

  function enterFullscreen() {
    const element = document.documentElement; // Fullscreen the entire document

    if (element.requestFullscreen) {
      element.requestFullscreen().catch((err) => {
        console.error("Error attempting to enter fullscreen:", err);
      });
    } else if (element.mozRequestFullScreen) {
      /* Firefox */
      element.mozRequestFullScreen();
    } else if (element.webkitRequestFullscreen) {
      /* Chrome, Safari, and Opera */
      element.webkitRequestFullscreen();
    } else if (element.msRequestFullscreen) {
      /* IE/Edge */
      element.msRequestFullscreen();
    }

    // Adjust styles for fullscreen
    mainContainer.style.display = "none";

    tvChart.style.width = "100%";
    isFullscreen = true;
  }

  function exitFullscreen() {
    if (document.exitFullscreen) {
      document.exitFullscreen().catch((err) => {
        console.error("Error attempting to exit fullscreen:", err);
      });
    } else if (document.mozCancelFullScreen) {
      /* Firefox */
      document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) {
      /* Chrome, Safari, and Opera */
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      /* IE/Edge */
      document.msExitFullscreen();
    }

    // Reset styles when exiting fullscreen
    mainContainer.style.display = "block";

    tvChart.style.width = "95%";

    isFullscreen = false;
  }

  fullscreenButton.addEventListener("click", function () {
    if (!isFullscreen) {
      enterFullscreen();
    } else {
      exitFullscreen();
    }
  });

  // Listen for fullscreen changes (e.g., user exits with ESC key)
  document.addEventListener("fullscreenchange", function () {
    if (!document.fullscreenElement) {
      exitFullscreen();
    }
  });
  document.addEventListener("webkitfullscreenchange", function () {
    if (!document.webkitFullscreenElement) {
      exitFullscreen();
    }
  });
  document.addEventListener("mozfullscreenchange", function () {
    if (!document.mozFullScreenElement) {
      exitFullscreen();
    }
  });
  document.addEventListener("MSFullscreenChange", function () {
    if (!document.msFullscreenElement) {
      exitFullscreen();
    }
  });

  
  console.timeEnd("DOMContentLoaded Execution Time for search button/SR zones/Full Screen "); // Start measuring DOMContentLoaded execution time
});

let selectedOptions = [];

document.getElementById("refresh-button").addEventListener("click", () => {
  chart.timeScale().resetTimeScale();
});
// Pattern Select Dropdown
document.addEventListener("DOMContentLoaded", () => {
  const dropdownHeader = document.getElementById("dropdown-header");
  const dropdownContent = document.getElementById("dropdown-content");
  const options = document.querySelectorAll(".option");

  // Toggle dropdown visibility on header click
  dropdownHeader.addEventListener("click", () => {
    dropdownContent.style.display =
      dropdownContent.style.display === "block" ? "none" : "block";
  });

  // Handle option click to toggle selection
  options.forEach((option) => {
    option.addEventListener("click", () => {
      const value = option.getAttribute("data-value");
      option.classList.toggle("selected");

      if (option.classList.contains("selected")) {
        selectedOptions.push(value);
      } else {
        selectedOptions = selectedOptions.filter((item) => item !== value);
      }

      const selectedRow = document.querySelector(".stock-row.selected");
      if (selectedRow) {
        const symbol = selectedRow.getAttribute("data-symbol");
        const interval = document.getElementById("interval-select").value;
        if (selectedOptions.includes("sup-res")) {
          fetchAndDrawSupportResistance(symbol, interval);
        } else {
          srLineSeries.forEach((series) => chart.removeSeries(series));
          srLineSeries = [];
        }
        if (selectedOptions.includes("trlines")) {
          fetchAndDrawTrendLines(symbol, interval, mode);
        } else {
          trendlineSeries.forEach((series) => chart.removeSeries(series));
          trendlineSeries = [];
          angleMarkers.forEach((marker) => chart.removeSeries(marker));

          angleMarkers = [];
          parallelChannelSeries.forEach((series) => chart.removeSeries(series));
          parallelChannelSeries = [];
        }
        if (selectedOptions.includes("ibarss")) {
          fetchAndDrawIbars(symbol, interval);
        } else {
          ibars.forEach((series) => chart.removeSeries(series));
          ibars = [];
        }
        if (selectedOptions.includes("head-and-shoulders")) {
          fetchAndDrawHeadAndShoulders(symbol, interval);
        } else {
          headAndShoulders.forEach((series) => chart.removeSeries(series));
          headAndShoulders = [];
        }
        if (selectedOptions.includes("double-tops")) {
          fetchAndDrawPatterns(symbol, interval);
        } else {
          doubleTops.forEach((series) => chart.removeSeries(series));
          doubleTops = [];
          doubleBottoms.forEach((series) => chart.removeSeries(series));
          doubleBottoms = [];
        }
        if (selectedOptions.includes("vshape")) {
          fetchAndDrawVShapes(symbol, interval);
        } else {
          vShapes.forEach((series) => chart.removeSeries(series));
          vShapes = [];
        }
        if (selectedOptions.includes("cupandhandle")) {
          fetchAndDrawCupAndHandle(symbol, interval);
        } else {
          cupAndHandle.forEach((series) => chart.removeSeries(series));
          cupAndHandle = [];
        }
        if (selectedOptions.includes("morn-even")) {
          fetchAndDrawMorningEveningStar(symbol, interval);
        } else {
          morningStarMarkers.forEach((series) => chart.removeSeries(series));
          morningStarMarkers = [];
          eveningStarMarkers.forEach((series) => chart.removeSeries(series));
          eveningStarMarkers = [];
        }
        if (selectedOptions.includes("ema")) {
          fetchAndDrawEma(symbol, interval);
        } else {
          Object.values(emaSeries).forEach((series) =>
            chart.removeSeries(series)
          );
          emaSeries = {}; // Reset emaSeries
        }
        if (selectedOptions.includes("boxx")) {
          fetchAndDrawDarvasBoxes(symbol, interval);
        } else {
          darvasBoxes.forEach((series) => chart.removeSeries(series));
          darvasBoxes = [];
        }
        if (selectedOptions.includes("vcp")) {
          fetchAndDrawVCP(symbol, interval);
        } else {
          vcpPatterns.forEach((series) => chart.removeSeries(series));
          vcpPatterns = [];
        }
        if (selectedOptions.includes("consecutive_candles")) {
          fetchAndDrawConsecutiveCandlePatterns(symbol, interval);
        } else {
          consecutiveGreenMarkers.forEach((marker) =>
            chart.removeSeries(marker)
          );
          consecutiveRedMarkers.forEach((marker) => chart.removeSeries(marker));
          consecutiveGreenMarkers = [];
          consecutiveRedMarkers = [];
        }
        if (selectedOptions.includes("dc")) {
          fetchAndDrawDonchianChannel(symbol, interval);
        } else {
          donchianChannelSeries.forEach((series) => chart.removeSeries(series));
          donchianChannelSeries = [];
        }
        if (selectedOptions.includes("bolingerbandButton")) {
          fetchAndDrawPatterns(symbol, interval);
        } else {
          bollingerBandsSeries.forEach((series) => chart.removeSeries(series));
          bollingerBandsSeries = [];
        }
        if (selectedOptions.includes("trlines")) {
          fetchAndDrawVShapes(symbol, interval);
        } else {
          triangleSeries.forEach((series) => chart.removeSeries(series));
          triangleSeries = [];
        }
      }
    });
  });

  // Close dropdown when clicking outside
  window.addEventListener("click", (event) => {
    if (
      !dropdownHeader.contains(event.target) &&
      !dropdownContent.contains(event.target)
    ) {
      dropdownContent.style.display = "none";
    }
  });
});

document.getElementById("refresh-button").addEventListener("click", () => {
  chart.priceScale("right").applyOptions({
    autoScale: true,
  });
  chart.timeScale().resetTimeScale();
});

// document.addEventListener("DOMContentLoaded", function () {
//   const fullscreenButton = document.getElementById("fullscreen-button");
//   const mainContainer = document.getElementById("main-container");
//   const tvChart = document.getElementById("tvchart");

//   let isFullscreen = false; // Track fullscreen state

//   function enterFullscreen() {
//     const element = document.documentElement; // Fullscreen the entire document

//     if (element.requestFullscreen) {
//       element.requestFullscreen().catch((err) => {
//         console.error("Error attempting to enter fullscreen:", err);
//       });
//     } else if (element.mozRequestFullScreen) {
//       /* Firefox */
//       element.mozRequestFullScreen();
//     } else if (element.webkitRequestFullscreen) {
//       /* Chrome, Safari, and Opera */
//       element.webkitRequestFullscreen();
//     } else if (element.msRequestFullscreen) {
//       /* IE/Edge */
//       element.msRequestFullscreen();
//     }

//     // Adjust styles for fullscreen
//     mainContainer.style.display = "none";

//     tvChart.style.width = "100%";
//     isFullscreen = true;
//   }

//   function exitFullscreen() {
//     if (document.exitFullscreen) {
//       document.exitFullscreen().catch((err) => {
//         console.error("Error attempting to exit fullscreen:", err);
//       });
//     } else if (document.mozCancelFullScreen) {
//       /* Firefox */
//       document.mozCancelFullScreen();
//     } else if (document.webkitExitFullscreen) {
//       /* Chrome, Safari, and Opera */
//       document.webkitExitFullscreen();
//     } else if (document.msExitFullscreen) {
//       /* IE/Edge */
//       document.msExitFullscreen();
//     }

//     // Reset styles when exiting fullscreen
//     mainContainer.style.display = "block";

//     tvChart.style.width = "95%";

//     isFullscreen = false;
//   }

//   fullscreenButton.addEventListener("click", function () {
//     if (!isFullscreen) {
//       enterFullscreen();
//     } else {
//       exitFullscreen();
//     }
//   });

//   // Listen for fullscreen changes (e.g., user exits with ESC key)
//   document.addEventListener("fullscreenchange", function () {
//     if (!document.fullscreenElement) {
//       exitFullscreen();
//     }
//   });
//   document.addEventListener("webkitfullscreenchange", function () {
//     if (!document.webkitFullscreenElement) {
//       exitFullscreen();
//     }
//   });
//   document.addEventListener("mozfullscreenchange", function () {
//     if (!document.mozFullScreenElement) {
//       exitFullscreen();
//     }
//   });
//   document.addEventListener("MSFullscreenChange", function () {
//     if (!document.msFullscreenElement) {
//       exitFullscreen();
//     }
//   });
// });

// Add hover info mouse move event listener
chart.subscribeCrosshairMove(function (param) {
  if (!param || !param.time || !param.seriesData.size) {
    hoverInfo.innerHTML = "";
    return;
  }

  const data = param.seriesData.get(candleSeries);
  if (!data) {
    hoverInfo.innerHTML = "";
    return;
  }

  let { open, close, high, low } = data;

  open = open.toFixed(2);
  close = close.toFixed(2);
  high = high.toFixed(2);
  low = low.toFixed(2);

  hoverInfo.innerHTML = `
    Open: ${open}
    Close: ${close}
    High: ${high}
    Low: ${low}
  `;
});

var skt = fyersDataSocket.getInstance(accessToken);

function roundTimeToInterval(unixTimestamp, intervalMinutes) {
  const date = new Date((unixTimestamp + 5.5 * 60 * 60) * 1000);
  let minutes = date.getMinutes();
  let hours = date.getHours();

  if (intervalMinutes === 30) {
    if (minutes < 15) {
      minutes = 45;
      hours = hours - 1; // previous hour
    } else if (minutes < 45) {
      minutes = 15;
    } else {
      minutes = 45;
    }
  } else if (intervalMinutes === 60) {
    if (minutes < 15) {
      minutes = 15;
      hours = hours - 1; // previous hour
    } else {
      minutes = 15;
    }
  } else {
    minutes = Math.floor(minutes / intervalMinutes) * intervalMinutes;
  }

  date.setHours(hours);
  date.setMinutes(minutes, 0, 0);
  return Math.floor(date.getTime() / 1000);
}

// Function to update OHLC data
function updateOHLC(ltp, time) {
  const interval = document.getElementById("interval-select").value;
  const roundedTime = roundTimeToInterval(time, interval);

  if (!currentOHLC[roundedTime]) {
    currentOHLC[roundedTime] = {
      time: roundedTime,
      open: ltp,
      high: ltp,
      low: ltp,
      close: ltp,
    };
  } else {
    currentOHLC[roundedTime].high = Math.max(
      currentOHLC[roundedTime].high,
      ltp
    );
    currentOHLC[roundedTime].low = Math.min(currentOHLC[roundedTime].low, ltp);
    currentOHLC[roundedTime].close = ltp;
  }

  candleSeries.update(currentOHLC[roundedTime]);
}

// // Establish the WebSocket connection
// skt.connect();
function onmsg(message) {
  const parsedData = message;

  // Select the currently selected row in the table
  const selectedRow = document.querySelector(".stock-row.selected");
  if (!selectedRow) return; // If no row is selected, do nothing

  const symbol = selectedRow.getAttribute("data-symbol");

  // Find the corresponding row using the data-symbol attribute
  if (parsedData.symbol === symbol) {
    const time = parsedData.exch_feed_time;
    const ltp = parsedData.ltp;

    // Update the new container with the latest data
    document.getElementById("last-price").textContent = parsedData.ltp || "--";
    document.getElementById("change").textContent = parsedData.ch || "--";
    document.getElementById("change-percentage").textContent =
      parsedData.chp || "--";

    // Update OHLC chart
    updateOHLC(ltp, time);
  }
}

// Event listener for clicks on stock rows
let hasFetchedFromFlask = true;
skt.on("connect", function () {
  const selectedRow = document.querySelector(".stock-row.selected");
  if (!selectedRow) return; // Do nothing if no row is selected

  const symbol = selectedRow.getAttribute("data-symbol");
  // const interval = document.getElementById("interval-select").value;
  // Use symbolFromFlask only once on the first call
  const finalSymbol = symbolFromFlask ? symbolFromFlask || symbol : symbol;
  const finalPatterns = symbolFromFlask ? patternsFromFlask : []; // Use patternsFromFlask if available
  const interval = symbolFromFlask? "15":document.getElementById("interval-select").value;
  console.log("Final symbol : " + finalSymbol);
  console.log("Final patterns : " + finalPatterns);
  // If symbolFromFlask and patternsFromFlask were used, set the flag to true
  if (hasFetchedFromFlask) {
    hasFetchedFromFlask = false; // Prevent re-using the Flask-provided data
  }
  // Subscribe to the selected stock symbol
  skt.subscribe([finalSymbol], false, 1);
  skt.mode(skt.FullMode, 1);
  // console.log("Connected to WebSocket:", skt.isConnected());
  finalPatterns.forEach((pattern) => {
    // console.log("Pattern name : " + pattern);
    // if (pattern === "Cup and Handle") {
    //   fetchAndDrawCupAndHandle(finalSymbol, "15");
    // }
    if (pattern === "Double Patterns") {
      fetchAndDrawPatterns(finalSymbol, interval);
    }
    // if (pattern === "Double Top") {
    //   fetchAndDrawPatterns(finalSymbol, interval);
    // }
    if (pattern === "Head and Shoulders") {
      fetchAndDrawHeadAndShoulders(finalSymbol, interval);
    }
    if (pattern === "Inside Bar") {
      fetchAndDrawIbars(finalSymbol, interval);
    }
    if (pattern === "V Shape") {
      fetchAndDrawVShapes(finalSymbol, interval);
    }
    // if (pattern === "Double Top" || pattern === "Double Bottom") {
    //   fetchAndDrawPatterns(finalSymbol, interval);
    // }
  });
  fetchData(finalSymbol, interval);
  // Check for patterns in the finalPatterns list and call handlePatternButtonClick
  skt.autoreconnect();
});

// skt.on("connect", function () {
//   const selectedRow = document.querySelector(".stock-row.selected");
//   if (!selectedRow) return; // Do nothing if no row is selected

//   // Check if symbolFromFlask exists and has a value
//   const initialSymbol =
//     symbolFromFlask || selectedRow.getAttribute("data-symbol");
//   const interval = document.getElementById("interval-select").value;
//   // Subscribe to the selected stock symbol or the initial symbol from Flask
//   skt.subscribe([initialSymbol], false, 1);
//   skt.mode(skt.FullMode, 1);
//   console.log("Connected to WebSocket:", skt.isConnected());
//   // Call fetchData with the initial symbol from Flask if available, otherwise use the selected symbol
//   fetchData(initialSymbol, interval);
//   // Reset symbolFromFlask so that it is used only on the first call
//   symbolFromFlask = null;
//   // Enable automatic reconnection in case of disconnection
//   skt.autoreconnect();
// });

// Handle incoming WebSocket messages
skt.on("message", function (message) {
  onmsg(message);
});

// Handle WebSocket errors
skt.on("error", function (message) {
  console.log("WebSocket error:", message);
});

// Handle WebSocket connection close
skt.on("close", function () {
  console.log("WebSocket connection closed");
});

// Establish the WebSocket connection
skt.connect();

document.getElementById("add-button").addEventListener("click", function () {
  // Trigger the action, such as opening the search popup
  document.getElementById("search-popup").style.display = "block";
});

document.getElementById("sr-zones").addEventListener("click", function () {
  document.getElementById("dropdown-content").classList.toggle("hidden");
});

document
  .getElementById("customized-option")
  .addEventListener("mouseenter", function () {
    document.getElementById("customization-options").classList.remove("hidden");
  });

document
  .getElementById("customized-option")
  .addEventListener("mouseleave", function () {
    document.getElementById("customization-options").classList.add("hidden");
  });

// Optional: Close the dropdown if clicked outside
window.onclick = function (event) {
  if (!event.target.matches("#sr-zones")) {
    var dropdowns = document.getElementsByClassName("dropdown-content");
    for (var i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (!openDropdown.contains(event.target)) {
        openDropdown.classList.add("hidden");
      }
    }
  }
};

document.getElementById("sr-zones").addEventListener("click", function () {
  document.getElementById("dropdown-content").classList.toggle("hidden");
});

document
  .getElementById("customized-option")
  .addEventListener("mouseenter", function () {
    document.getElementById("customization-options").classList.remove("hidden");
  });

document
  .getElementById("customized-option")
  .addEventListener("mouseleave", function () {
    document.getElementById("customization-options").classList.add("hidden");
  });

// Optional: Close the dropdown if clicked outside
window.onclick = function (event) {
  if (!event.target.matches("#sr-zones")) {
    var dropdowns = document.getElementsByClassName("dropdown-content");
    for (var i = 0; i < dropdowns.length; i++) {
      var openDropdown = dropdowns[i];
      if (!openDropdown.contains(event.target)) {
        openDropdown.classList.add("hidden");
      }
    }
  }
};

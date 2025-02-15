var typed = new Typed(".text", {
  strings: [
    " Double Top. . .",
    "Double Bottom . . .",
    "SR Zones. . .",
    "Trendlines  . . .",
    "Trend Analysis. . . ",
    "Real-Time Stock Tracking. . .",
  ],
  typeSpeed: 70,
  backSpeed: 50,
  backDelay: 1000,
  loop: true,
});

const ctx = document.getElementById("movingGraph").getContext("2d");

// Gradient for Neon Shade Below Line
const neonGradient = ctx.createLinearGradient(0, 0, 0, 400);
neonGradient.addColorStop(0, "rgba(0, 255, 204, 0.5)"); /* Neon Green */
neonGradient.addColorStop(1, "rgba(0, 255, 204, 0)"); /* Transparent */

// Initialize Chart
const movingGraph = new Chart(ctx, {
  type: "line",
  data: {
    labels: [], // Time labels dynamically added
    datasets: [
      {
        label: "Stock Price Movement",
        data: [], // Data dynamically added
        borderColor: "#00ffcc" /* Neon Green Line */,
        backgroundColor: neonGradient /* Neon Gradient Shade */,
        borderWidth: 2,
        pointRadius: 0 /* No points on the line */,
        fill: true /* Fill area below line */,
        tension: 0.1 /* Smooth curve */,
      },
    ],
  },
  options: {
    animation: false /* Real-time updates */,
    responsive: true,
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: "#00ffcc" /* Neon Green X-Axis Labels */,
          font: { size: 12 },
        },
      },
      y: {
        grid: {
          color: "rgba(0, 255, 204, 0.1)" /* Subtle Neon Gridlines */,
        },
        ticks: {
          color: "#00ffcc" /* Neon Green Y-Axis Labels */,
          font: { size: 12 },
        },
      },
    },
    plugins: {
      legend: { display: false } /* Hide legend */,
    },
  },
});

// Add Real-Time Data
function addLiveData() {
  const now = new Date();
  const time = now.toLocaleTimeString("en-US", { hour12: false });

  // Simulated stock price between 24,320 and 24,600
  const price = (Math.random() * (24600 - 24320) + 24320).toFixed(2);

  // Add time and price
  movingGraph.data.labels.push(time);
  movingGraph.data.datasets[0].data.push(price);

  // Keep the last 30 data points
  if (movingGraph.data.labels.length > 30) {
    movingGraph.data.labels.shift();
    movingGraph.data.datasets[0].data.shift();
  }

  movingGraph.update();
}

// Update graph every second
setInterval(addLiveData, 1000);

// sliding of the cards
const slider = document.getElementById("scrollable-container");

let scrollSpeed = 1; // Adjust the speed of scrolling
let isPaused = false; // To track the pause state

function startScrolling() {
  if (!isPaused) {
    slider.scrollLeft += scrollSpeed;

    // If the scroll reaches the end, reset to the start
    if (slider.scrollLeft >= slider.scrollWidth / 2) {
      slider.scrollLeft = 0;
    }
  }

  requestAnimationFrame(startScrolling);
}

// Pause scrolling when the mouse enters the container
slider.addEventListener("mouseenter", () => {
  isPaused = true; // Pause scrolling
});

// Resume scrolling when the mouse leaves the container
slider.addEventListener("mouseleave", () => {
  isPaused = false; // Resume scrolling
});

// Start scrolling on page load
window.onload = () => {
  startScrolling();
};



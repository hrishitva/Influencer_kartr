/**
 * Initialize charts for the stats display
 */
function initCharts(chartData) {
  // Initialize only if we have data and Chart.js is loaded
  if (!chartData || typeof Chart === 'undefined') {
    console.warn('Chart data is missing or Chart.js is not loaded');
    return;
  }
  
  // Create engagement chart
  createEngagementChart(chartData);
  
  // Create sentiment chart if we have sentiment data
  if (chartData.sentimentData) {
    createSentimentChart(chartData.sentimentData);
  }
  
  // Create keyword frequency chart if we have keyword data
  if (chartData.keywordData) {
    createKeywordChart(chartData.keywordData);
  }
}

/**
 * Create the engagement chart
 * @param {Object} data - Chart data
 */
function createEngagementChart(data) {
  const ctx = document.getElementById('engagementChart');
  if (!ctx) return;
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Views', 'Likes', 'Comments'],
      datasets: [{
        label: 'Engagement Metrics',
        data: [data.viewCount, data.likeCount, data.commentCount],
        backgroundColor: [
          'rgba(108, 99, 255, 0.7)',
          'rgba(255, 107, 107, 0.7)',
          'rgba(54, 162, 235, 0.7)'
        ],
        borderColor: [
          'rgba(108, 99, 255, 1)',
          'rgba(255, 107, 107, 1)',
          'rgba(54, 162, 235, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              if (value >= 1000000) {
                return (value / 1000000).toFixed(1) + 'M';
              } else if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K';
              }
              return value;
            }
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              let value = context.raw;
              if (value >= 1000000) {
                return (value / 1000000).toFixed(2) + ' Million';
              } else if (value >= 1000) {
                return (value / 1000).toFixed(2) + ' Thousand';
              }
              return value;
            }
          }
        }
      }
    }
  });
}

/**
 * Create the sentiment analysis chart
 * @param {Object} sentimentData - Sentiment analysis data
 */
function createSentimentChart(sentimentData) {
  const ctx = document.getElementById('sentimentChart');
  if (!ctx) return;
  
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [{
        data: [
          sentimentData.positive, 
          sentimentData.neutral, 
          sentimentData.negative
        ],
        backgroundColor: [
          'rgba(40, 167, 69, 0.7)',
          'rgba(108, 117, 125, 0.7)',
          'rgba(220, 53, 69, 0.7)'
        ],
        borderColor: [
          'rgba(40, 167, 69, 1)',
          'rgba(108, 117, 125, 1)',
          'rgba(220, 53, 69, 1)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.label + ': ' + context.raw + '%';
            }
          }
        }
      }
    }
  });
}

/**
 * Create the keyword frequency chart
 * @param {Object} keywordData - Keyword frequency data
 */
function createKeywordChart(keywordData) {
  const ctx = document.getElementById('keywordChart');
  if (!ctx) return;
  
  // Extract keywords and their counts
  const labels = keywordData.keywords;
  const counts = keywordData.counts;
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Keyword Frequency',
        data: counts,
        backgroundColor: 'rgba(108, 99, 255, 0.7)',
        borderColor: 'rgba(108, 99, 255, 1)',
        borderWidth: 1
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true
        }
      },
      plugins: {
        legend: {
          display: false
        }
      }
    }
  });
}

/**
 * Create a comparison chart (for comparing multiple videos/channels)
 * @param {Object} data - Comparison data
 */
function createComparisonChart(data) {
  const ctx = document.getElementById('comparisonChart');
  if (!ctx || !data.labels || !data.datasets) return;
  
  new Chart(ctx, {
    type: 'radar',
    data: {
      labels: data.labels,
      datasets: data.datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      },
      scales: {
        r: {
          angleLines: {
            display: true
          },
          suggestedMin: 0
        }
      }
    }
  });
}

/**
 * Initialize all dashboard charts
 * @param {Object} dashboardData - Dashboard data
 */
function initDashboardCharts(dashboardData) {
  if (!dashboardData) return;
  
  // Growth chart over time
  if (dashboardData.growthData && document.getElementById('growthChart')) {
    createGrowthChart(dashboardData.growthData);
  }
  
  // Engagement rate chart
  if (dashboardData.engagementRates && document.getElementById('engagementRateChart')) {
    createEngagementRateChart(dashboardData.engagementRates);
  }
}

/**
 * Create growth chart for dashboard
 * @param {Object} growthData - Growth data over time
 */
function createGrowthChart(growthData) {
  const ctx = document.getElementById('growthChart');
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: growthData.labels,
      datasets: [{
        label: 'Subscribers',
        data: growthData.subscribers,
        borderColor: 'rgba(108, 99, 255, 1)',
        backgroundColor: 'rgba(108, 99, 255, 0.1)',
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: false,
          ticks: {
            callback: function(value) {
              if (value >= 1000000) {
                return (value / 1000000).toFixed(1) + 'M';
              } else if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K';
              }
              return value;
            }
          }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: function(context) {
              let value = context.raw;
              if (value >= 1000000) {
                return (value / 1000000).toFixed(2) + ' Million Subscribers';
              } else if (value >= 1000) {
                return (value / 1000).toFixed(2) + ' Thousand Subscribers';
              }
              return value + ' Subscribers';
            }
          }
        }
      }
    }
  });
}

/**
 * Create engagement rate chart for dashboard
 * @param {Object} engagementData - Engagement rate data
 */
function createEngagementRateChart(engagementData) {
  const ctx = document.getElementById('engagementRateChart');
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: engagementData.labels,
      datasets: [{
        label: 'Engagement Rate (%)',
        data: engagementData.rates,
        backgroundColor: 'rgba(255, 107, 107, 0.7)',
        borderColor: 'rgba(255, 107, 107, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return 'Engagement Rate: ' + context.raw + '%';
            }
          }
        }
      }
    }
  });
}

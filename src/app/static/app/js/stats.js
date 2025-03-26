// stats.js - Version complète et fonctionnelle

// Configuration globale
document.addEventListener('DOMContentLoaded', function () {
    const chartData = (function () {
        try {
            const element = document.getElementById('chart-data');
            if (!element) throw new Error("Element chart-data non trouvé");

            return {
                score_distribution: JSON.parse(element.dataset.scoreDistribution),
                evolution_scores: JSON.parse(element.dataset.evolutionScores),
                evolution_dates: JSON.parse(element.dataset.evolutionDates),
                total_quizzes: parseInt(element.dataset.totalQuizzes)
            };
        } catch (e) {
            console.error("Erreur de chargement des données:", e);
            return null;
        }
    })();

    if (chartData) {
        // Initialisez vos graphiques ici
        initScoreDistributionChart(chartData);
        initEvolutionChart(chartData);
    }
    // Gestion des filtres
    setupPeriodFilters();
    setupQuizSearch();

    // Modal détails quiz
    setupQuizDetailModal();
});

// Fonction pour récupérer les données depuis le DOM
function getChartDataFromDOM() {
    try {
        const dataElement = document.getElementById('chart-data');
        if (!dataElement) return null;

        return {
            score_distribution: JSON.parse(dataElement.dataset.scoreDistribution),
            evolution_scores: JSON.parse(dataElement.dataset.evolutionScores),
            evolution_dates: JSON.parse(dataElement.dataset.evolutionDates),
            total_quizzes: parseInt(dataElement.dataset.totalQuizzes)
        };
    } catch (e) {
        console.error("Erreur lors du chargement des données:", e);
        return null;
    }
}

// Graphique de répartition des scores
function initScoreDistributionChart(data) {
    const options = {
        series: data.score_distribution,
        chart: {
            type: 'donut',
            height: 350,
            animations: {
                enabled: true,
                speed: 800
            }
        },
        colors: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e'],
        labels: ['Excellent (90-100%)', 'Bon (75-89%)', 'Moyen (50-74%)', 'À améliorer (<50%)'],
        plotOptions: {
            pie: {
                donut: {
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: 'Total',
                            formatter: function () {
                                return data.total_quizzes + ' quiz';
                            }
                        }
                    }
                }
            }
        },
        dataLabels: {
            enabled: false
        },
        legend: {
            position: 'right',
            formatter: function (val, opts) {
                return val + " - " + opts.w.globals.series[opts.seriesIndex] + " quiz";
            }
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    const percent = Math.round(val / data.total_quizzes * 100);
                    return val + " quiz (" + percent + "%)";
                }
            }
        }
    };

    const chart = new ApexCharts(document.querySelector("#scoreDistributionChart"), options);
    chart.render();
}

// Graphique d'évolution
function initEvolutionChart(data) {
    const options = {
        series: [{
            name: "Score Moyen (%)",
            data: data.evolution_scores
        }],
        chart: {
            height: 350,
            type: 'area',
            zoom: {
                enabled: true
            },
            toolbar: {
                tools: {
                    download: true
                }
            }
        },
        colors: ['#4e73df'],
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth',
            width: 3
        },
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.7,
                opacityTo: 0.3,
                stops: [0, 100]
            }
        },
        xaxis: {
            categories: data.evolution_dates,
            labels: {
                formatter: function (value) {
                    return new Date(value).toLocaleDateString('fr-FR', {
                        day: 'numeric',
                        month: 'short'
                    });
                }
            }
        },
        yaxis: {
            min: 0,
            max: 100,
            labels: {
                formatter: function (value) {
                    return value + "%";
                }
            }
        },
        tooltip: {
            x: {
                formatter: function (value) {
                    return new Date(value).toLocaleDateString('fr-FR', {
                        weekday: 'long',
                        day: 'numeric',
                        month: 'long'
                    });
                }
            },
            y: {
                formatter: function (value) {
                    return value + "%";
                }
            }
        }
    };

    const chart = new ApexCharts(document.querySelector("#evolutionChart"), options);
    chart.render();
}

// Gestion des filtres par période
function setupPeriodFilters() {
    document.querySelectorAll('.period-filter').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const days = this.getAttribute('data-days');
            updateStatsForPeriod(days);
        });
    });

    document.getElementById('applyCustomRange').addEventListener('click', function () {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (startDate && endDate) {
            updateStatsForCustomRange(startDate, endDate);
            bootstrap.Modal.getInstance(document.getElementById('dateRangeModal')).hide();
        }
    });
}

function updateStatsForPeriod(days) {
    fetch(`/api/stats/?period=${days}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('periodDropdown').innerHTML =
                `<i class="bi bi-calendar-range me-2"></i>${days} derniers jours`;

            // Mise à jour des graphiques
            initScoreDistributionChart(data);
            initEvolutionChart(data);
        });
}

function updateStatsForCustomRange(startDate, endDate) {
    fetch(`/api/stats/?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            const formattedStart = new Date(startDate).toLocaleDateString('fr-FR');
            const formattedEnd = new Date(endDate).toLocaleDateString('fr-FR');

            document.getElementById('periodDropdown').innerHTML =
                `<i class="bi bi-calendar-range me-2"></i>${formattedStart} - ${formattedEnd}`;

            // Mise à jour des graphiques
            initScoreDistributionChart(data);
            initEvolutionChart(data);
        });
}

// Recherche de quiz
function setupQuizSearch() {
    const searchInput = document.getElementById('quizSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase();
            document.querySelectorAll('.quiz-item').forEach(item => {
                const title = item.getAttribute('data-title').toLowerCase();
                item.style.display = title.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

// Modal détails quiz
function setupQuizDetailModal() {
    const modal = document.getElementById('quizDetailModal');
    if (modal) {
        modal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const quizId = button.getAttribute('data-quiz-id');

            fetch(`/api/quiz-stats/${quizId}/`)
                .then(response => response.json())
                .then(data => {
                    renderQuizDetails(data);
                    initQuizDetailChart(data);
                });
        });
    }
}

function renderQuizDetails(data) {
    const content = `
        <div class="row">
            <div class="col-md-6">
                <h5>${data.title}</h5>
                <p class="text-muted">${data.description}</p>
                
                <div class="mb-3">
                    <h6>Dernières Tentatives</h6>
                    <ul class="list-group">
                        ${data.attempts.map(attempt => `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>${new Date(attempt.date).toLocaleDateString('fr-FR')}</span>
                                <span class="badge ${getScoreBadgeClass(attempt.score)} rounded-pill">
                                    ${attempt.score}%
                                </span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
            <div class="col-md-6">
                <div id="quizDetailChart"></div>
            </div>
        </div>
    `;

    document.getElementById('quizDetailContent').innerHTML = content;
}

function initQuizDetailChart(data) {
    const options = {
        series: [{
            name: 'Score',
            data: data.attempts.map(a => a.score)
        }],
        chart: {
            height: 300,
            type: 'radar',
            toolbar: {
                show: false
            }
        },
        colors: ['#4e73df'],
        xaxis: {
            categories: data.attempts.map((a, i) => `Tentative ${i + 1}`)
        },
        yaxis: {
            min: 0,
            max: 100
        },
        markers: {
            size: 5,
            hover: {
                size: 7
            }
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    return val + "%";
                }
            }
        }
    };

    const chart = new ApexCharts(document.querySelector("#quizDetailChart"), options);
    chart.render();
}

// Helper functions
function getScoreBadgeClass(score) {
    if (score >= 70) return 'bg-success';
    if (score >= 50) return 'bg-warning';
    return 'bg-danger';
}
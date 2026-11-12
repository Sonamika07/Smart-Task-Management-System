
function confirmDelete() {
    return confirm("Are you sure you want to delete this task?");
}

document.addEventListener("DOMContentLoaded", function () {

    const chartElement = document.getElementById("priorityChart");

    if (chartElement && typeof Chart !== "undefined") {

        const high = Number(chartElement.dataset.high);
        const medium = Number(chartElement.dataset.medium);
        const low = Number(chartElement.dataset.low);

        new Chart(chartElement, {
            type: "doughnut",

            data: {
                labels: ["High", "Medium", "Low"],

                datasets: [{
                    data: [high, medium, low],
                    backgroundColor: [
                        "#ef5350",
                        "#f5b942",
                        "#20ae7b"
                    ],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display: false
                    }
                },

                cutout: "68%"
            }
        });
    }

});

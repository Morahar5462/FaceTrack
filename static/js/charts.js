/**
 * Chart utilities for attendance system
 */

class AttendanceCharts {
    constructor() {
        // Default chart colors
        this.colors = {
            primary: '#0d6efd',
            secondary: '#6c757d',
            success: '#198754',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#0dcaf0',
            light: '#f8f9fa',
            dark: '#212529'
        };
        
        // Default chart options
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        };
    }
    
    /**
     * Create a donut chart for attendance overview
     * @param {string} canvasId - ID of the canvas element
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Chart} Chart instance
     */
    createDonutChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        const chartOptions = {
            ...this.defaultOptions,
            cutout: '70%',
            ...options
        };
        
        return new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: chartOptions
        });
    }
    
    /**
     * Create a bar chart for attendance data
     * @param {string} canvasId - ID of the canvas element
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Chart} Chart instance
     */
    createBarChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        const chartOptions = {
            ...this.defaultOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            ...options
        };
        
        return new Chart(ctx, {
            type: 'bar',
            data: data,
            options: chartOptions
        });
    }
    
    /**
     * Create a line chart for attendance trends
     * @param {string} canvasId - ID of the canvas element
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Chart} Chart instance
     */
    createLineChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        const chartOptions = {
            ...this.defaultOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            ...options
        };
        
        return new Chart(ctx, {
            type: 'line',
            data: data,
            options: chartOptions
        });
    }
    
    /**
     * Create a pie chart
     * @param {string} canvasId - ID of the canvas element
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     * @returns {Chart} Chart instance
     */
    createPieChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        const chartOptions = {
            ...this.defaultOptions,
            ...options
        };
        
        return new Chart(ctx, {
            type: 'pie',
            data: data,
            options: chartOptions
        });
    }
    
    /**
     * Generate attendance status colors based on percentage
     * @param {number} percentage - Attendance percentage
     * @returns {string} Color code
     */
    getAttendanceStatusColor(percentage) {
        if (percentage >= 75) {
            return this.colors.success;
        } else if (percentage >= 50) {
            return this.colors.warning;
        } else {
            return this.colors.danger;
        }
    }
    
    /**
     * Generate gradient for chart backgrounds
     * @param {CanvasRenderingContext2D} ctx - Canvas context
     * @param {string} startColor - Start color
     * @param {string} endColor - End color
     * @returns {CanvasGradient} Gradient
     */
    createGradient(ctx, startColor, endColor) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, startColor);
        gradient.addColorStop(1, endColor);
        return gradient;
    }
}

// Example usage:
// document.addEventListener('DOMContentLoaded', function() {
//     const charts = new AttendanceCharts();
//     
//     // Create a donut chart
//     const donutData = {
//         labels: ['Present', 'Absent', 'Late'],
//         datasets: [{
//             data: [75, 15, 10],
//             backgroundColor: [
//                 charts.colors.success,
//                 charts.colors.danger,
//                 charts.colors.warning
//             ],
//             borderWidth: 0
//         }]
//     };
//     
//     charts.createDonutChart('attendanceDonut', donutData);
// });

/**
 * Satellite Cloud Removal & Analysis System
 * Frontend Controller for SIH 2026 Space Technology Solution (ID: 26209)
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const dropContent = document.getElementById('drop-content');
    const previewStage = document.getElementById('preview-stage');
    const inputPreview = document.getElementById('input-preview');
    const fileNameLabel = document.getElementById('file-name-label');
    const removeFileBtn = document.getElementById('remove-file-btn');
    
    const processBtn = document.getElementById('process-btn');
    const loadingState = document.getElementById('loading');
    
    const resultsCard = document.getElementById('results-card');
    const metricsGrid = document.getElementById('metrics-grid');
    const downloadBtn = document.getElementById('download-btn');
    
    const inputImg = document.getElementById('input-image');
    const outputImg = document.getElementById('output-image');
    
    // Comparison Slider Elements
    const sliderWrapper = document.getElementById('slider-wrapper');
    const beforeWrapper = document.getElementById('before-wrapper');
    const sliderHandle = document.getElementById('slider-handle');

    // Analysis Section Elements
    const analysisSection = document.getElementById('analysis-section');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const analysisOutputImg = document.getElementById('analysis-output-img');
    const analysisLoading = document.getElementById('analysis-loading');
    const analysisTitle = document.getElementById('analysis-module-title');
    const analysisDesc = document.getElementById('analysis-module-desc');
    const analysisStatsContainer = document.getElementById('analysis-stats-container');
    const analysisDownloadBtn = document.getElementById('analysis-download-btn');

    let selectedFile = null;
    let currentProcessedFilename = null;
    let isDraggingSlider = false;
    let histogramChart = null;
    let analysisChart = null;
    let radarChart = null;
    let analysisDataStore = { ndvi: null, flood: null, building: null, landcover: null };

    // New DOM Elements
    const exportPdfBtn = document.getElementById('export-pdf-btn');
    const maskToggleBtn = document.getElementById('mask-toggle-btn');
    const maskImage = document.getElementById('mask-image');
    const magnifierGlass = document.getElementById('magnifier-glass');
    const globalDashboardSection = document.getElementById('global-dashboard-section');

    // --- File Drag & Drop Handlers ---
    dropArea.addEventListener('click', (e) => {
        if (e.target !== removeFileBtn && !removeFileBtn.contains(e.target)) {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropArea.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropArea.classList.remove('dragover');
        });
    });

    dropArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files && dt.files.length > 0) {
            handleSelectedFile(dt.files[0]);
        }
    });

    function handleSelectedFile(file) {
        selectedFile = file;
        fileNameLabel.textContent = file.name;

        const reader = new FileReader();
        reader.onload = (ev) => {
            inputPreview.src = ev.target.result;
            dropContent.classList.add('hidden');
            previewStage.classList.remove('hidden');
            processBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }

    removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = '';
        inputPreview.src = '';
        dropContent.classList.remove('hidden');
        previewStage.classList.add('hidden');
        processBtn.disabled = true;
    });

    // --- Image Processing Request ---
    processBtn.addEventListener('click', async () => {
        if (!selectedFile) {
            alert('Please select or drag a cloudy satellite image first!');
            return;
        }

        const formData = new FormData();
        formData.append('file', selectedFile);

        loadingState.classList.remove('hidden');
        processBtn.disabled = true;

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(data.error || 'Server error during cloud removal.');
            }

            // Store current processed filename for analysis triggers
            currentProcessedFilename = data.filename;

            // Populate Metrics Dashboard
            document.getElementById('time-metric').textContent = `${data.processing_time}s`;
            document.getElementById('input-size-metric').textContent = `${data.input_size} KB`;
            document.getElementById('output-size-metric').textContent = `${data.output_size} KB`;
            document.getElementById('contrast-metric').textContent = `+${data.contrast_improvement}%`;
            document.getElementById('haze-metric').textContent = `${data.haze_reduction_percent}%`;
            document.getElementById('cloud-coverage-est').textContent = `${data.cloud_coverage_est}%`;
            
            // Store cloud coverage for Radar Chart
            analysisDataStore.cloud_coverage = data.cloud_coverage_est;

            renderHistogram(data);

            // Set images for comparison
            inputImg.src = data.input_image_url;
            outputImg.src = `data:image/png;base64,${data.output_image}`;
            maskImage.src = data.mask_image_url;

            // Reset UI states
            maskToggleBtn.checked = false;
            maskImage.classList.add('hidden');
            analysisDataStore = { ndvi: null, flood: null, building: null, landcover: null, cloud_coverage: data.cloud_coverage_est };
            globalDashboardSection.classList.add('hidden');

            // Set Download URL
            downloadBtn.href = `/download/${data.filename}`;

            // Reset Split Slider position to 50%
            updateSliderPosition(50, true);

            // Display Results & Analysis Card
            resultsCard.classList.remove('hidden');
            analysisSection.classList.remove('hidden');

            // Scroll smoothly to results
            resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Trigger default NDVI analysis module automatically
            triggerAnalysis('ndvi');

        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            loadingState.classList.add('hidden');
            processBtn.disabled = false;
        }
    });

    // --- Interactive Split-Screen Image Slider ---
    function updateSliderPosition(clientX, isPercent = false) {
        const rect = sliderWrapper.getBoundingClientRect();
        let percent;

        if (isPercent) {
            percent = clientX; // clientX is already a percent value (0-100)
        } else {
            const relativeX = clientX - rect.left;
            percent = (relativeX / rect.width) * 100;
        }

        percent = Math.max(0, Math.min(100, percent));

        // Set full-width CSS var so .image-before renders at slider container width
        sliderWrapper.style.setProperty('--slider-full-width', rect.width + 'px');

        beforeWrapper.style.width = `${percent}%`;
        sliderHandle.style.left = `${percent}%`;
    }

    sliderWrapper.addEventListener('mousedown', (e) => {
        isDraggingSlider = true;
        updateSliderPosition(e.clientX);
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDraggingSlider) return;
        updateSliderPosition(e.clientX);
    });

    window.addEventListener('mouseup', () => {
        isDraggingSlider = false;
    });

    // Touch support for mobile devices
    sliderWrapper.addEventListener('touchstart', (e) => {
        isDraggingSlider = true;
        updateSliderPosition(e.touches[0].clientX);
    });

    window.addEventListener('touchmove', (e) => {
        if (!isDraggingSlider) return;
        updateSliderPosition(e.touches[0].clientX);
    });

    window.addEventListener('touchend', () => {
        isDraggingSlider = false;
    });

    // --- Post-Processing Analysis Module Selection ---
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const moduleName = btn.getAttribute('data-module');
            triggerAnalysis(moduleName);
        });
    });

    async function triggerAnalysis(moduleName) {
        if (!currentProcessedFilename) return;

        analysisLoading.classList.remove('hidden');

        try {
            const response = await fetch(`/analyze/${moduleName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename: currentProcessedFilename })
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(data.error || 'Failed to compute sector analysis.');
            }

            // Update UI with analysis data
            analysisOutputImg.src = data.analysis_image_url;
            analysisTitle.textContent = data.title;
            analysisDesc.textContent = data.description;
            analysisDownloadBtn.href = data.download_url;

            // Render dynamic stats cards
            analysisStatsContainer.innerHTML = '';
            data.stats.forEach(stat => {
                const statCard = document.createElement('div');
                statCard.className = 'stat-card';
                statCard.style.borderLeftColor = stat.color || '#00f3ff';
                statCard.innerHTML = `
                    <span class="stat-label">${stat.label}</span>
                    <span class="stat-val" style="color: ${stat.color || '#fff'}">${stat.value}</span>
                `;
                analysisStatsContainer.appendChild(statCard);
            });

            if (data.chart_data) {
                renderAnalysisChart(data.chart_data);
            }

            // Store data for Global Dashboard
            analysisDataStore[moduleName] = data;
            checkAndRenderRadarChart();

        } catch (err) {
            console.error('Analysis error:', err);
            alert(`Analysis Error: ${err.message}`);
        } finally {
            analysisLoading.classList.add('hidden');
        }
    }

    // --- Advanced Features Logic ---

    // 1. Cloud Mask Toggle
    maskToggleBtn.addEventListener('change', (e) => {
        if (e.target.checked) {
            maskImage.classList.remove('hidden');
        } else {
            maskImage.classList.add('hidden');
        }
    });

    // 2. Export PDF Report
    exportPdfBtn.addEventListener('click', () => {
        const element = document.querySelector('.app-container');
        const opt = {
            margin:       0.5,
            filename:     `SIH_Report_${currentProcessedFilename || 'Satellite'}.pdf`,
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2, useCORS: true },
            jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
        };
        
        // Hide elements we don't want in the PDF
        const actionBtns = document.querySelectorAll('.action-buttons, .analysis-actions, .slider-instruction, .btn-primary');
        actionBtns.forEach(btn => btn.style.display = 'none');
        
        html2pdf().set(opt).from(element).save().then(() => {
            // Restore hidden elements
            actionBtns.forEach(btn => btn.style.display = '');
        });
    });

    // 3. Magnifying Glass
    sliderWrapper.addEventListener('mousemove', (e) => {
        if (isDraggingSlider) return;
        
        const rect = sliderWrapper.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Only show if hovering over the image
        if (x > 0 && y > 0 && x < rect.width && y < rect.height) {
            magnifierGlass.classList.remove('hidden');
            magnifierGlass.style.left = `${x}px`;
            magnifierGlass.style.top = `${y}px`;
            
            // Calculate background position based on mouse position percentages
            const xPercent = (x / rect.width) * 100;
            const yPercent = (y / rect.height) * 100;
            
            magnifierGlass.style.backgroundImage = `url('${outputImg.src}')`;
            magnifierGlass.style.backgroundSize = `${rect.width * 2.5}px ${rect.height * 2.5}px`; // Zoom level
            magnifierGlass.style.backgroundPosition = `${xPercent}% ${yPercent}%`;
        } else {
            magnifierGlass.classList.add('hidden');
        }
    });

    sliderWrapper.addEventListener('mouseleave', () => {
        magnifierGlass.classList.add('hidden');
    });

    // 4. Global Radar Chart Logic
    function checkAndRenderRadarChart() {
        // Render if at least one module is run
        globalDashboardSection.classList.remove('hidden');

        // Extract normalized metrics (0-100 scale)
        const cloudMetric = 100 - (analysisDataStore.cloud_coverage || 0); // Inverse: Higher is better (less clouds)
        
        let vegMetric = 0;
        if (analysisDataStore.ndvi) {
            vegMetric = parseFloat(analysisDataStore.ndvi.stats[0].value) || 0; // Dense Veg %
        }
        
        let waterMetric = 0;
        if (analysisDataStore.flood) {
            waterMetric = parseFloat(analysisDataStore.flood.stats[0].value) || 0; // Water %
        }
        
        let urbanMetric = 0;
        if (analysisDataStore.building) {
            urbanMetric = parseFloat(analysisDataStore.building.stats[1].value) || 0; // Urban Density %
        }

        renderRadarChart([cloudMetric, vegMetric, waterMetric, urbanMetric]);
    }

    // --- Chart.js Rendering Functions ---
    function renderHistogram(data) {
        const ctx = document.getElementById('intensity-histogram').getContext('2d');
        if (histogramChart) histogramChart.destroy();
        
        histogramChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.histogram_labels,
                datasets: [
                    {
                        label: 'Before (Cloudy)',
                        data: data.histogram_before,
                        borderColor: '#94a3b8',
                        backgroundColor: 'rgba(148, 163, 184, 0.2)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'After (Clear)',
                        data: data.histogram_after,
                        borderColor: '#00f3ff',
                        backgroundColor: 'rgba(0, 243, 255, 0.2)',
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#f8fafc', font: { family: "'Inter', sans-serif" } } } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true, title: { display: true, text: '% of Pixels', color: '#94a3b8' } }
                }
            }
        });
    }

    function renderAnalysisChart(chartData) {
        const ctx = document.getElementById('analysis-chart').getContext('2d');
        if (analysisChart) analysisChart.destroy();
        
        analysisChart = new Chart(ctx, {
            type: chartData.type,
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.data,
                    backgroundColor: chartData.colors,
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#f8fafc', padding: 15, font: { family: "'Inter', sans-serif" } } }
                },
                cutout: chartData.type === 'doughnut' ? '65%' : 0 // For doughnut charts
            }
        });
    }

    function renderRadarChart(dataArr) {
        const ctx = document.getElementById('radar-chart').getContext('2d');
        if (radarChart) radarChart.destroy();

        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Visibility Score', 'Vegetation Index', 'Hydrological Index', 'Urban Footprint'],
                datasets: [{
                    label: 'Region Fingerprint',
                    data: dataArr,
                    backgroundColor: 'rgba(0, 243, 255, 0.3)',
                    borderColor: '#00f3ff',
                    pointBackgroundColor: '#00f3ff',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#00f3ff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255,255,255,0.1)' },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        pointLabels: { color: '#f8fafc', font: { size: 14, family: "'Inter', sans-serif" } },
                        ticks: { display: false, min: 0, max: 100 }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
});

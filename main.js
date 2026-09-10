/**
 * Satellite Cloud Removal & Analysis System
 * Frontend Controller for SIH 2026 Space Technology Solution (ID: 26209)
 */

document.addEventListener('DOMContentLoaded', () => {
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
    const downloadBtn = document.getElementById('download-btn');
    
    const inputImg = document.getElementById('input-image');
    const outputImg = document.getElementById('output-image');
    
    const sliderWrapper = document.getElementById('slider-wrapper');
    const beforeWrapper = document.getElementById('before-wrapper');
    const sliderHandle = document.getElementById('slider-handle');

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

            currentProcessedFilename = data.filename;

            document.getElementById('time-metric').textContent = `${data.processing_time}s`;
            document.getElementById('input-size-metric').textContent = `${data.input_size} KB`;
            document.getElementById('output-size-metric').textContent = `${data.output_size} KB`;
            document.getElementById('contrast-metric').textContent = `+${data.contrast_improvement}%`;
            document.getElementById('haze-metric').textContent = `${data.haze_reduction_percent}%`;

            inputImg.src = data.input_image_url;
            outputImg.src = `data:image/png;base64,${data.output_image}`;

            downloadBtn.href = `/download/${data.filename}`;

            updateSliderPosition(50);

            resultsCard.classList.remove('hidden');
            analysisSection.classList.remove('hidden');

            resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

            triggerAnalysis('ndvi');

        } catch (err) {
            alert(`Error: ${err.message}`);
        } finally {
            loadingState.classList.add('hidden');
            processBtn.disabled = false;
        }
    });

    function updateSliderPosition(posX) {
        const rect = sliderWrapper.getBoundingClientRect();
        let percent = (posX / rect.width) * 100;

        if (typeof posX === 'number' && posX === 50) {
            percent = 50;
        } else {
            const relativeX = posX - rect.left;
            percent = (relativeX / rect.width) * 100;
        }

        percent = Math.max(0, Math.min(100, percent));
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

            analysisOutputImg.src = data.analysis_image_url;
            analysisTitle.textContent = data.title;
            analysisDesc.textContent = data.description;
            analysisDownloadBtn.href = data.download_url;

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

        } catch (err) {
            console.error('Analysis error:', err);
            alert(`Analysis Error: ${err.message}`);
        } finally {
            analysisLoading.classList.add('hidden');
        }
    }
});

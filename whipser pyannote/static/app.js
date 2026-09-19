document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements - Settings & Single Mode
    const singleModeBtn = document.getElementById('singleModeBtn');
    const batchModeBtn = document.getElementById('batchModeBtn');
    const singleDropzone = document.getElementById('dropzone');
    const audioInput = document.getElementById('audioInput');
    const fileInfo = document.getElementById('fileInfo');

    // DOM Elements - Batch Mode
    const batchDropzoneContainer = document.getElementById('batchDropzoneContainer');
    const batchDropzone = document.getElementById('batchDropzone');
    const folderInput = document.getElementById('folderInput');
    const multiFileInput = document.getElementById('multiFileInput');
    const batchQueueCard = document.getElementById('batchQueueCard');
    const batchQueueTitle = document.getElementById('batchQueueTitle');
    const batchQueueSummary = document.getElementById('batchQueueSummary');
    const batchFileList = document.getElementById('batchFileList');
    const clearBatchBtn = document.getElementById('clearBatchBtn');

    // DOM Elements - Common Controls & Configuration
    const hfTokenInput = document.getElementById('hfToken');
    const whisperModel = document.getElementById('whisperModel');
    const deviceSelect = document.getElementById('deviceSelect');
    const languageSelect = document.getElementById('languageSelect');
    const initialPromptInput = document.getElementById('initialPrompt');
    const processBtn = document.getElementById('processBtn');

    // DOM Elements - Outcomes & Progress
    const emptyState = document.getElementById('emptyState');
    const progressContainer = document.getElementById('progressContainer');
    const progressMessage = document.getElementById('progressMessage');
    const progressPercent = document.getElementById('progressPercent');
    const progressBarFill = document.getElementById('progressBarFill');
    const progressSubdetail = document.getElementById('progressSubdetail');
    const timerElapsed = document.getElementById('timerElapsed');
    const timerETA = document.getElementById('timerETA');
    const stopBtn = document.getElementById('stopBtn');

    // DOM Elements - Batch Progress Tracker
    const batchOverallTracker = document.getElementById('batchOverallTracker');
    const batchOverallTitle = document.getElementById('batchOverallTitle');
    const batchOverallPercent = document.getElementById('batchOverallPercent');
    const batchOverallBarFill = document.getElementById('batchOverallBarFill');
    const batchOverallDetail = document.getElementById('batchOverallDetail');
    const batchCurrentFileName = document.getElementById('batchCurrentFileName');

    // DOM Elements - Results & Error
    const errorBox = document.getElementById('errorBox');
    const errorMessage = document.getElementById('errorMessage');
    const errorActions = document.getElementById('errorActions');
    const resultsViewer = document.getElementById('resultsViewer');

    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const diarizationPreview = document.getElementById('diarizationPreview');
    const sttPreview = document.getElementById('sttPreview');
    const mergedPreview = document.getElementById('mergedPreview');
    const metaInfo = document.getElementById('metaInfo');
    const copyBtn = document.getElementById('copyBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    // Application State
    let currentMode = 'single'; // 'single' | 'batch'
    let selectedFile = null;
    let batchFiles = []; // Array of { file: File, name: string, size: number, status: 'queued'|'skipped'|'processing'|'completed'|'failed', jobId: string|null }
    let isBatchRunning = false;
    let currentJobId = null;
    let currentJobData = null;
    let activeTab = 'diarization';
    let pollInterval = null;
    let jobStartTime = null;
    let timerInterval = null;
    let isSubmitting = false;

    // Restore saved HF token from localStorage
    const savedToken = localStorage.getItem('hf_token');
    if (savedToken) {
        hfTokenInput.value = savedToken;
    }
    hfTokenInput.addEventListener('change', () => {
        localStorage.setItem('hf_token', hfTokenInput.value.trim());
    });

    // Restore saved Google Gemini API Key from localStorage
    const geminiApiKeyInput = document.getElementById('geminiApiKey');
    const savedGeminiKey = localStorage.getItem('gemini_api_key');
    if (savedGeminiKey && geminiApiKeyInput) {
        geminiApiKeyInput.value = savedGeminiKey;
    }
    if (geminiApiKeyInput) {
        geminiApiKeyInput.addEventListener('change', () => {
            localStorage.setItem('gemini_api_key', geminiApiKeyInput.value.trim());
        });
        geminiApiKeyInput.addEventListener('input', () => {
            localStorage.setItem('gemini_api_key', geminiApiKeyInput.value.trim());
        });
    }

    // Check System GPU / CPU status and downloaded models
    const cudaHelpText = document.getElementById('cudaHelpText');
    fetch('/api/system-info')
        .then(res => res.json())
        .then(info => {
            if (cudaHelpText) {
                if (info.cuda_available) {
                    cudaHelpText.innerHTML = `<span style="color: #10b981; font-weight: 600;">✓ GPU Active:</span> ${info.device_name}`;
                } else {
                    cudaHelpText.innerHTML = `<span style="color: #f59e0b; font-weight: 500;">CPU Mode (PyTorch CPU build detected)</span>`;
                }
            }

            const cachedModels = info.cached_models || [];
            Array.from(whisperModel.options).forEach(opt => {
                const isCached = cachedModels.includes(opt.value);
                const baseText = opt.text.split(' - ')[0];
                if (isCached) {
                    opt.text = `${baseText} - [Downloaded ✓]`;
                } else {
                    opt.text = `${baseText} - [Requires Download]`;
                }
            });
        })
        .catch(() => {});

    // Mode Switcher Handlers
    function switchMode(mode) {
        currentMode = mode;
        if (mode === 'single') {
            if (singleModeBtn) singleModeBtn.classList.add('active');
            if (batchModeBtn) batchModeBtn.classList.remove('active');
            if (singleDropzone) singleDropzone.classList.remove('hidden');
            if (batchDropzoneContainer) batchDropzoneContainer.classList.add('hidden');
            updateProcessBtnState();
        } else {
            if (batchModeBtn) batchModeBtn.classList.add('active');
            if (singleModeBtn) singleModeBtn.classList.remove('active');
            if (batchDropzoneContainer) batchDropzoneContainer.classList.remove('hidden');
            if (singleDropzone) singleDropzone.classList.add('hidden');
            updateProcessBtnState();
        }
    }

    if (singleModeBtn) singleModeBtn.addEventListener('click', () => switchMode('single'));
    if (batchModeBtn) batchModeBtn.addEventListener('click', () => switchMode('batch'));

    function updateProcessBtnState() {
        if (isSubmitting || isBatchRunning) return;
        if (currentMode === 'single') {
            if (selectedFile) {
                processBtn.disabled = false;
                processBtn.style.opacity = '1';
                processBtn.style.cursor = 'pointer';
                processBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Start Processing Audio`;
            } else {
                processBtn.disabled = true;
                processBtn.style.opacity = '0.6';
                processBtn.style.cursor = 'not-allowed';
                processBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Start Processing Audio`;
            }
        } else {
            const pendingCount = batchFiles.filter(f => f.status === 'queued').length;
            if (pendingCount > 0) {
                processBtn.disabled = false;
                processBtn.style.opacity = '1';
                processBtn.style.cursor = 'pointer';
                processBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Start Batch Queue (${pendingCount} files)`;
            } else if (batchFiles.length > 0) {
                processBtn.disabled = true;
                processBtn.style.opacity = '0.6';
                processBtn.style.cursor = 'not-allowed';
                processBtn.innerHTML = `All ${batchFiles.length} files already completed ✓`;
            } else {
                processBtn.disabled = true;
                processBtn.style.opacity = '0.6';
                processBtn.style.cursor = 'not-allowed';
                processBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Start Batch Queue`;
            }
        }
    }

    // Single Dropzone Drag & Drop Handlers
    ['dragenter', 'dragover'].forEach(eventName => {
        singleDropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            singleDropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        singleDropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            singleDropzone.classList.remove('dragover');
        });
    });

    singleDropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    audioInput.onchange = function() {
        if (this.files && this.files.length > 0) {
            handleFileSelect(this.files[0]);
        }
    };

    function handleFileSelect(file) {
        if (!file) return;
        selectedFile = file;
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        fileInfo.innerHTML = `<span style="color: #10b981; font-weight: 600;">✓ Selected:</span> <strong>${file.name}</strong> (${sizeMb} MB)`;
        singleDropzone.classList.add('has-file');
        updateProcessBtnState();
        if (errorBox) errorBox.classList.add('hidden');
    }

    // Batch Dropzone Drag & Drop Handlers
    if (batchDropzone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            batchDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                batchDropzone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            batchDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                batchDropzone.classList.remove('dragover');
            });
        });

        batchDropzone.addEventListener('drop', async (e) => {
            const items = e.dataTransfer.items;
            const collectedFiles = [];

            if (items && items.length > 0) {
                const entries = [];
                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    if (item.webkitGetAsEntry) {
                        const entry = item.webkitGetAsEntry();
                        if (entry) entries.push(entry);
                    }
                }
                if (entries.length > 0) {
                    for (const entry of entries) {
                        await scanEntry(entry, collectedFiles);
                    }
                }
            }

            if (collectedFiles.length === 0 && e.dataTransfer.files.length > 0) {
                for (let i = 0; i < e.dataTransfer.files.length; i++) {
                    const f = e.dataTransfer.files[i];
                    if (f.name.toLowerCase().endsWith('.wav')) {
                        collectedFiles.push(f);
                    }
                }
            }

            if (collectedFiles.length > 0) {
                await addFilesToBatch(collectedFiles);
            }
        });
    }

    async function scanEntry(entry, collectedFiles) {
        if (entry.isFile) {
            const name = entry.name || '';
            if (name.toLowerCase().endsWith('.wav')) {
                const file = await new Promise(res => entry.file(res));
                collectedFiles.push(file);
            }
        } else if (entry.isDirectory) {
            const dirReader = entry.createReader();
            const readBatch = () => new Promise(res => dirReader.readEntries(res, () => res([])));
            let entries = await readBatch();
            while (entries && entries.length > 0) {
                for (const subEntry of entries) {
                    await scanEntry(subEntry, collectedFiles);
                }
                entries = await readBatch();
            }
        }
    }

    if (folderInput) {
        folderInput.onchange = async function() {
            if (this.files && this.files.length > 0) {
                const wavs = Array.from(this.files).filter(f => f.name.toLowerCase().endsWith('.wav'));
                await addFilesToBatch(wavs);
            }
            this.value = '';
        };
    }

    if (multiFileInput) {
        multiFileInput.onchange = async function() {
            if (this.files && this.files.length > 0) {
                const wavs = Array.from(this.files).filter(f => f.name.toLowerCase().endsWith('.wav'));
                await addFilesToBatch(wavs);
            }
            this.value = '';
        };
    }

    if (clearBatchBtn) {
        clearBatchBtn.addEventListener('click', () => {
            batchFiles = [];
            renderBatchQueue();
            if (batchQueueCard) batchQueueCard.classList.add('hidden');
            updateProcessBtnState();
        });
    }

    function getCleanBaseName(rawName) {
        if (!rawName) return 'audio.wav';
        return rawName.replace(/^.*[\\\/]/, '').trim();
    }

    async function addFilesToBatch(filesList) {
        if (!filesList || filesList.length === 0) return;
        const existingNames = new Set(batchFiles.map(f => f.name.toLowerCase()));

        for (const file of filesList) {
            const cleanName = getCleanBaseName(file.name);
            if (!existingNames.has(cleanName.toLowerCase()) && cleanName.toLowerCase().endsWith('.wav')) {
                existingNames.add(cleanName.toLowerCase());
                batchFiles.push({
                    file: file,
                    name: cleanName,
                    size: file.size,
                    status: 'queued',
                    jobId: null,
                    error: null
                });
            }
        }

        if (batchQueueCard) batchQueueCard.classList.remove('hidden');
        await checkBatchFilesWithBackend();
        renderBatchQueue();
        updateProcessBtnState();
    }

    async function checkBatchFilesWithBackend() {
        if (batchFiles.length === 0) return;
        try {
            const filenames = batchFiles.map(f => f.name);
            const res = await fetch('/api/check-files', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filenames })
            });
            if (res.ok) {
                const data = await res.json();
                const checkMap = data.results || {};
                for (const item of batchFiles) {
                    const info = checkMap[item.name];
                    if (info && info.exists && info.status === 'completed') {
                        item.status = 'skipped';
                        item.jobId = info.job_id;
                    } else if (item.status !== 'completed') {
                        item.status = 'queued';
                    }
                }
            }
        } catch (e) {
            console.warn('Check files error:', e);
        }
    }

    function renderBatchQueue() {
        if (!batchFileList) return;
        if (batchFiles.length === 0) {
            batchFileList.innerHTML = '<p class="text-muted" style="text-align: center; padding: 10px; font-size: 0.8rem;">No audio files in queue.</p>';
            if (batchQueueCard) batchQueueCard.classList.add('hidden');
            return;
        }

        if (batchQueueCard) batchQueueCard.classList.remove('hidden');
        const completedOrSkipped = batchFiles.filter(f => f.status === 'skipped' || f.status === 'completed').length;
        const queuedCount = batchFiles.filter(f => f.status === 'queued').length;

        if (batchQueueTitle) batchQueueTitle.textContent = `Batch Queue (${batchFiles.length} files)`;
        if (batchQueueSummary) batchQueueSummary.textContent = `${queuedCount} ready to process, ${completedOrSkipped} already completed (will skip)`;

        batchFileList.innerHTML = batchFiles.map((item, idx) => {
            const sizeMb = (item.size / (1024 * 1024)).toFixed(1);
            let badgeHtml = '';
            let extraClass = '';

            if (item.status === 'skipped') {
                badgeHtml = `<span class="badge-status badge-skip view-job-btn" data-jobid="${item.jobId || ''}" title="Already processed in past job. Click to open results." style="cursor: pointer;">⏩ Skipped (Completed)</span>`;
                extraClass = 'is-skipped';
            } else if (item.status === 'completed') {
                badgeHtml = `<span class="badge-status badge-completed view-job-btn" data-jobid="${item.jobId || ''}" title="Processing finished. Click to open results." style="cursor: pointer;">✓ Completed</span>`;
                extraClass = 'is-completed';
            } else if (item.status === 'processing') {
                badgeHtml = `<span class="badge-status badge-processing">⚙️ Processing...</span>`;
                extraClass = 'current-processing';
            } else if (item.status === 'failed') {
                badgeHtml = `<span class="badge-status badge-error" title="${item.error || 'Failed'}">❌ Failed</span>`;
            } else {
                badgeHtml = `<span class="badge-status badge-queued">⏳ Queued</span>`;
            }

            return `
                <div class="batch-file-item ${extraClass}" id="batch-item-${idx}">
                    <div>
                        <div class="batch-file-name" title="${item.name}">${item.name}</div>
                        <small style="color: var(--text-muted); font-size: 0.72rem;">${sizeMb} MB</small>
                    </div>
                    <div>
                        ${badgeHtml}
                    </div>
                </div>
            `;
        }).join('');

        // Bind quick view click on skipped / completed badges
        batchFileList.querySelectorAll('.view-job-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const jId = e.currentTarget.dataset.jobid;
                if (!jId) return;
                try {
                    const res = await fetch(`/api/job/${jId}`);
                    if (res.ok) {
                        const data = await res.json();
                        if (data.results) {
                            currentJobId = jId;
                            showResults(data.results);
                            resultsViewer.scrollIntoView({ behavior: 'smooth' });
                        }
                    }
                } catch (_) {}
            });
        });
    }

    function formatDuration(sec) {
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        const s = Math.floor(sec % 60);
        if (h > 0) return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    }

    function startTimer() {
        jobStartTime = Date.now();
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            if (!jobStartTime) return;
            const elapsedSec = Math.floor((Date.now() - jobStartTime) / 1000);
            if (timerElapsed) timerElapsed.textContent = `Elapsed: ${formatDuration(elapsedSec)}`;
        }, 1000);
    }

    // Stop / Cancel Button Handler
    stopBtn.addEventListener('click', async () => {
        isBatchRunning = false;
        if (!currentJobId) return;
        stopBtn.disabled = true;
        stopBtn.textContent = 'Cancelling...';

        try {
            await fetch(`/api/cancel/${currentJobId}`, { method: 'POST' });
        } catch (e) {
            console.error('Cancel request error:', e);
        }
    });

    // Poll Status with retry resilience
    async function pollJobStatus(jobId) {
        if (pollInterval) clearInterval(pollInterval);
        let consecutiveErrors = 0;

        pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/job/${jobId}`);
                if (!res.ok) throw new Error('Server status pending');

                const job = await res.json();
                currentJobData = job;
                consecutiveErrors = 0;

                updateProgress(job.progress, job.message, job.step_detail);
                updateSteps(job.status);

                if (job.step_detail && job.step_detail.includes('ETA:')) {
                    const parts = job.step_detail.split('|');
                    if (timerETA && parts[0]) timerETA.textContent = parts[0].trim();
                    if (progressSubdetail && parts[1]) progressSubdetail.textContent = parts[1].trim();
                }

                if (job.status === 'completed') {
                    clearInterval(pollInterval);
                    if (timerInterval) clearInterval(timerInterval);
                    if (timerETA) timerETA.textContent = 'ETA: Completed!';
                    showResults(job.results);
                    processBtn.disabled = false;
                    loadPreviousJobs();
                } else if (job.status === 'error') {
                    clearInterval(pollInterval);
                    if (timerInterval) clearInterval(timerInterval);
                    showError(job.error || job.message);
                    processBtn.disabled = false;
                } else if (job.status === 'cancelled') {
                    clearInterval(pollInterval);
                    if (timerInterval) clearInterval(timerInterval);
                    showError('Processing cancelled by user.');
                    processBtn.disabled = false;
                    stopBtn.disabled = false;
                    stopBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg> Stop Processing`;
                }

            } catch (err) {
                consecutiveErrors++;
                if (consecutiveErrors >= 5) {
                    clearInterval(pollInterval);
                    if (timerInterval) clearInterval(timerInterval);
                    showError('Connection lost. Server unavailable.');
                    processBtn.disabled = false;
                }
            }
        }, 1200);
    }

    // Promise wrapper for polling used by Batch Runner
    function pollJobUntilFinished(jobId) {
        return new Promise((resolve, reject) => {
            let consecutiveFailures = 0;
            let pInterval = setInterval(async () => {
                if (!isBatchRunning) {
                    clearInterval(pInterval);
                    reject(new Error('Batch cancelled by user'));
                    return;
                }
                try {
                    const res = await fetch(`/api/job/${jobId}`);
                    if (!res.ok) {
                        consecutiveFailures++;
                        if (consecutiveFailures > 10) {
                            clearInterval(pInterval);
                            reject(new Error(`Server error reading job ${jobId} (HTTP ${res.status})`));
                        }
                        return;
                    }
                    const job = await res.json();
                    consecutiveFailures = 0;

                    updateProgress(job.progress || 5, job.message || 'Processing audio...', job.step_detail || '');
                    updateSteps(job.status);

                    if (job.status === 'completed') {
                        clearInterval(pInterval);
                        resolve(job);
                    } else if (job.status === 'error') {
                        clearInterval(pInterval);
                        reject(new Error(job.error || job.message || 'Job failed'));
                    } else if (job.status === 'cancelled') {
                        clearInterval(pInterval);
                        reject(new Error('Processing was cancelled'));
                    }
                } catch (e) {
                    consecutiveFailures++;
                    if (consecutiveFailures > 10) {
                        clearInterval(pInterval);
                        reject(new Error('Connection lost to audio processor backend.'));
                    }
                }
            }, 1500);
        });
    }

    // Ollama AI Guard UI Elements
    const ollamaUrlInput = document.getElementById('ollamaUrl');
    const fetchOllamaModelsBtn = document.getElementById('fetchOllamaModelsBtn');
    const ollamaModelSelect = document.getElementById('ollamaModelSelect');
    const statusText = document.getElementById('ollamaStatusText');

    if (fetchOllamaModelsBtn) {
        fetchOllamaModelsBtn.addEventListener('click', () => loadOllamaModels());
    }

    const RECOMMENDED_AI_PROMPT = `شما یک پزشک متخصص و بازساز ارشد پرونده‌های صوتی کلینیک و مطب پزشکی هستید.
متن ورودی زیر مکالمه صوتی پیاده‌سازی شده از گفتگوی بین پزشک و بیماران در مطب است.

وظایف الزامی و بدون تغییر شما:
۱. تعیین و تفکیک دقیق نقش گویندگان و حفظ شماره بیماران (Doctor vs Patients):
   - برچسب "doctor:": برای پزشک (فردی که سوالات تشخیصی و معاینه می‌پرسد، علائم را بررسی می‌کند و دستور مصرف دارو یا آزمایش می‌دهد).
   - حفظ شماره دقیق بیماران: در صورت حضور چند بیمار یا همراه مختلف (مانند patient_1, patient_2, patient_3, ...)، شماره هر بیمار را عیناً و با دقت کامل در خروجی حفظ کنید: "patient_1:", "patient_2:", "patient_3:", ... هرگز شماره بیمار را حذف نکنید و آن را به "patient:" عمومی تبدیل نکنید.
   - اگر فقط یک بیمار در کل مکالمه حضور دارد، از برچسب "patient:" استفاده کنید.
   - اگر گویندگان با برچسب‌های بدون نام مانند SPEAKER_00, SPEAKER_01, SPEAKER_02 آمده‌اند، آن‌ها را بر اساس مکالمه به doctor: و patient_1:, patient_2: تبدیل کنید.
   - هرگز از برچسب نامشخص و خنثی "SPEAKER:" استفاده نکنید.
۲. حفظ کامل برچسب‌های تداخل کلامی و صحبت همزمان (Overlapped Talks):
   - اگر در ورودی هر خط دارای عبارت تداخل کلامی است (مانند "doctor (overlapped by patient_1):" یا "patient_1 (overlapped by doctor):" یا "patient_2 (overlapped by doctor):")، عبارت داخل پرانتز یعنی "(overlapped by ...)" را دقیقاً و به طور کامل در خروجی بعد از نام گوینده حفظ کنید.
   - هرگز خطوط تداخل کلامی را حذف یا در خط دیگر ادغام نکنید.
۳. اصلاح و روان‌سازی اصطلاحات پزشکی و خطاهای شنیداری:
   - املای داروها، بیماری‌ها، آزمایش‌ها و اصطلاحات پزشکی را به شکل صحیح، علمی و استاندارد فارسی اصلاح کنید.
   - کلمات عامیانه، جویده‌شده یا ناقص را بدون تحریف پیام اصلی به فارسی سلیس و روان تبدیل کنید.
۴. پالایش و حذف نویزها و توهمات صوتی:
   - جملات نامربوط ناشی از موزیک پس‌زمینه یا تکرار کلمات بی‌معنی را پالایش کنید.
۵. حفظ ساختار خط‌به‌خط و زمان‌بندی:
   - ساختار زمان‌بندی [HH:MM:SS.mmm --> HH:MM:SS.mmm] را در ابتدای هر خط به طور کامل و بدون کوچک‌ترین تغییری حفظ کنید.
   - تمام خطوط دارای زمان‌بندی ورودی را به ترتیب بازسازی کنید و از حذف، خلاصه کردن یا ادغام بی‌مورد خطوط خودداری نمایید.

قالب خروجی دقیق خط‌به‌خط:
[00:00:30.000 --> 00:00:32.000] patient_1: از دیشب تب شدید دارد.
[00:00:32.000 --> 00:00:34.000] doctor (overlapped by patient_1): تبش چقدر بوده؟
[00:00:34.500 --> 00:00:38.000] patient_2 (overlapped by doctor): منم همراهش بودم، دیشب بالای ۳۹ درجه بود.`;

    async function loadOllamaModels() {
        if (!ollamaModelSelect) return;
        const baseUrl = ollamaUrlInput ? (ollamaUrlInput.value.trim() || 'http://127.0.0.1:11434') : 'http://127.0.0.1:11434';
        try {
            if (fetchOllamaModelsBtn) fetchOllamaModelsBtn.classList.add('spinning');
            const res = await fetch(`/api/ollama/models?base_url=${encodeURIComponent(baseUrl)}`);
            if (!res.ok) throw new Error('Ollama connection failed');
            const data = await res.json();
            
            const geminiModels = data.gemini_models || [];
            const models = data.models || [];
            const standaloneModels = data.standalone_models || [];

            let optionsHtml = '<option value="">Disabled / Off</option>';

            if (geminiModels.length > 0) {
                optionsHtml += `<optgroup label="☁️ Google Gemini Cloud API (Ultra Fast - Zero GPU Heat)">`;
                optionsHtml += geminiModels.map((gm) => {
                    const sel = (gm.name === 'gemini:gemini-3.5-flash-lite') ? 'selected' : '';
                    return `<option value="${gm.name}" ${sel}>${gm.label}</option>`;
                }).join('');
                optionsHtml += `</optgroup>`;
            }

            if (models.length > 0) {
                optionsHtml += `<optgroup label="🦙 Ollama Local Server Models">`;
                optionsHtml += models.map((m) => {
                    const isRecommended = (m === 'gemma3:12b' || m.includes('12b') || m.includes('llama3'));
                    const sel = (geminiModels.length === 0 && isRecommended) ? 'selected' : '';
                    return `<option value="${m}" ${sel}>${m}${isRecommended ? ' (Recommended)' : ''}</option>`;
                }).join('');
                optionsHtml += `</optgroup>`;
            }

            if (standaloneModels.length > 0) {
                optionsHtml += `<optgroup label="⚡ Standalone App LLMs (Auto-Download - No Ollama Needed)">`;
                optionsHtml += standaloneModels.map((sm) => {
                    return `<option value="${sm.name}">${sm.label}</option>`;
                }).join('');
                optionsHtml += `</optgroup>`;
            }

            ollamaModelSelect.innerHTML = optionsHtml;

            const aiPromptInput = document.getElementById('aiPrompt');
            const targetPrompt = data.default_prompt || RECOMMENDED_AI_PROMPT;
            if (aiPromptInput) {
                if (!aiPromptInput.value || 
                    aiPromptInput.value.includes('هر خط باید منحصراً و حتماً با برچسب') || 
                    aiPromptInput.value.includes('هر خط باید منحصرا و حتما با برچسب') ||
                    !aiPromptInput.value.includes('patient_1')) {
                    aiPromptInput.value = targetPrompt;
                }
            }

            if (statusText) statusText.innerHTML = `<span style="color: #10b981; font-weight: 500;">✓ Connected (${geminiModels.length} Cloud + ${models.length} Ollama + ${standaloneModels.length} Standalone available)</span>`;
            if (fetchOllamaModelsBtn) {
                setTimeout(() => { fetchOllamaModelsBtn.classList.remove('spinning'); }, 500);
            }
        } catch (err) {
            if (fetchOllamaModelsBtn) {
                fetchOllamaModelsBtn.classList.remove('spinning');
            }
            if (statusText) statusText.innerHTML = `<span style="color: #f59e0b; font-weight: 500;">Ollama offline (Gemini Cloud & Standalone available)</span>`;
            ollamaModelSelect.innerHTML = `
                <option value="">Disabled / Off</option>
                <optgroup label="☁️ Google Gemini Cloud API (API Key Required)">
                    <option value="gemini:gemini-3.5-flash-lite" selected>⚡ Gemini 3.5 Flash Lite (Ultra Fast Cloud - Recommended)</option>
                    <option value="gemini:gemini-3.1-flash-lite">⚡ Gemini 3.1 Flash Lite (Ultra Fast Cloud)</option>
                    <option value="gemini:gemini-3.1-flash">⚡ Gemini 3.1 Flash (High Performance Cloud)</option>
                    <option value="gemini:gemini-3.1-pro">🧠 Gemini 3.1 Pro (Highest Accuracy Reasoning Cloud)</option>
                    <option value="gemini:gemini-2.5-flash-lite">☁️ Gemini 2.5 Flash Lite</option>
                    <option value="gemini:gemini-2.5-flash">☁️ Gemini 2.5 Flash</option>
                </optgroup>
                <optgroup label="⚡ Standalone App LLMs (No Ollama Needed)">
                    <option value="hf:CohereForAI/aya-23-8b">⚡ Standalone: Cohere Aya-23 8B (5.2 GB - Best Persian Model)</option>
                    <option value="hf:Qwen/Qwen2.5-14B-Instruct">⚡ Standalone: Qwen2.5 14B Instruct (14.2 GB - High Capacity)</option>
                    <option value="hf:Qwen/Qwen2.5-7B-Instruct">⚡ Standalone: Qwen2.5 7B Instruct (7.2 GB)</option>
                    <option value="hf:meta-llama/Meta-Llama-3.1-8B-Instruct">⚡ Standalone: Meta Llama 3.1 8B Instruct (5.1 GB - High Accuracy Persian)</option>
                    <option value="hf:deepseek-ai/DeepSeek-R1-Distill-Qwen-7B">⚡ Standalone: DeepSeek R1 Distill 7B (4.7 GB - Reasoning Engine)</option>
                    <option value="hf:Qwen/Qwen2.5-3B-Instruct">⚡ Standalone: Qwen2.5 3B Instruct (3.0 GB)</option>
                    <option value="hf:meta-llama/Llama-3.2-3B-Instruct">⚡ Standalone: Llama 3.2 3B Instruct (3.2 GB)</option>
                    <option value="hf:google/gemma-2-2b-it">⚡ Standalone: Gemma 2 2B IT (2.6 GB)</option>
                </optgroup>
            `;
            const aiPromptInput = document.getElementById('aiPrompt');
            if (aiPromptInput && (!aiPromptInput.value || !aiPromptInput.value.includes('patient_1'))) {
                aiPromptInput.value = RECOMMENDED_AI_PROMPT;
            }
        }
    }

    // Reset prompt button listener
    const resetPromptBtn = document.getElementById('resetPromptBtn');
    if (resetPromptBtn) {
        resetPromptBtn.addEventListener('click', () => {
            const aiPromptInput = document.getElementById('aiPrompt');
            if (aiPromptInput) {
                aiPromptInput.value = RECOMMENDED_AI_PROMPT;
                resetPromptBtn.textContent = '✓ Reset!';
                setTimeout(() => { resetPromptBtn.textContent = '🔄 Reset to Recommended Prompt'; }, 1500);
            }
        });
    }

    setTimeout(() => { loadOllamaModels(); }, 500);

    // Main Process Button Action (Routes to Single or Batch)
    processBtn.addEventListener('click', async (e) => {
        if (e) e.preventDefault();
        if (isSubmitting || isBatchRunning) return;

        const selectedOllamaModel = ollamaModelSelect ? ollamaModelSelect.value : '';
        const geminiApiKeyInput = document.getElementById('geminiApiKey');
        const apiKey = geminiApiKeyInput ? geminiApiKeyInput.value.trim() : '';

        if (selectedOllamaModel.startsWith('gemini:') && !apiKey) {
            alert('Please enter your Google Gemini API Key in the settings first to use Gemini AI refinement.');
            if (geminiApiKeyInput) geminiApiKeyInput.focus();
            return;
        }

        if (currentMode === 'batch') {
            await runBatchQueue();
        } else {
            await runSingleProcess();
        }
    });

    // Single File Processing
    async function runSingleProcess() {
        if (!selectedFile) return;

        const selectedOllamaModel = ollamaModelSelect ? ollamaModelSelect.value : '';
        const geminiApiKeyInput = document.getElementById('geminiApiKey');
        const aiPromptInput = document.getElementById('aiPrompt');
        const apiKey = geminiApiKeyInput ? geminiApiKeyInput.value.trim() : '';
        const speakerModeSelect = document.getElementById('speakerMode');
        const cleanName = getCleanBaseName(selectedFile.name);

        isSubmitting = true;
        processBtn.disabled = true;
        processBtn.style.opacity = '0.6';
        processBtn.style.cursor = 'not-allowed';

        emptyState.classList.add('hidden');
        errorBox.classList.add('hidden');
        resultsViewer.classList.add('hidden');
        if (batchOverallTracker) batchOverallTracker.classList.add('hidden');
        progressContainer.classList.remove('hidden');

        updateProgress(5, `Uploading ${cleanName}...`, 'Preparing single audio job');
        startTimer();

        const formData = new FormData();
        formData.append('file', selectedFile, cleanName);
        formData.append('whisper_model', whisperModel.value);
        formData.append('hf_token', hfTokenInput.value.trim());
        formData.append('device', deviceSelect.value);
        formData.append('language', languageSelect ? languageSelect.value : 'fa');
        formData.append('initial_prompt', initialPromptInput ? initialPromptInput.value.trim() : '');
        formData.append('speaker_mode', speakerModeSelect ? speakerModeSelect.value : 'doctor_patient');

        formData.append('enable_ai', selectedOllamaModel ? 'true' : 'false');
        formData.append('ollama_model', selectedOllamaModel);
        formData.append('ollama_url', ollamaUrlInput ? ollamaUrlInput.value.trim() : 'http://127.0.0.1:11434');
        formData.append('ai_prompt', aiPromptInput ? aiPromptInput.value.trim() : '');
        formData.append('gemini_api_key', apiKey);
        formData.append('skip_if_exists', 'false');

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errText = 'Upload failed';
                let isDuplicate = (response.status === 409);
                try {
                    const errData = await response.json();
                    errText = errData.detail || errText;
                } catch (_) {
                    errText = await response.text();
                }

                showError(errText, isDuplicate, cleanName);
                return;
            }

            const data = await response.json();
            currentJobId = data.job_id;
            pollJobStatus(currentJobId);
            loadPreviousJobs();

        } catch (err) {
            showError(err.message);
        } finally {
            isSubmitting = false;
            updateProcessBtnState();
        }
    }

    // Batch Queue Sequential Runner
    async function runBatchQueue() {
        const queuedItems = batchFiles.filter(f => f.status === 'queued');
        if (queuedItems.length === 0) {
            alert('All files in the queue have already been processed or skipped.');
            return;
        }

        isBatchRunning = true;
        processBtn.disabled = true;
        processBtn.style.opacity = '0.6';

        emptyState.classList.add('hidden');
        errorBox.classList.add('hidden');
        resultsViewer.classList.add('hidden');
        progressContainer.classList.remove('hidden');
        if (batchOverallTracker) batchOverallTracker.classList.remove('hidden');

        startTimer();

        const selectedOllamaModel = ollamaModelSelect ? ollamaModelSelect.value : '';
        const geminiApiKeyInput = document.getElementById('geminiApiKey');
        const aiPromptInput = document.getElementById('aiPrompt');
        const apiKey = geminiApiKeyInput ? geminiApiKeyInput.value.trim() : '';
        const speakerModeSelect = document.getElementById('speakerMode');

        let completedCount = batchFiles.filter(f => f.status === 'completed').length;
        let skippedCount = batchFiles.filter(f => f.status === 'skipped').length;
        const totalFiles = batchFiles.length;

        for (let i = 0; i < batchFiles.length; i++) {
            if (!isBatchRunning) break;
            const item = batchFiles[i];
            const cleanName = getCleanBaseName(item.name);

            // Update overall progress banner
            const progressRatio = Math.round(((i) / totalFiles) * 100);
            if (batchOverallTitle) batchOverallTitle.textContent = `Batch Progress: File ${i + 1} of ${totalFiles}`;
            if (batchOverallPercent) batchOverallPercent.textContent = `${progressRatio}%`;
            if (batchOverallBarFill) batchOverallBarFill.style.width = `${progressRatio}%`;
            if (batchOverallDetail) batchOverallDetail.textContent = `Completed: ${completedCount} | Skipped: ${skippedCount} | Remaining: ${totalFiles - i}`;
            if (batchCurrentFileName) batchCurrentFileName.textContent = `Current: ${cleanName}`;

            if (item.status === 'skipped') {
                continue;
            }

            item.status = 'processing';
            renderBatchQueue();

            updateProgress(5, `[File ${i + 1}/${totalFiles}] Uploading ${cleanName}...`, 'Submitting audio to queue worker');

            const formData = new FormData();
            formData.append('file', item.file, cleanName);
            formData.append('whisper_model', whisperModel.value);
            formData.append('hf_token', hfTokenInput.value.trim());
            formData.append('device', deviceSelect.value);
            formData.append('language', languageSelect ? languageSelect.value : 'fa');
            formData.append('initial_prompt', initialPromptInput ? initialPromptInput.value.trim() : '');
            formData.append('speaker_mode', speakerModeSelect ? speakerModeSelect.value : 'doctor_patient');

            formData.append('enable_ai', selectedOllamaModel ? 'true' : 'false');
            formData.append('ollama_model', selectedOllamaModel);
            formData.append('ollama_url', ollamaUrlInput ? ollamaUrlInput.value.trim() : 'http://127.0.0.1:11434');
            formData.append('ai_prompt', aiPromptInput ? aiPromptInput.value.trim() : '');
            formData.append('gemini_api_key', apiKey);
            formData.append('skip_if_exists', 'true');

            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    let errText = 'Processing failed';
                    try {
                        const errData = await response.json();
                        errText = errData.detail || errText;
                    } catch (_) {
                        errText = await response.text();
                    }
                    throw new Error(errText);
                }

                const data = await response.json();
                if (data.skipped) {
                    item.status = 'skipped';
                    item.jobId = data.job_id;
                    skippedCount++;
                } else {
                    currentJobId = data.job_id;
                    item.jobId = data.job_id;
                    const jobResult = await pollJobUntilFinished(data.job_id);
                    item.status = 'completed';
                    completedCount++;
                    currentJobData = jobResult;
                }
            } catch (err) {
                console.error(`Error on file ${cleanName}:`, err);
                item.status = 'failed';
                item.error = err.message;
            }

            renderBatchQueue();
            loadPreviousJobs();

            // Short 1s GPU memory recovery rest between queue jobs
            if (i < batchFiles.length - 1 && isBatchRunning) {
                await new Promise(r => setTimeout(r, 1000));
            }
        }

        // Finalize Batch Run
        isBatchRunning = false;
        if (batchOverallTitle) batchOverallTitle.textContent = 'Batch Queue Processing Completed!';
        if (batchOverallPercent) batchOverallPercent.textContent = '100%';
        if (batchOverallBarFill) batchOverallBarFill.style.width = '100%';
        if (batchOverallDetail) batchOverallDetail.textContent = `Completed: ${completedCount} | Skipped: ${skippedCount} | Total: ${totalFiles}`;
        updateProgress(100, 'Batch queue finished!', 'All eligible files processed.');

        if (currentJobData && currentJobData.results) {
            showResults(currentJobData.results);
        }
        updateProcessBtnState();
    }

    function updateProgress(percent, msg, stepDetail = '') {
        progressPercent.textContent = `${percent}%`;
        progressBarFill.style.width = `${percent}%`;
        progressMessage.textContent = msg;
        if (progressSubdetail) {
            progressSubdetail.textContent = stepDetail || 'Processing step in progress...';
        }
    }

    function updateSteps(status) {
        document.getElementById('stepUpload').classList.toggle('active', status === 'queued' || status === 'diarizing');
        document.getElementById('stepDiarize').classList.toggle('active', status === 'diarizing');
        document.getElementById('stepSTT').classList.toggle('active', status === 'transcribing');
        document.getElementById('stepExport').classList.toggle('active', status === 'exporting' || status === 'completed');
    }

    function showError(message, isDuplicate = false, filename = '') {
        progressContainer.classList.add('hidden');
        errorBox.classList.remove('hidden');
        const errorTitle = document.getElementById('errorTitle');
        if (errorMessage) errorMessage.textContent = message;

        if (isDuplicate) {
            if (errorTitle) errorTitle.textContent = '⚠️ File Already Processed';
            if (errorActions) {
                errorActions.style.display = 'flex';
                errorActions.innerHTML = `
                    <button class="btn btn-secondary" id="findExistingJobBtn" style="padding: 6px 12px; font-size: 0.8rem; border-color: rgba(99, 102, 241, 0.4); color: #a5b4fc;">
                        🔍 Open Existing Results
                    </button>
                    <button class="btn btn-secondary" id="findExistingRefineBtn" style="padding: 6px 12px; font-size: 0.8rem; border-color: rgba(6, 182, 212, 0.4); color: #67e8f9;">
                        🤖 Refine Existing Transcript
                    </button>
                `;

                const findExistingJobBtn = document.getElementById('findExistingJobBtn');
                if (findExistingJobBtn) {
                    findExistingJobBtn.addEventListener('click', async () => {
                        const jId = extractJobIdFromError(message);
                        if (jId) {
                            openJobResults(jId);
                        } else {
                            loadJobByFilename(filename);
                        }
                    });
                }

                const findExistingRefineBtn = document.getElementById('findExistingRefineBtn');
                if (findExistingRefineBtn) {
                    findExistingRefineBtn.addEventListener('click', async () => {
                        const jId = extractJobIdFromError(message);
                        if (jId) {
                            triggerRefinement(jId);
                        }
                    });
                }
            }
        } else {
            if (errorTitle) errorTitle.textContent = 'Processing Failed';
            if (errorActions) errorActions.style.display = 'none';
        }
    }

    function extractJobIdFromError(msg) {
        const m = msg.match(/job ['"]([^'"]+)['"]/);
        return m ? m[1] : null;
    }

    async function loadJobByFilename(fn) {
        try {
            const res = await fetch('/api/history');
            if (res.ok) {
                const data = await res.json();
                const found = (data.jobs || []).find(j => j.filename && j.filename.toLowerCase() === fn.toLowerCase() && j.status === 'completed');
                if (found && found.results) {
                    currentJobId = found.job_id;
                    showResults(found.results);
                    resultsViewer.scrollIntoView({ behavior: 'smooth' });
                }
            }
        } catch (_) {}
    }

    async function openJobResults(jId) {
        try {
            const res = await fetch(`/api/job/${jId}`);
            if (res.ok) {
                const data = await res.json();
                if (data.results) {
                    currentJobId = jId;
                    showResults(data.results);
                    resultsViewer.scrollIntoView({ behavior: 'smooth' });
                }
            }
        } catch (_) {}
    }

    function showResults(results) {
        progressContainer.classList.add('hidden');
        errorBox.classList.add('hidden');
        resultsViewer.classList.remove('hidden');

        diarizationPreview.textContent = results.diarization_preview;
        sttPreview.textContent = results.stt_preview;
        mergedPreview.textContent = results.merged_preview;

        const tabBtnAiRefined = document.getElementById('tabBtnAiRefined');
        const tabBtnRefinedStt = document.getElementById('tabBtnRefinedStt');
        const tabBtnRefinedDiarization = document.getElementById('tabBtnRefinedDiarization');

        const aiRefinedPreview = document.getElementById('aiRefinedPreview');
        const refinedSttPreview = document.getElementById('refinedSttPreview');
        const refinedDiarizationPreview = document.getElementById('refinedDiarizationPreview');
        const refineCurrentJobBtn = document.getElementById('refineCurrentJobBtn');

        if (results.ai_refined_preview) {
            if (aiRefinedPreview) aiRefinedPreview.textContent = results.ai_refined_preview;
            if (refinedSttPreview) refinedSttPreview.textContent = results.refined_stt_preview || '';
            if (refinedDiarizationPreview) refinedDiarizationPreview.textContent = results.refined_diarization_preview || '';

            if (tabBtnAiRefined) tabBtnAiRefined.style.display = 'inline-block';
            if (tabBtnRefinedStt) tabBtnRefinedStt.style.display = 'inline-block';
            if (tabBtnRefinedDiarization) tabBtnRefinedDiarization.style.display = 'inline-block';

            if (refineCurrentJobBtn) refineCurrentJobBtn.textContent = '🤖 Re-Refine AI';
            if (tabBtnAiRefined) tabBtnAiRefined.click();
        } else {
            if (tabBtnAiRefined) tabBtnAiRefined.style.display = 'none';
            if (tabBtnRefinedStt) tabBtnRefinedStt.style.display = 'none';
            if (tabBtnRefinedDiarization) tabBtnRefinedDiarization.style.display = 'none';

            if (refineCurrentJobBtn) refineCurrentJobBtn.textContent = '🤖 Refine with AI';
            const firstTab = document.querySelector('.tab-btn[data-tab="diarization"]');
            if (firstTab) firstTab.click();
        }

        metaInfo.textContent = `Speakers Identified: ${results.speaker_count} | Transcribed Segments: ${results.segment_count}`;
        updateDownloadLink();
    }

    // AI Refinement Trigger Helper
    async function triggerRefinement(jobId) {
        const selectedModel = ollamaModelSelect ? (ollamaModelSelect.value || 'gemini:gemini-3.5-flash-lite') : 'gemini:gemini-3.5-flash-lite';
        const apiKey = geminiApiKeyInput ? geminiApiKeyInput.value.trim() : '';
        const ollamaUrl = ollamaUrlInput ? (ollamaUrlInput.value.trim() || 'http://127.0.0.1:11434') : 'http://127.0.0.1:11434';

        if (selectedModel.startsWith('gemini:') && !apiKey) {
            alert('Please enter your Google Gemini API Key in the settings first to use Gemini AI refinement.');
            if (geminiApiKeyInput) geminiApiKeyInput.focus();
            return;
        }

        emptyState.classList.add('hidden');
        errorBox.classList.add('hidden');
        resultsViewer.classList.add('hidden');
        progressContainer.classList.remove('hidden');
        processBtn.disabled = true;
        updateProgress(5, `Starting AI Refinement with ${selectedModel}...`, 'Sending transcript to AI refinement engine');
        startTimer();

        const aiPromptInput = document.getElementById('aiPrompt');
        const formData = new FormData();
        formData.append('ollama_model', selectedModel);
        formData.append('ollama_url', ollamaUrl);
        formData.append('ai_prompt', aiPromptInput ? aiPromptInput.value.trim() : '');
        formData.append('gemini_api_key', apiKey);

        try {
            const res = await fetch(`/api/refine/${jobId}`, {
                method: 'POST',
                body: formData
            });
            if (!res.ok) {
                let errText = 'Refinement request failed';
                try {
                    const errData = await res.json();
                    errText = errData.detail || errText;
                } catch (_) {
                    errText = await response.text();
                }
                throw new Error(errText);
            }
            currentJobId = jobId;
            pollJobStatus(currentJobId);
        } catch (err) {
            showError('Failed to start AI Refinement: ' + err.message);
            processBtn.disabled = false;
        }
    }

    const refineCurrentJobBtn = document.getElementById('refineCurrentJobBtn');
    if (refineCurrentJobBtn) {
        refineCurrentJobBtn.addEventListener('click', () => {
            if (currentJobId) {
                triggerRefinement(currentJobId);
            } else {
                alert('No active job selected to refine.');
            }
        });
    }

    // Tabs logic
    const allTabBtns = document.querySelectorAll('.tab-btn');
    const allTabContents = document.querySelectorAll('.tab-content');

    allTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            allTabBtns.forEach(b => b.classList.remove('active'));
            allTabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            activeTab = btn.dataset.tab;
            const targetContent = document.getElementById(`tab-${activeTab}`);
            if (targetContent) targetContent.classList.add('active');

            updateDownloadLink();
        });
    });

    function updateDownloadLink() {
        if (!currentJobId) return;
        downloadBtn.href = `/api/download/${currentJobId}/${activeTab}`;
        const baseName = selectedFile ? selectedFile.name.replace(/\.[^/.]+$/, '') : (currentJobData ? currentJobData.filename : 'output');
        downloadBtn.download = `${baseName}_${activeTab}.txt`;
    }

    // Copy to clipboard
    copyBtn.addEventListener('click', () => {
        let textToCopy = '';
        const aiRefinedPreview = document.getElementById('aiRefinedPreview');
        const refinedSttPreview = document.getElementById('refinedSttPreview');
        const refinedDiarizationPreview = document.getElementById('refinedDiarizationPreview');

        if (activeTab === 'diarization') textToCopy = diarizationPreview.textContent;
        else if (activeTab === 'stt') textToCopy = sttPreview.textContent;
        else if (activeTab === 'merged') textToCopy = mergedPreview.textContent;
        else if (activeTab === 'ai_refined') textToCopy = aiRefinedPreview ? aiRefinedPreview.textContent : '';
        else if (activeTab === 'refined_stt') textToCopy = refinedSttPreview ? refinedSttPreview.textContent : '';
        else if (activeTab === 'refined_diarization') textToCopy = refinedDiarizationPreview ? refinedDiarizationPreview.textContent : '';

        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            setTimeout(() => { copyBtn.textContent = originalText; }, 2000);
        });
    });

    // Previous Analysis History Logic
    const historyListContainer = document.getElementById('historyListContainer');
    const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');

    async function loadPreviousJobs() {
        if (!historyListContainer) return;
        try {
            const res = await fetch('/api/history');
            if (!res.ok) {
                historyListContainer.innerHTML = '<p class="text-muted" style="text-align: center; grid-column: 1 / -1; padding: 20px; color: var(--text-muted);">No previous analysis history found on disk.</p>';
                return;
            }
            const data = await res.json();
            const jobs = data.jobs || [];

            if (jobs.length === 0) {
                historyListContainer.innerHTML = '<p class="text-muted" style="text-align: center; grid-column: 1 / -1; padding: 20px; color: var(--text-muted);">No previous analysis history found on disk.</p>';
                return;
            }

            historyListContainer.innerHTML = jobs.map(job => {
                const statusClass = job.status === 'completed' ? 'badge-completed' : (job.status === 'error' ? 'badge-error' : 'badge-processing');
                const statusLabel = job.status === 'completed' ? 'Completed ✓' : (job.status === 'error' ? 'Error ❌' : job.status.toUpperCase());
                
                let timeStr = 'Unknown';
                if (job.mtime) {
                    const date = new Date(job.mtime * 1000);
                    timeStr = date.toLocaleString();
                }

                const filename = job.filename || job.job_id;
                const spkCount = job.results ? (job.results.speaker_count || 0) : 0;
                const segCount = job.results ? (job.results.segment_count || 0) : 0;
                const hasRefined = Boolean(job.results && (job.results.ai_refined_file || job.results.refined_file || job.results.ai_refined_preview));

                return `
                    <div class="history-item-card" id="card-${job.job_id}">
                        <div>
                            <div class="history-item-header">
                                <div class="history-filename" title="${filename}">${filename}</div>
                                <div style="display: flex; gap: 4px; align-items: center;">
                                    ${hasRefined ? '<span class="badge-status badge-refined" title="AI Refined Transcript Available">🤖 Refined</span>' : ''}
                                    <span class="badge-status ${statusClass}">${statusLabel}</span>
                                </div>
                            </div>
                            <div class="history-meta">
                                <span>📅 ${timeStr}</span>
                                ${job.status === 'completed' ? `<span>👥 Speakers: ${spkCount} | Segments: ${segCount}</span>` : ''}
                            </div>
                        </div>
                        <div class="history-actions">
                            ${job.status === 'completed' ? `
                                <button class="btn btn-secondary load-job-btn" data-jobid="${job.job_id}" style="padding: 6px 10px; font-size: 0.8rem; flex: 1;">
                                    🔍 Open Results
                                </button>
                                <button class="btn btn-secondary refine-job-btn" data-jobid="${job.job_id}" style="padding: 6px 10px; font-size: 0.8rem; border-color: rgba(99, 102, 241, 0.4); color: #a5b4fc;" title="${hasRefined ? 'Re-run AI Refinement on this job' : 'Refine this transcript with AI'}">
                                    🤖 ${hasRefined ? 'Re-Refine' : 'Refine AI'}
                                </button>
                            ` : `
                                <button class="btn btn-secondary resume-job-btn" data-jobid="${job.job_id}" style="padding: 6px 12px; font-size: 0.8rem; flex: 1; color: var(--accent-cyan); border-color: rgba(6, 182, 212, 0.4);">
                                    ▶️ Resume Checkpoint
                                </button>
                            `}
                            <button class="btn btn-secondary delete-job-btn" data-jobid="${job.job_id}" style="padding: 6px 10px; font-size: 0.8rem; color: #f87171; border-color: rgba(239, 68, 68, 0.3);">
                                🗑️
                            </button>
                        </div>
                    </div>
                `;
            }).join('');

            // Bind click events
            document.querySelectorAll('.load-job-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const jId = e.currentTarget.dataset.jobid;
                    openJobResults(jId);
                });
            });

            document.querySelectorAll('.refine-job-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const jId = e.currentTarget.dataset.jobid;
                    triggerRefinement(jId);
                });
            });

            document.querySelectorAll('.resume-job-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const jId = e.currentTarget.dataset.jobid;
                    try {
                        const rRes = await fetch(`/api/resume/${jId}`, { method: 'POST' });
                        if (!rRes.ok) {
                            const errData = await rRes.json();
                            throw new Error(errData.detail || 'Resume failed');
                        }
                        currentJobId = jId;
                        emptyState.classList.add('hidden');
                        errorBox.classList.add('hidden');
                        resultsViewer.classList.add('hidden');
                        progressContainer.classList.remove('hidden');
                        processBtn.disabled = true;
                        pollJobStatus(currentJobId);
                    } catch (err) {
                        alert('Could not resume job: ' + err.message);
                    }
                });
            });

            document.querySelectorAll('.delete-job-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const jId = e.currentTarget.dataset.jobid;
                    if (confirm('Are you sure you want to delete this analysis job from disk?')) {
                        try {
                            await fetch(`/api/job/${jId}`, { method: 'DELETE' });
                            await loadPreviousJobs();
                            // If in batch mode, re-check files so deleted file becomes queued again!
                            if (batchFiles.length > 0) {
                                await checkBatchFilesWithBackend();
                                renderBatchQueue();
                                updateProcessBtnState();
                            }
                        } catch (err) {
                            alert('Failed to delete job: ' + err.message);
                        }
                    }
                });
            });

        } catch (e) {
            console.error('Failed to load history:', e);
        }
    }

    if (refreshHistoryBtn) {
        refreshHistoryBtn.addEventListener('click', loadPreviousJobs);
    }

    // Initial load
    loadPreviousJobs();
});

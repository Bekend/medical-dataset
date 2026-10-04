# -*- coding: utf-8 -*-
"""
Generates an interactive, standalone Clinical Analytics Dashboard & Encounter Explorer HTML.
Works offline and directly in any modern browser.
"""

import json
import sys

def build_dashboard():
    with open('clinical_encounters_corpus.json', encoding='utf-8') as f:
        encounters = json.load(f)

    # Prepare data for dashboard
    encounters_json = json.dumps(encounters, ensure_ascii=False)

    html_template = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PCCC Clinical Intelligence Dashboard | داشبورد هوشمند پیکره بالینی</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&display=swap');
        * {
            font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .custom-scroll::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        .custom-scroll::-webkit-scrollbar-track {
            background: #1e293b;
        }
        .custom-scroll::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 4px;
        }
        .gradient-border {
            background: linear-gradient(135deg, #3b82f6, #06b6d4, #10b981);
            padding: 1px;
            border-radius: 0.75rem;
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">

    <!-- Top Header -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 text-xl font-bold">
                    <i class="fa-solid fa-stethoscope"></i>
                </div>
                <div>
                    <h1 class="text-lg font-extrabold bg-gradient-to-r from-blue-400 via-cyan-300 to-teal-300 bg-clip-text text-transparent">
                        PCCC: سامانه هوشمند تحلیل پیکره بالینی و تولید خودکار پرونده (Ambient EHR)
                    </h1>
                </div>
            </div>

            <div class="flex items-center gap-2">
                <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    ۴۶۱ ویزیت بالینی معتبر استخراج‌شده
                </span>
                <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    ۱۴۰ ساعت صوت واقعی
                </span>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex gap-2 border-t border-slate-800/60 pt-2 pb-1">
            <button onclick="switchTab('analytics')" id="tab-analytics" class="px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 bg-blue-600 text-white shadow-md shadow-blue-600/30">
                <i class="fa-solid fa-chart-pie"></i> اطلس آماری پیکره (Analytics Atlas)
            </button>
            <button onclick="switchTab('explorer')" id="tab-explorer" class="px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 text-slate-400 hover:text-white hover:bg-slate-800">
                <i class="fa-solid fa-users-rectangle"></i> کاوشگر ویزیت‌های بالینی (Encounter Explorer)
            </button>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

        <!-- TAB 1: ANALYTICS ATLAS -->
        <section id="content-analytics" class="space-y-6">
            <!-- Metric Cards -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl relative overflow-hidden shadow-sm">
                    <div class="absolute -right-2 -bottom-2 text-blue-500/10 text-6xl"><i class="fa-solid fa-headset"></i></div>
                    <span class="text-xs font-medium text-slate-400">کل ساعات ضبط صوتی</span>
                    <div class="text-2xl font-black text-blue-400 mt-1">۱۴۰+ ساعت</div>
                    <span class="text-[11px] text-slate-500">۲۹ سشن پیوسته در شیفت‌های ۳ تا ۸ ساعته</span>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl relative overflow-hidden shadow-sm">
                    <div class="absolute -right-2 -bottom-2 text-emerald-500/10 text-6xl"><i class="fa-solid fa-hospital-user"></i></div>
                    <span class="text-xs font-medium text-slate-400">ویزیت‌های بالینی خالص</span>
                    <div class="text-2xl font-black text-emerald-400 mt-1">۴۶۱ ویزیت</div>
                    <span class="text-[11px] text-emerald-500/80">فیلترشده از جلسات اداری، نویز و تماس‌ها</span>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl relative overflow-hidden shadow-sm">
                    <div class="absolute -right-2 -bottom-2 text-cyan-500/10 text-6xl"><i class="fa-solid fa-clock"></i></div>
                    <span class="text-xs font-medium text-slate-400">مکالمات خالص درمانی</span>
                    <div class="text-2xl font-black text-cyan-400 mt-1">۵۹.۰ ساعت</div>
                    <span class="text-[11px] text-slate-500">میانگین ۷.۷ دقیقه به‌ازای هر ویزیت</span>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl relative overflow-hidden shadow-sm">
                    <div class="absolute -right-2 -bottom-2 text-purple-500/10 text-6xl"><i class="fa-solid fa-pills"></i></div>
                    <span class="text-xs font-medium text-slate-400">سهم بیماران اطفال</span>
                    <div class="text-2xl font-black text-purple-400 mt-1">۸۵.۷٪</div>
                    <span class="text-[11px] text-slate-500">۳۹۵ ویزیت از ۴ پزشک اطفال و ۱ عمومی</span>
                </div>
            </div>

            <!-- Charts Row 1 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Demographics Chart -->
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-sm">
                    <h3 class="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-child text-cyan-400"></i> تفکیک جمعیتی مراجعین (Demographics)
                    </h3>
                    <div class="h-64 flex items-center justify-center">
                        <canvas id="chartDemographics"></canvas>
                    </div>
                </div>

                <!-- Complaints Chart -->
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-sm">
                    <h3 class="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-virus text-rose-400"></i> شایع‌ترین شکایات بالینی (Chief Complaints)
                    </h3>
                    <div class="h-64 flex items-center justify-center">
                        <canvas id="chartComplaints"></canvas>
                    </div>
                </div>
            </div>

            <!-- Charts Row 2 -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Diagnoses Chart -->
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-sm">
                    <h3 class="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-clipboard-check text-emerald-400"></i> تشخیص‌های بالینی و یافته‌ها (Diagnoses)
                    </h3>
                    <div class="h-64 flex items-center justify-center">
                        <canvas id="chartDiagnoses"></canvas>
                    </div>
                </div>

                <!-- Meds Chart -->
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-sm">
                    <h3 class="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                        <i class="fa-solid fa-capsules text-amber-400"></i> الگوی تجویز دارویی (Medication Patterns)
                    </h3>
                    <div class="h-64 flex items-center justify-center">
                        <canvas id="chartMeds"></canvas>
                    </div>
                </div>
            </div>
        </section>

        <!-- TAB 2: ENCOUNTER EXPLORER -->
        <section id="content-explorer" class="hidden space-y-4">
            <!-- Filter & Search Controls -->
            <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3">
                <div class="flex flex-wrap gap-4 items-center justify-between">
                    <div class="flex flex-wrap items-center gap-3">
                        <div class="relative">
                            <input type="text" id="searchInput" oninput="filterEncounters()" placeholder="جستجوی بیماری، دارو یا علامت..." class="bg-slate-950 border border-slate-700 text-sm rounded-lg px-3 py-2 pr-9 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 w-64">
                            <i class="fa-solid fa-search absolute right-3 top-3 text-slate-500 text-xs"></i>
                        </div>

                        <select id="demographicFilter" onchange="filterEncounters()" class="bg-slate-950 border border-slate-700 text-sm rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-blue-500">
                            <option value="ALL">همه مراجعین (۴۶۱ ویزیت)</option>
                            <option value="کودک">کودک و خردسال (۶۲.۰٪)</option>
                            <option value="نوزاد">نوزاد و شیرخوار (۲۳.۶٪)</option>
                            <option value="بزرگسال">بزرگسال عمومی (۱۴.۳٪)</option>
                        </select>
                    </div>

                    <div class="text-xs text-slate-400 flex items-center gap-3">
                        <span>نمایش <span id="filteredCount" class="font-bold text-blue-400">۴۶۱</span> از ۴۶۱ ویزیت</span>
                        <button onclick="resetAllFilters()" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] transition flex items-center gap-1 border border-slate-700">
                            <i class="fa-solid fa-arrows-rotate text-[10px]"></i> بازنشانی فیلترها
                        </button>
                    </div>
                </div>

                <!-- Dynamic Medication Quick-Filter Chips Bar -->
                <div class="pt-2.5 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5" id="medicationFilterChips">
                    <!-- Populated dynamically via JS -->
                </div>
            </div>

            <!-- Split View: List on Right, Detail on Left -->
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
                <!-- Encounter List -->
                <div class="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-3 h-[700px] overflow-y-auto custom-scroll space-y-2.5" id="encountersListContainer">
                    <!-- Populated dynamically via JS -->
                </div>

                <!-- Encounter Detail Panel -->
                <div class="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 h-[700px] overflow-y-auto custom-scroll" id="encounterDetailPanel">
                    <div class="h-full flex flex-col items-center justify-center text-slate-500">
                        <i class="fa-solid fa-hand-pointer text-4xl mb-3 text-slate-600 animate-bounce"></i>
                        <p class="text-sm">جهت مشاهده جزئیات گفتگو، معاینات و پرونده، یک ویزیت را از لیست انتخاب کنید.</p>
                    </div>
                </div>
            </div>
        </section>

    </main>

    <!-- Global JS Script with Embedded Data -->
    <script>
        const RAW_ENCOUNTERS = """ + encounters_json + """;

        let currentFiltered = [...RAW_ENCOUNTERS];
        let selectedEncounter = RAW_ENCOUNTERS[0];
        let selectedMedicationFilter = 'ALL';

        function switchTab(tabId) {
            ['analytics', 'explorer'].forEach(t => {
                const sec = document.getElementById('content-' + t);
                if (sec) sec.classList.add('hidden');
                const btn = document.getElementById('tab-' + t);
                if (btn) btn.className = 'px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 text-slate-400 hover:text-white hover:bg-slate-800';
            });
            const activeSec = document.getElementById('content-' + tabId);
            if (activeSec) activeSec.classList.remove('hidden');
            const activeBtn = document.getElementById('tab-' + tabId);
            if (activeBtn) activeBtn.className = 'px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 bg-blue-600 text-white shadow-md shadow-blue-600/30';

            if (tabId === 'explorer' && !window.explorerInitialized) {
                initMedicationChips();
                renderEncountersList();
                if (selectedEncounter) selectEncounter(selectedEncounter.encounter_id);
                window.explorerInitialized = true;
            }
        }

        function initMedicationChips() {
            const medCounts = {};
            RAW_ENCOUNTERS.forEach(e => {
                (e.prescriptions || []).forEach(p => {
                    const name = p.name_fa;
                    medCounts[name] = (medCounts[name] || 0) + 1;
                });
            });

            const sortedMeds = Object.entries(medCounts).sort((a, b) => b[1] - a[1]);
            const container = document.getElementById('medicationFilterChips');
            if (!container) return;

            let html = `
                <span class="text-xs font-bold text-slate-400 ml-1.5 flex items-center gap-1 shrink-0">
                    <i class="fa-solid fa-pills text-purple-400"></i> فیلتر دارویی:
                </span>
                <button onclick="setMedicationFilter('ALL')" class="px-2.5 py-1 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${selectedMedicationFilter === 'ALL' ? 'bg-purple-600 text-white shadow-sm shadow-purple-600/30' : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'}">
                    <span>همه داروها</span>
                </button>
            `;

            sortedMeds.forEach(([med, count]) => {
                const isSelected = (selectedMedicationFilter === med);
                html += `
                    <button onclick="setMedicationFilter('${med}')" class="px-2.5 py-1 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${isSelected ? 'bg-purple-600 text-white shadow-sm shadow-purple-600/30' : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'}">
                        <span>${med}</span>
                        <span class="text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-purple-800 text-purple-200' : 'bg-slate-700/80 text-slate-400'} font-mono">${count}</span>
                    </button>
                `;
            });

            const noPresCount = RAW_ENCOUNTERS.filter(e => !e.prescriptions || e.prescriptions.length === 0).length;
            const isNoPres = (selectedMedicationFilter === 'NONE');
            html += `
                <button onclick="setMedicationFilter('NONE')" class="px-2.5 py-1 rounded-lg text-xs font-medium transition flex items-center gap-1.5 ${isNoPres ? 'bg-purple-600 text-white shadow-sm shadow-purple-600/30' : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'}">
                    <span>بدون نسخه / مراقبتی</span>
                    <span class="text-[10px] px-1.5 py-0.2 rounded-full ${isNoPres ? 'bg-purple-800 text-purple-200' : 'bg-slate-700/80 text-slate-400'} font-mono">${noPresCount}</span>
                </button>
            `;

            container.innerHTML = html;
        }

        function setMedicationFilter(med) {
            selectedMedicationFilter = med;
            initMedicationChips();
            filterEncounters();
        }

        function resetAllFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('demographicFilter').value = 'ALL';
            selectedMedicationFilter = 'ALL';
            initMedicationChips();
            filterEncounters();
        }

        // Render List
        function renderEncountersList() {
            const container = document.getElementById('encountersListContainer');
            container.innerHTML = '';

            currentFiltered.forEach(enc => {
                const card = document.createElement('div');
                const isSelected = selectedEncounter && selectedEncounter.encounter_id === enc.encounter_id;
                card.className = `p-3 rounded-lg border transition cursor-pointer ${
                    isSelected 
                        ? 'bg-blue-950/60 border-blue-500 shadow-sm shadow-blue-500/20' 
                        : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'
                }`;
                card.onclick = () => selectEncounter(enc.encounter_id);

                const complaintsStr = enc.chief_complaints.slice(0, 3).join('، ') || 'معاینه عمومی';
                const presList = enc.prescriptions || [];

                let medsHtml = '';
                if (presList.length > 0) {
                    medsHtml = presList.map(p => `
                        <span onclick="event.stopPropagation(); setMedicationFilter('${p.name_fa}');" class="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full ${selectedMedicationFilter === p.name_fa ? 'bg-purple-600 text-white' : 'bg-purple-950/70 text-purple-300 border border-purple-800/50 hover:bg-purple-800'} transition cursor-pointer" title="کلیک برای فیلتر بیماران دریافت‌کننده ${p.name_fa}">
                            <i class="fa-solid fa-pills text-[8px]"></i> ${p.name_fa}
                        </span>
                    `).join(' ');
                } else {
                    medsHtml = '<span class="text-[10px] text-slate-500">بدون نسخه</span>';
                }

                card.innerHTML = `
                    <div class="flex items-center justify-between text-xs mb-1.5">
                        <span class="font-bold text-slate-200 flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full ${enc.patient_category.includes('نوزاد') ? 'bg-amber-400' : (enc.patient_category.includes('کودک') ? 'bg-cyan-400' : 'bg-emerald-400')}"></span>
                            ${enc.patient_category}
                        </span>
                        <span class="text-slate-400 font-mono text-[11px]">${enc.start_time} - ${enc.end_time} (${enc.duration_minutes}m)</span>
                    </div>
                    <div class="text-[12px] text-slate-300 font-medium truncate mb-1">
                        علائم: <span class="text-cyan-300">${complaintsStr}</span>
                    </div>
                    <div class="text-[11px] text-slate-400 truncate mb-1.5">
                        تشخیص: <span class="text-emerald-400">${enc.clinical_diagnosis[0] || 'معاینه'}</span>
                    </div>
                    <div class="flex items-center gap-1.5 flex-wrap pt-1.5 border-t border-slate-900">
                        ${medsHtml}
                    </div>
                `;
                container.appendChild(card);
            });
            document.getElementById('filteredCount').innerText = currentFiltered.length;
        }

        function selectEncounter(encId) {
            selectedEncounter = RAW_ENCOUNTERS.find(e => e.encounter_id === encId);
            renderEncountersList();
            renderEncounterDetail();
        }

        function renderEncounterDetail() {
            const panel = document.getElementById('encounterDetailPanel');
            if (!selectedEncounter) {
                panel.innerHTML = `
                    <div class="h-full flex flex-col items-center justify-center text-slate-500 py-12">
                        <i class="fa-solid fa-filter-circle-xmark text-4xl mb-3 text-slate-600"></i>
                        <p class="text-sm">هیچ ویزیت بالینی با این مشخصات یافت نشد.</p>
                    </div>
                `;
                return;
            }

            const enc = selectedEncounter;

            // E-Prescriptions Table (Iranian Pharmacopeia Verified)
            let presHtml = '';
            const presList = enc.prescriptions || [];
            if (presList.length > 0) {
                presHtml = `
                    <div class="overflow-x-auto rounded-lg border border-slate-800">
                        <table class="w-full text-right text-xs">
                            <thead class="bg-slate-900/90 text-slate-400 border-b border-slate-800 text-[11px]">
                                <tr>
                                    <th class="p-2.5">نام ژنریک دارو (فارسی / انگلیسی)</th>
                                    <th class="p-2.5">شکل دارویی</th>
                                    <th class="p-2.5">دسته درمانی</th>
                                    <th class="p-2.5">دستور و نوبت مصرف استخراج‌شده</th>
                                    <th class="p-2.5 text-center">اقدام</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-800/60 bg-slate-950/40">
                                ${presList.map(p => `
                                    <tr class="hover:bg-slate-900/50 transition">
                                        <td class="p-2.5">
                                            <div class="font-bold text-white">${p.name_fa}</div>
                                            <div class="text-[10px] text-cyan-400 font-mono">${p.name_en}</div>
                                        </td>
                                        <td class="p-2.5">
                                            <span class="inline-block px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 text-[11px] font-medium">
                                                ${p.form}
                                            </span>
                                        </td>
                                        <td class="p-2.5 text-slate-300 text-[11px]">${p.category}</td>
                                        <td class="p-2.5">
                                            <span class="inline-flex items-center gap-1 text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded text-[11px]">
                                                <i class="fa-regular fa-clock text-[10px]"></i> ${p.dosage_instruction}
                                            </span>
                                        </td>
                                        <td class="p-2.5 text-center">
                                            <button onclick="setMedicationFilter('${p.name_fa}')" class="inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded bg-purple-600/20 hover:bg-purple-600 text-purple-300 hover:text-white border border-purple-500/30 transition" title="فیلتر همه بیماران با این دارو">
                                                <i class="fa-solid fa-filter text-[9px]"></i> فیلتر بیماران
                                            </button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            } else {
                presHtml = `
                    <div class="p-3.5 rounded-lg bg-slate-900/40 border border-dashed border-slate-800 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
                        <i class="fa-solid fa-shield-heart text-blue-400"></i>
                        <span>در این ویزیت داروی شیمیایی تجویز نشده است (توصیه‌های پایش سلامت، رژیم غذایی یا دستورات مراقبتی ارائه شد).</span>
                    </div>
                `;
            }

            // Clinical Findings & Complaints tags
            const examsList = enc.clinical_findings || [];
            let examsHtml = '';
            if (examsList.length > 0) {
                examsHtml = examsList.map(ex => `
                    <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/20 text-xs">
                        <i class="fa-solid fa-stethoscope text-[10px]"></i> ${ex}
                    </span>
                `).join(' ');
            } else {
                examsHtml = '<span class="text-xs text-slate-500">معاینه بالینی عمومی انجام شد</span>';
            }

            const complaintsList = enc.chief_complaints || [];
            const complaintsHtml = complaintsList.length > 0 ? complaintsList.map(c => `
                <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 text-xs">
                    <i class="fa-solid fa-circle-exclamation text-[10px]"></i> ${c}
                </span>
            `).join(' ') : '<span class="text-xs text-slate-500">پایش عمومی</span>';

            const soap = enc.soap_note || {};

            panel.innerHTML = `
                <div class="space-y-4">
                    <!-- Top header info -->
                    <div class="flex flex-wrap items-center justify-between border-b border-slate-800 pb-3">
                        <div>
                            <h3 class="text-base font-extrabold text-white flex items-center gap-2">
                                <i class="fa-solid fa-hospital-user text-blue-400"></i> ${enc.encounter_id}
                            </h3>
                            <p class="text-xs text-slate-400 mt-0.5">سشن صوتی: <span class="font-mono text-slate-300">${enc.session_id}</span></p>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="px-2.5 py-1 rounded text-xs bg-slate-800 text-slate-300 font-mono">
                                <i class="fa-regular fa-clock ml-1 text-slate-400"></i> زمان: ${enc.start_time} تا ${enc.end_time} (${enc.duration_minutes} دقیقه)
                            </span>
                            <span class="px-2.5 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">
                                ${enc.patient_category}
                            </span>
                        </div>
                    </div>

                    <!-- Clinical Findings & Complaints Grid -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div class="bg-slate-950 p-3 rounded-lg border border-slate-800">
                            <span class="text-xs font-bold text-slate-400 block mb-2 flex items-center gap-1.5">
                                <i class="fa-solid fa-heart-pulse text-cyan-400"></i> شکایات و علائم اصلی اظهارشده:
                            </span>
                            <div class="flex flex-wrap gap-1.5">
                                ${complaintsHtml}
                            </div>
                        </div>
                        <div class="bg-slate-950 p-3 rounded-lg border border-slate-800">
                            <span class="text-xs font-bold text-slate-400 block mb-2 flex items-center gap-1.5">
                                <i class="fa-solid fa-user-doctor text-amber-400"></i> معاینات و یافته‌های بالینی پزشک:
                            </span>
                            <div class="flex flex-wrap gap-1.5">
                                ${examsHtml}
                            </div>
                        </div>
                    </div>

                    <!-- Diagnosis Banner -->
                    <div class="bg-slate-950 p-3.5 rounded-lg border border-slate-800 flex items-start gap-3">
                        <div class="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                            <i class="fa-solid fa-clipboard-check"></i>
                        </div>
                        <div>
                            <span class="text-xs font-bold text-slate-400 block mb-1">تشخیص بالینی نهایی و افتراقی:</span>
                            <span class="text-sm text-emerald-400 font-bold">${enc.clinical_diagnosis.join(' | ')}</span>
                        </div>
                    </div>

                    <!-- E-Prescription Pharmacopeia Table (Replaces Dialogue snippet) -->
                    <div class="space-y-2">
                        <div class="flex items-center justify-between">
                            <h4 class="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                                <i class="fa-solid fa-prescription text-purple-400"></i> نسخه الکترونیک ساختاریافته (تطبیق‌شده با فارماکوپه ایران):
                            </h4>
                            <span class="text-[11px] text-slate-400">تعداد اقلام: <span class="font-bold text-purple-400">${presList.length}</span></span>
                        </div>
                        ${presHtml}
                    </div>

                    <!-- Compact Embedded SOAP Card -->
                    <div class="bg-slate-900/60 rounded-xl border border-slate-800 p-4 space-y-3">
                        <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
                            <h4 class="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                                <i class="fa-solid fa-file-medical text-blue-400"></i> خلاصه پرونده استاندارد بالینی (SOAP Note):
                            </h4>
                            <button onclick="exportSoapAsText()" class="text-[11px] px-2.5 py-1 rounded bg-blue-600/30 hover:bg-blue-600 text-blue-300 hover:text-white transition flex items-center gap-1 border border-blue-500/30">
                                <i class="fa-regular fa-copy"></i> کپی پرونده
                            </button>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs">
                            <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-800/70">
                                <span class="font-bold text-blue-400 block mb-1">[S] Subjective (شرح حال):</span>
                                <p class="text-slate-300 leading-relaxed text-[11px]">${soap.S_Subjective || '---'}</p>
                            </div>
                            <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-800/70">
                                <span class="font-bold text-amber-400 block mb-1">[O] Objective (معاینات بالینی):</span>
                                <p class="text-slate-300 leading-relaxed text-[11px]">${soap.O_Objective || '---'}</p>
                            </div>
                            <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-800/70">
                                <span class="font-bold text-emerald-400 block mb-1">[A] Assessment (تشخیص):</span>
                                <p class="text-slate-300 leading-relaxed text-[11px]">${soap.A_Assessment || '---'}</p>
                            </div>
                            <div class="bg-slate-950 p-2.5 rounded-lg border border-slate-800/70">
                                <span class="font-bold text-purple-400 block mb-1">[P] Plan (برنامه درمانی و نسخه):</span>
                                <p class="text-slate-300 leading-relaxed text-[11px]">${soap.P_Plan || '---'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        function exportSoapAsText() {
            if (!selectedEncounter) return;
            const soap = selectedEncounter.soap_note || {};
            const text = `پرونده بالینی ویزیت ${selectedEncounter.encounter_id}
رده سنی: ${selectedEncounter.patient_category}
زمان: ${selectedEncounter.start_time} - ${selectedEncounter.end_time}

[S - Subjective]
${soap.S_Subjective}

[O - Objective]
${soap.O_Objective}

[A - Assessment]
${soap.A_Assessment}

[P - Plan]
${soap.P_Plan}`;
            navigator.clipboard.writeText(text);
            alert('متن کامل پرونده بالینی SOAP در کلیپ‌بورد کپی شد.');
        }

        function filterEncounters() {
            const query = document.getElementById('searchInput').value.trim().toLowerCase();
            const demo = document.getElementById('demographicFilter').value;

            currentFiltered = RAW_ENCOUNTERS.filter(e => {
                // Demographic filter
                const matchDemo = (demo === 'ALL' || e.patient_category.includes(demo));

                // Medication chip filter
                let matchMed = true;
                if (selectedMedicationFilter === 'NONE') {
                    matchMed = (!e.prescriptions || e.prescriptions.length === 0);
                } else if (selectedMedicationFilter !== 'ALL') {
                    matchMed = (e.prescriptions || []).some(p => p.name_fa === selectedMedicationFilter || (p.name_en && p.name_en.toLowerCase().includes(selectedMedicationFilter.toLowerCase())));
                }

                // Query search
                const presText = (e.prescriptions || []).map(p => (p.name_fa || '') + ' ' + (p.name_en || '') + ' ' + (p.form || '') + ' ' + (p.dosage_instruction || '')).join(' ');
                const fullSearchText = (
                    e.encounter_id + ' ' + 
                    e.patient_category + ' ' +
                    (e.chief_complaints || []).join(' ') + ' ' + 
                    (e.prescribed_medications || []).join(' ') + ' ' + 
                    presText + ' ' +
                    (e.clinical_diagnosis || []).join(' ')
                ).toLowerCase();
                const matchQuery = !query || fullSearchText.includes(query);

                return matchDemo && matchMed && matchQuery;
            });

            renderEncountersList();
            if (currentFiltered.length > 0) {
                selectEncounter(currentFiltered[0].encounter_id);
            } else {
                selectedEncounter = null;
                renderEncounterDetail();
            }
        }

        // Initialize Charts and Chips on Load
        window.addEventListener('DOMContentLoaded', () => {
            initCharts();
            initMedicationChips();
        });

        function initCharts() {
            // Demographics Chart
            new Chart(document.getElementById('chartDemographics'), {
                type: 'doughnut',
                data: {
                    labels: ['کودک و خردسال اطفال (۳۹.۰٪)', 'نوزاد و شیرخوار اطفال (۲۳.۶٪)', 'کودکان مراجع به عمومی (۲۳.۰٪)', 'بزرگسال عمومی (۱۴.۳٪)'],
                    datasets: [{
                        data: [180, 109, 106, 66],
                        backgroundColor: ['#06b6d4', '#f59e0b', '#3b82f6', '#10b981'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { family: 'Vazirmatn' } } }
                    }
                }
            });

            // Complaints Chart
            new Chart(document.getElementById('chartComplaints'), {
                type: 'bar',
                data: {
                    labels: ['تب', 'پایش رشد و نوزاد', 'سرفه و تنفسی', 'مشکلات گوارشی', 'مشکلات ادراری', 'آبریزش و احتقان', 'مشکلات پوستی', 'درد بالینی', 'بی‌قراری و خواب'],
                    datasets: [{
                        label: 'تعداد تکرار در ویزیت‌ها',
                        data: [147, 138, 109, 108, 62, 43, 43, 39, 37],
                        backgroundColor: '#f43f5e',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
                        x: { ticks: { color: '#94a3b8', font: { family: 'Vazirmatn' } }, grid: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });

            // Diagnoses Chart
            new Chart(document.getElementById('chartDiagnoses'), {
                type: 'bar',
                data: {
                    labels: ['معاینه و پایش رشد', 'برونشیولیت و عفونت تنفسی', 'اوتیت گوش (Otitis)', 'بررسی آنزیم کبد و پلاکت', 'عفونت ویروسی حاد', 'ریفلاکس نوزادی (GERD)', 'عفونت ادراری (UTI)', 'برفک دهان نوزاد'],
                    datasets: [{
                        label: 'تعداد تشخیص',
                        data: [269, 120, 46, 41, 21, 18, 6, 5],
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
                        y: { ticks: { color: '#94a3b8', font: { family: 'Vazirmatn' } }, grid: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });

            // Meds Chart
            new Chart(document.getElementById('chartMeds'), {
                type: 'bar',
                data: {
                    labels: ['شربت خوراکی اطفال', 'قطره موضعی/خوراکی', 'استامینوفن (تب‌بر)', 'ایبوپروفن (مسکن/تب‌بر)', 'قطره پدی‌لاکت (پروبیوتیک)', 'قطره دایمتیکون (کولیک)', 'آزیترومایسین (آنتی‌بیوتیک)', 'شیاف اطفال', 'پلارژین کیدز (ضدسرفه)', 'سیتریزین (آنتی‌هیستامین)'],
                    datasets: [{
                        label: 'تعداد تجویز فارماکوپه‌ای',
                        data: [46, 42, 35, 33, 17, 14, 11, 11, 11, 11],
                        backgroundColor: '#8b5cf6',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e293b' } },
                        x: { ticks: { color: '#94a3b8', font: { family: 'Vazirmatn' } }, grid: { display: false } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        }
    </script>
</body>
</html>
"""

    with open('clinical_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    print("Successfully generated clinical_dashboard.html!")

if __name__ == '__main__':
    build_dashboard()

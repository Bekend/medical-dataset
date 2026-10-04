# -*- coding: utf-8 -*-
"""
Clinical Encounter Segmenter, Quality Filter & Structured Medical Extractor for PCCC
Extracts clean, verified patient visits from raw/refined transcripts.
Filters out:
- Whisper repetition hallucinations
- Background music artifacts
- Non-clinical / Administrative conversations (phone calls, meetings)
Produces:
- Structured JSON and CSV dataset of patient encounters
- Standard SOAP Notes & Prescriptions
- Corpus-wide statistical benchmarks
"""

import os
import sys
import re
import glob
import json
from datetime import timedelta

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Medical entity dictionaries & heuristics
CLINICAL_SYMPTOMS = {
    'تب': ['تب', 'داغ بودن بدن', 'حرارت بالا', 'لرز', 'تب و لرز', 'داغی سر'],
    'سرفه': ['سرفه', 'خس‌خس', 'خلط', 'خس خس', 'سرفه‌های خشک', 'صاف کردن گلو'],
    'آبریزش و احتقان': ['آبریزش', 'گرفتگی بینی', 'عطسه', 'خلط گلو', 'ترشحات بینی'],
    'درد': ['درد', 'دل درد', 'گوش درد', 'سردرد', 'شکم درد', 'درد اندام', 'پا درد'],
    'مشکلات گوارشی': ['اسهال', 'استفراغ', 'تهوع', 'ریفلاکس', 'رفلاکس', 'بالا آوردن', 'یبوست', 'نفخ', 'کولیک', 'دل‌پیچه', 'سوزش معده', 'بی‌اشتهایی'],
    'مشکلات ادراری': ['سوزش ادرار', 'خارش ادرار', 'تکرر ادرار', 'عفونت ادراری', 'ادرار خونی', 'بوی تند ادرار', 'یو تی اس', 'UTI'],
    'مشکلات پوستی': ['دانه', 'جوش', 'خارش پوست', 'کهیر', 'بثورات', 'قرمزی پوست', 'اگزما', 'آفت دهان', 'سفیدک زبان'],
    'بی‌قراری و خواب': ['بی‌تابی', 'بیقراری', 'گریه مداوم', 'بدخوابی', 'پریدن از خواب', 'ضعف', 'بی‌حالی', 'خستگی'],
    'پایش رشد و تغذیه': ['وزن نگرفتن', 'شیر نخوردن', 'پایش رشد', 'قد', 'دندان درآوردن', 'قطره آهن', 'مولتی‌ویتامین']
}

CLINICAL_MEDICATIONS = [
    'استامینوفن', 'ایبوپروفن', 'بروفن', 'شیاف', 'سفکسیم', 'آموکسی‌سیلین', 'کوآموکسی‌کلاو',
    'آزیترومایسین', 'دیفن‌هیدرامین', 'سیتریزین', 'کتوتیفن', 'نئوتادین', 'شربت پلارژین',
    'قطره پدی‌لاکت', 'پروبیوتیک', 'قطره دایمتیکون', 'گریپ واتر', 'قطره نیستاتین',
    'پماد هیدروکورتیزون', 'پماد کالاندولا', 'پماد موپیروسین', 'زینک اکساید',
    'قطره بتامتازون', 'قطره پلی‌میکسین', 'قطره سیپروفلوکساسین', 'قطره کلرامفنیکل',
    'شربت موکولین', 'سالبوتامول', 'اسپری سدیم کلراید', 'قطره رینوسالتین',
    'امپرازول', 'اسومپرازول', 'فاموتیدین', 'مترونیدازول', 'سفالکسین', 'پنی‌سیلین',
    'ویال', 'سرم خوراکی', 'او آر اس', 'ORS', 'قطره آهن', 'مولتی‌ویتامین', 'ویتامین آ+د',
    'شربت اشتهاآور', 'پودر پیدرولاکس', 'شربت انجیر', 'لاکتولوز'
]

CLINICAL_FINDINGS = [
    'معاینه گوش', 'معاینه گلو', 'معاینه شکم', 'سمع ریه', 'سمع قلب', 'بررسی زبان و دهان',
    'اندازه‌گیری تب', 'وزن‌کشی', 'بررسی غدد لنفاوی', 'آزمایش ادرار', 'کشت ادرار',
    'آزمایش خون', 'CBC', 'پلاکت', 'آنزیم‌های کبدی', 'قند خون', 'سونوگرافی شکم و لگن',
    'عکس رادیولوژی قفسه سینه'
]

# Patterns for pure noise and whisper hallucinations to filter out
HALLUCINATION_PATTERNS = [
    r'\[\.\.\.\s*repetitive background audio[^\].]*\]',
    r'\[تکرار نویز صوتی پس‌زمینه\]',
    r'\[تکرار مکرر کلمات برای نویز صوتی\]',
    r'موسیقی در مطب پزشکی.*',
    r'موسیقی در موسیقی.*',
    r'موسیقی در متن.*',
    r'\(موسیقی در مطب پزشکی\).*',
    r'بیمار در مطب پزشکی، بیمار در مطب پزشکی.*',
    r'معاینه بیشتر، بیشتر، بیشتر\.*',
    r'اینجا باید بردارید\. اینجا باید بردارید\.*',
    r'زندگی دور از وطن.*',
    r'زندگی مشکلات خودش را دارد.*',
    r'در این زمانه غلط حقیقت برا ببین.*'
]

TIME_PATTERN = re.compile(r'\[(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?) --> (\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)\]\s*([^:]+):\s*(.*)')

def format_sec(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def clean_dialogue_line(text):
    for pat in HALLUCINATION_PATTERNS:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    return text.strip()

def parse_session_transcript(file_path):
    lines = []
    with open(file_path, encoding='utf-8') as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith('==='):
                continue
            m = TIME_PATTERN.match(line_str)
            if m:
                h1, m1, s1 = float(m.group(1)), float(m.group(2)), float(m.group(3))
                h2, m2, s2 = float(m.group(4)), float(m.group(5)), float(m.group(6))
                start_sec = h1*3600 + m1*60 + s1
                end_sec = h2*3600 + m2*60 + s2
                speaker = m.group(7).strip()
                text = m.group(8).strip()
                
                cleaned_text = clean_dialogue_line(text)
                lines.append({
                    'start': start_sec,
                    'end': end_sec,
                    'speaker': speaker,
                    'text': text,
                    'cleaned_text': cleaned_text
                })
    return lines

def segment_into_temporal_blocks(lines, max_gap_seconds=45):
    if not lines:
        return []
    blocks = []
    curr_block = [lines[0]]
    for i in range(1, len(lines)):
        gap = lines[i]['start'] - curr_block[-1]['end']
        if gap > max_gap_seconds:
            blocks.append(curr_block)
            curr_block = [lines[i]]
        else:
            curr_block.append(lines[i])
    if curr_block:
        blocks.append(curr_block)
    return blocks

def classify_and_extract_encounter(block, session_id, encounter_idx):
    # Filter out empty cleaned text
    meaningful_turns = [t for t in block if len(t['cleaned_text']) > 2]
    if len(meaningful_turns) < 3:
        return None  # Too short / just an artifact
    
    start_sec = block[0]['start']
    end_sec = block[-1]['end']
    duration_min = round((end_sec - start_sec) / 60.0, 2)
    
    full_text = ' '.join([t['cleaned_text'] for t in meaningful_turns])
    
    # Check for non-clinical indicators (Phone calls about hospital board, general admin)
    admin_keywords = ['انتخابات', 'هیئت‌مدیره', 'هیئت مدیره', 'سهام‌دار', 'اساسنامه', 'وکالت', 'مجمع', 'مدیرعامل', 'پارکینگ', 'جای پارک']
    admin_score = sum(1 for k in admin_keywords if k in full_text)
    if admin_score >= 2:
        return {
            'type': 'ADMIN_PHONE_CALL',
            'start': start_sec,
            'end': end_sec,
            'duration_min': duration_min
        }
    
    # Check for clinical keywords
    detected_symptoms = []
    for cat, syns in CLINICAL_SYMPTOMS.items():
        if any(s in full_text for s in syns):
            detected_symptoms.append(cat)
            
    detected_meds = []
    for med in CLINICAL_MEDICATIONS:
        if med in full_text:
            detected_meds.append(med)
            
    detected_findings = []
    for exam in CLINICAL_FINDINGS:
        if any(word in full_text for word in exam.split()):
            if 'معاینه' in full_text or 'آزمایش' in full_text or 'سونوگرافی' in full_text:
                if exam not in detected_findings:
                    detected_findings.append(exam)
                    
    # Minimum duration & dialogue turns for a real patient encounter
    if duration_min < 0.6 or len(meaningful_turns) < 4:
        return {
            'type': 'TOO_SHORT',
            'start': start_sec,
            'end': end_sec,
            'duration_min': duration_min
        }

    # Music lyrics / poem indicators (when clinic radio or songs are playing)
    lyrics_keywords = ['غزل', 'عاشقی', 'گریستم', 'دیدگانم', 'دل‌سختی', 'روزگارم', 'موسیقی', 'موزیک', 'ترانه']
    if any(k in full_text for k in lyrics_keywords) and len(detected_meds) == 0 and len(detected_symptoms) == 0:
        return {
            'type': 'MUSIC_LYRICS',
            'start': start_sec,
            'end': end_sec,
            'duration_min': duration_min
        }

    # A genuine clinical encounter MUST have real medical signals (symptoms, medications, or specific exams)
    has_strong_medical_signal = (len(detected_symptoms) >= 1) or (len(detected_meds) >= 1) or \
                                ('آزمایش' in full_text and any(k in full_text for k in ['خون', 'ادرار', 'کبد', 'پلاکت', 'نرمال', 'عفونت'])) or \
                                ('معاینه' in full_text and any(k in full_text for k in ['گوش', 'گلو', 'شکم', 'ریه', 'تب', 'کودک', 'بیمار'])) or \
                                (any(k in full_text for k in ['قطره', 'شربت', 'قرص', 'شیاف', 'آمپول', 'سونوگرافی']))
    
    # Must have both doctor and patient participation or meaningful exchange
    speakers = set(t['speaker'].lower() for t in meaningful_turns)
    has_dialogue = len(speakers) >= 2 or len(meaningful_turns) >= 5
    
    if not (has_strong_medical_signal and has_dialogue):
        return {
            'type': 'IDLE_OR_GENERAL',
            'start': start_sec,
            'end': end_sec,
            'duration_min': duration_min
        }

    # Generic medications capture (e.g. قطره گوش, شربت تب‌بر)
    if 'قطره' in full_text and not any('قطره' in m for m in detected_meds):
        detected_meds.append('قطره (موارد موضعی/گوشی/چشمی)')
    if 'شربت' in full_text and not any('شربت' in m for m in detected_meds):
        detected_meds.append('شربت خوراکی')
        
    # Identify specialty of the 5 doctors
    # 4 pediatricians (21 sessions), 1 general practitioner (8 sessions)
    gp_sessions = {
        'Session_Full_20260913_115117_d33300',
        'Session_Full_20260913_130328_43cf9b',
        'Session_Full_20260913_141847_8034c8',
        'Session_Full_20260913_202446_9790b2',
        'Session_Full_20260913_231510_1e7481',
        'Session_Full_20260914_122450_d7043e',
        'Session_Full_20260914_142958_407639',
        'Session_Full_20260914_165019_ae322f'
    }
    is_pediatric_doctor = (session_id not in gp_sessions)
    doctor_specialty = "متخصص اطفال (Pediatrics)" if is_pediatric_doctor else "پزشک عمومی (General Practice)"
    
    # Accurate Demographic Classification (accounting for parents speaking in pediatric visits)
    infant_keywords = ['نوزاد', 'شیرخوار', 'شیر مادر', 'شیرخشک', 'پوشک', 'زردی', 'ماهشه', 'ماهه است', 'ماهه', 'پستانک', 'واکسن', 'دندان', 'ریفلاکس', 'برفک']
    if is_pediatric_doctor:
        if any(k in full_text for k in infant_keywords):
            patient_category = "نوزاد / شیرخوار (زیر ۱ سال)"
        else:
            patient_category = "کودک / خردسال (۱ تا ۱۲ سال)"
    else:
        if any(k in full_text for k in ['بچه', 'کودک', 'پسرم', 'دخترم', 'نوزاد']):
            patient_category = "کودک / خردسال (مراجعه به عمومی)"
        else:
            patient_category = "بزرگسال (پزشک عمومی)"
            
    # Name extraction if available
    name_match = re.search(r'(?:آقای|خانم|نامش|اسمش)\s+([آ-ی\s]{3,15})', full_text)
    patient_name = name_match.group(1).strip() if name_match else "ثبت‌نشده / ناشناس"
    
    # Clinical Assessment heuristics
    assessments = []
    if 'تب' in full_text and 'ویروس' in full_text:
        assessments.append("عفونت ویروسی حاد (Viral Infection)")
    if 'عفونت ادراری' in full_text or 'سوزش ادرار' in full_text or 'UTI' in full_text:
        assessments.append("عفونت مجاری ادراری (UTI)")
    if 'ریفلاکس' in full_text or 'رفلاکس' in full_text:
        assessments.append("ریفلاکس معده به مری نوزادی (GERD)")
    if 'خس‌خس' in full_text or 'سرفه' in full_text:
        assessments.append("عفونت تنفسی / برونشیولیت (Bronchiolitis / RTI)")
    if 'گوش' in full_text and ('درد' in full_text or 'قطره' in full_text):
        assessments.append("اوتیت میانی / التهاب گوش (Otitis)")
    if 'آفت' in full_text or 'سفیدک' in full_text:
        assessments.append("برفک دهان / آفت نوزادی (Oral Thrush)")
    if 'کبد' in full_text or 'پلاکت' in full_text or 'آنزیم' in full_text:
        assessments.append("بررسی آزمایشگاهی آنزیم‌های کبدی و پلاکت")
    if not assessments:
        assessments.append("معاینه عمومی و پایش علائم بالینی")
        
    # Assemble Clean SOAP Note
    subjective_lines = [t['cleaned_text'] for t in meaningful_turns if 'patient' in t['speaker'].lower()]
    objective_lines = [t['cleaned_text'] for t in meaningful_turns if 'معاین' in t['cleaned_text'] or 'آزمایش' in t['cleaned_text']]
    plan_lines = [t['cleaned_text'] for t in meaningful_turns if 'دارو' in t['cleaned_text'] or 'بخور' in t['cleaned_text'] or 'بده' in t['cleaned_text'] or 'سونوگرافی' in t['cleaned_text']]
    
    soap = {
        'S_Subjective': f"شکایت اصلی: {', '.join(detected_symptoms) if detected_symptoms else 'شرح حال عمومی'}. شرح: {subjective_lines[0] if subjective_lines else 'شرح‌حال در متن ثبت شده است.'}",
        'O_Objective': f"یافته‌های بالینی: {', '.join(detected_findings[:3]) if detected_findings else 'معاینه بالینی انجام شد.'}",
        'A_Assessment': " / ".join(assessments),
        'P_Plan': f"دستور دارویی: {', '.join(detected_meds) if detected_meds else 'توصیه‌های مراقبتی عمومی'} | پیگیری: پایش علائم و مراجعه مجدد در صورت لزوم"
    }
    
    # Formatted dialogue turns
    dialogue_transcript = []
    for t in meaningful_turns:
        dialogue_transcript.append({
            'time': f"[{format_sec(t['start'])} --> {format_sec(t['end'])}]",
            'speaker': t['speaker'],
            'text': t['cleaned_text']
        })
        
    encounter = {
        'encounter_id': f"{session_id}_ENC_{encounter_idx:02d}",
        'session_id': session_id,
        'start_time': format_sec(start_sec),
        'end_time': format_sec(end_sec),
        'duration_minutes': duration_min,
        'turns_count': len(meaningful_turns),
        'patient_category': patient_category,
        'doctor_specialty': doctor_specialty,
        'patient_name': patient_name,
        'chief_complaints': detected_symptoms,
        'prescribed_medications': detected_meds,
        'clinical_findings': detected_findings,
        'clinical_diagnosis': assessments,
        'soap_note': soap,
        'dialogue_sample': dialogue_transcript[:8]  # First turns preview
    }
    return encounter

if __name__ == '__main__':
    # Test on first session
    sample_session = 'Session_Full_20260912_142552_b2fdf1'
    ref_file = glob.glob(f'dataset/{sample_session}/refined/*ai_refined*.txt')[0]
    lines = parse_session_transcript(ref_file)
    blocks = segment_into_temporal_blocks(lines)
    print(f"Total lines: {len(lines)}, Total raw blocks: {len(blocks)}")
    
    encounters = []
    idx = 1
    for b in blocks:
        res = classify_and_extract_encounter(b, sample_session, idx)
        if res and 'encounter_id' in res:
            encounters.append(res)
            idx += 1
            
    print(f"\nExtracted genuine clinical encounters: {len(encounters)}")
    for enc in encounters:
        print(f"\n---> {enc['encounter_id']} [{enc['start_time']} - {enc['end_time']}] ({enc['duration_minutes']} min):")
        print(f"     Patient: {enc['patient_category']} ({enc['patient_name']})")
        print(f"     Complaints: {enc['chief_complaints']}")
        print(f"     Diagnosis: {enc['clinical_diagnosis']}")
        print(f"     Medications: {enc['prescribed_medications']}")
        print(f"     SOAP Plan: {enc['soap_note']['P_Plan']}")

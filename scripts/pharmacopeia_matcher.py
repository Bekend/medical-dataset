# -*- coding: utf-8 -*-
"""
Iranian Pediatric & Outpatient Pharmacopeia and Clinical Entity Matcher
Provides canonical generic naming, English translations, dosage forms,
phonetic fuzzy matching, and dosage/frequency instruction extraction.
"""

import re
import difflib

IRANIAN_PHARMACOPEIA = {
    # آنتی‌بیوتیک‌ها (Antibiotics)
    'سفیکسیم': {
        'name_en': 'Cefixime',
        'category': 'آنتی‌بیوتیک سفلوسپورین',
        'form': 'سوسپانسیون خوراکی (۱۰۰mg/5ml)',
        'aliases': ['سفیکسیم', 'سفیک‌سیم', 'سفیک سیم', 'سفکسیم', 'cefixime']
    },
    'آموکسی‌سیلین': {
        'name_en': 'Amoxicillin',
        'category': 'آنتی‌بیوتیک پنی‌سیلینی',
        'form': 'سوسپانسیون خوراکی (۱۲۵/۲۵۰mg)',
        'aliases': ['آموکسی‌سیلین', 'اموکسی سیلین', 'آموکسی سیلین', 'اموکسی']
    },
    'کوآموکسی‌کلاو': {
        'name_en': 'Co-Amoxiclav',
        'category': 'آنتی‌بیوتیک ترکیبی',
        'form': 'سوسپانسیون خوراکی',
        'aliases': ['کوآموکسی‌کلاو', 'کواموکسی کلاو', 'کلاویسیلین', 'کلاو']
    },
    'آزیترومایسین': {
        'name_en': 'Azithromycin',
        'category': 'آنتی‌بیوتیک ماکرولید',
        'form': 'سوسپانسیون خوراکی (۱۰۰/۲۰۰mg)',
        'aliases': ['آزیترومایسین', 'ازیترومایسین', 'زیمکس', 'آزیترو']
    },
    'سفالکسین': {
        'name_en': 'Cephalexin',
        'category': 'آنتی‌بیوتیک',
        'form': 'سوسپانسیون خوراکی (۱۲۵/۲۵۰mg)',
        'aliases': ['سفالکسین', 'سفالکس']
    },
    'مترونیدازول': {
        'name_en': 'Metronidazole',
        'category': 'آنتی‌بیوتیک و ضد انگل',
        'form': 'سوسپانسیون خوراکی',
        'aliases': ['مترونیدازول', 'مترونیداز']
    },

    # تب‌برها و ضددردها (Antipyretics & Analgesics)
    'استامینوفن': {
        'name_en': 'Acetaminophen (Paracetamol)',
        'category': 'تب‌بر و ضددرد',
        'form': 'قطره خوراکی / شربت',
        'aliases': ['استامینوفن', 'پاراستامول', 'شربت استامینوفن', 'قطره استامینوفن', 'تایلنول']
    },
    'شیاف استامینوفن': {
        'name_en': 'Acetaminophen Suppository',
        'category': 'تب‌بر مقعدی سریع‌الاثر',
        'form': 'شیاف اطفال (۱۲۵mg / ۳۲۵mg)',
        'aliases': ['شیاف استامینوفن', 'شیاف ۱۲۵', 'شیاف ۳۲۵', 'شیاف تب']
    },
    'ایبوپروفن': {
        'name_en': 'Ibuprofen',
        'category': 'ضدالتهاب و تب‌بر قوی (NSAID)',
        'form': 'شربت سوسپانسیون (۱۰۰mg/5ml)',
        'aliases': ['ایبوپروفن', 'بروفن', 'شربت بروفن', 'ادویل']
    },
    'شیاف دیکلوفناک': {
        'name_en': 'Diclofenac Suppository',
        'category': 'ضددرد و ضدالتهاب',
        'form': 'شیاف (۵۰mg / ۱۰۰mg)',
        'aliases': ['شیاف دیکلوفناک', 'دیکلوفناک']
    },

    # ضدسرفه، ضدحساسیت و تنفسی (Cough, Cold & Respiratory)
    'شربت پلارژین کیدز': {
        'name_en': 'Pelargin Kids',
        'category': 'ضدسرفه و سرماخوردگی گیاهی',
        'form': 'شربت عصاره پلارگونیوم',
        'aliases': ['پلارژین', 'پلارژین کیدز', 'پلارجین']
    },
    'دیفن‌هیدرامین': {
        'name_en': 'Diphenhydramine',
        'category': 'آنتی‌هیستامین و ضدسرفه',
        'form': 'شربت خوراکی',
        'aliases': ['دیفن‌هیدرامین', 'دیفین', 'دیفن هیدرامین', 'دینتاکیل', 'دیفن']
    },
    'کتوتیفن': {
        'name_en': 'Ketotifen',
        'category': 'ضدحساسیت و پیشگیری از آسم',
        'form': 'شربت خوراکی',
        'aliases': ['کتوتیفن', 'زادتن', 'زادیتن']
    },
    'سیتریزین': {
        'name_en': 'Cetirizine',
        'category': 'آنتی‌هیستامین نسل دوم',
        'form': 'شربت / قطره خوراکی',
        'aliases': ['سیتریزین', 'ستریزین', 'زیرتک']
    },
    'نئوتادین': {
        'name_en': 'Neotadin (Desloratadine)',
        'category': 'آنتی‌هیستامین غیرخواب‌آور',
        'form': 'شربت خوراکی',
        'aliases': ['نئوتادین', 'دس‌لوراتادین']
    },
    'سالبوتامول': {
        'name_en': 'Salbutamol',
        'category': 'گشادکننده برونش (Bronchodilator)',
        'form': 'شربت / اسپری استنشاقی',
        'aliases': ['سالبوتامول', 'ونتولین', 'اسپری آبی']
    },
    'اسپری سدیم کلراید': {
        'name_en': 'Sodium Chloride 0.65%',
        'category': 'شستشو و بازکننده بینی نوزاد',
        'form': 'اسپری / قطره رینوسالتین',
        'aliases': ['سدیم کلراید', 'رینوسالتین', 'قطره نمکی', 'سرم شستشو']
    },

    # گوارش، ریفلاکس و کولیک نوزاد (GI, Reflux & Colic)
    'امپرازول': {
        'name_en': 'Omeprazole',
        'category': 'مهارکننده پمپ پروتون (آنتی‌ریفلاکس)',
        'form': 'ساشه پودر خوراکی / کپسول میکروگرانول',
        'aliases': ['امپرازول', 'امپراز', 'امپرازول ساشه']
    },
    'اسومپرازول': {
        'name_en': 'Esomeprazole (Nexium)',
        'category': 'آنتی‌ریفلاکس پیشرفته نوزاد',
        'form': 'ساشه گرانول پودری',
        'aliases': ['اسومپرازول', 'نکسیوم']
    },
    'فاموتیدین': {
        'name_en': 'Famotidine',
        'category': 'کاهنده اسید معده (H2 Blocker)',
        'form': 'شربت سوسپانسیون / قرص',
        'aliases': ['فاموتیدین', 'فاموتید']
    },
    'قطره پدی‌لاکت': {
        'name_en': 'PediLact Probiotic',
        'category': 'پروبیوتیک قطره‌ای نوزاد و کودک',
        'form': 'قطره خوراکی پروبیوتیک',
        'aliases': ['پدی‌لاکت', 'پدیلاکت', 'پدی لاک', 'پروبیوتیک']
    },
    'شربت گریپ واتر': {
        'name_en': 'Gripe Water',
        'category': 'ضدنفخ و کولیک نوزادی گیاهی',
        'form': 'شربت خوراکی',
        'aliases': ['گریپ واتر', 'گریپ‌واتر', 'گریپ']
    },
    'قطره دایمتیکون': {
        'name_en': 'Dimethicone (ColicEz)',
        'category': 'ضدکولیک و گاز معده نوزاد',
        'form': 'قطره خوراکی ضد نفخ',
        'aliases': ['دایمتیکون', 'دایمیتیکون', 'کولیک ایز', 'کولیکیز']
    },
    'پودر پیدرولاکس': {
        'name_en': 'Pidrolax (PEG 4000)',
        'category': 'ملین اسمزی پودری',
        'form': 'پودر خوراکی ساشه',
        'aliases': ['پیدرولاکس', 'پلی‌اتیلن گلیکول']
    },
    'سرم خوراکی او آر اس': {
        'name_en': 'Oral Rehydration Salts (ORS)',
        'category': 'محلول جبران کم‌آبی در اسهال و استفراغ',
        'form': 'ساشه پودر محلول در آب',
        'aliases': ['او آر اس', 'ORS', 'او ار اس', 'سرم خوراکی']
    },

    # گوش، چشم و موضعی (Otic, Ophthalmic & Topical)
    'قطره نیستاتین': {
        'name_en': 'Nystatin Drops',
        'category': 'ضدقارچ موضعی (درمان برفک دهان نوزاد)',
        'form': 'قطره سوسپانسیون دهانی',
        'aliases': ['نیستاتین', 'نیستات', 'قطره برفک']
    },
    'قطره بتامتازون گوش': {
        'name_en': 'Betamethasone Otic',
        'category': 'کورتیکواستروئید ضدالتهاب گوش',
        'form': 'قطره گوشی',
        'aliases': ['بتامتازون', 'قطره بتامتازون']
    },
    'قطره سیپروفلوکساسین گوش': {
        'name_en': 'Ciprofloxacin Otic',
        'category': 'آنتی‌بیوتیک قطره‌ای گوش',
        'form': 'قطره گوشی ۰.۳٪',
        'aliases': ['سیپروفلوکساسین', 'سیپروکسین']
    },
    'قطره پلی‌میکسین گوش': {
        'name_en': 'Polymyxin-Neomycin Otic',
        'category': 'آنتی‌بیوتیک ترکیبی گوش',
        'form': 'قطره گوشی',
        'aliases': ['پلی‌میکسین', 'پلی میکسین']
    },
    'پماد موپیروسین': {
        'name_en': 'Mupirocin 2%',
        'category': 'آنتی‌بیوتیک موضعی پوستی (زخم و زردزخم)',
        'form': 'پماد موضعی ۲٪',
        'aliases': ['موپیروسین', 'باکتروبان']
    },
    'پماد هیدروکورتیزون': {
        'name_en': 'Hydrocortisone 1%',
        'category': 'ضدالتهاب و اگزما پوستی',
        'form': 'پماد موضعی ۱٪',
        'aliases': ['هیدروکورتیزون']
    },
    'پماد کالاندولا': {
        'name_en': 'Calendula Ointment',
        'category': 'ترمیم‌کننده و ضدسوختگی ادرار نوزاد',
        'form': 'پماد موضعی گیاهی',
        'aliases': ['کالاندولا', 'کالاندولا سوختگی']
    },
    'پماد زینک اکساید': {
        'name_en': 'Zinc Oxide 20%',
        'category': 'محافظ پوست و ضدسوختگی پوشک',
        'form': 'پماد موضعی',
        'aliases': ['زینک اکساید', 'اکسید دوزنگ']
    },

    # مکمل‌ها و پایش رشد (Supplements & Growth)
    'قطره آهن (فروس سولفات)': {
        'name_en': 'Ferrous Sulfate / Iron Drops',
        'category': 'مکمل آهن پیشگیری از آنمی نوزاد',
        'form': 'قطره خوراکی آهن',
        'aliases': ['قطره آهن', 'آهن لیپوزومال', 'فروگلوبین', 'سیدرال']
    },
    'قطره مولتی‌ویتامین و آ+د': {
        'name_en': 'Multivitamin + A&D Drops',
        'category': 'مکمل ویتامین‌های رشد نوزاد',
        'form': 'قطره خوراکی',
        'aliases': ['مولتی‌ویتامین', 'مولتی ویتامین', 'ویتامین آ+د', 'آ د', 'آ+د']
    }
}

DOSAGE_REGEX = re.compile(
    r'(?:'
    r'هر\s*(?:\d+|[\u06f0-\u06f9]+|یک|دو|سه|چهار|شش|هشت|دوازده)\s*ساعت(?:\s*(?:\d+|[\u06f0-\u06f9]+|یک|دو|سه|نصف)\s*(?:قطره|سی‌سی|قاشق|پیمانه|شیاف|ساشه|پاف))?'
    r'|روزی\s*(?:\d+|[\u06f0-\u06f9]+|یک|دو|سه|چهار)\s*بار(?:\s*(?:\d+|[\u06f0-\u06f9]+|یک|دو|نصف)\s*(?:قطره|سی‌سی|قاشق|پیمانه|شیاف))?'
    r'|(?:\d+|[\u06f0-\u06f9]+|دو|سه|چهار|پنج|ده|دوازده)\s*قطره'
    r'|(?:\d+|[\u06f0-\u06f9]+|یک|دو|نصف)\s*(?:سی‌سی|پیمانه|قاشق)'
    r'|صبح\s*و\s*شب'
    r'|قبل\s*از\s*خواب'
    r'|سر\s*ساعت'
    r')'
)

def has_persian_word(term, text):
    return bool(re.search(r'(?<![آ-یء-ي])' + re.escape(term) + r'(?![آ-یء-ي])', text))

def extract_prescriptions_with_pharmacopeia(full_text):
    """
    Scans clinical dialogue with exact and fuzzy pharmacopeia matching.
    Extracts canonical drug name, English generic name, dosage form, and instructions.
    """
    matched_drugs = []
    
    # Extract candidate dosage instructions across the dialogue
    all_dosages = DOSAGE_REGEX.findall(full_text)
    
    # Tokenize text into words for fuzzy matching
    words = re.findall(r'[آ-یء-ي]{4,}', full_text)
    
    for canon_name, info in IRANIAN_PHARMACOPEIA.items():
        is_matched = False
        matched_alias = None
        
        # 1. Exact alias check
        for alias in info['aliases']:
            if has_persian_word(alias, full_text):
                is_matched = True
                matched_alias = alias
                break
                
        # 2. Fuzzy match check if not already matched
        if not is_matched:
            for alias in info['aliases']:
                if len(alias) >= 5:
                    close = difflib.get_close_matches(alias, words, n=1, cutoff=0.82)
                    if close:
                        is_matched = True
                        matched_alias = close[0]
                        break
                        
        if is_matched:
            # Find specific dosage near the drug mention if possible
            specific_dose = "طبق دستور پزشک"
            if matched_alias:
                # Search within a 60-character window around the matched alias
                idx = full_text.find(matched_alias)
                if idx != -1:
                    window = full_text[max(0, idx - 40): min(len(full_text), idx + 80)]
                    window_doses = DOSAGE_REGEX.findall(window)
                    if window_doses:
                        specific_dose = window_doses[0]
                    elif all_dosages:
                        specific_dose = all_dosages[0]
            elif all_dosages:
                specific_dose = all_dosages[0]
                
            matched_drugs.append({
                'name_fa': canon_name,
                'name_en': info['name_en'],
                'category': info['category'],
                'form': info['form'],
                'dosage_instruction': specific_dose
            })
            
    # Handle generic pediatric drops/syrup if no specific generic was caught
    if not matched_drugs:
        if has_persian_word('شربت', full_text):
            dose = all_dosages[0] if all_dosages else "طبق دستور پزشک"
            matched_drugs.append({
                'name_fa': 'شربت خوراکی اطفال',
                'name_en': 'Pediatric Oral Syrup',
                'category': 'درمان علامتی سرماخوردگی / گوارشی',
                'form': 'شربت خوراکی',
                'dosage_instruction': dose
            })
        if has_persian_word('قطره', full_text):
            dose = all_dosages[0] if all_dosages else "طبق دستور پزشک"
            matched_drugs.append({
                'name_fa': 'قطره موضعی / خوراکی',
                'name_en': 'Pediatric Drops',
                'category': 'قطره دارویی',
                'form': 'قطره',
                'dosage_instruction': dose
            })
        if has_persian_word('شیاف', full_text):
            matched_drugs.append({
                'name_fa': 'شیاف اطفال',
                'name_en': 'Pediatric Suppository',
                'category': 'تب‌بر / مسکن',
                'form': 'شیاف مقعدی',
                'dosage_instruction': 'در زمان تب بالا هر ۶ ساعت'
            })
            
    return matched_drugs

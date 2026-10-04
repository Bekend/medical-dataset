# -*- coding: utf-8 -*-
import os, glob, json, sys
import pandas as pd
import extract_clinical_dataset as ex

sys.stdout.reconfigure(encoding='utf-8')

sessions = sorted([d for d in os.listdir('dataset') if os.path.isdir(os.path.join('dataset', d))])
print(f'Starting extraction across {len(sessions)} sessions with specialty-aware demographic model...')

all_encounters = []

for s in sessions:
    ref_files = glob.glob(f'dataset/{s}/refined/*ai_refined*.txt')
    if not ref_files:
        continue
    ref_file = ref_files[0]
    lines = ex.parse_session_transcript(ref_file)
    blocks = ex.segment_into_temporal_blocks(lines)
    
    encs = []
    idx = 1
    for b in blocks:
        res = ex.classify_and_extract_encounter(b, s, idx)
        if res and 'encounter_id' in res:
            encs.append(res)
            idx += 1
            
    all_encounters.extend(encs)
    print(f'{s[:28]}: lines={len(lines)}, encounters={len(encs)}')

print(f'\nTotal extracted clinical encounters: {len(all_encounters)}')
total_clin_hours = sum(e['duration_minutes'] for e in all_encounters) / 60.0
print(f'Total pure clinical dialogue duration: {total_clin_hours:.2f} hours')

# Save updated JSON
with open('clinical_encounters_corpus.json', 'w', encoding='utf-8') as f:
    json.dump(all_encounters, f, ensure_ascii=False, indent=2)

# Build DataFrame and save CSV
rows = []
for e in all_encounters:
    rows.append({
        'Encounter_ID': e['encounter_id'],
        'Session_ID': e['session_id'],
        'Doctor_Specialty': e.get('doctor_specialty', ''),
        'Start_Time': e['start_time'],
        'End_Time': e['end_time'],
        'Duration_Minutes': e['duration_minutes'],
        'Turns_Count': e['turns_count'],
        'Patient_Category': e['patient_category'],
        'Chief_Complaints': ', '.join(e['chief_complaints']),
        'Prescribed_Medications': ', '.join(e['prescribed_medications']),
        'Diagnoses': ' | '.join(e['clinical_diagnosis']),
        'SOAP_Subjective': e['soap_note']['S_Subjective'],
        'SOAP_Assessment': e['soap_note']['A_Assessment'],
        'SOAP_Plan': e['soap_note']['P_Plan']
    })

df = pd.DataFrame(rows)
df.to_csv('clinical_encounters_summary.csv', index=False, encoding='utf-8-sig')
print('Successfully saved updated clinical_encounters_corpus.json and clinical_encounters_summary.csv!')

# Print demographics breakdown
print('\n=== Demographic Breakdown ===')
print(df['Patient_Category'].value_counts())
print('\n=== Specialty Breakdown ===')
print(df['Doctor_Specialty'].value_counts())

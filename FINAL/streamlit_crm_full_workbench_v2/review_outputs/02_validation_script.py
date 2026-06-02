"""
CRM 검증 스크립트 v1.0
실행: python3 02_validation_script.py
모든 CSV를 /home/claude/review/ 에 자동 생성합니다.
입력 경로는 스크립트 상단에서 직접 지정합니다.
"""
import pandas as pd, numpy as np, os, hashlib

# ── 경로 설정 ──────────────────────────────────────────────
BASE   = '/home/claude/handoff'
RAW    = '/home/claude/rawdata'
OUT    = '/home/claude/review'
F06X   = f'{BASE}/06x_expanded_dataset.csv'
FMEM   = f'{RAW}/Membership_v2.csv'
FMAP   = f'{RAW}/User_Mapping_v2.csv'
FHIST  = f'{RAW}/View_History_v2.csv'
FMOV   = f'{RAW}/Movie_Master_v2.csv'
os.makedirs(OUT, exist_ok=True)

# ── 데이터 로드 ────────────────────────────────────────────
df   = pd.read_csv(F06X)
mem  = pd.read_csv(FMEM)
mmap = pd.read_csv(FMAP)
hist = pd.read_csv(FHIST)
mov  = pd.read_csv(FMOV).drop_duplicates('MOVIE_NUM')

df['w1w2'] = df['watch_time_min_w1'] + df['watch_time_min_w2']

# ── 세그먼트 함수 ──────────────────────────────────────────
def late(w3):
    if w3 >= 141: return 'active'
    elif w3 > 0:  return 'weak'
    else:         return 'dormant'

def seg_hg(row):     # 광일 hard gate
    e = (row['w1w2'] >= 119) and (row['watch_ratio_under_5m'] <= 0.25)
    l = late(row['watch_time_min_w3'])
    if e: return 'S1' if l=='active' else ('S2' if l=='weak' else 'S3')
    else: return 'S4' if l=='active' else ('S5' if l=='weak' else 'S6')

def seg_ng(row):     # hard gate 제거
    e = row['w1w2'] >= 119
    l = late(row['watch_time_min_w3'])
    if e: return 'S1' if l=='active' else ('S2' if l=='weak' else 'S3')
    else: return 'S4' if l=='active' else ('S5' if l=='weak' else 'S6')

df['seg_hg'] = df.apply(seg_hg, axis=1)
df['seg_ng'] = df.apply(seg_ng, axis=1)
dfp = df[df['is_promotion']==1].copy()

# ══════════════════════════════════════════════════════════
# CSV 1: crm_segment_summary_promotion_gwangil.csv
# ══════════════════════════════════════════════════════════
rows = []
for seg in ['S1','S2','S3','S4','S5','S6']:
    sub = dfp[dfp['seg_hg']==seg]
    n   = len(sub)
    ch  = sub['is_repurchase'].eq(0).sum()
    rows.append({'segment':seg,'event_count':n,'churn_count':ch,
                 'churn_rate':round(ch/n*100,2),'segment_rule':'광일 hard gate (w1w2>=119 AND ratio<=0.25)'})
pd.DataFrame(rows).to_csv(f'{OUT}/crm_segment_summary_promotion_gwangil.csv',index=False)
print("CSV1 완료")

# ══════════════════════════════════════════════════════════
# CSV 2: crm_segment_migration_hardgate_vs_nohardgate.csv
# ══════════════════════════════════════════════════════════
mig = dfp.groupby(['seg_ng','seg_hg']).agg(
    event_count=('USER_KEY','count'),
    churn_rate_hg=('is_repurchase', lambda x: round(x.eq(0).mean()*100,2))
).reset_index()
mig.columns = ['seg_no_hardgate','seg_hardgate','event_count','churn_rate_hardgate_seg']
mig.to_csv(f'{OUT}/crm_segment_migration_hardgate_vs_nohardgate.csv',index=False)
print("CSV2 완료")

# ══════════════════════════════════════════════════════════
# CSV 3: crm_s6_internal_split_full.csv
# ══════════════════════════════════════════════════════════
# w4 계산
mem['reg_date'] = pd.to_datetime(mem['reg_date'])
hist['watch_day'] = pd.to_datetime(hist['watch_day'].astype(str))
mh = mem.merge(mmap, on='USER_KEY', how='left').merge(hist, on='USER_NUM', how='left')
mh['day_offset'] = (mh['watch_day'] - mh['reg_date']).dt.days
w4 = mh[mh['day_offset'].between(21,27)].groupby('USER_KEY')['watch_time(min)'].sum().reset_index()
w4.columns = ['USER_KEY','w4_min']
dfp2 = dfp.merge(w4, on='USER_KEY', how='left')
dfp2['w4_min'] = dfp2['w4_min'].fillna(0)
dfp2['has_w4'] = dfp2['w4_min'] > 0

s6 = dfp2[dfp2['seg_hg']=='S6'].copy()
def s6_type(row):
    if row['w1w2'] == 0: return 'A_무시청형'
    elif row['w1w2'] <= 30: return 'B_탐색형'
    elif row['w1w2'] < 119: return 'C_저소비형'
    else: return 'D_ratio탈락고시청형'
s6['s6_type'] = s6.apply(s6_type, axis=1)

s6_rows = []
for t in ['A_무시청형','B_탐색형','C_저소비형','D_ratio탈락고시청형']:
    sub = s6[s6['s6_type']==t]
    n  = len(sub)
    if n == 0: continue
    ch = sub['is_repurchase'].eq(0).sum()
    w4y = sub[sub['has_w4']==True]
    w4n = sub[sub['has_w4']==False]
    s6_rows.append({
        's6_type':t, 'event_count':n, 'churn_count':ch,
        'churn_rate':round(ch/n*100,2),
        'w1w2_median':round(sub['w1w2'].median(),1),
        'w3_median':round(sub['watch_time_min_w3'].median(),1),
        'w4_view_rate':round(sub['has_w4'].mean()*100,2),
        'w4_churn_rate_if_view':round(w4y['is_repurchase'].eq(0).mean()*100,2) if len(w4y)>0 else None,
        'w4_churn_rate_if_no_view':round(w4n['is_repurchase'].eq(0).mean()*100,2) if len(w4n)>0 else None,
        'note':'w1w2=0 포함 / ratio>0.25 AND w1w2>=119 포함' if t=='D_ratio탈락고시청형' else ''
    })
pd.DataFrame(s6_rows).to_csv(f'{OUT}/crm_s6_internal_split_full.csv',index=False)
print("CSV3 완료")

# ══════════════════════════════════════════════════════════
# CSV 4: crm_w4_by_segment.csv
# ══════════════════════════════════════════════════════════
w4_rows = []
for seg in ['S1','S2','S3','S4','S5','S6']:
    sub = dfp2[dfp2['seg_hg']==seg]
    yes = sub[sub['has_w4']==True]
    no  = sub[sub['has_w4']==False]
    w4_rows.append({
        'segment':seg,
        'total_events':len(sub),
        'w4_view_events':len(yes),
        'w4_view_rate_pct':round(len(yes)/len(sub)*100,2),
        'churn_rate_w4_yes':round(yes['is_repurchase'].eq(0).mean()*100,2) if len(yes)>0 else None,
        'churn_rate_w4_no':round(no['is_repurchase'].eq(0).mean()*100,2) if len(no)>0 else None,
        'gap_pct':round((no['is_repurchase'].eq(0).mean()-yes['is_repurchase'].eq(0).mean())*100,2) if len(yes)>0 else None,
        'w4_definition':'Day 21~27 (day_offset between 21 and 27)',
        'join_key':'USER_KEY via User_Mapping_v2 USER_NUM',
    })
pd.DataFrame(w4_rows).to_csv(f'{OUT}/crm_w4_by_segment.csv',index=False)
print("CSV4 완료")

# ══════════════════════════════════════════════════════════
# CSV 5: crm_w2_w4_cross_table.csv
# ══════════════════════════════════════════════════════════
dfp2['w2_increased'] = dfp2['diff_between_w2_w1'] > 0
cross_rows = []
for seg in ['S3','S6']:
    sub = dfp2[dfp2['seg_hg']==seg]
    for w2u in [True,False]:
        for w4v in [True,False]:
            mask = (sub['w2_increased']==w2u)&(sub['has_w4']==w4v)
            n  = mask.sum()
            ch = sub.loc[mask,'is_repurchase'].eq(0).sum()
            cross_rows.append({'segment':seg,'w2_increased':w2u,'has_w4':w4v,
                               'event_count':n,'churn_count':ch,
                               'churn_rate':round(ch/n*100,2) if n>0 else None})
pd.DataFrame(cross_rows).to_csv(f'{OUT}/crm_w2_w4_cross_table.csv',index=False)
print("CSV5 완료")

# ══════════════════════════════════════════════════════════
# CSV 6: crm_w4_volume_bins.csv
# ══════════════════════════════════════════════════════════
vol_rows = []
for seg in ['S2','S3','S5','S6']:
    sub_w4 = dfp2[(dfp2['seg_hg']==seg)&(dfp2['has_w4']==True)].copy()
    bins = [0,30,100,300,9999]
    labels = ['1~30','31~100','101~300','300+']
    sub_w4['bin'] = pd.cut(sub_w4['w4_min'], bins=bins, labels=labels)
    for b in labels:
        g = sub_w4[sub_w4['bin']==b]
        n = len(g); ch = g['is_repurchase'].eq(0).sum()
        vol_rows.append({'segment':seg,'w4_minutes_bin':b,'event_count':n,
                         'churn_count':ch,'churn_rate':round(ch/n*100,2) if n>0 else None})
pd.DataFrame(vol_rows).to_csv(f'{OUT}/crm_w4_volume_bins.csv',index=False)
print("CSV6 완료")

print("\n=== 기본 CSV 6개 완료 ===")

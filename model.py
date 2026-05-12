import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from tabulate import tabulate
import unicodedata

# --- TERMINAL ALIGNMENT FIXES ---
pd.set_option('display.max_colwidth', None)
pd.set_option('display.unicode.east_asian_width', True)

def get_visual_width(text):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)

def pad_title(title, width=50):
    current_width = get_visual_width(title)
    padding_needed = max(0, width - current_width)
    return str(title) + (" " * padding_needed)

# --- CORE LOGIC (BLACK BOX) ---
def get_recommendations(df_master, df_b30, target_rating, min_const, max_const, min_score, target_score, include_unplayed):
    features = [
        '4k', 'Keyboard', 'Jacks', 'Xhanding', 'Trill', 'Rolls', 'Stamina', 
        'USAO', 'Cyaegha', 'Small Notes', 'Tap Slides', 'Anchor Hold', 
        'Split Trill', 'Gimmick', 'Tateren', 'Train'
    ]

    # 1. BULLETPROOF FEATURE PARSING
    df_master.columns = df_master.columns.str.strip()
    for feat in features:
        if feat in df_master.columns:
            df_master[feat] = df_master[feat].apply(
                lambda x: 1.0 if str(x).strip().upper() in ['TRUE', '1', '1.0', 'YES'] else 0.0
            )
        else:
            df_master[feat] = 0.0 

    # 2. AGGRESSIVE NORMALIZATION
    df_master['Match_Key'] = df_master['Title'].astype(str).str.lower().str.replace('"', '').str.replace(' ', '').str.replace('　', '').str.strip()
    df_b30['match_key'] = df_b30['title'].astype(str).str.lower().str.replace('"', '').str.replace(' ', '').str.replace('　', '').str.strip()
    
    if 'const' in df_b30.columns:
        df_b30 = df_b30.sort_values('score', ascending=False).drop_duplicates(subset=['match_key', 'const'])
    else:
        df_b30 = df_b30.sort_values('score', ascending=False).drop_duplicates(subset=['match_key'])

    # 3. EXTRACT SKILLSET 
    matched_data = df_master[df_master['Match_Key'].isin(df_b30['match_key'])]
    if matched_data.empty: return "Error: 0 titles matched. Verify your CSV titles."
    
    user_vector = pd.DataFrame(matched_data[features].mean().values.reshape(1, -1), columns=features)

    # 4. POOLING (WITH UNPLAYED TOGGLE)
    eligible_b30 = df_b30[(df_b30['score'] >= min_score) & (df_b30['score'] < target_score)].copy()

    merge_cols = ['match_key', 'score', 'const'] if 'const' in eligible_b30.columns else ['match_key', 'score']
    
    upscore_pool = pd.merge(
        eligible_b30[merge_cols],
        df_master,
        left_on='match_key',
        right_on='Match_Key',
        how='inner'
    )
    
    if 'const' in upscore_pool.columns:
        upscore_pool = upscore_pool[abs(upscore_pool['const'].astype(float) - upscore_pool['constant'].astype(float)) < 0.2]

    upscore_pool = upscore_pool[
        (upscore_pool['constant'] >= min_const) & 
        (upscore_pool['constant'] <= max_const)
    ]
    
    def get_push_status(score):
        if score == 1010000: return "MAX (AJC)" 
        if score >= 1009900: return "PUSH (from 99AJ)"
        if score >= 1009000: return "PUSH (from SSS+)"
        if score >= 1007500: return "PUSH (from SSS)"
        if score >= 1005000: return "PUSH (from SS+)"
        if score >= 1000000: return "PUSH (from SS)"
        if score >= 990000:  return "PUSH (from S+)"
        if score >= 975000:  return "PUSH (from S)"
        return "PUSH (from <S)"

    upscore_pool['Status'] = upscore_pool['score'].apply(get_push_status)

    # --- THE TOGGLE LOGIC ---
    if include_unplayed:
        def is_unplayed(row):
            matches = df_b30[df_b30['match_key'] == row['Match_Key']]
            if matches.empty: return True 
            if 'const' in matches.columns:
                for played_const in matches['const']:
                    try:
                        if abs(float(played_const) - float(row['constant'])) < 0.2:
                            return False 
                    except ValueError:
                        continue
                return True 
            return False 

        df_master['Is_Unplayed'] = df_master.apply(is_unplayed, axis=1)

        new_pool = df_master[
            (df_master['constant'] >= min_const) & 
            (df_master['constant'] <= max_const) &
            (df_master['Is_Unplayed'])
        ].copy()
        new_pool['Status'] = "NEW"

        combined_pool = pd.concat([upscore_pool, new_pool], ignore_index=True)
    else:
        # If toggle is False, we ONLY look at your existing scores. No new charts allowed.
        combined_pool = upscore_pool.copy()

    if combined_pool.empty:
        return f"No charts found in the {min_const} to {max_const} range ready for this push."

    # 5. KNN: Pattern Matching
    knn = NearestNeighbors(n_neighbors=min(len(combined_pool), 20), metric='cosine')
    training_data = combined_pool[features].fillna(0).astype(float)
    knn.fit(training_data) 
    
    distances, indices = knn.kneighbors(user_vector)
    
    results = combined_pool.iloc[indices[0]].copy()
    results['Match'] = (1 - distances[0]).round(3)

    # 6. DYNAMIC TARGETING & CLEANUP
    def get_dynamic_req(target_val):
        ladder = {
            1010000: "AJC (1,010,000)",
            1009900: "99AJ (1,009,900)",
            1009000: "SSS+ (1,009,000)",
            1007500: "SSS (1,007,500)",
            1005000: "SS+ (1,005,000)",
            1000000: "SS (1,000,000)",
            990000:  "S+ (990,000)",
            975000:  "S (975,000)"
        }
        return ladder.get(target_val, f"TARGET ({target_val:,})")

    results['Requirement'] = get_dynamic_req(target_score)
    results = results.drop_duplicates(subset=['Title'])
    results = results.sort_values(by=['Match', 'constant'], ascending=[False, True])
    results['Title'] = results['Title'].apply(lambda x: pad_title(x, width=50))
    
    return results.head(20)


# ==============================================================================
# --- EXECUTION & USER CONFIGURATION ---
# ==============================================================================

df_master = pd.read_csv('chuni_model.csv', quotechar='"')
df_best30 = pd.read_csv('b30_sample.csv', quotechar='"', skipinitialspace=True, on_bad_lines='skip')

# --- CHANGE THESE SETTINGS FOR YOUR GRIND ---
TARGET_RATING    = 17.3
MIN_CONST        = 15.6
MAX_CONST        = 15.6

MIN_SCORE        = 0  # Bottom of the bracket
TARGET_SCORE     = 1007500  # The finish line (Dict maps this to AJC automatically)

INCLUDE_UNPLAYED = True    # <-- Set to False to completely hide "NEW" charts
# --------------------------------------------

final_results = get_recommendations(
    df_master, 
    df_best30, 
    target_rating=TARGET_RATING, 
    min_const=MIN_CONST, 
    max_const=MAX_CONST,
    min_score=MIN_SCORE,
    target_score=TARGET_SCORE,
    include_unplayed=INCLUDE_UNPLAYED
)

# Grab the clean label for the print statement
print_label = final_results['Requirement'].iloc[0] if not isinstance(final_results, str) else f"TARGET ({TARGET_SCORE:,})"

print(f"\n--- TARGET GRIND: {print_label} ({MIN_CONST} - {MAX_CONST}) ---")
if isinstance(final_results, str):
    print(final_results)
else:
    print(tabulate(final_results[['Title', 'constant', 'Requirement', 'Match', 'Status']], 
                   headers=['Title', 'Const', 'Requirement', 'Match', 'Status'], tablefmt='grid'))
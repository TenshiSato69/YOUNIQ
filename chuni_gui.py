import pandas as pd
import numpy as np
import os
from sklearn.neighbors import NearestNeighbors
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

# --- MODERN RATING MATH ---
def calculate_rating(score, constant):
    if score >= 1009000: return constant + 2.15
    if score >= 1007500: return constant + 2.0 + (score - 1007500) * 0.0001
    if score >= 1005000: return constant + 1.5 + (score - 1005000) * 0.0002
    if score >= 1000000: return constant + 1.0 + (score - 1000000) * 0.0001
    if score >= 990000:  return constant + 0.6 + (score - 990000) * 0.00004
    if score >= 975000:  return constant + 0.0 + (score - 975000) * 0.00004
    return 0.0

def get_required_score(target_chart_rating, constant):
    diff = round(target_chart_rating - constant, 4)
    if diff > 2.15: return 1010001 
    if diff == 2.15: return 1009000
    if diff >= 2.0: return int(round(1007500 + (diff - 2.0) / 0.0001))
    if diff >= 1.5: return int(round(1005000 + (diff - 1.5) / 0.0002))
    if diff >= 1.0: return int(round(1000000 + (diff - 1.0) / 0.0001))
    if diff >= 0.6: return int(round(990000 + (diff - 0.6) / 0.00004))
    if diff >= 0.0: return int(round(975000 + (diff - 0.0) / 0.00004))
    return 0

def get_rank_name(score):
    if score >= 1009000: return "SSS+"
    if score >= 1007500: return "SSS"
    if score >= 1005000: return "SS+"
    if score >= 1000000: return "SS"
    if score >= 990000:  return "S+"
    if score >= 975000:  return "S"
    return "Below S"

# --- CORE LOGIC ---
def get_recommendations(df_master, df_player, target_mode, target_val, filter_mode, min_c, max_c, min_s, max_s, include_unplayed, user_vector, current_b50, b50_bottom, b50_dict):
    features = ['4k', 'Keyboard', 'Jacks', 'Xhanding', 'Trill', 'Rolls', 'Stamina', 'USAO', 'Cyaegha', 'Small Notes', 'Tap Slides', 'Anchor Hold', 'Split Trill', 'Gimmick', 'Tateren', 'Train']
    df_master = df_master.copy()
    df_master.columns = df_master.columns.str.strip()
    for feat in features:
        if feat in df_master.columns:
            df_master[feat] = df_master[feat].apply(lambda x: 1.0 if str(x).strip().upper() in ['TRUE', '1', '1.0', 'YES'] else 0.0)
        else:
            df_master[feat] = 0.0 
    df_master['Match_Key'] = df_master['Title'].astype(str).str.lower().str.replace(' ', '').str.replace('　', '').str.strip()
    df_master['master_idx'] = range(len(df_master))

    upscore_pool = pd.merge(df_player, df_master, left_on='match_key', right_on='Match_Key', how='inner')
    p_const_col = 'level' if 'level' in upscore_pool.columns else ('const' if 'const' in upscore_pool.columns else None)
    if p_const_col:
        upscore_pool = upscore_pool[abs(upscore_pool[p_const_col].astype(float) - upscore_pool['constant'].astype(float)) < 0.2]

    played_master_indices = set(upscore_pool['master_idx'])
    upscore_pool['Status'] = upscore_pool['score'].apply(lambda x: f"PUSH (from {get_rank_name(x)})")

    if include_unplayed:
        new_pool = df_master[~df_master['master_idx'].isin(played_master_indices)].copy()
        new_pool['Status'] = "NEW"
        new_pool['score'] = 0 
        combined_pool = pd.concat([upscore_pool, new_pool], ignore_index=True)
    else:
        combined_pool = upscore_pool.copy()

    if target_mode == "Target Rating":
        combined_pool['Req_Score'] = combined_pool.apply(lambda x: get_required_score(target_val, x['constant']), axis=1)
    else:
        combined_pool['Req_Score'] = int(target_val)

    combined_pool['Achieved_Rating'] = combined_pool.apply(lambda x: calculate_rating(x['Req_Score'], x['constant']), axis=1)
    
    def calc_b50_metrics(row):
        ukey = f"{row['Match_Key']}_{float(row['constant']):.1f}"
        replace_rating = b50_dict.get(ukey, b50_bottom)
        jump = (row['Achieved_Rating'] - replace_rating) / 50.0
        new_b50_val = current_b50 + max(0.0, jump)
        return pd.Series([max(0.0, jump), new_b50_val])

    combined_pool[['Rating_Jump', 'B50_After']] = combined_pool.apply(calc_b50_metrics, axis=1)
    
    pool = combined_pool[
        (combined_pool['Req_Score'] <= 1010000) & 
        (combined_pool['Req_Score'] > combined_pool['score']) &
        (combined_pool['Rating_Jump'] > 0)
    ].copy()

    if filter_mode in ["Constant Range", "Both"]:
        pool = pool[(pool['constant'] >= min_c) & (pool['constant'] <= max_c)]
    if filter_mode in ["Score Range", "Both"]:
        pool = pool[(pool['Req_Score'] >= min_s) & (pool['Req_Score'] <= max_s)]

    if pool.empty: return "No matching charts found."

    knn = NearestNeighbors(n_neighbors=min(len(pool), 50), metric='cosine')
    knn.fit(pool[features].fillna(0).astype(float)) 
    distances, indices = knn.kneighbors(user_vector)
    
    results = pool.iloc[indices[0]].copy()
    results['Match'] = 1 - distances[0]
    results = results.drop_duplicates(subset=['master_idx']).sort_values(by=['Match', 'constant'], ascending=[False, True])
    return results

# --- GUI ---
class ChunithmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOUNIQ")
        self.root.geometry("1100x800")
        
        try:
            # This set the small icon in the window title bar and taskbar
            self.root.iconbitmap("youniq.ico") 
        except Exception as e:
            print(f"Icon Error: {e}")
        
        self.df_master = None
        self.df_player = None 
        self.user_vector = None
        self.current_b50 = 0.0
        self.b50_bottom = 0.0
        self.b50_dict = {}

        self.build_ui()
        self.autoload_master()

    def build_ui(self):
        self.drop_label = ttk.Label(self.root, text="DRAG PLAYER_DATA.CSV HERE", background="#2c3e50", foreground="white", anchor="center", padding=15)
        self.drop_label.pack(fill=tk.X, padx=20, pady=10)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)

        rating_frame = ttk.LabelFrame(self.root, text=" Player Rating Analysis ", padding=10)
        rating_frame.pack(fill=tk.X, padx=20, pady=5)
        self.rating_text = tk.StringVar(value="Current B50 Rating: --.---- | Bottom B50: --.----")
        ttk.Label(rating_frame, textvariable=self.rating_text, font=("Arial", 14, "bold"), foreground="#2980b9").pack()

        param_frame = ttk.LabelFrame(self.root, text=" Target Parameters ", padding=10)
        param_frame.pack(fill=tk.X, padx=20, pady=10)

        self.target_mode = ttk.Combobox(param_frame, values=["Target Rating", "Target Score"], width=13, state="readonly")
        self.target_mode.set("Target Rating")
        self.target_mode.grid(row=0, column=0, padx=5)
        self.target_mode.bind("<<ComboboxSelected>>", self.on_mode_change)

        self.target_val_entry = ttk.Entry(param_frame, width=12)
        self.target_val_entry.insert(0, "17.6") 
        self.target_val_entry.grid(row=0, column=1, padx=5)

        ttk.Label(param_frame, text="Filter Mode:").grid(row=0, column=2, padx=10)
        self.filter_mode = ttk.Combobox(param_frame, values=["Constant Range", "Score Range", "Both"], width=13, state="readonly")
        self.filter_mode.set("Both")
        self.filter_mode.grid(row=0, column=3, padx=5)
        self.filter_mode.bind("<<ComboboxSelected>>", self.toggle_inputs)

        ttk.Label(param_frame, text="Min Const:").grid(row=1, column=0, pady=10)
        self.min_c_entry = ttk.Entry(param_frame, width=12); self.min_c_entry.insert(0, "15.0"); self.min_c_entry.grid(row=1, column=1)

        ttk.Label(param_frame, text="Max Const:").grid(row=1, column=2)
        self.max_c_entry = ttk.Entry(param_frame, width=12); self.max_c_entry.insert(0, "16.0"); self.max_c_entry.grid(row=1, column=3)

        ttk.Label(param_frame, text="Min Score:").grid(row=2, column=0, pady=5)
        self.min_s_entry = ttk.Entry(param_frame, width=12); self.min_s_entry.insert(0, "1000000"); self.min_s_entry.grid(row=2, column=1)

        ttk.Label(param_frame, text="Max Score:").grid(row=2, column=2)
        self.max_s_entry = ttk.Entry(param_frame, width=12); self.max_s_entry.insert(0, "1009000"); self.max_s_entry.grid(row=2, column=3)

        self.unplayed_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(param_frame, text="Include Unplayed", variable=self.unplayed_var).grid(row=1, column=4, padx=15)
        
        ttk.Button(param_frame, text="Recommend Charts", command=self.run_model).grid(row=2, column=5, padx=5)

        self.tree = ttk.Treeview(self.root, columns=("T", "C", "RS", "NR", "RJ", "BA", "M", "S"), show="headings")
        for col, head, w in zip(("T", "C", "RS", "NR", "RJ", "BA", "M", "S"), 
                                ("Song Title", "Const", "Req Score", "Achieved Rating", "Jump", "B50 After", "Match %", "Status"), 
                                (240, 50, 90, 100, 80, 90, 80, 160)):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor=tk.W if col=="T" else tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.toggle_inputs()

    def on_mode_change(self, event=None):
        if self.target_mode.get() == "Target Score":
            # Auto-restrict to Constant Range only
            self.filter_mode.set("Constant Range")
            self.filter_mode.config(state="disabled") # Lock the dropdown
            self.target_val_entry.delete(0, tk.END)
            self.target_val_entry.insert(0, "1007500")
        else:
            # Unlock and allow all modes
            self.filter_mode.config(state="readonly")
            self.filter_mode.set("Both")
            self.target_val_entry.delete(0, tk.END)
            self.target_val_entry.insert(0, "17.6")
        self.toggle_inputs()

    def toggle_inputs(self, event=None):
        mode = self.filter_mode.get()
        state_c = "normal" if mode in ["Constant Range", "Both"] else "disabled"
        state_s = "normal" if mode in ["Score Range", "Both"] else "disabled"
        self.min_c_entry.config(state=state_c); self.max_c_entry.config(state=state_c)
        self.min_s_entry.config(state=state_s); self.max_s_entry.config(state=state_s)

    def autoload_master(self):
        if os.path.exists('master.csv'):
            self.df_master = pd.read_csv('master.csv')
            self.drop_label.config(text="MASTER LOADED - READY FOR PLAYER DATA", background="#2980b9")

    def handle_drop(self, event):
        path = event.data.strip('{}')
        try:
            df = pd.read_csv(path)
            df.columns = df.columns.str.lower().str.strip()
            df['match_key'] = df['title'].astype(str).str.lower().str.replace(' ', '').str.replace('　', '').str.strip()
            const_col = 'level' if 'level' in df.columns else 'const'
            df['unique_key'] = df['match_key'] + "_" + df[const_col].astype(float).round(1).astype(str)
            top50 = df.sort_values('rating', ascending=False).head(50)
            self.current_b50 = top50['rating'].mean()
            self.b50_bottom = top50['rating'].min() if len(top50) == 50 else 0.0
            self.b50_dict = dict(zip(top50['unique_key'], top50['rating']))
            self.df_player = df
            self.rating_text.set(f"Current B50 Rating: {self.current_b50:.4f} | Lowest: {self.b50_bottom:.4f}")
            self.drop_label.config(text=f"LOADED: {os.path.basename(path)}", background="#27ae60")
            played_master = self.df_master[self.df_master['Title'].str.lower().str.replace(' ','').isin(df['match_key'])]
            features = ['4k', 'Keyboard', 'Jacks', 'Xhanding', 'Trill', 'Rolls', 'Stamina', 'USAO', 'Cyaegha', 'Small Notes', 'Tap Slides', 'Anchor Hold', 'Split Trill', 'Gimmick', 'Tateren', 'Train']
            self.user_vector = pd.DataFrame(played_master[features].mean().values.reshape(1,-1), columns=features)
        except Exception as e:
            messagebox.showerror("Error", f"CSV Error: {e}")

    def run_model(self):
        if self.df_player is None: return messagebox.showwarning("Warning", "Load player_data.csv!")
        for i in self.tree.get_children(): self.tree.delete(i)
        def sf(e):
            try: return float(e.get().replace(',', ''))
            except: return 0.0
        res = get_recommendations(
            self.df_master, self.df_player, self.target_mode.get(), sf(self.target_val_entry),
            self.filter_mode.get(), sf(self.min_c_entry), sf(self.max_c_entry), 
            sf(self.min_s_entry), sf(self.max_s_entry), self.unplayed_var.get(), self.user_vector,
            self.current_b50, self.b50_bottom, self.b50_dict
        )
        if isinstance(res, str): self.tree.insert("", tk.END, values=(res, "", "", "", "", "", "", ""))
        else:
            for _, r in res.iterrows():
                self.tree.insert("", tk.END, values=(
                    r['Title'], r['constant'], f"{int(r['Req_Score']):,}", 
                    f"{r['Achieved_Rating']:.4f}", f"+{r['Rating_Jump']:.4f}", f"{r['B50_After']:.4f}", 
                    f"{r['Match'] * 100:.2f}%", r['Status']
                ))

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ChunithmApp(root)
    root.mainloop()
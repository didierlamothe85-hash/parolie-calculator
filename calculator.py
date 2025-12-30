# -*- coding: utf-8 -*-
"""
Calculatrice v3.9.2 — PRO
NOUVELLES MODIFICATIONS v3.9.2-PRO-FINAL :
- ✅ Bouton S ajouté dans l'historique (avant EXP)
- ✅ Moyennes temps et impact sur les en-têtes de jour
- ✅ Taille de la corbeille réduite (12pt → 10pt)
- ✅ Fix "Oui" pour démarrer nouvelle session immédiatement
- ✅ Hauteur fenêtre historique bloquée (= hauteur calculatrice complète)
- ✅ Affichage OBJ en temps réel avant de cliquer sur GO
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json, os, time, math
from copy import deepcopy
from datetime import datetime, timedelta
from collections import defaultdict

APP_VERSION = "3.9.2-PRO-FINAL"

# =================== CONSTANTES UI ===================
WIN_W = 246
PAD_OUT_X = 4
PAD_OUT_TOP = 7
PAD_OUT_BETWEEN = 4
DISP_H = 104
DISP_BD = 2
CELL_W = 56
CELL_H = 48
GAP = 2
BOTTOM_MARGIN = 3
SHELL_W = WIN_W - 2 * PAD_OUT_X

DARK_BG = "#1E1E1E"
DISPLAY_BG = "#000000"
DISPLAY_FG = "#FFFFFF"
BTN_BG = "#2D2D2D"
BTN_FG = "#FFFFFF"

ACCENT_BLUE = "#0078D7"
ACCENT_RED = "#C0392B"
ACCENT_GREEN = "#28A745"
ACCENT_GREY = "#3A3A3A"
ACCENT_GREY_H = "#5a5a5a"
ACCENT_EQUAL = "#00A2FF"
LINE_GREY = "#444444"
OK_GREEN = "#20c997"
WAIT_RED = "#ff5c5c"
WIN_YELLOW = "#FFD54A"
VIOLET_UNLOCK = "#8A2BE2"
RESET_BG = "#444444"
RESET_BG_H = "#666666"
IMPACT_RED = "#ff5c5c"

DATA_PATH = os.path.join(os.path.dirname(__file__), "calc_stats_data.json")

OBJ_PCT_MIN = 0.1
OBJ_PCT_MAX = 10.0
OBJ_PCT_STEP = 0.1

EXPORT_W = 120

# =================== DIMENSIONS FENÊTRE HISTORIQUE ===================
HISTORY_WINDOW_WIDTH = 409    # Largeur fixée
HISTORY_WINDOW_HEIGHT = 439   # Hauteur fixée
# ======================================================================

def ceil_0_1(x):
    return 0.0 if x <= 0 else math.ceil(x * 10) / 10.0

def spacer_size():
    avail = SHELL_W - 4 * CELL_W
    return max(0, int(round(avail / 5.0)))

def centered_row(parent):
    row = tk.Frame(parent, bg=DARK_BG, width=SHELL_W, height=CELL_H)
    row.pack_propagate(False)
    SP = spacer_size()
    for c in range(9):
        row.grid_columnconfigure(c, minsize=(SP if c % 2 == 0 else CELL_W))
    row.grid_rowconfigure(0, minsize=CELL_H)
    return row

def add4(row, widgets):
    for i, w in enumerate(widgets):
        w.grid(row=0, column=1 + 2 * i, sticky="nsew")

def fmt_time(seconds):
    seconds = int(round(max(0, seconds)))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0:
        return f"{h}h{m:02d}"
    else:
        return f"{m}min"

def fmt_dt(ts):
    try:
        dt = datetime.fromtimestamp(ts)
        if dt.second >= 30:
            dt = datetime.fromtimestamp(ts + 60)
        return dt.strftime("%d/%m/%y %H:%M")
    except Exception:
        return "(date inconnue)"

def fmt_time_only(ts):
    """Retourne uniquement l'heure au format HH:MM"""
    try:
        dt = datetime.fromtimestamp(ts)
        if dt.second >= 30:
            dt = datetime.fromtimestamp(ts + 60)
        return dt.strftime("%H:%M")
    except Exception:
        return "??:??"


# =================== FENETRE HISTORIQUE INTERACTIVE ===================
class HistoryWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Historique des sessions")
        self.configure(bg=DARK_BG)
        self.resizable(False, True)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        # MODIFICATION 5 : Dimensions fixes (409x439)
        self.resizable(False, False)  # VERROUILLÉ
        
        w = HISTORY_WINDOW_WIDTH   # Taille initiale
        h = HISTORY_WINDOW_HEIGHT  # Taille initiale
        x = max(0, app.winfo_x() - w // 2)
        y = app.winfo_y()
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Header avec titre + boutons EXP, LC et EFFACER - ALIGNÉS PAR PADDING FIXE
        header = tk.Frame(self, bg=DARK_BG)
        header.pack(side="top", fill="x", padx=6, pady=(6, 3))
        
        tk.Label(header, text="📊 Historique des sessions", bg=DARK_BG, fg="#CCCC66",
                font=("Segoe UI", 11, "bold")).pack(side="left")
        
        # Frame pour les 3 boutons côte à côte
        buttons_group = tk.Frame(header, bg=DARK_BG)
        buttons_group.pack(side="right", padx=0)
        
        btn_delete_all = tk.Button(buttons_group, text="EFFACER", bg="#aa3333", fg="#fff",
                                   bd=1, relief="raised", font=("Segoe UI", 8, "bold"),
                                   activebackground="#cc4444", activeforeground="#fff",
                                   cursor="hand2", command=self.delete_all_sessions,
                                   width=7)
        btn_delete_all.pack(side="right", padx=0)
        
        btn_lc = tk.Button(buttons_group, text="LC", bg="#555", fg="#fff",
                          bd=1, relief="raised", font=("Segoe UI", 8, "bold"),
                          activebackground="#777", activeforeground="#fff",
                          cursor="hand2", command=self.open_casino_list,
                          width=3)
        btn_lc.pack(side="right", padx=(0, 2))
        
        btn_export = tk.Button(buttons_group, text="EXP", bg="#555", fg="#fff",
                              bd=1, relief="raised", font=("Segoe UI", 8, "bold"),
                              activebackground="#777", activeforeground="#fff",
                              cursor="hand2", command=self.export_text,
                              width=3)
        btn_export.pack(side="right", padx=(0, 2))
        
        # MODIFICATION 1 : Ajout du bouton S (Stats)
        btn_stats = tk.Button(buttons_group, text="S", bg="#555", fg="#fff",
                             bd=1, relief="raised", font=("Segoe UI", 8, "bold"),
                             activebackground="#777", activeforeground="#fff",
                             cursor="hand2", command=self.open_stats, width=2)
        btn_stats.pack(side="right", padx=(0, 2))

        # Ligne de filtres - ULTRA COMPACT
        filter_frame = tk.Frame(self, bg=DARK_BG, bd=1, relief="solid")
        filter_frame.pack(side="top", fill="x", padx=6, pady=(2, 6))
        
        tk.Label(filter_frame, text="Filtre:", bg=DARK_BG, fg="#aaa",
                font=("Segoe UI", 8)).pack(side="left", padx=(4, 2), pady=3)
        
        self.filter_var = tk.StringVar(value="Tous les casinos")
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                        state='readonly', width=13, font=("Segoe UI", 8))
        self.filter_combo.pack(side="left", padx=1)
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())
        
        tk.Label(filter_frame, text="📅", bg=DARK_BG, fg="#aaa",
                font=("Segoe UI", 8)).pack(side="left", padx=(4, 1))
        
        self.period_var = tk.StringVar(value="Toutes les périodes")
        self.period_combo = ttk.Combobox(filter_frame, textvariable=self.period_var,
                                        state='readonly', width=13, font=("Segoe UI", 8))
        self.period_combo['values'] = ["Toutes les périodes", "Derniers 7 jours", 
                                        "Derniers 30 jours", "Derniers 90 jours"]
        self.period_combo.pack(side="left", padx=1)
        self.period_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())
        
        tk.Label(filter_frame, text="🔍", bg=DARK_BG, fg="#aaa",
                font=("Segoe UI", 8)).pack(side="left", padx=(4, 1))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.refresh_list())
        search_entry = tk.Entry(filter_frame, textvariable=self.search_var,
                               bg="#2A2A2A", fg="#fff", insertbackground="#fff",
                               bd=1, relief="sunken", font=("Segoe UI", 8), width=10)
        search_entry.pack(side="left", padx=1)

        # Zone scrollable
        self.canvas = tk.Canvas(self, bg=DARK_BG, highlightthickness=0, bd=0)
        self.vs = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=DARK_BG)
        
        self.scroll_frame.bind("<Configure>", 
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vs.set)
        
        self.canvas.pack(side="left", fill="both", expand=True, padx=6, pady=(0, 6))
        self.vs.pack(side="right", fill="y", pady=(0, 6))

        def _on_wheel(event):
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        self.canvas.bind_all("<MouseWheel>", _on_wheel)

        # État des jours repliés/dépliés (par défaut tout replié)
        self.day_expanded = {}  # {jour: True/False}

        # Afficher les dimensions dans la console
        self._last_size = (0, 0)
        
        def _on_configure_with_display(event=None):
            self._on_window_configure(event)
            # Afficher seulement si la taille a changé
            w = self.winfo_width()
            h = self.winfo_height()
            if (w, h) != self._last_size and w > 1 and h > 1:
                self._last_size = (w, h)
                print(f"📐 DIMENSIONS HISTORIQUE : Largeur={w} | Hauteur={h}")
        
        self.bind("<Configure>", _on_configure_with_display)

        self.refresh_list()
        self.update_filter_combo()

    def _on_window_configure(self, event=None):
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

    def open_casino_list(self):
        """Ouvre la fenêtre de liste des casinos"""
        CasinoListWindow(self.app)

    def open_stats(self):
        """Ouvre la fenêtre des statistiques"""
        self.app.open_stats()

    def update_filter_combo(self):
        """Met à jour la liste des casinos dans le filtre"""
        casino_names = ["Tous les casinos"] + [c['name'] for c in self.app.casinos if c['name'].strip()]
        self.filter_combo['values'] = casino_names


    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Filtres actifs
        filter_casino = self.filter_var.get()
        filter_period = self.period_var.get()
        search_text = self.search_var.get().strip().lower()
        
        # Calcul de la période
        now = time.time()
        period_cutoff = None
        if filter_period == "Derniers 7 jours":
            period_cutoff = now - (7 * 24 * 3600)
        elif filter_period == "Derniers 30 jours":
            period_cutoff = now - (30 * 24 * 3600)
        elif filter_period == "Derniers 90 jours":
            period_cutoff = now - (90 * 24 * 3600)

        # Collecter les sessions avec filtres
        all_sessions = []
        for idx, casino in enumerate(self.app.casinos):
            cname = casino.get("name", "").strip() or f"casino {idx+1}"
            
            # Filtre casino
            if filter_casino != "Tous les casinos" and cname != filter_casino:
                continue
            
            for sess_idx, s in enumerate(casino.get("sessions", [])):
                ts = s.get("start_ts") or s.get("end_ts") or 0
                
                # Filtre période
                if period_cutoff and ts < period_cutoff:
                    continue
                
                # Filtre recherche
                if search_text and search_text not in cname.lower():
                    continue
                
                day = datetime.fromtimestamp(ts).strftime("%d/%m/%y") if ts else "(jour inconnu)"
                all_sessions.append({'casino_idx': idx, 'session_idx': sess_idx,
                    'casino_name': cname, 'session': s, 'day': day, 'timestamp': ts})

        all_sessions.sort(key=lambda x: x['timestamp'], reverse=True)

        if not all_sessions:
            tk.Label(self.scroll_frame, text="(aucune session trouvée)", 
                    bg=DARK_BG, fg="#888", font=("Segoe UI", 12)).pack(pady=20)
            return

        by_day = defaultdict(list)
        for item in all_sessions:
            by_day[item['day']].append(item)

        days_seen = []
        for item in all_sessions:
            if item['day'] not in days_seen:
                days_seen.append(item['day'])

        for day_idx, day in enumerate(days_seen):
            if day_idx > 0:
                sep = tk.Frame(self.scroll_frame, bg=LINE_GREY, height=2)
                sep.pack(fill="x", pady=(6, 6))  # Réduit encore

            # MODIFICATION 2 : Moyennes sur en-tête de jour
            day_sessions = by_day[day]
            total_duration = sum(s['session'].get('duration', 0) for s in day_sessions)
            total_impact = sum(s['session'].get('impact_pct', 0.0) for s in day_sessions)
            avg_duration = total_duration / len(day_sessions) if day_sessions else 0
            avg_impact = total_impact / len(day_sessions) if day_sessions else 0.0
            
            # Par défaut, les jours sont repliés
            if day not in self.day_expanded:
                self.day_expanded[day] = False
            
            is_expanded = self.day_expanded[day]
            arrow = "▼" if is_expanded else "▶"
            
            day_header = tk.Frame(self.scroll_frame, bg="#2A2A2A", bd=1, relief="raised", cursor="hand2")
            day_header.pack(fill="x", pady=(0, 2))
            
            # Frame interne pour gérer l'alignement
            inner_frame = tk.Frame(day_header, bg="#2A2A2A")
            inner_frame.pack(fill="x", padx=6, pady=3)
            
            # Flèche cliquable à gauche
            arrow_label = tk.Label(inner_frame, text=arrow, bg="#2A2A2A", fg=WIN_YELLOW,
                                   font=("Segoe UI", 12, "bold"), cursor="hand2")
            arrow_label.pack(side="left", padx=(0, 8))
            
            # Texte de l'en-tête
            header_text = f"Jour {day}  —  Moy: {fmt_time(avg_duration)} | Impact: {avg_impact:.1f}%"
            header_label = tk.Label(inner_frame, text=header_text, bg="#2A2A2A", fg=WIN_YELLOW,
                                   font=("Segoe UI", 10, "bold"), cursor="hand2")
            header_label.pack(side="left", anchor="w")
            
            # Corbeille pour supprimer tout le jour - alignée à droite
            trash_day_label = tk.Label(inner_frame, text="🗑️", bg="#2A2A2A", fg="#fff",
                                      font=("Segoe UI", 10), cursor="hand2")
            trash_day_label.pack(side="right", padx=(3, 0))
            trash_day_label.bind("<Button-1>", lambda e, d=day: self.delete_day(d))
            
            # Fonction pour basculer l'état
            def toggle_day(d=day):
                self.day_expanded[d] = not self.day_expanded[d]
                self.refresh_list()
            
            # Rendre tout le header cliquable (sauf la corbeille)
            day_header.bind("<Button-1>", lambda e, d=day: toggle_day(d))
            arrow_label.bind("<Button-1>", lambda e, d=day: toggle_day(d))
            header_label.bind("<Button-1>", lambda e, d=day: toggle_day(d))

            # Afficher les sessions seulement si le jour est déplié
            if is_expanded:
                for item in by_day[day]:
                    self._create_session_row(item)

    def _create_session_row(self, item):
        s = item['session']
        cname = item['casino_name']
        
        row_frame = tk.Frame(self.scroll_frame, bg="#252525", bd=1, relief="solid")
        row_frame.pack(fill="x", pady=1, padx=2)  # pady réduit de 2 à 1

        start = fmt_time_only(s.get("start_ts"))
        end = fmt_time_only(s.get("end_ts"))
        dur = fmt_time(s.get("duration", 0))
        impact = s.get('impact_pct', 0.0)
        profit = s.get('profit', 0.0)
        impacts_detail = s.get('impacts_detail', [0.0, 0.0, 0.0])
        num_mode = s.get('num_mode', 18)  # Par défaut 18N si pas enregistré

        main_row = tk.Frame(row_frame, bg="#252525")
        main_row.pack(fill="x", padx=3, pady=2)

        # Casino - compact
        tk.Label(main_row, text=cname[:14], bg="#252525", fg=WIN_YELLOW,
                font=("Segoe UI", 9, "bold"), width=12, anchor="w").pack(side="left", padx=(0, 2))

        # Début
        tk.Label(main_row, text=start, bg="#252525", fg="#ddd",
                font=("Segoe UI", 9), width=5, anchor="center").pack(side="left", padx=1)

        # Fin
        tk.Label(main_row, text=end, bg="#252525", fg="#ddd",
                font=("Segoe UI", 9), width=5, anchor="center").pack(side="left", padx=1)

        # Durée
        tk.Label(main_row, text=dur, bg="#252525", fg="#ddd",
                font=("Segoe UI", 9), width=6, anchor="center").pack(side="left", padx=1)

        # Impact
        tk.Label(main_row, text=f"{impact:.1f}%", bg="#252525", fg=IMPACT_RED,
                font=("Segoe UI", 9, "bold"), width=6, anchor="center").pack(side="left", padx=1)

        # Profit - compact
        tk.Label(main_row, text=f"{profit:.1f} $", bg="#252525", fg=OK_GREEN,
                font=("Segoe UI", 9, "bold"), width=7, anchor="center").pack(side="left", padx=1)

        # Mode (18N ou 24N) - en jaune comme le casino
        tk.Label(main_row, text=f"{num_mode}N", bg="#252525", fg=WIN_YELLOW,
                font=("Segoe UI", 9, "bold"), width=4, anchor="center").pack(side="left", padx=1)

        # Corbeille - collée au mode
        trash_label = tk.Label(main_row, text="🗑️", bg="#252525", fg="#fff",
                              font=("Segoe UI", 10), cursor="hand2")  # MODIFICATION 3: Réduit
        trash_label.pack(side="left", padx=(3, 0))  # 3px à gauche, 0px à droite
        trash_label.bind("<Button-1>", lambda e: self.delete_session(item))

        # Ligne(s) détails sessions - 3 par ligne avec alignement en colonnes
        impacts_detail = s.get('impacts_detail', [0.0, 0.0, 0.0])
        num_sessions = len(impacts_detail)
        
        # Afficher par groupes de 3 avec grid pour alignement parfait
        for row_idx in range((num_sessions + 2) // 3):  # Nombre de lignes nécessaires
            detail_row = tk.Frame(row_frame, bg="#252525")
            detail_row.pack(fill="x", padx=6, pady=(0, 4 if row_idx == (num_sessions + 2) // 3 - 1 else 2))
            
            # Préfixe "└─"
            tk.Label(detail_row, text="  └─ ", bg="#252525", fg="#888",
                    font=("Segoe UI", 9)).pack(side="left")
            
            # Frame pour les 3 colonnes avec grid
            grid_frame = tk.Frame(detail_row, bg="#252525")
            grid_frame.pack(side="left")
            
            # Calculer la largeur de référence basée sur "S10 -10.9%" (le plus large possible)
            # S10 (3 car) + espace réduit + "-10.9%" (6 car) = environ 9 caractères
            # On utilise minsize pour forcer une largeur minimale par colonne
            col_width = 70  # Largeur en pixels basée sur "S10 -10.9%"
            
            for col in range(3):
                grid_frame.grid_columnconfigure(col, minsize=col_width)
            
            # Afficher 3 sessions max par ligne
            start_idx = row_idx * 3
            end_idx = min(start_idx + 3, num_sessions)
            
            for col_idx, i in enumerate(range(start_idx, end_idx)):
                # Frame pour chaque session (label + impact)
                session_frame = tk.Frame(grid_frame, bg="#252525")
                session_frame.grid(row=0, column=col_idx, sticky="w", padx=(0, 10))  # Espacement entre colonnes
                
                # Label session (S1, S2, etc.)
                tk.Label(session_frame, text=f"S{i+1}", bg="#252525", fg=ACCENT_BLUE,
                        font=("Segoe UI", 9, "bold")).pack(side="left")
                
                # Espace réduit entre label et pourcentage (2 espaces au lieu de 4-5)
                tk.Label(session_frame, text="  ", bg="#252525",
                        font=("Segoe UI", 9)).pack(side="left")
                
                # Pourcentage
                tk.Label(session_frame, text=f"{impacts_detail[i]:.1f}%", bg="#252525", fg="#aaa",
                        font=("Segoe UI", 9)).pack(side="left")

    def delete_session(self, item):
        s = item['session']
        cname = item['casino_name']
        
        msg = (f"Casino: {cname}\n" f"Date: {fmt_dt(s.get('start_ts'))}\n"
               f"Profit: {s.get('profit', 0.0):.1f} $\n" f"Impact: {s.get('impact_pct', 0.0):.1f}%\n\n"
               f"⚠️ Cette action est irréversible !\n" f"Les statistiques seront recalculées.")
        
        if messagebox.askyesno("Supprimer cette session ?", msg):
            casino_idx = item['casino_idx']
            session_idx = item['session_idx']
            del self.app.casinos[casino_idx]['sessions'][session_idx]
            
            self.app.save_data()
            self.refresh_list()
            
            if getattr(self.app, 'stats_win', None) and self.app.stats_win.winfo_exists():
                self.app.stats_win.update_stats_ui()
            
            messagebox.showinfo("✅ Session supprimée", 
                              "Les statistiques ont été recalculées automatiquement.")

    def delete_day(self, day):
        """Supprime toutes les sessions d'un jour donné"""
        # Collecter toutes les sessions de ce jour
        sessions_to_delete = []
        for idx, casino in enumerate(self.app.casinos):
            for s_idx, s in enumerate(casino['sessions']):
                session_day = datetime.fromtimestamp(s.get('start_ts', 0)).strftime('%d-%m-%y')
                if session_day == day:
                    sessions_to_delete.append((idx, s_idx))
        
        if not sessions_to_delete:
            return
        
        count = len(sessions_to_delete)
        msg = f"⚠️ ATTENTION ⚠️\n\nVous allez supprimer {count} session(s) du jour {day}.\n\nCette action est IRRÉVERSIBLE !\n\nÊtes-vous sûr ?"
        
        if messagebox.askyesno("Supprimer tout le jour ?", msg):
            # Supprimer en ordre inverse pour ne pas décaler les indices
            for casino_idx, session_idx in sorted(sessions_to_delete, reverse=True):
                del self.app.casinos[casino_idx]['sessions'][session_idx]
            
            self.app.save_data()
            self.refresh_list()
            
            if getattr(self.app, 'stats_win', None) and self.app.stats_win.winfo_exists():
                self.app.stats_win.update_stats_ui()
            
            messagebox.showinfo("✅ Jour supprimé", 
                              f"{count} session(s) supprimée(s). Les statistiques ont été recalculées.")


    def delete_all_sessions(self):
        """Supprime toutes les sessions après confirmation"""
        total = sum(len(c['sessions']) for c in self.app.casinos)
        
        if total == 0:
            messagebox.showinfo("Info", "Aucune session à supprimer.")
            return
        
        msg = f"⚠️ ATTENTION ⚠️\n\nVous allez supprimer {total} session(s).\n\nCette action est IRRÉVERSIBLE !\n\nÊtes-vous sûr ?"
        
        if messagebox.askyesno("Tout effacer ?", msg):
            for c in self.app.casinos:
                c['sessions'].clear()
            
            self.app.save_data()
            self.refresh_list()
            
            if getattr(self.app, 'stats_win', None) and self.app.stats_win.winfo_exists():
                self.app.stats_win.update_stats_ui()
            
            messagebox.showinfo("✅ Toutes les sessions supprimées", 
                              "Toutes les données ont été effacées.")

    def export_text(self):
        self.app.open_export_direct()


# Le reste du code (StatsWindow, CasinoListWindow, Calculator) reste identique
# SAUF les modifications suivantes dans Calculator.__init__ :



# =================== FENETRE STATS ===================
class StatsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Statistiques")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        # Ajuster la taille à juste le contenu (Total casino uniquement)
        w = app.winfo_width()
        h = 200  # Hauteur réduite (juste pour le tableau stats)
        x = max(0, app.winfo_x() - w - 10)
        y = app.winfo_y()
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Frame principal avec stats
        head = tk.Frame(self, bg=DARK_BG, bd=2, relief="groove")
        head.pack(side="top", fill="both", expand=True, padx=PAD_OUT_X, pady=PAD_OUT_TOP)
        
        title_row = tk.Frame(head, bg=DARK_BG)
        title_row.pack(fill="x", padx=6, pady=(6, 0))
        tk.Label(title_row, text="📊 Total des casinos", fg="#CCCC66", bg=DARK_BG, 
                font=("Segoe UI", 10, "bold")).pack(side="left")

        self.total_body = tk.Frame(head, bg=DARK_BG)
        self.total_body.pack(fill="x", padx=6, pady=(2, 6))
        for c in range(2):
            self.total_body.grid_columnconfigure(c, weight=(1 if c == 0 else 0))

        self.t_avg_lbl_v = tk.Label(self.total_body, fg="#ddd", bg=DARK_BG, 
                                    font=("Segoe UI", 9), anchor="e", width=10)
        self.t_imp_lbl_v = tk.Label(self.total_body, fg="#ddd", bg=DARK_BG, 
                                    font=("Segoe UI", 9), anchor="e", width=10)
        self.t_minmax_lbl_v = tk.Label(self.total_body, fg="#ddd", bg=DARK_BG, 
                                       font=("Segoe UI", 9), anchor="e", width=12)
        self.t_hour_lbl_v = tk.Label(self.total_body, fg="#ddd", bg=DARK_BG, 
                                     font=("Segoe UI", 9), anchor="e", width=10)

        self._mk_row(self.total_body, 0, "temps moyen / session", self.t_avg_lbl_v)
        self._mk_row(self.total_body, 1, "moy impact bankroll %", self.t_imp_lbl_v)
        self._mk_row(self.total_body, 2, "moy impact bankroll % m/M", self.t_minmax_lbl_v)
        self._mk_row(self.total_body, 3, "moy gain à l'heure  $/H", self.t_hour_lbl_v)

        # PLUS DE BOUTONS (LISTE, HISTORIQUE, RESET supprimés)

        self.update_stats_ui()

    def _mk_row(self, parent, r, left_text, right_label):
        l = tk.Label(parent, text=left_text, fg="#aaa", bg=DARK_BG, font=("Segoe UI", 9))
        l.grid(row=r, column=0, sticky="w", padx=(0, 6), pady=1)
        right_label.grid(row=r, column=1, sticky="e", pady=1)

    def update_stats_ui(self):
        tot = self.app.compute_total_stats()
        self.t_avg_lbl_v.config(text=fmt_time(tot['avg_time']))
        self.t_imp_lbl_v.config(text=f"{tot['avg_impact']:.1f}%")
        self.t_minmax_lbl_v.config(text=f"{tot['max_impact']:.1f}%/{tot['min_impact']:.1f}%")
        self.t_hour_lbl_v.config(text=f"{tot['avg_gain_per_hour']:.2f}")


# =================== FENETRE LISTE DES CASINOS ===================
class CasinoListWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
        self.title("Liste des casinos")
        self.configure(bg=DARK_BG)
        self.resizable(False, True)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        w = 225
        h = app.winfo_height()
        x = app.winfo_x() + (app.winfo_width() - w) // 2
        y = app.winfo_y()
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.canvas = tk.Canvas(self, bg=DARK_BG, highlightthickness=0, bd=0)
        self.vs = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll = tk.Frame(self.canvas, bg=DARK_BG)
        self.scroll.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vs.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=PAD_OUT_X, pady=PAD_OUT_TOP)
        self.vs.pack(side="right", fill="y", pady=PAD_OUT_TOP)

        def _on_wheel(event):
            delta = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(delta, "units")
        self.canvas.bind_all("<MouseWheel>", _on_wheel)

        self.rows = []
        for idx in range(200):
            self._make_casino_block(idx)

    def _make_casino_block(self, idx: int):
        fr = tk.Frame(self.scroll, bg=DARK_BG, bd=1, relief="solid")
        fr.pack(fill="x", padx=2, pady=2)

        title = tk.Frame(fr, bg=DARK_BG)
        title.pack(fill="x", padx=4, pady=4)
        tk.Label(title, text=f"Casino {idx+1}", fg="#CCCC66", bg=DARK_BG, 
                font=("Segoe UI", 9, "bold"), width=8).pack(side="left")

        name_var = tk.StringVar(value=self.app.casinos[idx]['name'])
        ent = tk.Entry(title, textvariable=name_var, bg="#222", fg="#fff", 
                      insertbackground="#fff", bd=1, relief="sunken", 
                      font=("Segoe UI", 10), width=15)
        ent.pack(side="left", fill="x", expand=True, padx=(6, 4))

        def _on_name_change(*_):
            self.app.casinos[idx]['name'] = name_var.get().strip()
            self.app.save_data()
            if hasattr(self.app, 'history_win') and self.app.history_win and self.app.history_win.winfo_exists():
                self.app.history_win.update_filter_combo()
        
        name_var.trace_add('write', _on_name_change)

        self.rows.append({"name_var": name_var})

    def on_close(self):
        self.app.refresh_casino_combo()
        self.destroy()




# =================== FENETRE SIMULATEUR 365 JOURS ===================
class SimulatorWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Simulateur 365 jours - Calendrier")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        # Dimensions pour afficher 12 mois côte à côte
        w = 1227
        h = 677
        x = max(0, app.winfo_x() - (w - app.winfo_width()) // 2)
        y = max(0, app.winfo_y() - 50)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        # Rendre la fenêtre redimensionnable
        self.resizable(False, False)

        # ═══════════════════════════════════════════════════════
        # HEADER avec contrôles
        # ═══════════════════════════════════════════════════════
        header = tk.Frame(self, bg=DARK_BG, bd=2, relief="groove")
        header.pack(side="top", fill="x", padx=6, pady=6)

        # Titre
        title_frame = tk.Frame(header, bg=DARK_BG)
        title_frame.pack(fill="x", padx=6, pady=(6, 8))
        tk.Label(title_frame, text="📅 Simulateur 365 jours - Calendrier annuel", bg=DARK_BG, fg="#CCCC66",
                font=("Segoe UI", 11, "bold")).pack(side="left")

        # ─────────────────────────────────────────────────────
        # LIGNE CONTRÔLES : Casino + Capital + % + Date + Bouton
        # ─────────────────────────────────────────────────────
        controls = tk.Frame(header, bg=DARK_BG)
        controls.pack(fill="x", padx=6, pady=(0, 6))

        # Casino
        tk.Label(controls, text="Casino:", bg=DARK_BG, fg="#aaa",
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        
        self.casino_var = tk.StringVar(value="Sélectionner...")
        casino_names = ["Sélectionner..."] + [c['name'] for c in app.casinos if c['name'].strip()]
        self.casino_combo = ttk.Combobox(controls, textvariable=self.casino_var,
                                        values=casino_names, state='readonly',
                                        width=15, font=("Segoe UI", 9))
        self.casino_combo.pack(side="left", padx=(0, 12))
        self.casino_combo.bind('<<ComboboxSelected>>', self.on_casino_selected)

        # Capital
        tk.Label(controls, text="Capital:", bg=DARK_BG, fg="#aaa",
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        
        self.capital_var = tk.StringVar(value="1000,0")
        self.capital_entry = tk.Entry(controls, textvariable=self.capital_var,
                                      bg="#222", fg=OK_GREEN, insertbackground=OK_GREEN,
                                      bd=1, relief="sunken", font=("Segoe UI", 9, "bold"),
                                      width=10, justify="right")
        self.capital_entry.pack(side="left", padx=(0, 12))

        # Pourcentage
        tk.Label(controls, text="Obj %:", bg=DARK_BG, fg="#aaa",
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        
        self.pct_var = tk.StringVar(value="2,0")
        self.pct_entry = tk.Entry(controls, textvariable=self.pct_var,
                                 bg="#222", fg="#FFD54A", insertbackground="#FFD54A",
                                 bd=1, relief="sunken", font=("Segoe UI", 9, "bold"),
                                 width=5, justify="right")
        self.pct_entry.pack(side="left", padx=(0, 12))

        # Date de début
        tk.Label(controls, text="Date:", bg=DARK_BG, fg="#aaa",
                font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        
        today = datetime.now()
        date_options = [f"01/01/{today.year}", "Aujourd'hui"] + [f"01/{i:02d}/{today.year}" for i in range(1, 13)]
        
        self.date_var = tk.StringVar(value=f"01/01/{today.year}")
        self.date_combo = ttk.Combobox(controls, textvariable=self.date_var,
                                      values=date_options, state='readonly',
                                      width=12, font=("Segoe UI", 9))
        self.date_combo.pack(side="left", padx=(0, 12))

        # Bouton SIMULER
        btn_simulate = tk.Button(controls, text="🚀 SIMULER", command=self.run_simulation,
                                bg=ACCENT_BLUE, fg="#fff", font=("Segoe UI", 9, "bold"),
                                bd=2, relief="raised", cursor="hand2",
                                activebackground="#1E90FF", activeforeground="#fff",
                                padx=15, pady=3)
        btn_simulate.pack(side="left")

        # ═══════════════════════════════════════════════════════
        # ZONE RÉCAPITULATIF (si simulation faite)
        # ═══════════════════════════════════════════════════════
        self.summary_frame = tk.Frame(self, bg="#1a1a1a", bd=2, relief="sunken")
        # Pas affiché au départ

        # ═══════════════════════════════════════════════════════
        # ZONE CALENDRIER avec en-têtes fixes
        # ═══════════════════════════════════════════════════════
        calendar_container = tk.Frame(self, bg=DARK_BG, bd=2, relief="sunken")
        calendar_container.pack(side="top", fill="both", expand=True, padx=6, pady=(0, 6))

        # EN-TÊTES FIXES (ne scrollent pas)
        self.headers_frame = tk.Frame(calendar_container, bg=DARK_BG)
        self.headers_frame.pack(side="top", fill="x")

        # ZONE SCROLLABLE (pour les jours)
        scroll_container = tk.Frame(calendar_container, bg=DARK_BG)
        scroll_container.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(scroll_container, bg=DARK_BG, highlightthickness=0, bd=0)
        self.vs = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=DARK_BG)
        
        self.scroll_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vs.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vs.pack(side="right", fill="y")

        def _on_wheel(event):
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        self.canvas.bind_all("<MouseWheel>", _on_wheel)

        # Message initial
        tk.Label(self.scroll_frame, text="Configurez les paramètres et cliquez sur SIMULER",
                bg=DARK_BG, fg="#888", font=("Segoe UI", 11, "italic")).pack(pady=100)

    def on_casino_selected(self, event=None):
        """Callback quand un casino est sélectionné (ne fait plus rien)"""
        pass

    def run_simulation(self):
        """Lance la simulation et affiche le calendrier"""
        # Validation des paramètres
        try:
            capital = float(self.capital_var.get().replace(",", "."))
            pct = float(self.pct_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erreur", "Capital et Pourcentage doivent être des nombres valides!")
            return

        if capital <= 0:
            messagebox.showerror("Erreur", "Le capital doit être positif!")
            return
        
        if pct <= 0 or pct > 100:
            messagebox.showerror("Erreur", "Le pourcentage doit être entre 0 et 100!")
            return

        # Date de début
        date_str = self.date_var.get()
        if date_str == "Aujourd'hui":
            start_date = datetime.now()
        else:
            try:
                start_date = datetime.strptime(date_str, "%d/%m/%Y")
            except:
                messagebox.showerror("Erreur", "Format de date invalide!")
                return

        # Simulation
        results = self.simulate_365_days(capital, pct, start_date)
        
        # Affichage
        self.display_calendar(results, capital, pct, start_date)

    def simulate_365_days(self, capital, pct, start_date):
        """Calcule la simulation jour par jour"""
        results = []
        current_capital = capital
        
        for day in range(365):
            date = start_date + timedelta(days=day)
            obj = ceil_0_1(current_capital * (pct / 100.0))
            new_capital = round(current_capital + obj, 1)
            
            # Jour de la semaine
            day_letter = ['L', 'M', 'M', 'J', 'V', 'S', 'D'][date.weekday()]
            
            results.append({
                'day': day + 1,
                'date': date,
                'day_of_month': date.day,
                'month': date.month,
                'day_letter': day_letter,
                'capital_start': current_capital,
                'objective': obj,
                'capital_end': new_capital,
                'profit': obj
            })
            
            current_capital = new_capital
        
        return results

    def display_calendar(self, results, initial_capital, pct, start_date):
        """Affiche le calendrier en grille 12 colonnes avec en-têtes fixes"""
        # Effacer contenu précédent
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        for widget in self.headers_frame.winfo_children():
            widget.destroy()

        # Afficher récapitulatif
        self.summary_frame.pack(side="top", fill="x", padx=6, pady=(0, 6))
        self.summary_frame.pack_forget()  # On le recrée
        self.summary_frame = tk.Frame(self, bg="#1a1a1a", bd=2, relief="raised")
        self.summary_frame.pack(side="top", fill="x", padx=6, pady=(0, 6), after=self.children['!frame'])
        
        final_capital = results[-1]['capital_end']
        total_profit = final_capital - initial_capital
        pct_gain = (total_profit / initial_capital * 100) if initial_capital > 0 else 0
        
        summary_text = f"💰 Capital: {initial_capital:.1f} → {self.format_number(final_capital)} $ (+{pct_gain:.1f}%) | Profit total: +{self.format_number(total_profit)} $"
        tk.Label(self.summary_frame, text=summary_text, bg="#1a1a1a", fg=WIN_YELLOW,
                font=("Segoe UI", 10, "bold")).pack(pady=6)

        # Organiser résultats par mois
        by_month = defaultdict(list)
        for r in results:
            by_month[r['month']].append(r)

        # Noms des mois
        month_names = ['JANVIER', 'FÉVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN',
                      'JUILLET', 'AOÛT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DÉCEMBRE']

        # RÉORGANISER selon date départ
        start_month = start_date.month
        start_day = start_date.day
        month_order = [((start_month - 1 + i) % 12) + 1 for i in range(12)]

        # LARGEUR FIXE pour toutes les colonnes
        COLUMN_WIDTH = 95
        SEPARATOR_WIDTH = 3  # Séparateur entre mois

        # ═══════════════════════════════════════════════════════
        # EN-TÊTES FIXES (ne scrollent pas)
        # ═══════════════════════════════════════════════════════
        headers_grid = tk.Frame(self.headers_frame, bg=DARK_BG)
        headers_grid.pack(side="left", padx=6)
        
        # Configurer les colonnes pour correspondre à la grille des jours
        for col in range(12):
            headers_grid.grid_columnconfigure(col*2, minsize=COLUMN_WIDTH)
            if col < 11:  # Séparateurs
                headers_grid.grid_columnconfigure(col*2+1, minsize=SEPARATOR_WIDTH)

        for col in range(12):
            if col > 0:
                separator = tk.Frame(headers_grid, bg=LINE_GREY, width=SEPARATOR_WIDTH, height=28)
                separator.grid(row=0, column=col*2-1, sticky="ns", pady=0)
                separator.grid_propagate(False)
            
            month_num = month_order[col]
            month_header = tk.Frame(headers_grid, bg="#2A2A2A", bd=1, relief="raised", 
                                   width=COLUMN_WIDTH, height=28)
            month_header.grid(row=0, column=col*2, sticky="ew", pady=0)
            month_header.grid_propagate(False)
            
            tk.Label(month_header, text=month_names[month_num-1], bg="#2A2A2A", fg=WIN_YELLOW,
                    font=("Segoe UI", 9, "bold")).pack(expand=True)

        # ═══════════════════════════════════════════════════════
        # GRILLE DES JOURS (scrollable)
        # ═══════════════════════════════════════════════════════
        grid = tk.Frame(self.scroll_frame, bg=DARK_BG)
        grid.pack(fill="both", expand=True, padx=6, pady=(0, 50))  # 50px de marge en bas

        # Configurer les colonnes pour largeur fixe
        for col in range(12):
            grid.grid_columnconfigure(col*2, minsize=COLUMN_WIDTH)
            if col < 11:  # Séparateurs
                grid.grid_columnconfigure(col*2+1, minsize=SEPARATOR_WIDTH)

        # ═══════════════════════════════════════════════════════
        # LIGNES DE JOURS (31 lignes max)
        # ═══════════════════════════════════════════════════════
        for row in range(1, 32):  # Jours 1 à 31
            for col in range(12):
                if col > 0:
                    separator = tk.Frame(grid, bg=LINE_GREY, width=SEPARATOR_WIDTH)
                    separator.grid(row=row-1, column=col*2-1, sticky="ns")
                
                month_num = month_order[col]
                month_data = by_month.get(month_num, [])
                
                # Trouver le jour correspondant
                day_data = next((d for d in month_data if d['day_of_month'] == row), None)
                
                # Créer la cellule avec largeur fixe
                is_start_day = (month_num == start_month and row == start_day)
                cell_bg_outer = "#ff0000" if is_start_day else DARK_BG
                cell = tk.Frame(grid, bg=cell_bg_outer, bd=2 if is_start_day else 0, relief="flat", 
                               width=COLUMN_WIDTH, height=20)
                cell.grid(row=row-1, column=col*2, sticky="ew", pady=0)
                cell.grid_propagate(False)
                
                if day_data:
                    # Cellule avec données - ORGANISATION IDENTIQUE PARTOUT
                    cell_content = tk.Frame(cell, bg="#1a1a1a")
                    cell_content.pack(fill="both", expand=True, padx=1)
                    
                    # GAUCHE : Jour + Lettre (ex: "15 M") - plus compact
                    day_text = f"{day_data['day_of_month']:2d}{day_data['day_letter']}"
                    tk.Label(cell_content, text=day_text, bg="#1a1a1a", fg="#888",
                            font=("Segoe UI", 9), anchor="w", width=4).pack(side="left")
                    
                    # DROITE : Capital en nombre entier avec espaces
                    capital_color = self.get_color_for_amount(day_data['capital_end'])
                    capital_text = self.format_number_full(day_data['capital_end'])
                    tk.Label(cell_content, text=capital_text, bg="#1a1a1a", fg=capital_color,
                            font=("Segoe UI", 9, "bold"), anchor="e").pack(side="right", fill="x", expand=True)

        # ═══════════════════════════════════════════════════════
        # LIGNE DE TOTAUX PAR MOIS (profits)
        # ═══════════════════════════════════════════════════════
        for col in range(12):
            if col > 0:
                separator = tk.Frame(grid, bg=LINE_GREY, width=SEPARATOR_WIDTH)
                separator.grid(row=31, column=col*2-1, sticky="ns")
            
            month_num = month_order[col]
            month_data = by_month.get(month_num, [])
            
            if month_data:
                first_day = month_data[0]
                last_day = month_data[-1]
                month_profit = last_day['capital_end'] - first_day['capital_start']
                
                footer = tk.Frame(grid, bg="#252525", bd=1, relief="flat", 
                                 width=COLUMN_WIDTH, height=22)
                footer.grid(row=31, column=col*2, sticky="ew", pady=(2, 0))
                footer.grid_propagate(False)
                
                profit_text = f"+{self.format_number_full(month_profit)}"
                tk.Label(footer, text=profit_text, bg="#252525", fg=WIN_YELLOW,
                        font=("Segoe UI", 9, "bold")).pack(expand=True)

    def format_number(self, num):
        """Formate un nombre pour affichage compact (pour le récapitulatif)"""
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.0f}k"
        else:
            return f"{num:.0f}"

    def format_number_full(self, num):
        """Formate un nombre ENTIER avec espaces tous les 3 chiffres"""
        # Arrondir à l'entier le plus proche
        num_int = int(round(num))
        # Formater avec espaces tous les 3 chiffres
        return f"{num_int:,}".replace(",", " ")

    def get_color_for_amount(self, amount):
        """Retourne une couleur selon le montant"""
        if amount >= 1000000:
            return "#FFA500"  # Orange pour > 1M
        elif amount >= 100000:
            return "#FFD54A"  # Jaune pour 100k-1M
        elif amount >= 10000:
            return "#20c997"  # Vert clair pour 10k-100k
        else:
            return OK_GREEN   # Vert pour < 10k


# =================== APP ===================
class Calculator(tk.Tk):
    def _r01(self, x):
        """Arrondit un nombre à 0.1 (un dixième)"""
        return round(x, 1)

    def __init__(self):
        super().__init__()
        self.title("Calculatrice Personnalisée")
        self.configure(bg=DARK_BG)
        self.resizable(False, False)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        self.current = "0"
        self.acc = None
        self.pending_op = None
        self.just_evaluated = False
        self.history = ""
        self.previous_result = 0.0

        self.bk_start = 0.0
        self.bk_live  = 0.0
        self.bk_on_table = 0.0
        self.obj_total = 0.0
        self.bk_target = 0.0

        self.sessions = [0.0, 0.0, 0.0]
        self.all_sessions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # 10 sessions max
        self.session_offset = 0  # Décalage affichage rotatif
        self.cur_session = 0
        self.phase = 1

        self.session_mode = False
        self.kb_unlocked = True

        self.obj_pct = 2.0
        self.num_mode = 18  # 18N par défaut

        self.session_losses = [0.0, 0.0, 0.0]
        self.session_impact_pct = [0.0, 0.0, 0.0]  # Impacts des 3 sessions visibles
        self.all_session_impacts = [0.0] * 10  # Impacts de TOUTES les sessions S1-S10
        
        # Système de division des pertes (mode 24N uniquement)
        self.next_threshold = -2.0  # Prochain palier (-2%, -4%, -6%...)
        self.active_sessions_count = 3  # Sessions actives (3 à 10)
        self.all_sessions = [0.0] * 10  # Toutes les sessions (S1 à S10)
        self.session_offset = 0  # Pour affichage rotatif

        self.casinos = [{'name': "", 'sessions': []} for _ in range(200)]
        self.cur_casino_idx = None
        self.session_start_ts = None
        self.session_stake_sum = 0.0
        self.session_initial_target = 0.0
        self.state_stack = []
        self._compact = False
        self.normal_height_px = None
        
        # Compteur de sessions consécutives
        self.consecutive_session_count = 0
        self.last_session_casino_idx = None
        
        self.load_data()

        top = tk.Frame(self, bg=DARK_BG)
        top.pack(side="top", fill="x", padx=PAD_OUT_X, pady=(PAD_OUT_TOP, PAD_OUT_BETWEEN))

        disp_outer_h = DISP_H + 2 * DISP_BD
        self.display_frame = tk.Frame(top, bg=DISPLAY_BG, bd=DISP_BD, relief="sunken", width=SHELL_W, height=disp_outer_h)
        self.display_frame.pack_propagate(False)
        self.display_frame.pack(fill="x")

        self.display_frame.grid_rowconfigure(0, weight=1)
        self.display_frame.grid_rowconfigure(1, weight=2)
        self.display_frame.grid_columnconfigure(0, weight=1, uniform="disp")
        self.display_frame.grid_columnconfigure(1, weight=1, uniform="disp")

        self.separator = tk.Frame(self.display_frame, bg=LINE_GREY, width=1)
        self.separator.place(relx=0.5, rely=0.0, relheight=1.0, anchor="n")

        left = tk.Frame(self.display_frame, bg=DISPLAY_BG)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(7, 4), pady=4)

        self.s_rows = []
        for i in range(3):
            row = tk.Frame(left, bg=DISPLAY_BG)
            row.pack(fill="x")
            lbl = tk.Label(row, text=f"S{i+1} 0,0", bg=DISPLAY_BG, fg=WIN_YELLOW, anchor="w",
                           font=("Segoe UI", 8, "bold"))
            lbl.pack(side="left", fill="x", expand=True)
            pct = tk.Label(row, text="0,0%", bg=DISPLAY_BG, fg=IMPACT_RED, anchor="e",
                           font=("Segoe UI", 8, "bold"), width=6)
            pct.pack(side="right")
            self.s_rows.append((lbl, pct))

        tk.Frame(left, bg=LINE_GREY, height=1).pack(fill="x", pady=(4, 2))
        
        bk_row = tk.Frame(left, bg=DISPLAY_BG)
        bk_row.pack(fill="x")
        
        self.bk_start_label = tk.Label(bk_row, text="BK 0,0", bg=DISPLAY_BG, fg=OK_GREEN, anchor="w", font=("Segoe UI", 8, "bold"))
        self.bk_start_label.pack(side="left", fill="x", expand=False)
        
        self.bk_arrow = tk.Label(bk_row, text="", bg=DISPLAY_BG, fg="#888888", font=("Segoe UI", 8))
        self.bk_arrow.pack(side="left", padx=(2, 2))
        
        self.bk_label = tk.Label(bk_row, text="", bg=DISPLAY_BG, fg="#bbbbbb", anchor="w", font=("Segoe UI", 8))
        self.bk_label.pack(side="left", fill="x", expand=False)

        obj_row = tk.Frame(left, bg=DISPLAY_BG)
        obj_row.pack(fill="x")
        self.obj_label = tk.Label(obj_row, text="OBJ 0,0 (2.0%)", bg=DISPLAY_BG, fg="#888888",
                                  anchor="w", font=("Segoe UI", 8))
        self.obj_label.pack(side="left", fill="x", expand=True)

        def mk_min_btn(txt, cmd):
            return tk.Button(obj_row, text=txt, command=cmd,
                             font=("Segoe UI", 9, "bold"),
                             fg="#FFFFFF", bg=DISPLAY_BG,
                             relief="flat", bd=0, highlightthickness=0,
                             activeforeground="#FFFFFF", activebackground=DISPLAY_BG,
                             padx=0, pady=0, width=2, cursor="hand2")
        self.btn_obj_minus = mk_min_btn("−", lambda: self.adjust_obj_pct(-OBJ_PCT_STEP))
        self.btn_obj_plus  = mk_min_btn("+",  lambda: self.adjust_obj_pct(+OBJ_PCT_STEP))
        self.btn_obj_plus.pack(side="right")
        self.btn_obj_minus.pack(side="right")

        self.cib_label = tk.Label(left, text="CIB S1 0,0 → 0,0", bg=DISPLAY_BG, fg="#aaaaaa", anchor="w", font=("Segoe UI", 8))
        self.cib_label.pack(fill="x")

        right = tk.Frame(self.display_frame, bg=DISPLAY_BG)
        right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(2, 7), pady=2)
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=2)
        right.grid_columnconfigure(0, weight=1)

        top_right = tk.Frame(right, bg=DISPLAY_BG)
        top_right.grid(row=0, column=0, sticky="new", padx=0, pady=(0, 0))
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Dark.TCombobox',
                        fieldbackground='#000', background='#000',
                        foreground='#E6D84B', bordercolor='#000',
                        lightcolor='#000', darkcolor='#000',
                        arrowcolor='#000', arrowsize=14, padding=0)
        style.map('Dark.TCombobox',
                  fieldbackground=[('readonly', '#000'), ('!focus', '#000'), ('focus', '#000')],
                  foreground=[('readonly', '#E6D84B'), ('!focus', '#E6D84B'), ('focus', '#E6D84B')],
                  selectbackground=[('readonly', '#000'), ('!focus', '#000'), ('focus', '#000')],
                  selectforeground=[('readonly', '#E6D84B'), ('!focus', '#E6D84B'), ('focus', '#E6D84B')],
                  arrowcolor=[('active', '#fff'), ('!active', '#000')])
        self.option_add('*TCombobox*Listbox.background', '#000')
        self.option_add('*TCombobox*Listbox.foreground', '#E6D84B')
        self.option_add('*TCombobox*Listbox.selectBackground', '#111')
        self.option_add('*TCombobox*Listbox.selectForeground', '#E6D84B')

        self.casino_var = tk.StringVar(value="")
        self.combo = ttk.Combobox(top_right, textvariable=self.casino_var, state='readonly',
                                  width=18, style='Dark.TCombobox', justify='center')
        self.combo.pack(side='right', anchor='n')
        self.combo.bind('<<ComboboxSelected>>', self.on_casino_selected)

        self.history_display = tk.Label(top_right, text="", bg=DISPLAY_BG, fg="#888",
                                        font=("Segoe UI", 8), anchor="w", justify="left")
        self.history_display.pack(side="left", expand=True, fill="x")

        self.refresh_casino_combo()
        
        self.cur_casino_idx = None
        self._update_combo_color()
        
        try:
            self.combo.selection_clear()
        except Exception:
            pass

        self.display = tk.Label(right, text="0", bg=DISPLAY_BG, fg=DISPLAY_FG,
                                font=("Segoe UI", 16, "bold"), anchor="e", justify="right")
        self.display.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 2))

        # Frame conteneur pour hashtag + boutons (disposés verticalement)
        shortcuts_container = tk.Frame(right, bg=DISPLAY_BG)
        shortcuts_container.grid(row=2, column=0, sticky="w", padx=4, pady=(0, 4))
        
        # Ligne 1 : Hashtag de session
        hashtag_frame = tk.Frame(shortcuts_container, bg=DISPLAY_BG)
        hashtag_frame.pack(side="top", fill="x", anchor="w")
        
        self.session_hashtag_label = tk.Label(hashtag_frame, text="", bg=DISPLAY_BG, fg="#aaa",
                                             font=("Segoe UI", 8), anchor="w")
        self.session_hashtag_label.pack(side="left")
        
        # Ligne 2 : Boutons raccourcis
        shortcuts_frame = tk.Frame(shortcuts_container, bg=DISPLAY_BG)
        shortcuts_frame.pack(side="top", fill="x", anchor="w")
        
        shortcut_style = {
            "bg": "#333",
            "fg": "#aaa",
            "bd": 1,
            "relief": "raised",
            "font": ("Segoe UI", 7, "bold"),
            "activebackground": "#555",
            "activeforeground": "#fff",
            "cursor": "hand2",
            "width": 3,
            "height": 1
        }
        
        self.btn_shortcut_s = tk.Button(shortcuts_frame, text="S", 
                                        command=self.open_stats, **shortcut_style)
        self.btn_shortcut_s.pack(side="left", padx=(0, 2))
        
        self.btn_shortcut_exp = tk.Button(shortcuts_frame, text="EXP", 
                                         command=self.open_export_direct, **shortcut_style)
        self.btn_shortcut_exp.pack(side="left", padx=(0, 2))
        
        # NOUVEAU BOUTON LC
        self.btn_shortcut_lc = tk.Button(shortcuts_frame, text="LC", 
                                        command=self.open_casino_list_shortcut, **shortcut_style)
        self.btn_shortcut_lc.pack(side="left", padx=(0, 2))
        
        # NOUVEAU BOUTON 365 - Simulateur
        self.btn_shortcut_365 = tk.Button(shortcuts_frame, text="365", 
                                         command=self.open_simulator, **shortcut_style)
        self.btn_shortcut_365.pack(side="left")

        self.keypad_outer = tk.Frame(self, bg=DARK_BG, width=SHELL_W)
        self.keypad_outer.pack(side="top", fill="x", padx=PAD_OUT_X)

        def mk_btn(parent, text, cmd, font_sz=9, bg=BTN_BG, fg=BTN_FG, active="#404040"):
            return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, bd=2, relief="raised",
                             font=("Segoe UI", font_sz, "bold"), highlightthickness=0,
                             activebackground=active, activeforeground=fg, cursor="hand2")

        self.top_row = centered_row(self.keypad_outer)
        self.top_row.pack(side="top", fill="x", pady=GAP // 2)
        self.btn_go = mk_btn(self.top_row, "GO", self.on_go, bg=ACCENT_BLUE, active="#1E90FF")
        self.btn_P = mk_btn(self.top_row, "P", self.on_lose, bg=ACCENT_RED)
        self.btn_G = mk_btn(self.top_row, "G", self.on_win, bg=ACCENT_GREEN)
        self.btn_kb = mk_btn(self.top_row, "🔓", self.toggle_kb_lock, font_sz=11, bg=ACCENT_GREY, active=ACCENT_GREY_H)
        add4(self.top_row, (self.btn_go, self.btn_P, self.btn_G, self.btn_kb))

        self.mid_container = tk.Frame(self.keypad_outer, bg=DARK_BG, width=SHELL_W, height=4 * CELL_H)
        self.mid_container.pack_propagate(False)
        self.mid_container.pack(side="top", fill="x")

        def mid_row():
            fr = centered_row(self.mid_container)
            fr.pack(side="top", fill="x", pady=GAP // 2)
            return fr

        r1 = mid_row()
        self.d7 = mk_btn(r1, "7", lambda: self.on_digit("7"))
        self.d8 = mk_btn(r1, "8", lambda: self.on_digit("8"))
        self.d9 = mk_btn(r1, "9", lambda: self.on_digit("9"))
        self.btn_div = mk_btn(r1, "÷", lambda: self.on_op("÷"), font_sz=12)
        add4(r1, (self.d7, self.d8, self.d9, self.btn_div))

        r2 = mid_row()
        self.d4 = mk_btn(r2, "4", lambda: self.on_digit("4"))
        self.d5 = mk_btn(r2, "5", lambda: self.on_digit("5"))
        self.d6 = mk_btn(r2, "6", lambda: self.on_digit("6"))
        self.btn_mul = mk_btn(r2, "×", lambda: self.on_op("×"), font_sz=12)
        add4(r2, (self.d4, self.d5, self.d6, self.btn_mul))

        r3 = mid_row()
        self.d1 = mk_btn(r3, "1", lambda: self.on_digit("1"))
        self.d2 = mk_btn(r3, "2", lambda: self.on_digit("2"))
        self.d3 = mk_btn(r3, "3", lambda: self.on_digit("3"))
        self.btn_sub = mk_btn(r3, "-", lambda: self.on_op("-"), font_sz=12)
        add4(r3, (self.d1, self.d2, self.d3, self.btn_sub))

        r4 = mid_row()
        self.btn_comma = mk_btn(r4, ",", self.on_comma)
        self.d0 = mk_btn(r4, "0", lambda: self.on_digit("0"))
        self.btn_eq = mk_btn(r4, "=", self.on_equal, font_sz=12, bg=ACCENT_EQUAL, active="#1E90FF")
        self.btn_add = mk_btn(r4, "+", lambda: self.on_op("+"), font_sz=12)
        add4(r4, (self.btn_comma, self.d0, self.btn_eq, self.btn_add))

        self.digit_buttons = [self.d0, self.d1, self.d2, self.d3, self.d4, self.d5, self.d6, self.d7, self.d8, self.d9]
        self.op_buttons = [self.btn_div, self.btn_mul, self.btn_sub, self.btn_add]

        self.bot_row = centered_row(self.keypad_outer)
        self.bot_row.pack(side="top", fill="x", pady=GAP // 2)
        self.btn_ret = mk_btn(self.bot_row, "↩", self.on_undo, font_sz=11, bg="#555555", active="#777777")
        self.btn_stat = mk_btn(self.bot_row, "18N", self.toggle_num_mode, bg="#2266aa")
        self.btn_res = mk_btn(self.bot_row, "RESET", self.on_reset, bg=RESET_BG, active=RESET_BG_H)
        self.btn_compact = mk_btn(self.bot_row, "⌨", self.toggle_compact, bg="#666666", active="#888888")
        add4(self.bot_row, (self.btn_ret, self.btn_stat, self.btn_res, self.btn_compact))

        self.bottom_spacer = tk.Frame(self, height=BOTTOM_MARGIN, bg=DARK_BG)
        self.bottom_spacer.pack(side="top", fill="x", padx=PAD_OUT_X, pady=0)

        self.bind("<KeyPress>", self.handle_key)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        self._compact = False
        self.apply_mode_sizes()
        self.update_idletasks()
        self.normal_height_px = self.winfo_reqheight()

        self.refresh_display()
        self.after_idle(self.apply_mode_sizes)
        self.after_idle(self.set_height_to_required)
        self.after(100, self.clear_combo_selection)
        self.protocol("WM_DELETE_WINDOW", self.on_close)


    def save_data(self):
        data = {"casinos": self.casinos, "obj_pct": self.obj_pct}
        try:
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde: {e}")

    def load_data(self):
        if os.path.exists(DATA_PATH):
            try:
                with open(DATA_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "casinos" in data and isinstance(data["casinos"], list):
                    old_len = len(data["casinos"])
                    # Migration : étendre de 50 à 200 casinos ou gérer tout nombre existant
                    if old_len < 200:
                        # Ajouter des casinos vides jusqu'à 200
                        data["casinos"].extend([{'name': "", 'sessions': []} for _ in range(200 - old_len)])
                    self.casinos = data["casinos"][:200]  # Garder seulement 200 maximum
                p = data.get("obj_pct", self.obj_pct)
                try:
                    p = float(p)
                except Exception:
                    p = self.obj_pct
                self.obj_pct = max(OBJ_PCT_MIN, min(OBJ_PCT_MAX, round(p, 1)))
            except Exception as e:
                print(f"Erreur chargement: {e}")

    def on_close(self):
        self.save_data()
        self.destroy()

    def adjust_obj_pct(self, delta):
        if self.session_mode:
            return
        new_val = self.obj_pct + delta
        self.obj_pct = max(OBJ_PCT_MIN, min(OBJ_PCT_MAX, round(new_val, 1)))
        self.save_data()
        self.refresh_display()
        self.update_objective_preview()  # MODIFICATION 6

    def update_objective_preview(self):
        """MODIFICATION 6 : Affiche l'objectif AVANT de cliquer sur GO"""
        if self.session_mode:
            return
        try:
            current_bk = self.to_float(self.current)
            if current_bk > 0:
                preview_obj = ceil_0_1(current_bk * (self.obj_pct / 100.0))
                self.obj_label.config(text=f"OBJ {self._fmt(preview_obj)} ({self.obj_pct:.1f}%)")
            else:
                self.obj_label.config(text=f"OBJ 0,0 ({self.obj_pct:.1f}%)")
        except:
            self.obj_label.config(text=f"OBJ 0,0 ({self.obj_pct:.1f}%)")

    def set_height_to_required(self):
        self.update_idletasks()
        req = self.winfo_reqheight()
        self.geometry(f"{WIN_W}x{req}")

    def apply_mode_sizes(self):
        if self._compact:
            if self.mid_container.winfo_ismapped():
                self.mid_container.pack_forget()
        else:
            if not self.mid_container.winfo_ismapped():
                self.mid_container.pack(side="top", fill="x")
        self.set_height_to_required()
        self.btn_kb.config(text=("🔓" if self.kb_unlocked else "🔒"))
        self.update_obj_controls_state()

    def _fmt(self, x): 
        return f"{x:.1f}".replace(".", ",")
    
    def _fmt_pct(self, p): 
        return f"{p:.1f}%".replace(".", ",")

    def refresh_display(self):
        t = self.current
        t = (t[:12] + "...") if len(t) > 15 else t
        self.display.config(text=t)

        h = self.history
        h = ("..." + h[-22:]) if len(h) > 25 else h
        self.history_display.config(text=h)

        for i, (lbl, pct_lbl) in enumerate(self.s_rows):
            R = self.sessions[i]
            display_num = self.session_offset + i + 1  # Vrai numéro
            if not self.session_mode:
                lbl.config(text=f"S{i+1} 0,0", fg=WIN_YELLOW)
            else:
                if R <= 0.0:
                    lbl.config(text=f"S{display_num} WIN", fg=WIN_YELLOW)
                elif i == self.cur_session:
                    lbl.config(text=f"S{display_num} {self._fmt(R)} EC", fg=OK_GREEN)
                else:
                    lbl.config(text=f"S{display_num} {self._fmt(R)} ATT", fg=WAIT_RED)
            
            pct_lbl.config(text=self._fmt_pct(self.session_impact_pct[i]), fg=IMPACT_RED, anchor="e")

        if self.session_mode and self.bk_start > 0:
            self.bk_start_label.config(text=f"BK {self._fmt(self.bk_start)}", fg=OK_GREEN)
            self.bk_arrow.config(text="→")
            bk_col = OK_GREEN if self.bk_live >= self.bk_start else WAIT_RED
            self.bk_label.config(text=self._fmt(self.bk_live), fg=bk_col)
        else:
            self.bk_start_label.config(text="BK 0,0", fg=OK_GREEN)
            self.bk_arrow.config(text="")
            self.bk_label.config(text="", fg="#bbbbbb")

        self.obj_label.config(text=f"OBJ {self._fmt(self.obj_total if self.session_mode else 0)} ({self.obj_pct:.1f}%)")
        
        # MODIFICATION 6 : Mettre à jour l'affichage avant GO
        if not self.session_mode:
            self.update_objective_preview()
        
        cib_rest = self.sessions[self.cur_session] if 0 <= self.cur_session < 3 else 0.0
        self.cib_label.config(text=f"CIB S{min(self.cur_session + 1, 3)} {self._fmt(cib_rest)} → {self._fmt(self.bk_target)}")
        self.btn_kb.config(text=("🔓" if self.kb_unlocked else "🔒"))
        
        # Mettre à jour le hashtag de session
        if self.session_mode:
            # Afficher #1 pour la première session, #2 pour la deuxième, etc.
            session_num = self.consecutive_session_count + 1
            self.session_hashtag_label.config(text=f"#{session_num}  ")
        else:
            self.session_hashtag_label.config(text="")
        
        self.refresh_casino_combo()
        self.update_obj_controls_state()

    def update_obj_controls_state(self):
        state = (tk.NORMAL if not self.session_mode else tk.DISABLED)
        self.btn_obj_minus.config(state=state)
        self.btn_obj_plus.config(state=state)

    def to_float(self, s):
        try:
            return float(s.replace(",", "."))
        except Exception:
            return 0.0

    def from_float(self, x):
        if x in (float("inf"), float("-inf")) or abs(x) > 1e15:
            return "Erreur"
        if abs(x) < 1e-10:
            x = 0.0
        return f"{x:.10g}".replace(".", ",")

    def apply_operation(self, l, op, r):
        try:
            if op == "+": return l + r
            if op == "-": return l - r
            if op == "*": return l * r
            if op == "/": return l / r if r != 0 else float("inf")
        except Exception:
            return float("inf")
        return r

    def on_digit(self, d):
        if self.session_mode and not self.kb_unlocked:
            return
        if self.just_evaluated or self.current == "Erreur":
            if self.just_evaluated:
                self.history = ""
            self.current = "0"
            self.just_evaluated = False
        if self.current == "0":
            self.current = d
        else:
            if len(self.current.replace(",", "")) < 12:
                self.current += d
        self.refresh_display()
        # MODIFICATION 6 : Mettre à jour OBJ pendant qu'on tape
        if not self.session_mode:
            self.update_objective_preview()

    def on_comma(self):
        if self.session_mode and not self.kb_unlocked:
            return
        if self.just_evaluated or self.current == "Erreur":
            self.current = "0"
            self.just_evaluated = False
        if "," not in self.current:
            self.current = "0," if self.current == "0" else (self.current + ",")
        self.refresh_display()

    def on_op(self, symbol):
        if self.session_mode and not self.kb_unlocked:
            return
        if self.current == "Erreur":
            self.on_reset()
            return
        op_map = {"÷": "/", "×": "*", "+": "+", "-": "-"}
        op = op_map.get(symbol)
        right = self.to_float(self.current)
        if self.acc is None:
            self.history = f"{self.current} {symbol} "
            self.acc = right
        else:
            self.acc = self.apply_operation(self.acc, self.pending_op, right)
            self.history = f"{self.from_float(self.acc)} {symbol} "
        self.pending_op = op
        self.current = "0"
        self.just_evaluated = False
        self.refresh_display()
        if self.acc is not None:
            self.current = self.from_float(self.acc)
            self.refresh_display()
            self.current = "0"

    def on_equal(self):
        try:
            right = self.to_float(self.current)
            if self.acc is None and self.pending_op is None:
                self.just_evaluated = True
                self.previous_result = self.to_float(self.current)
                return self.refresh_display()

            if self.acc is None:
                self.acc = self.to_float(self.current)

            res = self.apply_operation(self.acc, self.pending_op, right) if self.pending_op else right
            self.previous_result = res
            self.history = ""
            self.current = self.from_float(res)
            self.acc = None
            self.pending_op = None
            self.just_evaluated = True
            self.refresh_display()
        except Exception as e:
            try:
                messagebox.showerror("Erreur", f"Calcul impossible: {e}")
            except Exception:
                print("Erreur:", e)

    def _update_combo_color(self):
        style = ttk.Style()
        if self.cur_casino_idx is None:
            style.map('Dark.TCombobox',
                      foreground=[('readonly', '#000000'), ('!focus', '#000000'), ('focus', '#000000')],
                      selectforeground=[('readonly', '#000000'), ('!focus', '#000000'), ('focus', '#000000')])
        else:
            style.map('Dark.TCombobox',
                      foreground=[('readonly', '#E6D84B'), ('!focus', '#E6D84B'), ('focus', '#E6D84B')],
                      selectforeground=[('readonly', '#E6D84B'), ('!focus', '#E6D84B'), ('focus', '#E6D84B')])
    
    def refresh_casino_combo(self):
        names = [c['name'] for c in self.casinos if c['name'].strip()]
        cur = self.casino_var.get()
        self.combo['values'] = names
        
        if cur not in names or not cur.strip():
            self.casino_var.set("⚠️ SÉLECTIONNER CASINO")
            self.cur_casino_idx = None
        else:
            name = self.casino_var.get()
            self.cur_casino_idx = next((i for i, c in enumerate(self.casinos) if c['name'] == name), None)
        
        self._update_combo_color()
        
        try:
            self.combo.selection_clear()
            self.display.focus_set()
        except Exception:
            pass

    def on_casino_selected(self, event=None):
        name = self.casino_var.get()
        
        # Réinitialiser le compteur si on change de casino
        if self.cur_casino_idx is not None:
            old_idx = self.cur_casino_idx
        else:
            old_idx = None
        
        if name == "⚠️ SÉLECTIONNER CASINO":
            self.cur_casino_idx = None
            # Reset compteur si on désélectionne
            self.consecutive_session_count = 0
            self.last_session_casino_idx = None
        else:
            new_idx = next((i for i, c in enumerate(self.casinos) if c['name'] == name), None)
            
            # Si changement de casino, reset compteur
            if old_idx is not None and new_idx != old_idx:
                self.consecutive_session_count = 0
                self.last_session_casino_idx = None
            
            self.cur_casino_idx = new_idx
        
        self._update_combo_color()
        
        self.after(10, self.clear_combo_selection)

    def clear_combo_selection(self):
        try:
            self.combo.selection_clear()
            self.display.focus_set()
        except Exception:
            pass

    def open_stats(self):
        if getattr(self, 'stats_win', None) and self.stats_win.winfo_exists():
            self.stats_win.lift()
            return
        self.stats_win = StatsWindow(self)

    def open_casino_list_shortcut(self):
        """Ouvre la fenêtre de liste des casinos depuis le raccourci LC"""
        CasinoListWindow(self)

    def open_export_direct(self):
        """Ouvre la fenêtre d'historique interactive"""
        if getattr(self, 'history_win', None) and self.history_win.winfo_exists():
            self.history_win.lift()
            return
        self.history_win = HistoryWindow(self)

    def open_simulator(self):
        """Ouvre la fenêtre du simulateur 365 jours"""
        if getattr(self, 'simulator_win', None) and self.simulator_win.winfo_exists():
            self.simulator_win.lift()
            return
        self.simulator_win = SimulatorWindow(self)

    def _calc_avg_gain_per_hour(self, sessions):
        if not sessions:
            return 0.0
        total_gain = sum(s.get('profit', 0.0) for s in sessions)
        starts = [s.get('start_ts') for s in sessions if s.get('start_ts') is not None]
        ends   = [s.get('end_ts')   for s in sessions if s.get('end_ts')   is not None]
        if starts and ends:
            elapsed = max(0.001, (max(ends) - min(starts)))
        else:
            elapsed = sum(s.get('duration', 0.0) for s in sessions) or 0.001
        hours = elapsed / 3600.0
        return total_gain / hours

    def compute_casino_stats(self, idx):
        sess = self.casinos[idx]['sessions']
        if not sess:
            return {'avg_time': 0, 'avg_impact': 0, 'min_impact': 0, 'max_impact': 0, 'avg_gain_per_hour': 0}
        n = len(sess)
        avg_time = sum(s.get('duration', 0.0) for s in sess) / n
        impacts = [s.get('impact_pct', 0.0) for s in sess]
        avg_impact = sum(impacts) / n
        min_impact = min(impacts)
        max_impact = max(impacts)
        avg_gain_per_hour = self._calc_avg_gain_per_hour(sess)
        return {'avg_time': avg_time, 'avg_impact': avg_impact,
                'min_impact': min_impact, 'max_impact': max_impact,
                'avg_gain_per_hour': avg_gain_per_hour}

    def compute_total_stats(self):
        all_sess = [s for c in self.casinos for s in c['sessions']]
        if not all_sess:
            return {'avg_time': 0, 'avg_impact': 0, 'min_impact': 0, 'max_impact': 0, 'avg_gain_per_hour': 0}
        n = len(all_sess)
        avg_time = sum(s.get('duration', 0.0) for s in all_sess) / n
        impacts = [s.get('impact_pct', 0.0) for s in all_sess]
        avg_impact = sum(impacts) / n
        min_impact = min(impacts)
        max_impact = max(impacts)
        avg_gain_per_hour = self._calc_avg_gain_per_hour(all_sess)
        return {'avg_time': avg_time, 'avg_impact': avg_impact,
                'min_impact': min_impact, 'max_impact': max_impact,
                'avg_gain_per_hour': avg_gain_per_hour}

    def _log_full_session(self):
        """Enregistre la session complète avec détails de TOUTES les sessions actives (S1-S10)"""
        if self.cur_casino_idx is None or self.session_start_ts is None:
            print("[LOG] ⚠️ Pas de casino sélectionné ou session non démarrée")
            return
        
        end_ts = time.time()
        duration = end_ts - self.session_start_ts
        
        # Collecter les impacts de toutes les sessions actives
        all_impacts = []
        for i in range(self.active_sessions_count):
            all_impacts.append(self.all_session_impacts[i])
        
        impact_pct = min(all_impacts) if all_impacts else 0.0
        profit_total = float(self.obj_total)

        rec = {
            'duration': duration,
            'impact_pct': impact_pct,
            'profit': profit_total,
            'start_ts': self.session_start_ts,
            'end_ts': end_ts,
            'impacts_detail': all_impacts,  # TOUTES les sessions actives
            'num_sessions': self.active_sessions_count,  # Nombre de sessions utilisées
            'num_mode': self.num_mode  # Mode 18N ou 24N
        }
        self.casinos[self.cur_casino_idx]['sessions'].append(rec)
        
        self.save_data()
        
        # Affichage console adapté
        impacts_str = " ".join([f"S{i+1}={all_impacts[i]:.1f}%" for i in range(len(all_impacts))])
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 SESSION COMPLÈTE | Durée={fmt_time(duration)} Impact={impact_pct:.1f}% Profit={profit_total:.1f}")
        print(f"  Détail impacts: {impacts_str}")
        
        if getattr(self, 'stats_win', None) and self.stats_win.winfo_exists():
            self.stats_win.update_stats_ui()

        self.session_start_ts = None
        self.session_stake_sum = 0.0
        self.session_initial_target = 0.0

    def push_state(self):
        self.state_stack.append(self.snapshot())

    def snapshot(self):
        return {
            'current': self.current,
            'acc': self.acc,
            'pending_op': self.pending_op,
            'just_evaluated': self.just_evaluated,
            'history': self.history,
            'previous_result': self.previous_result,
            'bk_start': self.bk_start,
            'bk_live': self.bk_live,
            'bk_on_table': self.bk_on_table,
            'obj_total': self.obj_total,
            'bk_target': self.bk_target,
            'sessions': deepcopy(self.sessions),
            'cur_session': self.cur_session,
            'phase': self.phase,
            'session_mode': self.session_mode,
            'kb_unlocked': self.kb_unlocked,
            'go_enabled': (self.btn_go.cget("state") == tk.NORMAL),
            'cur_casino_idx': self.cur_casino_idx,
            'session_start_ts': self.session_start_ts,
            'session_stake_sum': self.session_stake_sum,
            'session_initial_target': self.session_initial_target,
            '_compact': self._compact,
            'obj_pct': self.obj_pct,
            'session_losses': deepcopy(self.session_losses),
            'session_impact_pct': deepcopy(self.session_impact_pct),
            'all_session_impacts': deepcopy(self.all_session_impacts),
            'num_mode': self.num_mode,
            'all_sessions': deepcopy(self.all_sessions),
            'session_offset': self.session_offset,
        }

    def restore(self, s):
        self.current = s['current']
        self.acc = s['acc']
        self.pending_op = s['pending_op']
        self.just_evaluated = s['just_evaluated']
        self.history = s['history']
        self.previous_result = s['previous_result']
        self.bk_start = s['bk_start']
        self.bk_live = s['bk_live']
        self.bk_on_table = s.get('bk_on_table', 0.0)
        self.obj_total = s['obj_total']
        self.bk_target = s['bk_target']
        self.sessions = deepcopy(s['sessions'])
        self.cur_session = s['cur_session']
        self.phase = s['phase']
        self.session_mode = s['session_mode']
        self.kb_unlocked = s['kb_unlocked']
        self.cur_casino_idx = s['cur_casino_idx']
        self.session_start_ts = s['session_start_ts']
        self.session_stake_sum = s['session_stake_sum']
        self.session_initial_target = s['session_initial_target']
        self._compact = s.get('_compact', self._compact)
        self.obj_pct = s.get('obj_pct', self.obj_pct)
        self.session_losses = deepcopy(s.get('session_losses', [0.0, 0.0, 0.0]))
        self.session_impact_pct = deepcopy(s.get('session_impact_pct', [0.0, 0.0, 0.0]))
        self.all_session_impacts = deepcopy(s.get('all_session_impacts', [0.0]*10))
        self.num_mode = s.get('num_mode', 18)
        self.all_sessions = deepcopy(s.get('all_sessions', [0.0]*6))
        self.session_offset = s.get('session_offset', 0)
        self.btn_stat.config(text=f"{self.num_mode}N")

        if s.get('go_enabled', True):
            self.btn_go.config(state=tk.NORMAL, bg=ACCENT_BLUE, activebackground="#1E90FF")
        else:
            self.btn_go.config(state=tk.DISABLED, bg=ACCENT_GREY, activebackground=ACCENT_GREY_H)

        self.update_kb_lock_ui()
        self.apply_mode_sizes()
        self.refresh_display()


    def on_go(self):
        if self.cur_casino_idx is None:
            messagebox.showerror("Erreur", "Veuillez sélectionner un casino avant de démarrer.")
            return
        
        self.push_state()
        self._compact = True
        self.apply_mode_sizes()

        self.bk_start = self.to_float(self.current)
        
        if self.bk_start <= 0:
            messagebox.showerror("Erreur", "La bankroll doit être positive.")
            self.state_stack.pop()
            return

        self.obj_total = ceil_0_1(self.bk_start * (self.obj_pct / 100.0))
        self.bk_target = self._r01(self._r01(self.bk_start) + self._r01(self.obj_total))

        s1 = ceil_0_1(self.obj_total / 3.0)
        rem = self._r01(self._r01(self.obj_total) - self._r01(s1))
        s2 = ceil_0_1(rem / 2.0) if rem > 0 else 0.0
        s3 = max(0.0, self._r01(self._r01(self.obj_total) - self._r01(s1) - self._r01(s2)))
        
        if self.num_mode == 24:
            # Mode 24N : S1-S3 ont objectif, S4-S10 = 0 (réserves)
            self.all_sessions = [s1, s2, s3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            self.sessions = [s1, s2, s3]  # Affichage initial
            self.session_offset = 0
            # Réinitialiser système division pertes
            self.next_threshold = -2.0
            self.active_sessions_count = 3
        else:
            # Mode 18N : 3 sessions + réserves jusqu'à S10
            self.all_sessions = [s1, s2, s3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            self.sessions = [s1, s2, s3]
            self.session_offset = 0
            # Réinitialiser système division pertes
            self.next_threshold = -2.0
            self.active_sessions_count = 3
        
        self.cur_session = 0
        self.phase = 1
        self.history = "GO"
        self.session_mode = True
        self.kb_unlocked = False

        stake = self.next_stake()
        display_stake, table_stake = self._prepare_stake(stake)
        
        if table_stake > self.bk_start:
            messagebox.showerror("Erreur", f"Bankroll insuffisante pour la première mise ({self._fmt(display_stake)})!")
            self.state_stack.pop()
            return
        
        self.bk_live = self._r01(self._r01(self.bk_start) - self._r01(table_stake))
        self.bk_on_table = self._r01(table_stake)

        self.session_losses = [0.0, 0.0, 0.0]
        self.session_impact_pct = [0.0, 0.0, 0.0]
        self.all_session_impacts = [0.0] * 10  # Reset tous les impacts
        
        initial_impact = -(table_stake / self.bk_start * 100.0) if self.bk_start > 0 else 0.0
        self.session_impact_pct[0] = initial_impact
        self.all_session_impacts[0] = initial_impact  # Aussi dans all_session_impacts

        self.combo.state(['disabled'])
        self.on_casino_selected()
        
        now = time.time()
        self.session_start_ts = now
        self.session_stake_sum = 0.0
        self.session_initial_target = self.sessions[self.cur_session]

        self.btn_go.config(state=tk.DISABLED, bg=ACCENT_GREY, activebackground=ACCENT_GREY_H)
        self.update_kb_lock_ui()
        
        self.current = self.from_float(stake)
        self.refresh_display()
        self._compact = True
        self.apply_mode_sizes()

        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 DÉMARRAGE SESSION")
        print(f"  Casino: {self.casinos[self.cur_casino_idx]['name'] or f'#{self.cur_casino_idx+1}'}")
        print(f"  BK_start: {self.bk_start:.1f} | BK_target: {self.bk_target:.1f}")
        print(f"  OBJ_total: {self.obj_total:.1f} ({self.obj_pct:.1f}%)")
        print(f"  S1={s1:.1f} | S2={s2:.1f} | S3={s3:.1f}")
        print(f"  💰 Première mise sur table: {table_stake:.1f}")
        print(f"  💼 Reste en poche: {self.bk_live:.1f}")
        print(f"  📊 BK totale (poche+table): {self.bk_live + self.bk_on_table:.1f}")
        print(f"{'='*60}\n")
        
        # DEBUG: Vérifier bk_on_table
        
        # Afficher la mise par douzaine à l'utilisateur
        self.current = self.from_float(display_stake)
        self.refresh_display()
        
        # DEBUG: Vérifier après refresh

    def next_stake(self):
        if not (0 <= self.cur_session < 3):
            return 0.0
        R = self.sessions[self.cur_session]
        if R <= 0:
            return 0.0
        return ceil_0_1(R / 3.0) if self.phase == 1 else ceil_0_1(R)

    def _update_impact(self):
        i = self.cur_session
        if not (0 <= i < 3) or self.bk_start <= 0:
            return False
        
        # Impact basé sur ce qui reste en POCHE (sans compter l'argent sur la table)
        current_impact = -((self.bk_start - self.bk_live) / self.bk_start * 100.0)
        
        # On garde le PIRE impact (le plus négatif)
        if current_impact < self.session_impact_pct[i]:
            self.session_impact_pct[i] = current_impact
            
            # AUSSI tracker dans all_session_impacts (session absolue)
            absolute_session_idx = self.session_offset + i
            if 0 <= absolute_session_idx < 10:
                self.all_session_impacts[absolute_session_idx] = current_impact
            
            # Vérifier si on doit diviser les pertes (mode 24N uniquement)
            division_effectuee = self._check_and_divide_losses()
            return division_effectuee
        
        return False

    def on_win(self):
        if not (0 <= self.cur_session < 3):
            return
        
        stake = self.to_float(self.current)
        R = self.sessions[self.cur_session]
        
        # DEBUG
        
        if stake <= 0 or R <= 0:
            return
        
        # Vérifier que la mise affichée correspond (en mode 24N, stake est par douzaine)
        expected_table = stake * 2 if self.num_mode == 24 else stake
        if abs(expected_table - self.bk_on_table) > 0.01:
            messagebox.showwarning("Attention", 
                f"La mise affichée ({self._fmt(stake)}) ne correspond pas à ce qui est sur la table ({self._fmt(self.bk_on_table)})!")
            return
        
        self.push_state()

        before_pocket = self.bk_live
        before_total = self.bk_live + self.bk_on_table
        
        # Calcul du gain basé sur la mise RÉELLE (bk_on_table)
        table_stake = self.bk_on_table
        
        if self.num_mode == 24:
            # Mode 24N : 2 douzaines, une seule gagne
            # Une douzaine rapporte 3× → récupère table_stake/2 × 3 = table_stake × 1.5
            # Gain = récupéré - mise = 1.5 × table_stake - table_stake = 0.5 × table_stake
            # MAIS il faut récupérer la mise d'abord, puis ajouter le gain
            # Total à ajouter = table_stake (mise récupérée) + 0.5 × table_stake (gain) = 1.5 × table_stake
            # NON! Une douzaine gagne (× 3 = 0.3), l'autre perd (-0.1)
            # Récupéré = 0.3, donc gain net = 0.3 - 0.2 = 0.1 = table_stake / 2
            # Mais on a déjà enlevé table_stake de la poche !
            # Donc il faut ajouter : mise + gain = table_stake + (table_stake/2) = 1.5 × table_stake
            won_amount = self._r01(self._r01(table_stake) * 1.5)
        else:
            # Mode 18N : simple chance, paiement 1:1
            # Code ORIGINAL: won_amount = stake × 2 (mise + gain)
            won_amount = self._r01(self._r01(table_stake) * 2)
        
        self.bk_live = self._r01(self._r01(self.bk_live) + self._r01(won_amount))
        
        self.bk_on_table = 0.0
        
        after_total = self.bk_live + self.bk_on_table

        # Ne PAS vérifier objectif ici - on le vérifie dans phase 1/2
        # (sinon on compte l'argent sur table qui n'est pas encore gagné)

        prepare_next = True  # Par défaut on prépare la mise suivante

        if self.phase == 1:
            if self.num_mode == 24:
                # Mode 24N : soustraire le GAIN NET (pas won_amount qui inclut la mise)
                gain_net = self._r01(table_stake / 2)
                remaining = round(max(0.0, R - gain_net), 1)
            else:
                # Mode 18N : logique originale (soustraire s1)
                s1 = ceil_0_1(R / 3.0)
                remaining = round(max(0.0, R - s1), 1)
            
            self.sessions[self.cur_session] = remaining
            self.all_sessions[self.session_offset + self.cur_session] = remaining
            
            # Si remaining = 0, traiter comme si c'était le coup 2 (session terminée)
            if remaining <= 0.0:
                self.sessions[self.cur_session] = 0.0
                self.all_sessions[self.session_offset + self.cur_session] = 0.0
                self.phase = 1
                self.history = "G (c1→c2)"
                
                # Vérifier objectif atteint AVANT de passer à session suivante
                # Compter BK totale = poche + argent sur table
                bk_totale_phase1 = self._r01(self._r01(self.bk_live) + self._r01(self.bk_on_table))
                objectif_atteint = bk_totale_phase1 >= self.bk_target if self.num_mode == 24 else False
                
                if objectif_atteint:
                    # Objectif atteint, session terminée
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 OBJECTIF ATTEINT! BK={bk_totale_phase1:.1f}€ ≥ {self.bk_target:.1f}€")
                    # Marquer toutes les sessions restantes comme WIN
                    for i in range(self.active_sessions_count):
                        self.all_sessions[i] = 0.0
                    for i in range(3):
                        self.sessions[i] = 0.0
                    self.refresh_display()
                    tout_win = True
                    prepare_next = False  # Ne pas préparer de mise suivante
                if self.num_mode == 24 and not objectif_atteint:
                    # Mode 24N : RECALCULER seulement si sessions supplémentaires actives
                    if remaining <= 0.0 and self.active_sessions_count > 3:
                        objectif_restant = max(0.1, self.bk_target - self.bk_live)
                        # Mode 24N paroli : gain = somme sessions
                        total_sessions_needed = objectif_restant
                        
                        sessions_non_win = []
                        for i in range(self.active_sessions_count):
                            if self.all_sessions[i] > 0:
                                sessions_non_win.append(i)
                        
                        num_restantes = len(sessions_non_win)
                        
                        if num_restantes > 0:
                            valeur_par_session = self._r01(total_sessions_needed / num_restantes)
                            
                            for i in sessions_non_win:
                                self.all_sessions[i] = valeur_par_session
                                if self.session_offset <= i < self.session_offset + 3:
                                    display_index = i - self.session_offset
                                    self.sessions[display_index] = valeur_par_session
                            
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Recalcul sessions: {num_restantes} sessions × {valeur_par_session:.1f}€ = {total_sessions_needed:.1f}€ pour atteindre {self.bk_target:.1f}€")
                    
                    # Mode 24N : chercher prochaine session non-WIN
                    next_found = False
                    
                    # Chercher dans la fenêtre actuelle
                    for i in range(3):
                        if i != self.cur_session and self.sessions[i] > 0:
                            self.cur_session = i
                            next_found = True
                            break
                    
                    # Si pas trouvé, scroller si possible
                    if not next_found and self.session_offset + 3 < self.active_sessions_count:
                        # Il y a des sessions après la fenêtre
                        self.session_offset += 1
                        self.sessions[0] = self.all_sessions[self.session_offset]
                        self.sessions[1] = self.all_sessions[self.session_offset + 1]
                        self.sessions[2] = self.all_sessions[self.session_offset + 2]
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📜 Scroll affichage → S{self.session_offset+1}-S{self.session_offset+2}-S{self.session_offset+3}")
                        
                        # Chercher première session > 0
                        for i in range(3):
                            if self.sessions[i] > 0:
                                self.cur_session = i
                                next_found = True
                                break
                    
                    if next_found:
                        self.session_initial_target = self.sessions[self.cur_session]
                        self.session_losses[self.cur_session] = 0.0
                        self.session_impact_pct[self.cur_session] = 0.0
                        display_num = self.session_offset + self.cur_session + 1
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Passage à S{display_num} | Objectif: {self.session_initial_target:.1f}")
                    else:
                        # Aucune session > 0 trouvée : recréer
                        objectif_restant = self.bk_target - self.bk_live
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Toutes sessions WIN - Recréation pour {objectif_restant:.1f}€")
                        
                        total_sessions = objectif_restant * 2.0
                        s1_val = self._r01(total_sessions / 3.0)
                        s2_val = self._r01(total_sessions / 3.0)
                        s3_val = self._r01(total_sessions - s1_val - s2_val)
                        
                        self.all_sessions[0] = s1_val
                        self.all_sessions[1] = s2_val
                        self.all_sessions[2] = s3_val
                        self.session_offset = 0
                        self.sessions[0] = s1_val
                        self.sessions[1] = s2_val
                        self.sessions[2] = s3_val
                        self.cur_session = 0
                        self.session_initial_target = s1_val
                        self.session_losses[0] = 0.0
                        self.session_impact_pct[0] = 0.0
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}]    → S1={s1_val:.1f} S2={s2_val:.1f} S3={s3_val:.1f}")
                        # prepare_next reste True pour préparer la première mise
                elif self.cur_session < 2 or (self.active_sessions_count > 3 and self.session_offset == 0 and self.sessions[0] == 0):
                    # Mode 18N : Passer à session suivante OU scroller si S1 WIN avec S4 active
                    # Mode 24N : Toujours passer à session suivante
                    
                    # RECALCUL pour mode 18N (même logique que mode 24N)
                    if self.num_mode == 18:
                        objectif_restant = max(0.1, self.bk_target - self.bk_live)
                        
                        sessions_non_win = []
                        for i in range(self.active_sessions_count):
                            if self.all_sessions[i] > 0:
                                sessions_non_win.append(i)
                        
                        num_restantes = len(sessions_non_win)
                        
                        if num_restantes > 0:
                            valeur_par_session = self._r01(objectif_restant / num_restantes)
                            
                            for i in sessions_non_win:
                                self.all_sessions[i] = valeur_par_session
                                if self.session_offset <= i < self.session_offset + 3:
                                    display_index = i - self.session_offset
                                    self.sessions[display_index] = valeur_par_session
                            
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Recalcul sessions: {num_restantes} sessions × {valeur_par_session:.1f}€ = {objectif_restant:.1f}€")
                    
                    # Chercher prochaine session non-WIN dans fenêtre actuelle
                    next_found = False
                    for i in range(self.cur_session + 1, 3):
                        if self.sessions[i] > 0:
                            self.cur_session = i
                            next_found = True
                            break
                    
                    # Si pas trouvé et S1 WIN avec sessions supplémentaires, scroller
                    if not next_found and self.session_offset == 0 and self.sessions[0] == 0 and self.active_sessions_count > 3:
                        self.session_offset = 1
                        self.sessions[0] = self.all_sessions[1]
                        self.sessions[1] = self.all_sessions[2]
                        self.sessions[2] = self.all_sessions[3]
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📜 Scroll affichage → S2-S3-S4")
                        
                        # Chercher première session > 0
                        for i in range(3):
                            if self.sessions[i] > 0:
                                self.cur_session = i
                                next_found = True
                                break
                    
                    if next_found:
                        self.session_initial_target = self.sessions[self.cur_session]
                        self.session_losses[self.cur_session] = 0.0
                        self.session_impact_pct[self.cur_session] = 0.0
                        display_num = self.session_offset + self.cur_session + 1
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Passage à S{display_num} | Objectif: {self.session_initial_target:.1f}")
                    
                    # Mode 24N : vérifier si on doit scroller l'affichage
                    if self.num_mode == 24 and self.session_offset > 0 and self.cur_session == 0:
                        # On revient à cur_session=0 après scroll, donc on doit avancer offset
                        self.session_offset += 1
                        if self.session_offset + 2 < self.active_sessions_count:
                            self.sessions[0] = self.all_sessions[self.session_offset]
                            self.sessions[1] = self.all_sessions[self.session_offset + 1]
                            self.sessions[2] = self.all_sessions[self.session_offset + 2]
                    
                    display_num = self.session_offset + self.cur_session + 1
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Passage à S{display_num} | Objectif: {self.session_initial_target:.1f}")
                    # prepare_next reste True pour préparer la première mise
                else:
                    # Session terminée
                    prepare_next = False  # Ne pas préparer de mise
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 SESSION COMPLÈTE!")
                    print(f"  BK finale: {self.bk_live:.1f} (départ: {self.bk_start:.1f})")
                    print(f"  Gain total: {self.obj_total:.1f}")
                    print(f"  Impacts: S1={self.all_session_impacts[0]:.1f}% | S2={self.all_session_impacts[1]:.1f}% | S3={self.all_session_impacts[2]:.1f}%")
                    
                    self.session_mode = False
                    self.kb_unlocked = True
                    self.combo.state(['!disabled'])
                    
                    # Rafraîchir l'affichage pour montrer S3 WIN
                    self.refresh_display()
                    
                    casino_name = self.casinos[self.cur_casino_idx]['name'] if self.cur_casino_idx is not None else "Inconnu"
                    duration = int(time.time() - self.session_start_ts) if self.session_start_ts else 0
                    # Impact total = le PIRE impact (le plus négatif)
                    total_impact = abs(min(self.session_impact_pct))
                    bk_finale_session = self.bk_live + self.bk_on_table  # Inclure argent sur table
                    obj_total_session = self.obj_total
                    bk_start_session = self.bk_start
                    obj_pct_session = self.obj_pct
                    
                    self._log_full_session()
                    
                    if self.last_session_casino_idx == self.cur_casino_idx:
                        self.consecutive_session_count += 1
                    else:
                        self.consecutive_session_count = 1
                        self.last_session_casino_idx = self.cur_casino_idx
                    
                    next_session_num = self.consecutive_session_count + 1
                    session_numbers = {
                        2: "deuxième", 3: "troisième", 4: "quatrième", 5: "cinquième",
                        6: "sixième", 7: "septième", 8: "huitième", 9: "neuvième", 10: "dixième"
                    }
                    session_text = session_numbers.get(next_session_num, f"{next_session_num}ème")
                    
                    dialog = tk.Toplevel(self)
                    dialog.title("Session terminée")
                    dialog.configure(bg="#f0f0f0")
                    dialog.resizable(False, False)
                    
                    try:
                        dialog.attributes("-topmost", True)
                    except Exception:
                        pass
                    
                    dialog.transient(self)
                    dialog.grab_set()
                    
                    content = tk.Frame(dialog, bg="#f0f0f0")
                    content.pack(padx=20, pady=20)
                    
                    msg_part1 = f"✅ SESSION TERMINÉE!\n\n" \
                               f"🎰 Casino: {casino_name}\n" \
                               f"⏱️ Durée: {fmt_time(duration)}\n" \
                               f"💰 BK départ: {bk_start_session:.1f}€\n" \
                               f"🎯 Objectif: {obj_total_session:.1f}€ ({obj_pct_session:.1f}%)\n" \
                               f"💼 BK finale: {bk_finale_session:.1f}€\n" \
                               f"📊 Gain: +{obj_total_session:.1f}€\n" \
                               f"💥 Impact total: {total_impact:.1f}%\n\n" \
                               f"Voulez-vous démarrer une "
                    
                    tk.Label(content, text=msg_part1, bg="#f0f0f0", 
                            font=("Segoe UI", 9), justify="left").pack()
                    
                    tk.Label(content, text=f"{session_text} session", bg="#f0f0f0",
                            font=("Segoe UI", 14, "bold italic")).pack()
                    
                    tk.Label(content, text=" avec cette bankroll ?", bg="#f0f0f0",
                            font=("Segoe UI", 9)).pack()
                    
                    btn_frame = tk.Frame(dialog, bg="#f0f0f0")
                    btn_frame.pack(pady=(0, 20))
                    
                    user_choice = [None]
                    
                    def on_yes():
                        user_choice[0] = True
                        dialog.destroy()
                    
                    def on_no():
                        user_choice[0] = False
                        dialog.destroy()
                    
                    tk.Button(btn_frame, text="Oui", width=10, command=on_yes,
                             default="active").pack(side="left", padx=5)
                    tk.Button(btn_frame, text="Non", width=10, command=on_no).pack(side="left", padx=5)
                    
                    dialog.update_idletasks()
                    w = dialog.winfo_reqwidth()
                    h = dialog.winfo_reqheight()
                    x = self.winfo_x() + (self.winfo_width() - w) // 2
                    y = self.winfo_y() + (self.winfo_height() - h) // 2
                    dialog.geometry(f"+{x}+{y}")
                    
                    self.wait_window(dialog)
                    
                    if user_choice[0]:
                        self.current = self.from_float(bk_finale_session)
                        self.refresh_display()
                        self.after(100, self.on_go)
                        return
                    else:
                        self.consecutive_session_count = 0
                        self.last_session_casino_idx = None
                        self.on_reset()
                        return
            else:
                # Normal: il reste de l'argent pour le coup 2
                self.phase = 2
                self.history = "G (c1)"
                # Pas de return ici, on continue pour préparer la mise suivante
        else:
            # Phase 2 : session actuelle WIN
            self.sessions[self.cur_session] = 0.0
            self.all_sessions[self.session_offset + self.cur_session] = 0.0
            self.phase = 1
            self.history = "G (c2)"
            
            # Vérifier si objectif atteint (prioritaire en mode 24N)
            # Compter BK totale = poche + argent sur table
            bk_totale = self._r01(self._r01(self.bk_live) + self._r01(self.bk_on_table))
            objectif_atteint = bk_totale >= self.bk_target
            
            if self.num_mode == 24:
                # Mode 24N : continuer tant que objectif pas atteint
                if objectif_atteint:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 OBJECTIF ATTEINT! BK={bk_totale:.1f}€ ≥ {self.bk_target:.1f}€")
                    # Marquer toutes les sessions restantes comme WIN
                    for i in range(self.active_sessions_count):
                        self.all_sessions[i] = 0.0
                    for i in range(3):
                        self.sessions[i] = 0.0
                    self.refresh_display()
                    tout_win = True
                    prepare_next = False  # Ne pas préparer de mise
                    # Continuer jusqu'au popup final (ligne 2440)
                else:
                    # RECALCULER seulement si sessions supplémentaires actives
                    if self.active_sessions_count > 3:
                        objectif_restant = max(0.1, self.bk_target - self.bk_live)
                        # Mode 24N paroli : gain = somme sessions
                        total_sessions_needed = objectif_restant
                        
                        sessions_non_win = []
                        for i in range(self.active_sessions_count):
                            if self.all_sessions[i] > 0:
                                sessions_non_win.append(i)
                        
                        num_restantes = len(sessions_non_win)
                        
                        if num_restantes > 0:
                            valeur_par_session = self._r01(total_sessions_needed / num_restantes)
                            
                            for i in sessions_non_win:
                                self.all_sessions[i] = valeur_par_session
                                if self.session_offset <= i < self.session_offset + 3:
                                    display_index = i - self.session_offset
                                    self.sessions[display_index] = valeur_par_session
                            
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Recalcul sessions: {num_restantes} sessions × {valeur_par_session:.1f}€ = {total_sessions_needed:.1f}€")
                    
                    # Objectif pas atteint
                    tout_win = False
            else:
                # Mode 18N : recalculer sessions restantes pour atteindre objectif exact
                objectif_atteint = self.bk_live >= self.bk_target
                
                if objectif_atteint:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 OBJECTIF ATTEINT! BK={self.bk_live:.1f}€ ≥ {self.bk_target:.1f}€")
                    # Marquer toutes les sessions restantes comme WIN
                    for i in range(self.active_sessions_count):
                        self.all_sessions[i] = 0.0
                    for i in range(3):
                        self.sessions[i] = 0.0
                    self.refresh_display()
                    tout_win = True
                    prepare_next = False  # Ne pas préparer de mise
                else:
                    # RECALCULER les sessions restantes pour atteindre l'objectif exact
                    objectif_restant = max(0.1, self.bk_target - self.bk_live)
                    
                    sessions_non_win = []
                    for i in range(self.active_sessions_count):
                        if self.all_sessions[i] > 0:
                            sessions_non_win.append(i)
                    
                    num_restantes = len(sessions_non_win)
                    
                    if num_restantes > 0:
                        valeur_par_session = self._r01(objectif_restant / num_restantes)
                        
                        for i in sessions_non_win:
                            self.all_sessions[i] = valeur_par_session
                            if self.session_offset <= i < self.session_offset + 3:
                                display_index = i - self.session_offset
                                self.sessions[display_index] = valeur_par_session
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Recalcul sessions: {num_restantes} sessions × {valeur_par_session:.1f}€ = {objectif_restant:.1f}€")
                    
                    # Vérifier si toutes les sessions actives sont WIN
                    sessions_restantes = [self.all_sessions[i] for i in range(self.active_sessions_count) if self.all_sessions[i] > 0]
                    tout_win = len(sessions_restantes) == 0
                
                if tout_win:
                    # Rafraîchir pour montrer toutes sessions WIN
                    self.refresh_display()
            
            if not tout_win:
                next_found = False
                
                # Si S1 WIN et sessions supplémentaires actives, scroller (18N et 24N)
                if self.session_offset == 0 and self.sessions[0] == 0 and self.active_sessions_count > 3:
                    # S1 est WIN, scroller vers S2-S3-S4
                    self.session_offset = 1
                    self.sessions[0] = self.all_sessions[1]
                    self.sessions[1] = self.all_sessions[2]
                    self.sessions[2] = self.all_sessions[3]
                    self.cur_session = 0  # Pointer vers S2 (première position affichée)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📜 Scroll affichage → S2-S3-S4")
                    
                    # Chercher première session non-WIN dans nouvelle fenêtre
                    for i in range(3):
                        if self.sessions[i] > 0:
                            self.cur_session = i
                            next_found = True
                            break
                else:
                    # Chercher session non-WIN normalement
                    # D'abord chercher APRÈS cur_session
                    for i in range(self.cur_session + 1, 3):
                        if self.sessions[i] > 0:
                            self.cur_session = i
                            next_found = True
                            break
                    
                    # Si pas trouvé, chercher AVANT cur_session (sessions qu'on a sautées)
                    if not next_found:
                        for i in range(self.cur_session):
                            if self.sessions[i] > 0:
                                self.cur_session = i
                                next_found = True
                                break
                    
                    # Si pas trouvé, essayer de scroller (18N et 24N)
                    if not next_found:
                        # Chercher la prochaine session non-WIN après la fenêtre
                        for i in range(self.session_offset + 3, self.active_sessions_count):
                            if self.all_sessions[i] > 0:
                                # Scroller jusqu'à cette session
                                self.session_offset = i - 2
                                self.sessions[0] = self.all_sessions[self.session_offset]
                                self.sessions[1] = self.all_sessions[self.session_offset + 1]
                                self.sessions[2] = self.all_sessions[self.session_offset + 2]
                                self.cur_session = 2
                                next_found = True
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📜 Scroll affichage → S{self.session_offset+1}-S{self.session_offset+2}-S{self.session_offset+3}")
                                break
                
                if next_found:
                    self.session_initial_target = self.sessions[self.cur_session]
                    self.session_losses[self.cur_session] = 0.0
                    self.session_impact_pct[self.cur_session] = 0.0
                    display_num = self.session_offset + self.cur_session + 1
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Passage à S{display_num} | Objectif: {self.session_initial_target:.1f}")
                else:
                    # Aucune session non-WIN trouvée
                    if self.num_mode == 24:
                        # Mode 24N : terminer (objectif proche ou atteint)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 Toutes sessions WIN - BK={self.bk_live:.1f}€")
                        tout_win = True
                    else:
                        # Mode 18N : arrêter
                        tout_win = True
            
            if tout_win:
                # SESSION TERMINÉE - ne pas préparer de mise
                prepare_next = False
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎉 SESSION COMPLÈTE!")
                print(f"  BK finale: {self.bk_live:.1f} (départ: {self.bk_start:.1f})")
                print(f"  Gain total: {self.obj_total:.1f}")
                print(f"  Impacts: S1={self.all_session_impacts[0]:.1f}% | S2={self.all_session_impacts[1]:.1f}% | S3={self.all_session_impacts[2]:.1f}%")
                
                self.session_mode = False
                self.kb_unlocked = True
                self.combo.state(['!disabled'])
                
                # Sauvegarder les valeurs AVANT _log_full_session pour l'affichage
                casino_name = self.casinos[self.cur_casino_idx]['name'] if self.cur_casino_idx is not None else "Inconnu"
                duration = int(time.time() - self.session_start_ts) if self.session_start_ts else 0
                total_impact = sum(abs(self.all_session_impacts[i]) for i in range(self.active_sessions_count))
                bk_finale_session = self.bk_live
                obj_total_session = self.obj_total
                bk_start_session = self.bk_start
                obj_pct_session = self.obj_pct
                
                # ⚠️ IMPORTANT : Enregistrer la session MAINTENANT
                self._log_full_session()
                
                # Incrémenter le compteur si c'est le même casino
                if self.last_session_casino_idx == self.cur_casino_idx:
                    self.consecutive_session_count += 1
                else:
                    self.consecutive_session_count = 1
                    self.last_session_casino_idx = self.cur_casino_idx
                
                # Numéro de la prochaine session (commence à 2)
                next_session_num = self.consecutive_session_count + 1
                
                # Texte pour le numéro : "deuxième", "troisième", "quatrième", etc.
                session_numbers = {
                    2: "deuxième", 3: "troisième", 4: "quatrième", 5: "cinquième",
                    6: "sixième", 7: "septième", 8: "huitième", 9: "neuvième", 10: "dixième"
                }
                session_text = session_numbers.get(next_session_num, f"{next_session_num}ème")
                
                # Créer une fenêtre identique au messagebox
                dialog = tk.Toplevel(self)
                dialog.title("Session terminée")
                dialog.configure(bg="#f0f0f0")
                dialog.resizable(False, False)
                
                try:
                    dialog.attributes("-topmost", True)
                except Exception:
                    pass
                
                # Bloquer l'interaction avec la fenêtre principale
                dialog.transient(self)
                dialog.grab_set()
                
                # Contenu principal
                content = tk.Frame(dialog, bg="#f0f0f0")
                content.pack(padx=20, pady=20)
                
                # Message texte normal - utiliser les valeurs sauvegardées
                msg_part1 = f"✅ SESSION TERMINÉE!\n\n" \
                           f"🎰 Casino: {casino_name}\n" \
                           f"⏱️ Durée: {fmt_time(duration)}\n" \
                           f"💰 BK départ: {bk_start_session:.1f}€\n" \
                           f"🎯 Objectif: {obj_total_session:.1f}€ ({obj_pct_session:.1f}%)\n" \
                           f"💼 BK finale: {bk_finale_session:.1f}€\n" \
                           f"📊 Gain: +{obj_total_session:.1f}€\n" \
                           f"💥 Impact total: {total_impact:.1f}%\n\n" \
                           f"Voulez-vous démarrer une "
                
                tk.Label(content, text=msg_part1, bg="#f0f0f0", 
                        font=("Segoe UI", 9), justify="left").pack()
                
                # TEXTE STYLISÉ : deuxième session en gras italique 14
                tk.Label(content, text=f"{session_text} session", bg="#f0f0f0",
                        font=("Segoe UI", 14, "bold italic")).pack()
                
                # Fin du message
                tk.Label(content, text=" avec cette bankroll ?", bg="#f0f0f0",
                        font=("Segoe UI", 9)).pack()
                
                # Boutons
                btn_frame = tk.Frame(dialog, bg="#f0f0f0")
                btn_frame.pack(pady=(0, 20))
                
                user_choice = [None]
                
                def on_yes():
                    user_choice[0] = True
                    dialog.destroy()
                
                def on_no():
                    user_choice[0] = False
                    dialog.destroy()
                
                tk.Button(btn_frame, text="Oui", width=10, command=on_yes,
                         default="active").pack(side="left", padx=5)
                tk.Button(btn_frame, text="Non", width=10, command=on_no).pack(side="left", padx=5)
                
                # Centrer et ajuster la taille automatiquement
                dialog.update_idletasks()
                w = dialog.winfo_reqwidth()
                h = dialog.winfo_reqheight()
                x = self.winfo_x() + (self.winfo_width() - w) // 2
                y = self.winfo_y() + (self.winfo_height() - h) // 2
                dialog.geometry(f"+{x}+{y}")
                
                # Attendre la réponse
                self.wait_window(dialog)
                
                # Traiter la réponse
                if user_choice[0]:
                    # Oui : Démarrer une nouvelle session avec la BK finale
                    self.current = self.from_float(bk_finale_session)
                    self.refresh_display()
                    self.after(100, self.on_go)
                    return
                else:
                    # Non : Reset complet
                    self.consecutive_session_count = 0
                    self.last_session_casino_idx = None
                    self.on_reset()
                    return

        if not prepare_next:
            # Ne pas préparer la mise, on a changé de session
            self.refresh_display()
            return

        next_stake = self.next_stake()
        display_stake, table_stake = self._prepare_stake(next_stake)
        
        # Capturer l'état AVANT de mettre la mise sur table
        after_pocket = self.bk_live
        after_total_before_stake = self.bk_live + self.bk_on_table
        
        if table_stake > self.bk_live:
            messagebox.showwarning("Attention", 
                f"Mise proposée ({self._fmt(display_stake)}) supérieure à la BK disponible ({self._fmt(self.bk_live)})!\n\n" +
                "Ajustement automatique à la BK restante.")
            table_stake = self.bk_live
            display_stake = table_stake / 2 if self.num_mode == 24 else table_stake
        
        self.bk_live = self._r01(self._r01(self.bk_live) - self._r01(table_stake))
        self.bk_on_table = self._r01(table_stake)
        
        self._update_impact()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ G | Poche: {before_pocket:.1f} → {after_pocket:.1f} | Total: {before_total:.1f} → {after_total:.1f}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💰 Nouvelle mise sur table: {table_stake:.1f} | Reste en poche: {self.bk_live:.1f} | Pertes: {self.session_losses[self.cur_session]:.1f} | Impact: {self.session_impact_pct[self.cur_session]:.2f}%")
        
        self.current = self.from_float(display_stake)
        self.refresh_display()

    def on_lose(self):
        if not (0 <= self.cur_session < 3):
            return
        
        stake = self.to_float(self.current)
        R = self.sessions[self.cur_session]
        
        if stake <= 0 or R <= 0:
            return
        
        # Vérifier que la mise affichée correspond (en mode 24N, stake est par douzaine)
        expected_table = stake * 2 if self.num_mode == 24 else stake
        if abs(expected_table - self.bk_on_table) > 0.01:
            messagebox.showwarning("Attention", 
                f"La mise affichée ({self._fmt(stake)}) ne correspond pas à ce qui est sur la table ({self._fmt(self.bk_on_table)})!")
            return
        
        self.push_state()

        before_pocket = self.bk_live
        before_total = self.bk_live + self.bk_on_table
        
        lost_amount = self.bk_on_table
        self.session_losses[self.cur_session] += lost_amount
        self.bk_on_table = 0.0
        
        after_total = self.bk_live + self.bk_on_table

        # Ajouter la perte RÉELLE à la session

        if self.phase == 1:
            # Phase 1 : ajouter toute la perte
            new_val = round(R + lost_amount, 1)
            self.sessions[self.cur_session] = new_val
            self.all_sessions[self.session_offset + self.cur_session] = new_val
            self.history = "P (c1)"
        else:
            # Phase 2 : ajouter toute la perte
            new_val = round(R + lost_amount, 1)
            self.sessions[self.cur_session] = new_val
            self.all_sessions[self.session_offset + self.cur_session] = new_val
            self.phase = 1
            self.history = "P (c2)"

        next_stake = self.next_stake()
        display_stake, table_stake = self._prepare_stake(next_stake)
        
        if table_stake > self.bk_live:
            messagebox.showerror("Bankroll insuffisante", 
                f"Mise requise: {self._fmt(display_stake)}\n" +
                f"BK disponible: {self._fmt(self.bk_live)}\n\n" +
                "Impossible de continuer. Veuillez ajuster votre stratégie ou arrêter la session.")
            table_stake = self.bk_live
            display_stake = table_stake / 2 if self.num_mode == 24 else table_stake
        
        self.bk_live = self._r01(self._r01(self.bk_live) - self._r01(table_stake))
        self.bk_on_table = self._r01(table_stake)
        
        division_effectuee = self._update_impact()
        
        # Si division effectuée, recalculer la mise avec les nouvelles valeurs
        if division_effectuee:
            # Récupérer l'argent de la table
            self.bk_live = self._r01(self.bk_live + self.bk_on_table)
            self.bk_on_table = 0.0
            
            # Recalculer avec nouvelle session
            next_stake_new = self.next_stake()
            display_stake, table_stake = self._prepare_stake(next_stake_new)
            
            if table_stake > self.bk_live:
                messagebox.showerror("Bankroll insuffisante", 
                    f"Mise requise: {self._fmt(display_stake)}\n" +
                    f"BK disponible: {self._fmt(self.bk_live)}\n\n" +
                    "Impossible de continuer. Veuillez ajuster votre stratégie ou arrêter la session.")
                table_stake = self.bk_live
                display_stake = table_stake / 2 if self.num_mode == 24 else table_stake
            
            self.bk_live = self._r01(self.bk_live - table_stake)
            self.bk_on_table = self._r01(table_stake)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ P | Poche: {before_pocket:.1f} (inchangée) | Total: {before_total:.1f} → {after_total:.1f} | Perte: {lost_amount:.1f}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💰 Nouvelle mise sur table: {self.bk_on_table:.1f} | Reste en poche: {self.bk_live:.1f} | Pertes: {self.session_losses[self.cur_session]:.1f} | Impact: {self.session_impact_pct[self.cur_session]:.2f}%")
        
        self.current = self.from_float(display_stake)
        self.refresh_display()

    def on_undo(self):
        if not self.state_stack:
            orig = self.btn_ret.cget("bg")
            self.btn_ret.config(bg="#aa4444")
            self.after(150, lambda: self.btn_ret.config(bg=orig))
            return
        
        snap = self.state_stack.pop()
        self.restore(snap)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ↶ UNDO")
        
        if getattr(self, 'stats_win', None) and self.stats_win.winfo_exists():
            self.stats_win.update_stats_ui()

    def on_reset(self):
        self.push_state()
        
        self.current = "0"
        self.acc = None
        self.pending_op = None
        self.just_evaluated = False
        self.history = ""

        self.bk_start = 0.0
        self.bk_live = 0.0
        self.bk_on_table = 0.0
        self.obj_total = 0.0
        self.bk_target = 0.0
        self.sessions = [0.0, 0.0, 0.0]
        self.all_sessions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.session_offset = 0
        self.cur_session = 0
        self.phase = 1

        self.session_mode = False
        self.kb_unlocked = True
        self.combo.state(['!disabled'])

        self.session_losses = [0.0, 0.0, 0.0]
        self.session_impact_pct = [0.0, 0.0, 0.0]
        self.all_session_impacts = [0.0] * 10  # Reset tous les impacts
        
        # Réinitialiser le compteur de sessions consécutives
        self.consecutive_session_count = 0
        self.last_session_casino_idx = None
        
        self.casino_var.set("⚠️ SÉLECTIONNER CASINO")
        self.cur_casino_idx = None
        self._update_combo_color()

        self._compact = False
        self.apply_mode_sizes()
        self.btn_go.config(state=tk.NORMAL, bg=ACCENT_BLUE, activebackground="#1E90FF")
        self.update_kb_lock_ui()
        self.refresh_display()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 RESET")

    def toggle_kb_lock(self):
        self.kb_unlocked = not self.kb_unlocked
        self.update_kb_lock_ui()
        self.refresh_display()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔐 Clavier {'déverrouillé' if self.kb_unlocked else 'verrouillé'}")

    def update_kb_lock_ui(self):
        self.btn_kb.config(bg=(VIOLET_UNLOCK if self.kb_unlocked else ACCENT_GREY))
        lock = (self.session_mode and not self.kb_unlocked)
        state = tk.DISABLED if lock else tk.NORMAL
        
        for b in self.digit_buttons:
            b.config(state=state)
        for b in self.op_buttons:
            b.config(state=state)
        self.btn_comma.config(state=state)
        self.btn_eq.config(state=state)

    def toggle_compact(self):
        self._compact = not self._compact
        self.apply_mode_sizes()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📱 Mode {'compact' if self._compact else 'complet'}")

    def toggle_num_mode(self):
        if self.session_mode:
            messagebox.showinfo("Mode verrouillé", "Le mode est verrouillé pendant la session.")
            return
        self.num_mode = 24 if self.num_mode == 18 else 18
        self.btn_stat.config(text=f"{self.num_mode}N")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 Mode {self.num_mode} numéros")

    def _prepare_stake(self, base_stake):
        """Prépare la mise : retourne (display_stake, table_stake)
        display_stake = ce qu'on affiche (mise par douzaine)
        table_stake = ce qu'on met sur table (× 2 en mode 24N)
        """
        display_stake = base_stake
        if self.num_mode == 24:
            table_stake = self._r01(base_stake * 2)
        else:
            table_stake = base_stake
        return display_stake, table_stake
    
    def _check_and_divide_losses(self):
        """Vérifie si un palier d'impact est atteint et divise les pertes si nécessaire.
        Modes 18N et 24N. Paliers: -2%, -4%, -6%, -8%, -10%...
        RÈGLE: Toujours diviser sur exactement 4 sessions.
        """
        # Trouver la pire session
        worst_impact = min(self.session_impact_pct)
        
        # Vérifier si on a atteint ou dépassé le prochain palier
        if worst_impact <= self.next_threshold:
            # Trouver quelle session a déclenché
            triggered_session = self.session_impact_pct.index(worst_impact)
            triggered_value = self.sessions[triggered_session]
            triggered_abs_index = self.session_offset + triggered_session
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔀 DIVISION PERTES: S{triggered_session+1} a atteint {worst_impact:.1f}% (seuil {self.next_threshold:.1f}%)")
            
            # Compter combien de sessions sont disponibles (session actuelle + sessions après)
            available_sessions = []
            for i in range(triggered_abs_index, self.active_sessions_count):
                available_sessions.append(i)
            
            num_available = len(available_sessions)
            
            # Créer des sessions supplémentaires pour atteindre 4 sessions
            sessions_needed = 4 - num_available
            if sessions_needed > 0:
                for _ in range(sessions_needed):
                    if self.active_sessions_count < 10:  # Max 10 sessions
                        self.active_sessions_count += 1
                        available_sessions.append(self.active_sessions_count - 1)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}]    → Activation S{self.active_sessions_count}")
            
            # Maintenant on a exactement 4 sessions (ou le max possible)
            num_sessions_for_division = len(available_sessions)
            
            # Diviser la valeur de la session déclenchée
            divided_amount = self._r01(triggered_value / num_sessions_for_division) if num_sessions_for_division > 0 else 0.1
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}]    → Division {triggered_value:.1f}€ ÷ {num_sessions_for_division} sessions = {divided_amount:.1f}€ par session")
            
            # Redistribuer sur les sessions disponibles
            for i in available_sessions:
                if i == triggered_abs_index:
                    # Session déclenchée: REMPLACER par la part
                    self.all_sessions[i] = divided_amount
                    if triggered_session < 3:
                        self.sessions[triggered_session] = divided_amount
                else:
                    # Autres sessions: AJOUTER la part (ou initialiser si nouvelle session)
                    if self.all_sessions[i] == 0.0:
                        # Nouvelle session créée
                        self.all_sessions[i] = divided_amount
                    else:
                        # Session existante
                        self.all_sessions[i] = self._r01(self.all_sessions[i] + divided_amount)
                    
                    # Mettre à jour sessions[] si dans la fenêtre affichée
                    if self.session_offset <= i < self.session_offset + 3:
                        display_index = i - self.session_offset
                        self.sessions[display_index] = self.all_sessions[i]
            
            # Préparer le prochain palier (-2% → -4% → -6%...)
            self.next_threshold -= 2.0
            print(f"[{datetime.now().strftime('%H:%M:%S')}]    → Prochain palier: {self.next_threshold:.1f}%")
            
            return True
        
        return False  # Pas de division

    def handle_key(self, event):
        ch = (event.char or "").lower()
        
        def locked(): 
            return (self.session_mode and not self.kb_unlocked)
        
        if ch.isdigit():
            if locked(): return
            self.on_digit(ch)
        elif ch in (".", ","):
            if locked(): return
            self.on_comma()
        elif ch in ("+", "-", "*", "/"):
            if locked(): return
            self.on_op(ch if ch != "*" else "×")
        elif ch == "=" or event.keysym in ("Return", "KP_Enter"):
            if locked(): return
            self.on_equal()
        elif ch == "g":
            self.on_win()
        elif ch == "p":
            self.on_lose()
        elif ch == "r":
            self.on_reset()
        elif ch == "o":
            self.on_go()
        elif ch == "k":
            self.toggle_kb_lock()
        elif ch == "z":
            self.on_undo()
        elif ch == "s":
            self.open_stats()
        elif ch == "c":
            self.toggle_compact()


    def _show_session_complete_dialog(self, casino_name, duration, total_impact, bk_finale, obj_total, bk_start, obj_pct):
        """Affiche le popup de session terminée"""
        next_session_num = self.consecutive_session_count + 1
        session_numbers = {
            2: "deuxième", 3: "troisième", 4: "quatrième", 5: "cinquième",
            6: "sixième", 7: "septième", 8: "huitième", 9: "neuvième", 10: "dixième"
        }
        session_text = session_numbers.get(next_session_num, f"{next_session_num}ème")
        
        dialog = tk.Toplevel(self)
        dialog.title("Session terminée")
        dialog.configure(bg="#f0f0f0")
        dialog.resizable(False, False)
        
        try:
            dialog.attributes("-topmost", True)
        except Exception:
            pass
        
        dialog.transient(self)
        dialog.grab_set()
        
        content = tk.Frame(dialog, bg="#f0f0f0")
        content.pack(padx=20, pady=20)
        
        msg = f"✅ SESSION TERMINÉE!\n\n🎰 Casino: {casino_name}\n⏱️ Durée: {fmt_time(duration)}\n💰 BK départ: {bk_start:.1f}€\n🎯 Objectif: {obj_total:.1f}€ ({obj_pct:.1f}%)\n💼 BK finale: {bk_finale:.1f}€\n📊 Gain: +{obj_total:.1f}€\n💥 Impact total: {total_impact:.1f}%\n\nVoulez-vous démarrer une "
        
        tk.Label(content, text=msg, bg="#f0f0f0", font=("Segoe UI", 9), justify="left").pack()
        tk.Label(content, text=f"{session_text} session", bg="#f0f0f0", font=("Segoe UI", 14, "bold italic")).pack()
        tk.Label(content, text=" avec cette bankroll ?", bg="#f0f0f0", font=("Segoe UI", 9)).pack()
        
        btn_frame = tk.Frame(dialog, bg="#f0f0f0")
        btn_frame.pack(pady=(0, 20))
        
        user_choice = [None]
        
        def on_yes():
            user_choice[0] = True
            dialog.destroy()
        
        def on_no():
            user_choice[0] = False
            dialog.destroy()
        
        tk.Button(btn_frame, text="Oui", width=10, command=on_yes, default="active").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Non", width=10, command=on_no).pack(side="left", padx=5)
        
        dialog.update_idletasks()
        w = dialog.winfo_reqwidth()
        h = dialog.winfo_reqheight()
        x = self.winfo_x() + (self.winfo_width() - w) // 2
        y = self.winfo_y() + (self.winfo_height() - h) // 2
        dialog.geometry(f"+{x}+{y}")
        
        self.wait_window(dialog)
        
        if user_choice[0]:
            self.current = self.from_float(bk_finale)
            self.refresh_display()
            self.on_go()
def main():
    try:
        print(f"\n{'='*60}")
        print(f"Calculatrice Casino v{APP_VERSION}")
        print(f"{'='*60}\n")
        
        app = Calculator()
        app.mainloop()
        
    except Exception as e:
        crash_log = os.path.join(os.path.dirname(__file__), "calc_crash.log")
        try:
            with open(crash_log, "a", encoding="utf-8") as f:
                import traceback
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"\n{'='*60}\n")
                f.write(f"[{timestamp}] CRASH v{APP_VERSION}\n")
                f.write(f"{'='*60}\n")
                f.write(f"Erreur: {e}\n\n")
                f.write(traceback.format_exc())
                f.write(f"{'='*60}\n")
            print(f"\n❌ Erreur fatale enregistrée dans: {crash_log}")
        except Exception:
            pass
        
        try:
            messagebox.showerror("Erreur fatale", f"Une erreur s'est produite:\n\n{e}")
        except Exception:
            print(f"\n❌ Erreur fatale: {e}")


if __name__ == "__main__":
    main()

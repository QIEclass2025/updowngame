import random
import tkinter as tk
from tkinter import messagebox, Toplevel, Label, Entry, Button, ttk, Canvas
import urllib.request
import urllib.error
import json
import threading
import ssl
import os
import platform 
from datetime import datetime
from io import BytesIO

# PIL 라이브러리 확인 및 임포트
try:
    from PIL import Image, ImageTk
except ImportError:
    import tkinter.messagebox as msgbox
    msgbox.showerror("오류", "Pillow 라이브러리가 필요합니다.\n설치 후 다시 실행해주세요.\n(pip install pillow)")
    exit()

class PokedexGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("포켓몬 도감 (서바이벌 모드)")
        self.geometry("500x900") 
        self.resizable(False, False)
        
        # 운영체제별 폰트 설정
        system_os = platform.system()
        if system_os == "Darwin": # macOS
            self.FONT_FAMILY = "AppleGothic"
        else: # Windows 및 기타
            self.FONT_FAMILY = "Malgun Gothic"

        # 디자인 컬러
        self.COLOR_BODY = "#DC0A2D"       # 도감 빨강
        self.COLOR_HINGE = "#8B0000"      # 힌지
        self.COLOR_BEZEL = "#222222"      # 베젤
        self.COLOR_TOP_BG = "#232323"     # 상단 화면 (어두움)
        self.COLOR_BOTTOM_BG = "#F8F8F8"  # 하단 화면 (밝음)
        self.COLOR_TEXT_BOX = "#FFFFFF"   # 텍스트 박스 배경
        self.COLOR_LENS_BLUE = "#1E90FF"
        
        # 배틀 메뉴 버튼 색상
        self.BTN_FIGHT = "#FF3333"  # 추측
        self.BTN_BAG = "#FFCC00"    # 가방
        self.BTN_PKMN = "#44BB00"   # 기록
        self.BTN_RUN = "#3399FF"    # 도망
        
        # 폰트 변수 설정
        self.FONT_BOLD = (self.FONT_FAMILY, 12, "bold")
        self.FONT_NORMAL = (self.FONT_FAMILY, 10)
        self.FONT_SMALL = (self.FONT_FAMILY, 9)
        
        # 기록 저장 파일명
        self.HISTORY_FILE = "pokedex_adventure_log.json"
        
        self.configure(bg=self.COLOR_BODY)

        # 세대별 도감 범위
        self.generations = {
            "1세대: 관동 (1~151)": (1, 151),
            "2세대: 성도 (152~251)": (152, 251),
            "3세대: 호연 (252~386)": (252, 386),
            "4세대: 신오 (387~493)": (387, 493),
            "5세대: 하나 (494~649)": (494, 649),
            "6세대: 칼로스 (650~721)": (650, 721),
            "7세대: 알로라 (722~809)": (722, 809),
            "8세대: 가라르 (810~905)": (810, 905),
            "9세대: 팔데아 (906~1025)": (906, 1025),
            "직접 설정": (1, 1025)
        }

        # 게임 변수
        self.min_num = 1
        self.max_num = 151
        self.current_min = 1
        self.current_max = 151
        self.secret_number = 0
        self.attempts = 0
        self.max_lives = 7 
        self.current_lives = 7
        self.current_image = None 
        self.menu_image = None 
        self.target_name_kor = "알 수 없음"
        self.current_gen_name = "1세대: 관동"
        
        # 아이템 관련 변수
        self.buff_x_attack = False 
        self.buff_x_attack_turns = 0
        self.item_used_turn = False 
        self.item_images = {}
        self.inventory = {}
        self.used_items_log = [] 
        
        self.guess_history = [] 
        self.warning_flash_job = None
        
        # 윈도우 관리 변수
        self.log_window = None 

        # 타입 한글 변환
        self.type_map = {
            "normal": "노말", "fire": "불꽃", "water": "물", "grass": "풀",
            "electric": "전기", "ice": "얼음", "fighting": "격투", "poison": "독",
            "ground": "땅", "flying": "비행", "psychic": "에스퍼", "bug": "벌레",
            "rock": "바위", "ghost": "고스트", "dragon": "드래곤", "steel": "강철",
            "dark": "악", "fairy": "페어리", "stellar": "스텔라"
        }

        self._create_header_lens()
        self.menu_frame = tk.Frame(self, bg=self.COLOR_BODY)
        self._create_menu_widgets()
        self.game_frame = tk.Frame(self, bg=self.COLOR_BODY)
        self._create_game_widgets()

        self.menu_frame.pack(expand=True, fill='both', padx=20, pady=10)
        
        # 앱 시작 시 메인 화면 랜덤 포켓몬 로드
        threading.Thread(target=self._load_random_menu_sprite, daemon=True).start()

    def _create_header_lens(self):
        header = Canvas(self, width=500, height=60, bg=self.COLOR_BODY, highlightthickness=0)
        header.pack(side="top", fill="x")
        header.create_oval(20, 10, 70, 60, fill="white", outline="black", width=2)
        header.create_oval(25, 15, 65, 55, fill=self.COLOR_LENS_BLUE, outline="")
        header.create_oval(30, 20, 45, 35, fill="#87CEFA", outline="")
        colors = ["#FF0000", "#FFFF00", "#00FF00"]
        start_x = 85
        for c in colors:
            header.create_oval(start_x, 15, start_x+15, 30, fill=c, outline="black")
            start_x += 25
        header.create_line(0, 58, 500, 58, fill="#800000", width=3)

    def _create_menu_widgets(self):
        # 상단 스크린
        top_bezel = tk.Frame(self.menu_frame, bg=self.COLOR_BEZEL, padx=10, pady=10, bd=3, relief="sunken")
        top_bezel.pack(fill="x", pady=(10, 10))
        
        self.menu_top_screen = tk.Frame(top_bezel, bg=self.COLOR_TOP_BG)
        self.menu_top_screen.pack(fill="x") 
        
        Label(self.menu_top_screen, text="포켓몬 도감", font=(self.FONT_FAMILY, 32, "bold"), bg=self.COLOR_TOP_BG, fg="white").pack(pady=(20, 0))
        
        self.menu_img_label = Label(self.menu_top_screen, bg=self.COLOR_TOP_BG)
        self.menu_img_label.pack(expand=True, pady=10)
        
        Label(self.menu_top_screen, text="타겟 탐색 시스템", font=(self.FONT_FAMILY, 14, "bold"), bg=self.COLOR_TOP_BG, fg="#00FF00").pack(side="bottom", pady=10)
        
        # 힌지
        hinge = tk.Frame(self.menu_frame, bg=self.COLOR_HINGE, height=25, bd=2, relief="ridge")
        hinge.pack(fill="x", pady=5)
        
        # 하단 스크린
        bottom_bezel = tk.Frame(self.menu_frame, bg=self.COLOR_BEZEL, padx=10, pady=10, bd=3, relief="sunken")
        bottom_bezel.pack(fill="both", expand=True, pady=(10, 0))
        bottom_screen = tk.Frame(bottom_bezel, bg=self.COLOR_BOTTOM_BG)
        bottom_screen.pack(fill="both", expand=True)
        
        deco_frame = tk.Frame(bottom_screen, bg="#E0E0E0", bd=2, relief="groove", padx=10, pady=10)
        deco_frame.pack(fill="both", expand=True, padx=20, pady=20)

        Label(deco_frame, text="[ 탐색 지역 선택 ]", font=self.FONT_BOLD, bg="#E0E0E0").pack(pady=(10, 5))
        
        self.gen_var = tk.StringVar()
        self.gen_combo = ttk.Combobox(deco_frame, textvariable=self.gen_var, state="readonly", font=self.FONT_NORMAL, width=25)
        self.gen_combo['values'] = list(self.generations.keys())
        self.gen_combo.current(0)
        self.gen_combo.pack(pady=5)
        self.gen_combo.bind("<<ComboboxSelected>>", self._on_gen_selected)

        self.range_label = Label(deco_frame, text="범위: 1 ~ 151", font=("Arial", 12, "bold"), bg="#E0E0E0", fg="#333")
        self.range_label.pack(pady=5)

        notice = tk.Frame(deco_frame, bg="#E0F7FA", bd=1, relief="solid", padx=5, pady=5)
        notice.pack(pady=10, fill="x")
        Label(notice, text="※ 트레이너 지침 ※", font=(self.FONT_FAMILY, 9, "bold"), bg="#E0F7FA", fg="#D32F2F").pack()
        Label(notice, text="아이템 사용 시에도 턴이 소모됩니다.\n신중하게 전략을 세우세요!", font=(self.FONT_FAMILY, 8), bg="#E0F7FA").pack()

        btn_frame = tk.Frame(deco_frame, bg="#E0E0E0")
        btn_frame.pack(side="bottom", pady=10, fill="x")

        Button(btn_frame, text="📜 모험 기록", font=(self.FONT_FAMILY, 11, "bold"), bg="#FF9800", fg="white", relief="raised", bd=3, command=self.open_adventure_log).pack(side="left", expand=True, padx=5, fill="x")
        Button(btn_frame, text="탐색 개시!", font=(self.FONT_FAMILY, 11, "bold"), bg="#2196F3", fg="white", relief="raised", bd=3, command=self.start_game).pack(side="right", expand=True, padx=5, fill="x")

    def _load_random_menu_sprite(self):
        try:
            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            rand_id = random.randint(1, 1000)
            url = f"https://pokeapi.co/api/v2/pokemon/{rand_id}"
            with urllib.request.urlopen(url, context=ctx, timeout=5) as r:
                d = json.loads(r.read().decode())
                img_url = d['sprites']['front_default']
            
            if img_url:
                with urllib.request.urlopen(img_url, context=ctx, timeout=5) as r:
                    raw_data = r.read()
                    pil_img = Image.open(BytesIO(raw_data)).resize((120, 120), Image.NEAREST)
                    self.menu_image = ImageTk.PhotoImage(pil_img)
                    self.after_idle(lambda: self.menu_img_label.config(image=self.menu_image))
        except: pass

    def _create_game_widgets(self):
        top_bezel = tk.Frame(self.game_frame, bg=self.COLOR_BEZEL, padx=10, pady=10, bd=3, relief="sunken")
        top_bezel.pack(fill="x", padx=10, pady=(10, 5))
        
        self.top_screen = tk.Frame(top_bezel, bg=self.COLOR_TOP_BG)
        self.top_screen.pack(fill="x")

        self.hp_label = Label(self.top_screen, text="몬스터볼: ◎◎◎◎◎◎◎", font=(self.FONT_FAMILY, 14, "bold"), bg=self.COLOR_TOP_BG, fg="#FF5555")
        self.hp_label.pack(pady=(10, 5))

        self.basic_info_label = Label(self.top_screen, text="타겟 포착 중...", font=(self.FONT_FAMILY, 16, "bold"), bg=self.COLOR_TOP_BG, fg="white")
        self.basic_info_label.pack()
        
        self.img_label = Label(self.top_screen, bg=self.COLOR_TOP_BG)
        self.img_label.pack(expand=True, pady=10)

        hinge = tk.Frame(self.game_frame, bg=self.COLOR_HINGE, height=25, bd=2, relief="ridge")
        hinge.pack(fill="x", padx=5, pady=5)

        bottom_bezel = tk.Frame(self.game_frame, bg=self.COLOR_BEZEL, padx=10, pady=10, bd=3, relief="sunken")
        bottom_bezel.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        self.bottom_screen_container = tk.Frame(bottom_bezel, bg=self.COLOR_BOTTOM_BG)
        self.bottom_screen_container.pack(fill="both", expand=True)

        self.play_mode_frame = tk.Frame(self.bottom_screen_container, bg=self.COLOR_BOTTOM_BG)
        self.play_mode_frame.pack(fill="both", expand=True)

        dialog_frame = tk.Frame(self.play_mode_frame, bg=self.COLOR_TEXT_BOX, bd=2, relief="solid", padx=10, pady=10)
        dialog_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.stats_label = Label(dialog_frame, text="", font=self.FONT_SMALL, bg=self.COLOR_TEXT_BOX, fg="#555", justify="left")
        self.stats_label.pack(anchor="w")
        
        self.desc_label = Label(dialog_frame, text="아생의 포켓몬이 튀어나왔다!", font=self.FONT_NORMAL, bg=self.COLOR_TEXT_BOX, justify="left", wraplength=400, height=5, anchor="nw")
        self.desc_label.pack(fill="both", expand=True, pady=(5,0))

        control_frame = tk.Frame(self.play_mode_frame, bg=self.COLOR_BOTTOM_BG)
        control_frame.pack(fill="x", padx=15, pady=5)
        
        self.game_range_label = Label(control_frame, text="범위: 1 ~ 151", font=("Arial", 11, "bold"), bg=self.COLOR_BOTTOM_BG, fg="#2E7D32")
        self.game_range_label.pack(pady=5)
        
        input_sub_frame = tk.Frame(control_frame, bg=self.COLOR_BOTTOM_BG)
        input_sub_frame.pack()
        Label(input_sub_frame, text="No.", font=("Arial", 12, "bold"), bg=self.COLOR_BOTTOM_BG).pack(side="left")
        self.guess_entry = Entry(input_sub_frame, font=("Arial", 16), width=6, justify='center', bd=2, relief="sunken")
        self.guess_entry.pack(side="left", padx=5)
        self.guess_entry.bind("<Return>", self._check_guess_event)

        battle_menu = tk.Frame(self.play_mode_frame, bg="#404040", bd=3, relief="raised")
        battle_menu.pack(side="bottom", fill="x", padx=10, pady=10)
        battle_menu.columnconfigure(0, weight=1); battle_menu.columnconfigure(1, weight=1)
        
        btn_opts = {'font': self.FONT_BOLD, 'relief': 'raised', 'bd': 3, 'height': 2, 'fg': 'white'}
        
        Button(battle_menu, text="⚔ 몬스터볼 (추측)", bg=self.BTN_FIGHT, command=self._check_guess, **btn_opts).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        Button(battle_menu, text="🎒 가방 (도구)", bg=self.BTN_BAG, command=self.open_bag_menu, **btn_opts).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        Button(battle_menu, text="📝 포켓몬 (기록)", bg=self.BTN_PKMN, command=self.open_history_menu, **btn_opts).grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        Button(battle_menu, text="🏃 도망친다", bg=self.BTN_RUN, command=self.confirm_run_away, **btn_opts).grid(row=1, column=1, sticky="nsew", padx=2, pady=2)

        self.bag_mode_frame = tk.Frame(self.bottom_screen_container, bg=self.COLOR_BOTTOM_BG)
        Label(self.bag_mode_frame, text="[ 도구 주머니 ]", font=self.FONT_BOLD, bg=self.COLOR_BOTTOM_BG).pack(pady=10)
        self.bag_status_label = Label(self.bag_mode_frame, text="", font=self.FONT_NORMAL, bg=self.COLOR_BOTTOM_BG)
        self.bag_status_label.pack()
        self.bag_contents_frame = tk.Frame(self.bag_mode_frame, bg=self.COLOR_BOTTOM_BG)
        self.bag_contents_frame.pack(fill="both", expand=True, padx=10, pady=10)
        Button(self.bag_mode_frame, text="✖ 닫기", font=self.FONT_NORMAL, command=self.close_bag_menu).pack(side="bottom", pady=20)

        self.history_mode_frame = tk.Frame(self.bottom_screen_container, bg=self.COLOR_BOTTOM_BG)
        # 히스토리 프레임 내용은 open_history_menu에서 동적 생성

    def _on_gen_selected(self, event):
        selected = self.gen_var.get()
        min_val, max_val = self.generations[selected]
        if selected == "직접 설정": 
            self.current_gen_name = "사용자 설정"
            self._open_custom_range()
        else:
            self.current_gen_name = selected
            self.min_num, self.max_num = min_val, max_val
            self.range_label.config(text=f"범위: {self.min_num} ~ {self.max_num}")

    def show_menu(self):
        self.game_frame.pack_forget()
        self.menu_frame.pack(expand=True, fill='both', padx=20, pady=20)
        threading.Thread(target=self._load_random_menu_sprite, daemon=True).start()

    def start_game(self):
        self.secret_number = random.randint(self.min_num, self.max_num)
        self.attempts = 0
        self.current_lives = self.max_lives
        self.current_min = self.min_num
        self.current_max = self.max_num
        self.buff_x_attack = False
        self.buff_x_attack_turns = 0 
        self.item_used_turn = False
        self.guess_history = []
        self.used_items_log = [] 
        self.target_name_kor = "???"
        self.inventory = {"scope-lens": 1, "x-attack": 1, "sitrus-berry": 1}
        
        self._cancel_warning_flash() 
        self._update_lives_ui()
        self.game_range_label.config(text=f"범위: {self.current_min} ~ {self.current_max}")
        self.basic_info_label.config(text="타겟 포착 중...", fg="white")
        self.stats_label.config(text="")
        self.desc_label.config(text="야생의 포켓몬이 튀어나왔다!\n도감 번호를 맞춰서 잡아야 한다!\n(숫자 입력 후 '몬스터볼' 버튼 클릭)")
        self.img_label.config(image='')
        self.current_image = None
        self.guess_entry.delete(0, tk.END)
        
        self.bag_mode_frame.pack_forget()
        self.history_mode_frame.pack_forget()
        self.play_mode_frame.pack(fill="both", expand=True)
        self.menu_frame.pack_forget()
        self.game_frame.pack(expand=True, fill='both')
        self.guess_entry.focus_set()
        
        threading.Thread(target=self._load_item_icons, daemon=True).start()
        threading.Thread(target=self._fetch_target_name_hidden, args=(self.secret_number,), daemon=True).start()

    def _fetch_target_name_hidden(self, number):
        try:
            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            url = f"https://pokeapi.co/api/v2/pokemon-species/{number}"
            with urllib.request.urlopen(url, context=ctx, timeout=5) as r:
                d = json.loads(r.read().decode())
                for n in d['names']:
                    if n['language']['name'] == 'ko':
                        self.target_name_kor = n['name']
                        break
        except: pass

    def _update_lives_ui(self):
        balls = "◎" * self.current_lives
        empty = "○" * (self.max_lives - self.current_lives)
        self.hp_label.config(text=f"몬스터볼: {balls}{empty}")
        if self.current_lives == 1: self._start_warning_flash()
        else:
            self._cancel_warning_flash()
            if self.current_lives <= 2: self.hp_label.config(fg="red")
            else: self.hp_label.config(fg="#FF5555")

    def _start_warning_flash(self):
        if self.warning_flash_job: return 
        def flash():
            current_color = self.hp_label.cget("fg")
            next_color = "white" if current_color == "red" else "red"
            self.hp_label.config(fg=next_color)
            self.warning_flash_job = self.after(300, flash) 
        flash()

    def _cancel_warning_flash(self):
        if self.warning_flash_job:
            self.after_cancel(self.warning_flash_job)
            self.warning_flash_job = None

    def confirm_run_away(self):
        if messagebox.askyesno("도망", "배틀에서 도망치시겠습니까?"): 
            self.save_record("도망") # [수정] 도망 시 기록 저장
            self.show_menu()

    def open_history_menu(self):
        self.play_mode_frame.pack_forget()
        self.history_mode_frame.pack(fill="both", expand=True)
        
        for widget in self.history_mode_frame.winfo_children():
            widget.destroy()
            
        Label(self.history_mode_frame, text="[ 배틀 로그 ]", font=self.FONT_BOLD, bg=self.COLOR_BOTTOM_BG).pack(pady=5)
        
        list_frame = tk.Frame(self.history_mode_frame, bg=self.COLOR_BOTTOM_BG)
        list_frame.pack(fill="both", expand=True, padx=10)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Ingame.Treeview", background="white", fieldbackground="white", font=("Malgun Gothic", 10), rowheight=25)
        style.configure("Ingame.Treeview.Heading", font=("Malgun Gothic", 10, "bold"), background="#ddd")

        tree = ttk.Treeview(list_frame, columns=("turn", "guess", "result"), show="headings", style="Ingame.Treeview")
        tree.heading("turn", text="순서"); tree.column("turn", width=40, anchor="center")
        tree.heading("guess", text="입력"); tree.column("guess", width=60, anchor="center")
        tree.heading("result", text="판정"); tree.column("result", width=150, anchor="w")
        
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        if not self.guess_history:
            tree.insert("", "end", values=("-", "-", "기록 없음"))
        else:
            for i, (num, result) in enumerate(self.guess_history, 1):
                tree.insert("", "end", values=(i, num, result))
                
        Button(self.history_mode_frame, text="✖ 닫기", font=self.FONT_NORMAL, command=self.close_history_menu).pack(pady=10)

    def close_history_menu(self):
        self.history_mode_frame.pack_forget()
        self.play_mode_frame.pack(fill="both", expand=True)
        self.guess_entry.focus_set()

    def open_bag_menu(self):
        self.play_mode_frame.pack_forget()
        self.bag_mode_frame.pack(fill="both", expand=True)
        for w in self.bag_contents_frame.winfo_children(): w.destroy()
        
        can_use = not self.item_used_turn
        state = "normal" if can_use else "disabled"
        msg = "어떤 도구를 사용할까? (턴 소모)" if can_use else "도구는 이미 사용했다!"
        self.bag_status_label.config(text=msg, fg="blue" if can_use else "red")
        
        self._create_item_btn("scope-lens", "🎯 스코프렌즈", "범위를 절반으로 줄인다.", "#FF9800", state)
        self._create_item_btn("x-attack", "💪 플러스파워", "3턴 동안 범위 압축률이 상승한다.", "#E91E63", state) 
        self._create_item_btn("sitrus-berry", "🍊 자뭉열매", "몬스터볼을 3개 회복한다. (최대치 초과 불가)", "#4CAF50", state) 

    def _create_item_btn(self, key, name, desc, bg, state):
        img = self.item_images.get(key)
        btn = Button(self.bag_contents_frame, text=f" {name}\n {desc}", font=self.FONT_NORMAL, bg=bg, fg="white", relief="raised", bd=3, justify="left", state=state, command=lambda: self.use_item(key, name))
        if img: btn.config(image=img, compound="left", padx=10)
        btn.pack(fill="x", pady=5, ipady=5)

    def _load_item_icons(self):
        items = ["scope-lens", "x-attack", "sitrus-berry"]
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        for item in items:
            if item in self.item_images: continue
            try:
                with urllib.request.urlopen(f"https://pokeapi.co/api/v2/item/{item}", context=ctx, timeout=5) as r:
                    d = json.loads(r.read().decode())
                    url = d['sprites']['default']
                if url:
                    with urllib.request.urlopen(url, context=ctx, timeout=5) as r:
                        img = ImageTk.PhotoImage(Image.open(BytesIO(r.read())).resize((40, 40), Image.NEAREST))
                        self.item_images[item] = img
            except: pass

    def use_item(self, key, item_name_display):
        if self.item_used_turn: return
        self.item_used_turn = True
        self.current_lives -= 1 
        
        clean_name = item_name_display.split(" ")[1] 
        self.used_items_log.append(clean_name)

        log = ""
        if key == "scope-lens":
            dist = max(1, (self.current_max - self.current_min) // 4)
            self.current_min = max(self.current_min, self.secret_number - dist)
            self.current_max = min(self.current_max, self.secret_number + dist)
            log = "스코프렌즈를 사용했다!\n초점이 맞춰져 범위가 대폭 줄어들었다!"
        elif key == "x-attack":
            self.buff_x_attack = True
            self.buff_x_attack_turns = 3 
            log = "플러스파워를 사용했다!\n3턴 동안 공격력이 크게 상승한다!"
        elif key == "sitrus-berry":
            self.current_lives = min(self.max_lives, self.current_lives + 3) 
            log = "자뭉열매를 사용했다!\n몬스터볼 개수가 회복되었다!"
            
        self._update_lives_ui()
        self.game_range_label.config(text=f"범위: {self.current_min} ~ {self.current_max}")
        self.close_bag_menu()
        self.desc_label.config(text=f"{log}\n(몬스터볼 1개 소모)")
        if self.current_lives <= 0: self.game_over()

    def close_bag_menu(self):
        self.bag_mode_frame.pack_forget()
        self.play_mode_frame.pack(fill="both", expand=True)
        self.guess_entry.focus_set()

    def game_over(self):
        self.save_record("실패") # [수정] 실패 시 기록 저장
        self._start_fade_out()

    def _start_fade_out(self):
        self.fade_window = Toplevel(self)
        self.fade_window.overrideredirect(True) 
        x = self.winfo_rootx(); y = self.winfo_rooty()
        w = self.winfo_width(); h = self.winfo_height()
        self.fade_window.geometry(f"{w}x{h}+{x}+{y}")
        self.fade_window.configure(bg="black")
        self.fade_window.attributes("-alpha", 0.0) 
        self._animate_fade(0.0)

    def _animate_fade(self, alpha):
        if alpha < 1.0:
            alpha += 0.05
            self.fade_window.attributes("-alpha", alpha)
            self.after(50, lambda: self._animate_fade(alpha))
        else:
            self._show_game_over_text()

    def _show_game_over_text(self):
        lbl_msg = Label(self.fade_window, text="몬스터볼이 다 떨어졌다!", font=("Malgun Gothic", 16), bg="black", fg="white")
        lbl_msg.pack(pady=(300, 20))
        lbl_main = Label(self.fade_window, text="트레이너는 눈앞이 깜깜해졌다!", font=("Malgun Gothic", 24, "bold"), bg="black", fg="#F8F8F8")
        lbl_main.pack()
        lbl_ans = Label(self.fade_window, text=f"(정답: 도감 No.{self.secret_number})", font=("Malgun Gothic", 11), bg="black", fg="#888")
        lbl_ans.pack(side="bottom", pady=50)
        
        for w in (self.fade_window, lbl_msg, lbl_main, lbl_ans): w.bind("<Button-1>", self._end_blackout)
        self.blackout_timer = self.after(4000, self._end_blackout)

    def _end_blackout(self, event=None):
        self._cancel_warning_flash() 
        if hasattr(self, 'blackout_timer'): self.after_cancel(self.blackout_timer)
        if hasattr(self, 'fade_window'): self.fade_window.destroy()
        self.show_menu()

    def _get_pokemon_data_thread(self, number):
        url_m = f"https://pokeapi.co/api/v2/pokemon/{number}"
        url_s = f"https://pokeapi.co/api/v2/pokemon-species/{number}"
        try:
            ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            hdr = {"User-Agent": "Mozilla/5.0"}
            
            with urllib.request.urlopen(urllib.request.Request(url_m, headers=hdr), timeout=5, context=ctx) as r:
                d_m = json.loads(r.read().decode())
                h = d_m['height'] / 10; w = d_m['weight'] / 10
                types = ", ".join([self.type_map.get(t['type']['name'], t['type']['name']) for t in d_m['types']])
                img_url = d_m['sprites']['front_default']
                img_data = None
                if img_url:
                    with urllib.request.urlopen(urllib.request.Request(img_url, headers=hdr), timeout=5, context=ctx) as ir:
                        img_data = ir.read()

            with urllib.request.urlopen(urllib.request.Request(url_s, headers=hdr), timeout=5, context=ctx) as r:
                d_s = json.loads(r.read().decode())
                name = d_m['name']
                for n in d_s['names']:
                    if n['language']['name'] == 'ko': name = n['name']; break
                desc = "설명 없음"
                for d in d_s['flavor_text_entries']:
                    if d['language']['name'] == 'ko':
                        desc = d['flavor_text'].replace("\n", " ").replace("\f", " ")
                        break
            
            self.after_idle(lambda: self._update_ui_complete(number, name, types, h, w, desc, img_data))
        except:
            self.after_idle(lambda: self.desc_label.config(text="데이터 로딩 실패..."))

    def _update_ui_complete(self, num, name, types, h, w, desc, img_data):
        self.basic_info_label.config(text=f"No.{num:03d} {name}")
        if img_data:
            try:
                p_img = Image.open(BytesIO(img_data)).resize((180, 180), Image.NEAREST)
                tk_img = ImageTk.PhotoImage(p_img)
                self.img_label.config(image=tk_img)
                self.current_image = tk_img
            except: self.img_label.config(image='')
        else: self.img_label.config(image='')
        
        stats_text = f"타입: {types} | 키: {h}m | 몸무게: {w}kg"
        self.stats_label.config(text=stats_text)
        
        curr_hint = self.desc_label.cget("text").split("\n")[0]
        if "분석" in curr_hint or "튀어" in curr_hint: curr_hint = ""
        self.desc_label.config(text=f"{curr_hint}\n\n{desc}")

    def _check_guess_event(self, event): self._check_guess()

    def _check_guess(self):
        try:
            val = self.guess_entry.get()
            if not val: return
            guess = int(val)
            if guess < self.current_min or guess > self.current_max:
                messagebox.showwarning("범위 이탈", "범위를 벗어났다!")
                return
            
            self.attempts += 1
            self.desc_label.config(text=f"도감 No.{guess}...\n데이터를 대조하고 있다...")
            threading.Thread(target=self._get_pokemon_data_thread, args=(guess,), daemon=True).start()

            if guess == self.secret_number:
                self.guess_history.append((guess, "정답"))
                self.save_record("성공") # [수정] 성공 시 기록 저장
                messagebox.showinfo("성공", f"신난다! 포켓몬을 잡았다!\n(남은 볼: {self.current_lives}개)\n정답: 도감 No.{self.secret_number}")
                self.show_menu()
            else:
                self.current_lives -= 1
                self._update_lives_ui()
                if self.current_lives <= 0:
                    self.guess_history.append((guess, "실패"))
                    self.game_over()
                    return
                
                sq = 0
                if self.buff_x_attack and self.buff_x_attack_turns > 0:
                    sq = max(1, int((self.current_max - self.current_min) * 0.05))
                    self.buff_x_attack_turns -= 1 
                    if self.buff_x_attack_turns <= 0:
                        self.buff_x_attack = False 
                
                hint = ""
                if guess < self.secret_number:
                    self.current_min = max(self.current_min, guess + 1 + sq)
                    if self.buff_x_attack: self.current_max = max(self.secret_number, self.current_max - sq)
                    hint = f"▲ UP! (더 높은 숫자입니다)"
                    self.guess_history.append((guess, "UP"))
                else:
                    self.current_max = min(self.current_max, guess - 1 - sq)
                    if self.buff_x_attack: self.current_min = min(self.secret_number, self.current_min + sq)
                    hint = f"▼ DOWN! (더 낮은 숫자입니다)"
                    self.guess_history.append((guess, "DOWN"))
                
                if sq > 0:
                    hint += f"\n(플러스파워 효과로 범위가 더 좁혀졌다! 남은 턴: {self.buff_x_attack_turns})"
                elif self.buff_x_attack == False and self.buff_x_attack_turns == 0 and sq > 0: 
                     hint += "\n(플러스파워의 효과가 사라졌다!)"

                if self.current_min > self.current_max:
                    self.current_min = self.secret_number; self.current_max = self.secret_number
                
                self.game_range_label.config(text=f"범위: {self.current_min} ~ {self.current_max}")
                self.desc_label.config(text=hint)
            self.guess_entry.delete(0, tk.END)
        except ValueError: messagebox.showwarning("오류", "숫자만 입력할 수 있다!")

    def open_adventure_log(self):
        if hasattr(self, 'log_window') and self.log_window is not None and self.log_window.winfo_exists():
            self.log_window.lift()
            return

        self.log_window = Toplevel(self)
        self.log_window.title("모험 기록")
        self.log_window.geometry("600x400")
        
        header = tk.Frame(self.log_window, bg="#6890F0", padx=10, pady=10, bd=2, relief="raised")
        header.pack(fill="x")
        Label(header, text="PC 박스 (모험 기록)", font=(self.FONT_FAMILY, 12, "bold"), bg="#6890F0", fg="white").pack(side="left")
        
        Button(header, text="✖ 닫기", font=self.FONT_SMALL, command=self.log_window.destroy).pack(side="right")
        Button(header, text="🗑️ 기록 초기화", font=self.FONT_SMALL, bg="#FF3333", fg="white", command=self.reset_history).pack(side="right", padx=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Log.Treeview", background="#E0F7FA", fieldbackground="#E0F7FA", font=(self.FONT_FAMILY, 9), rowheight=25)
        style.configure("Log.Treeview.Heading", font=(self.FONT_FAMILY, 10, "bold"), background="#4DD0E1", foreground="white")
        
        cols = ("date", "gen", "poke", "try", "item")
        self.history_tree = ttk.Treeview(self.log_window, columns=cols, show="headings", style="Log.Treeview") 
        
        self.history_tree.heading("date", text="날짜")
        self.history_tree.heading("gen", text="지역")
        self.history_tree.heading("poke", text="포켓몬")
        self.history_tree.heading("try", text="시도")
        self.history_tree.heading("item", text="도구")
        
        self.history_tree.column("date", width=100, anchor="center")
        self.history_tree.column("gen", width=80, anchor="center")
        self.history_tree.column("poke", width=100, anchor="center")
        self.history_tree.column("try", width=40, anchor="center")
        self.history_tree.column("item", width=120, anchor="w")
        
        sb = ttk.Scrollbar(self.log_window, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=sb.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        sb.pack(side="right", fill="y", pady=10, padx=(0,10))
        
        self.history_tree.tag_configure("success", foreground="blue")
        self.history_tree.tag_configure("fail", foreground="red")
        self.history_tree.tag_configure("gray", foreground="gray") # [신규] 도망 태그
        
        self.load_history_to_tree()

    def load_history_to_tree(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        # [수정] 태그 로직 변경: 실패/도망/성공 구분
                        attempts_str = item["attempts"]
                        if "실패" in attempts_str:
                            tag = "fail"
                        elif "도망" in attempts_str:
                            tag = "gray"
                        else:
                            tag = "success"
                            
                        self.history_tree.insert("", "end", values=(
                            item.get("date",""), item.get("generation",""), 
                            item.get("pokemon",""), attempts_str, item.get("items","")
                        ), tags=(tag,))
            except: pass
        else:
            self.history_tree.insert("", "end", values=("기록 없음", "-", "-", "-", "-"))

    def reset_history(self):
        if not os.path.exists(self.HISTORY_FILE):
            messagebox.showinfo("알림", "삭제할 기록이 없습니다.", parent=self.log_window)
            return

        if messagebox.askyesno("경고", "정말로 모든 모험 기록을 삭제하시겠습니까?\n삭제된 데이터는 복구할 수 없습니다.", parent=self.log_window):
            try:
                os.remove(self.HISTORY_FILE)
                self.load_history_to_tree() 
                messagebox.showinfo("완료", "모험 기록이 초기화되었습니다.", parent=self.log_window)
            except Exception as e:
                messagebox.showerror("오류", f"파일 삭제 중 오류 발생: {e}", parent=self.log_window)

    def save_record(self, outcome="성공"):
        # [수정] 결과(성공/실패/도망)에 따른 시도 횟수 포맷
        if outcome == "성공":
            try_str = f"{self.attempts}회"
        else:
            try_str = f"{self.attempts}회 ({outcome})"

        record_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "pokemon": f"{self.target_name_kor} (No.{self.secret_number})",
            "generation": self.current_gen_name,
            "attempts": try_str,
            "items": ", ".join(self.used_items_log) if self.used_items_log else "사용 안함"
        }
        try:
            if os.path.exists(self.HISTORY_FILE):
                with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                    history_list = json.load(f)
            else:
                history_list = []
        except: history_list = []
        
        history_list.insert(0, record_data)
        
        try:
            with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"저장 오류: {e}")

    def _open_custom_range(self):
        win = Toplevel(self)
        win.geometry("300x150")
        Label(win, text="직접 입력").pack(pady=10)
        f = tk.Frame(win); f.pack()
        e1 = Entry(f, width=5); e1.pack(side="left"); e1.insert(0,"1")
        Label(f, text="~").pack(side="left")
        e2 = Entry(f, width=5); e2.pack(side="left"); e2.insert(0,"1025")
        def apply():
            try:
                mn, mx = int(e1.get()), int(e2.get())
                if mn < mx:
                    self.min_num, self.max_num = mn, mx
                    self.range_label.config(text=f"범위: {mn} ~ {mx}")
                    win.destroy()
            except: pass
        Button(win, text="설정", command=apply).pack(pady=10)

if __name__ == "__main__":
    app = PokedexGame()
    app.mainloop()
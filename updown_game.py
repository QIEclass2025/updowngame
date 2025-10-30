
import tkinter as tk
from tkinter import messagebox
import random
import requests

# 게임의 모든 로직과 GUI를 관리하는 메인 클래스
class UpDownGame:
    # 생성자: 애플리케이션 초기화
    def __init__(self, root):
        self.root = root
        self.root.title("업다운 게임")
        self.root.geometry("300x220")  # 창 크기 설정

        # 게임 상태를 저장하는 변수들 초기화
        self.secret_number = random.randint(1, 100)  # 1~100 사이의 비밀 숫자 생성
        self.attempts = 0  # 시도 횟수
        self.min_range = 1  # 추측 범위의 최솟값
        self.max_range = 100  # 추측 범위의 최댓값

        # --- GUI 위젯(Widget) 생성 및 배치 ---
        # 안내 레이블
        self.label_info = tk.Label(root, text="1부터 100 사이의 숫자를 맞춰보세요!")
        self.label_info.pack(pady=5)

        # 추측 범위 표시 레이블
        self.label_range = tk.Label(root, text=f"범위: {self.min_range} - {self.max_range}")
        self.label_range.pack(pady=5)

        # 숫자 입력창
        self.entry_guess = tk.Entry(root)
        self.entry_guess.pack(pady=5)
        self.entry_guess.bind("<Return>", self.check_guess_event)  # 엔터 키로도 추측 가능하게 설정

        # 결과(업/다운) 표시 레이블
        self.label_result = tk.Label(root, text="")
        self.label_result.pack(pady=5)

        # 추측하기 버튼
        self.button_check = tk.Button(root, text="추측하기", command=self.check_guess)
        self.button_check.pack(pady=5)

        # 시도 횟수 표시 레이블
        self.label_attempts = tk.Label(root, text="시도 횟수: 0")
        self.label_attempts.pack(pady=5)

    # 사용자의 추측을 확인하는 메인 함수
    def check_guess(self):
        try:
            guess = int(self.entry_guess.get())  # 입력값을 정수로 변환

            # 1. 범위 검사: 추측한 숫자가 현재 범위 내에 있는지 확인
            if not (self.min_range <= guess <= self.max_range):
                self.label_result.config(text=f"범위({self.min_range}-{self.max_range}) 안의 숫자를 입력하세요.")
                self.entry_guess.delete(0, tk.END)
                return  # 시도 횟수를 올리지 않고 함수 종료

            # 2. 시도 횟수 증가: 유효한 추측일 경우에만 카운트
            self.attempts += 1
            self.label_attempts.config(text=f"시도 횟수: {self.attempts}")

            # 3. 업/다운/정답 판정
            if guess < self.secret_number:
                self.label_result.config(text="업!")
                self.min_range = guess + 1  # 범위 최솟값 업데이트
            elif guess > self.secret_number:
                self.label_result.config(text="다운!")
                self.max_range = guess - 1  # 범위 최댓값 업데이트
            else:
                self.correct_answer()  # 정답일 경우
                return

            # 4. 범위 레이블 텍스트 업데이트
            self.label_range.config(text=f"범위: {self.min_range} - {self.max_range}")

        except ValueError:
            # 사용자가 숫자가 아닌 값을 입력했을 경우
            self.label_result.config(text="숫자만 입력해주세요.")
        finally:
            # 추측 후 항상 입력창을 비움
            self.entry_guess.delete(0, tk.END)

    # 엔터 키를 눌렀을 때 check_guess 함수를 호출하는 이벤트 핸들러
    def check_guess_event(self, event):
        self.check_guess()

    # 외부 API를 호출하여 조언을 가져오는 함수
    def get_advice(self):
        try:
            response = requests.get("https://api.adviceslip.com/advice")
            response.raise_for_status()  # HTTP 오류가 발생하면 예외 발생
            advice_data = response.json()
            return advice_data['slip']['advice']
        except requests.exceptions.RequestException as e:
            return f"조언을 가져오는 데 실패했습니다: {e}"

    # 정답을 맞혔을 때 호출되는 함수
    def correct_answer(self):
        advice = self.get_advice()  # API에서 조언 가져오기

        # 시도 횟수에 따라 다른 축하 메시지 표시
        if self.attempts <= 4:
            result_text = f"대단해요! 단 {self.attempts}번 만에 맞추셨어요!"
            self.label_result.config(text=result_text)
            messagebox.showinfo("엄청난 실력이시네요!", f"{result_text}\n\n오늘의 조언: {advice}")
        else:
            result_text = f"정답입니다! {self.attempts}번 만에 맞추셨어요."
            self.label_result.config(text=result_text)
            messagebox.showinfo("축하합니다!", f"{result_text}\n\n오늘의 조언: {advice}")
        
        self.reset_game()  # 게임 상태 초기화

    # 새 게임을 위해 모든 변수와 레이블을 초기 상태로 되돌리는 함수
    def reset_game(self):
        self.secret_number = random.randint(1, 100)
        self.attempts = 0
        self.min_range = 1
        self.max_range = 100
        self.label_result.config(text="")
        self.label_attempts.config(text="시도 횟수: 0")
        self.label_range.config(text=f"범위: {self.min_range} - {self.max_range}")
        self.label_info.config(text="새로운 게임 시작! 숫자를 맞춰보세요.")


# 이 스크립트가 직접 실행될 때만 아래 코드를 실행
if __name__ == "__main__":
    root = tk.Tk()  # 메인 윈도우 생성
    game = UpDownGame(root)  # UpDownGame 클래스의 인스턴스 생성
    root.mainloop()  # GUI 애플리케이션 실행

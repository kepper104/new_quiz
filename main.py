import sys
import threading
import csv
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap, QPalette
from PyQt5.QtCore import Qt, QTimer
from threading import Thread
from os import getcwd
from os import path
from time import sleep
import matplotlib.pyplot as plt
import pygame
from json import load

with open("config.json", "r") as f:
    params = load(f)

# Extract the parameters from the dictionary
team_count = params["team_count"]
music_delay = params["music_guess_delay"]
show_window_borders = params["show_main_window_borders"]
use_background_image = params["use_background_image"]
window_offset = tuple(params["window_offset"])
question_window_size = tuple(params["question_window_size"])
plot_offset_from_screen_edge = tuple(params["plot_offset_from_screen_edge"])
plot_size_in_pixels = tuple(params["plot_size_in_pixels"])
numbers_on_bar_offset = params["numbers_on_bar_offset"]
plot_font_size = params["plot_font_size"]
scaling = params["scaling_stuff"]
question_font_size = params["question_font_size"]

opened_questions = 0
cur_team = 0
points = {}
for i in range(1, team_count + 1):
    points[i] = 0
print(points)

rubrics = ["История Нового Года", "Снеговики", "Новогодние Блюда",
           "Цитаты из фильмов", "Новый Год до Революции", "Дед Мороз", "Загадки", "Новый Год в Других Странах"]

if scaling:
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(
            Qt.AA_EnableHighDpiScaling, True)

    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

all_music = []
all_events = []

def playMusic(file_name, delay=0):
    global all_events
    global all_music
    all_events.append(threading.Event())
    all_music.append(Thread(target=playSound, args=(file_name, delay, all_events[-1])))
    all_music[-1].start()

def playSound(file_name, delay=0, stop_event=False):
    sleep(delay)
    cwd = getcwd()
    audio_file = path.join(cwd, "music", file_name)
    audio_file = audio_file.replace("\\", " /").replace(" ", "")
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play(1)
    while not stop_event.is_set():
        pygame.time.Clock().tick(10)
    print('JUST stopped', file_name)
    pygame.mixer.music.stop()

def kill_all_sounds():
    for index in range(len(all_events)):
        all_events[index].set()
        print("Stopped", index)
    all_music.clear()
    all_events.clear()

class App(QMainWindow):
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        super().__init__()


        if use_background_image:
            self.bg_label = QLabel(self)
            self.bg_label.setPixmap(QPixmap("bg-main.png"))
            self.bg_label.setFixedSize(1513, 710)
            self.bg_label.move(0, 0)

        uic.loadUi('design.ui', self)
        self.setWindowTitle("Новый Год 2023")

        if not show_window_borders:
            self.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.setWindowFlag(Qt.FramelessWindowHint)

        for i in self.buttonGroup.buttons():
            i.clicked.connect(self.bruh)

    def bruh(self):
        cost = self.sender().text()
        print(cost)
        # self.sender().setParent(None)
        self.sender().setText("")
        # self.sender().setStyle()
        self.sender().setEnabled(False)

        id = int(self.sender().objectName().split('_')[1])
        # print(id, cost)
        if id == 65:
            self.music_pause("alice_pause1.mp3")
        elif id == 42:
            self.music_pause("alice_pause2.mp3")
        elif id // 10 == 6:
            self.read_music(id // 10, cost)
        elif id // 10 == 0:
            playMusic("blackboxmusic.mp3")
            self.read_csv(id // 10, cost)
        else:
            playMusic("next.mp3")
            self.read_csv(id // 10, cost)

    def music_pause(self, music_name):
        x = self.geometry().x() - window_offset[0]
        y = self.geometry().y() - window_offset[1]
        self.window = QuestionWindow(self, pos=(
            x, y), isMusic=True, music_name=music_name)
        self.window.show()

    def read_csv(self, file_id, cost):
        with open(f"csv/{file_id}.csv", 'r', encoding='utf-8') as file:
            res = csv.reader(file, delimiter=';', quotechar='"')
            for i in res:
                if i[0] == cost:
                    x = self.geometry().x() - window_offset[0]
                    y = self.geometry().y() - window_offset[1]
                    # print(self.geometry())
                    self.window = QuestionWindow(
                        self, q=i[1], a=i[2], p=i[0], r=rubrics[file_id], pos=(x, y))
                    self.window.show()
    def read_music(self, file_id, cost):
        with open(f"csv/{file_id}.csv", 'r', encoding='utf-8') as file:
            res = csv.reader(file, delimiter=';', quotechar='"')
            for i in res:
                if i[0] == cost:
                    q = i[1]
                    file_name = i[2]
                    a = i[3]
                    playMusic(file_name, music_delay)
                    print(q, file_name, a)
                    x = self.geometry().x() - window_offset[0]
                    y = self.geometry().y() - window_offset[1]
                    self.window = QuestionWindow(
                        self, q=i[1], a=i[3], p=i[0], r=rubrics[file_id], pos=(x, y))
                    self.window.show()
    def keyPressEvent(self, event):
        if event.key() == 90:
            kill_all_sounds()
            plot_histogram()
            self.close()
        if event.key() == 45:
            kill_all_sounds()
    def closeEvent(self, event):
        # print("cLOSING")
        kill_all_sounds()
        event.accept()

class QuestionWindow(QWidget):
    def __init__(self, *args, q="Музыкальная пауза", a='', p='', r="", pos=(0, 0), isMusic=False, music_name=''):
        super().__init__()
        uic.loadUi("question.ui", self)
        print(pos)
        # self.setStyleSheet("background-color: red;")
        self.setGeometry(pos[0], pos[1], question_window_size[0], question_window_size[1])
        self.setWindowTitle('Вопрос')
        self.question = q
        self.answer = a
        self.price = p
        self.rubric = r
        self.shownAns = False
        self.showBorder = False
        self.isMusic = isMusic
        self.music_name = music_name

        self.setAutoFillBackground(True)

        palette = QPalette()
        palette.setColor(QPalette.Background, Qt.black)
        self.setPalette(palette)

        print(p, r, q, a, pos, isMusic, music_name)

        if not self.showBorder:
            self.verticalLayout.setContentsMargins(0, 0, 0, 0)
            self.setWindowFlag(Qt.FramelessWindowHint)

        self.label_3.setText(
            f"""<html><head/><body><p align="center"><span style=" font-size:{question_font_size}pt; color:#5e9ad7;">{q}</span></p></body></html>""")

        real_rubric = """<html><head/><body><p align="center"><span style=" font-size:28pt; color:#e88a2c;">""" + \
            r + " " + p + """</span></p></body></html>"""

        self.label_2.setText(real_rubric)
        if not self.isMusic:
            self.label_4.setText(f"""<html><head/><body><p align="center"><span style=" color:#5e9ad7;">Команда {cur_team + 1}</span></p></body></html>""")

    def showAnswer(self):
        self.label_3.setText(
            f"""<html><head/><body><p align="center"><span style=" font-size:26pt; color:#5e9ad7;">{self.answer}</span></p></body></html>""")

    def keyPressEvent(self, event):
        global cur_team, points
        print(event.key())
        if event.key() == 16777220:
            if not self.shownAns:
                if self.isMusic:
                    playMusic(self.music_name)
                else:
                    self.showAnswer()
                self.shownAns = True

            else:
                self.close()
        elif event.key() == 89:
            points[cur_team + 1] += int(self.price)
            plot_histogram((cur_team + 1, self.price))
            print(cur_team)

            cur_team += 1
            cur_team %= 3
            print(cur_team)

        elif event.key() == 78:
            plot_histogram()
            cur_team += 1
            cur_team %= 3
        elif event.key() - 48 == 1:
            cur_team = 0
            self.label_4.setText(
                f"""<html><head/><body><p align="center"><span style=" color:#5e9ad7;">Команда {cur_team + 1}</span></p></body></html>""")
        elif event.key() - 48 == 2:
            cur_team = 1
            self.label_4.setText(
                f"""<html><head/><body><p align="center"><span style=" color:#5e9ad7;">Команда {cur_team + 1}</span></p></body></html>""")
        elif event.key() - 48 == 3:
            cur_team = 2
            self.label_4.setText(
                f"""<html><head/><body><p align="center"><span style=" color:#5e9ad7;">Команда {cur_team + 1}</span></p></body></html>""")
        elif event.key() - 48 == 4:
            cur_team = 3
            self.label_4.setText(
                f"""<html><head/><body><p align="center"><span style=" color:#5e9ad7;">Команда {cur_team + 1}</span></p></body></html>""")
        elif event.key() == 45:
            kill_all_sounds()


def plot_histogram(last_points=(0, 0)):
    teams = list(points.keys())
    team_points = list(points.values())

    fig, ax = plt.subplots()
    canvas = fig.canvas
    canvas.manager.window.move(plot_offset_from_screen_edge[0], plot_offset_from_screen_edge[1])
    canvas.manager.window.resize(plot_size_in_pixels[0], plot_size_in_pixels[1])

    ax.set_ylabel("Очки", fontsize=plot_font_size)
    ax.set_title("Результаты", fontsize=plot_font_size)
    colors = [f"C{i}" for i in range(len(teams))]

    for i, team in enumerate(teams):
        ax.bar(team, team_points[i], color=colors[i])
        ax.text(team, team_points[i] - numbers_on_bar_offset, team_points[i],
                ha="center", color="black", fontsize=plot_font_size)

    if last_points != (0, 0):
        ax.text(last_points[0], team_points[last_points[0] - 1] + numbers_on_bar_offset, "+" + str(last_points[1]), ha="center",
                color="black", fontsize=plot_font_size)

    plt.xticks(teams, ["Команда {}".format(i) for i in teams], fontsize=plot_font_size)

    plt.yticks(team_points, fontsize=plot_font_size)
    plt.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())

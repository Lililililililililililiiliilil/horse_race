import random
import sqlite3
import sys
import time

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog


# 0  1 2 3 4
# 5 11 3 1 7
# 11 7 5 3 1
# 3  1 4 5 2

def calculate_position(distance):
    pos = [0] * len(distance)
    sorted_dis = sorted(distance, reverse=True)
    for i in range(len(sorted_dis)):
        pos[i] = sorted_dis.index(distance[i]) + 1
    return pos


class Horse:
    def __init__(self, name, image_path):
        self.name = name
        self.image_path = image_path
        self.speeds = [random.randint(1, 6) for _ in range(10)]


class HorseRace(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.reg_window = None
        self.login_window = None
        self.horses = []
        self.player_id = None
        self.player_pass = None
        self.horses_names = ["Тайфун", "Юджин", "Одиссея", "Буцефал", "Зевс"]
        self.position = [len(self.horses_names)] * len(self.horses_names)
        self.player = "Guest"
        self.bets = {}
        self.balance = 1000
        self.total_bets = 0
        self.winning_horses = []
        self.winning_players = {}
        self.ippodromo_share = 0.1
        self.init_ui()
        self.get_random_bets()

        self.add_horses(self.horses_names)

    def init_ui(self):
        self.setWindowTitle("Ипподром")
        self.setGeometry(100, 100, 800, 600)

        self.total_bet_amount = 0

        self.bets_label = QtWidgets.QLabel()
        self.bets_label.setText(str(self.total_bet_amount))

        self.bets_text = QtWidgets.QLabel()
        self.bets_text.setText("Сумма ставок: ")

        self.centralwidget = QtWidgets.QWidget(self)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()

        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.activated.connect(self.select_horse)
        self.verticalLayout.addWidget(self.comboBox)

        self.horse_label = QtWidgets.QLabel(self.centralwidget)
        self.horse_label.setPixmap(QtGui.QPixmap("race.jpeg").scaled(QSize(400, 300)))
        self.verticalLayout.addWidget(self.horse_label)

        self.verticalLayout.addWidget(self.bets_text)
        self.verticalLayout.addWidget(self.bets_label)

        balance_layout = QtWidgets.QHBoxLayout()

        add_button_balance = QtWidgets.QPushButton()
        add_button_balance.setText("+")
        add_button_balance.clicked.connect(lambda checked: self.show_add_balance_dialog())

        self.player_label = QtWidgets.QLabel(self.centralwidget)
        self.player_label.setText("Игрок: " + self.player + " - " + str(self.balance) + "$")
        balance_layout.addWidget(self.player_label)
        balance_layout.addWidget(add_button_balance)
        self.verticalLayout.addLayout(balance_layout)

        self.bet_spinbox = QtWidgets.QSpinBox(self.centralwidget)
        self.bet_spinbox.setRange(0, 10000)
        self.verticalLayout.addWidget(self.bet_spinbox)

        self.bet_button = QtWidgets.QPushButton(self.centralwidget)
        self.bet_button.setText("Заключить пари")
        self.bet_button.clicked.connect(self.place_bet)

        self.start_button = QtWidgets.QPushButton(self.centralwidget)
        self.start_button.setText("Старт")
        self.start_button.clicked.connect(self.start_race)
        self.verticalLayout.addWidget(self.bet_button)
        self.verticalLayout.addWidget(self.start_button)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.login_button = QtWidgets.QPushButton(self.centralwidget)
        self.login_button.setText("Вход")
        self.login_button.clicked.connect(lambda checked: self.show_login_window())

        self.registration_button = QtWidgets.QPushButton(self.centralwidget)
        self.registration_button.setText("Регистрация")
        self.registration_button.clicked.connect(lambda checked: self.show_reg_window())

        reg_layout = QtWidgets.QHBoxLayout()
        reg_layout.addWidget(self.login_button)
        reg_layout.addWidget(self.registration_button)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addLayout(reg_layout)

        self.horse_position_table = QTableWidget(5, 3, self.centralwidget)
        self.horse_position_table.setHorizontalHeaderLabels(["Лошадь", "Позиция", "Ставка"])
        self.update_horse_table()
        right_layout.addWidget(self.horse_position_table)
        self.horizontalLayout.addLayout(right_layout)
        self.setCentralWidget(self.centralwidget)

        self.menuBar = self.menuBar()
        self.file_menu = self.menuBar.addMenu("Файл")
        self.exit_action = QAction("Выход", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        self.show()

    def add_horses(self, horse_names):
        for name in horse_names:
            image_path = f"horse_{len(self.horses) + 1}.png"
            horse = Horse(name, image_path)
            self.horses.append(horse)
            self.comboBox.addItem(horse.name)

    def select_horse(self, name):
        for horse in self.horses:
            if horse.name == name:
                self.horse_label.setPixmap(QtGui.QPixmap(horse.image_path))
                break

    def place_bet(self):
        horse = self.comboBox.currentText()
        bet_amount = int(self.bet_spinbox.value())

        if bet_amount > self.balance:
            message = QMessageBox()
            message.critical(self, "Превышение баланса!", "Вы не можете поставить больше, чем у вас есть на счете!",
                             QMessageBox.StandardButton.Ok)
            return

        self.bet_button.setDisabled(True)

        # Если игрок уже сделал ставку на эту лошадь, удаляем старую ставку
        if -1 in self.bets[horse][1]:
            self.total_bet_amount -= bet_amount
            self.bets.pop(horse)

        self.balance -= bet_amount
        self.update_balance()

        # Добавляем новую ставку в словарь
        if horse in self.bets:
            self.bets[horse][0] += bet_amount
            self.bets[horse][1].append(-1)
        else:
            self.bets[horse] = [bet_amount, [-1]]
        self.total_bet_amount += bet_amount
        self.bets_label.setText(str(self.total_bet_amount))
        self.update_horse_table()

    def start_race(self):
        distance = [0] * 5

        for i in range(1000):
            for j in range(5):
                k = random.randint(0, 9)
                distance[j] += self.horses[j].speeds[k]

            self.position = calculate_position(distance)

            self.update_horse_position()
            time.sleep(0.01)

        winner = 0
        for i in range(len(self.position)):
            if self.position[i] == 1:
                winner = i
                break

        winner_name = self.horses_names[winner]
        winner_bets_info = self.bets[winner_name]
        print(winner_name)
        winner_bets = winner_bets_info[0] * (1 - self.ippodromo_share)
        winner_players = winner_bets_info[1]
        if -1 in winner_players:
            self.balance += winner_bets / len(winner_players)
        self.update_balance()

    def update_balance(self):
        self.player_label.setText("Player: " + self.player + " - " + str(self.balance) + "$")

    def update_horse_table(self):
        for i in range(5):
            name = QTableWidgetItem(self.horses_names[i])
            position = QTableWidgetItem(str(self.position[i]))
            if self.horses_names[i] in self.bets:
                bet = QTableWidgetItem(str(self.bets[self.horses_names[i]][0]))
            else:
                bet = QTableWidgetItem("0")
            self.horse_position_table.setItem(i, 0, name)
            self.horse_position_table.setItem(i, 1, position)
            self.horse_position_table.setItem(i, 2, bet)

    def update_horse_position(self):
        for i in range(5):
            position = QTableWidgetItem(str(self.position[i]))
            self.horse_position_table.setItem(i, 1, position)

    def get_random_bets(self):
        for i in range(10):
            id = random.randint(0, len(self.horses_names) - 1)
            horse_name = self.horses_names[id]
            bet = random.randint(100, 1000)
            if horse_name in self.bets:
                self.bets[horse_name][0] += bet
                self.bets[horse_name][1].append(i)
            else:
                self.bets[horse_name] = [bet, [i]]
            self.total_bet_amount += bet

    def show_login_window(self):
        self.login_window = LoginWindow()
        self.login_window.loginClicked.connect(self.show_logged_account)
        self.login_window.show()

    def show_reg_window(self):
        self.reg_window = RegistrationWindow()
        self.reg_window.show()

    def show_logged_account(self, id, login, password, balance):
        self.player_id = id
        self.player = login
        self.player_pass = password
        self.balance = balance
        self.player_label.setText("Player: " + self.player + " - " + str(self.balance) + "$")

    def show_add_balance_dialog(self):
        amount, ok = QInputDialog.getText(self, 'Пополение баланса',
                                          'Введите сумму:')
        if ok:
            if int(amount) > 0:
                self.balance += int(amount)
                self.player_label.setText("Player: " + self.player + " - " + str(self.balance) + "$")
            else:
                message = QMessageBox()
                message.critical(self, "Ошибка!", "Введите корректную сумму!",
                                 QMessageBox.StandardButton.Ok)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.player != "Guest":
            sqlite = sqlite3.connect('identifier.sqlite')
            cursor = sqlite.cursor()

            query = "UPDATE accounts SET balance = {0} WHERE id = {1}".format(self.balance, self.player_id)
            cursor.execute(query)
            sqlite.commit()


class LoginWindow(QtWidgets.QWidget):
    loginClicked = QtCore.Signal(int, str, int, int)

    def __init__(self):
        self.acc_id = None
        self.acc_login = None
        self.acc_pass = None
        self.acc_balance = None
        super().__init__()
        self.setWindowTitle("Вход")
        layout = QtWidgets.QVBoxLayout()
        self.login_input = QtWidgets.QLineEdit()
        self.login_input.setPlaceholderText("Логин")
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        login_button = QtWidgets.QPushButton()
        login_button.setText("Войти")
        login_button.clicked.connect(lambda checked: self.login())
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def login(self):
        login = self.login_input.text()
        password = self.password_input.text()
        print(login)

        if len(login) == 0:
            message = QMessageBox()
            message.critical(self, "Ошибка!", "Поле логина не может быть пустым!",
                             QMessageBox.StandardButton.Ok)
            return
        if len(password) == 0:
            message = QMessageBox()
            message.critical(self, "Ошибка!", "Поле пароля не может быть пустым!",
                             QMessageBox.StandardButton.Ok)
            return

        sqlite = sqlite3.connect('identifier.sqlite')
        cursor = sqlite.cursor()

        query = "SELECT * FROM accounts WHERE login = \'{0}\' AND password = {1}".format(login, password)
        cursor.execute(query)

        rows = cursor.fetchall()

        if len(rows) == 0:
            message = QMessageBox()
            message.critical(self, "Ошибка!", "Не верный логин или пароль!",
                             QMessageBox.StandardButton.Ok)
            return

        self.acc_id, self.acc_login, self.acc_pass, self.acc_balance = rows[0][0], rows[0][1], rows[0][2], rows[0][3]
        self.loginClicked.emit(self.acc_id, self.acc_login, self.acc_pass, self.acc_balance)
        self.close()


class RegistrationWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация")
        layout = QtWidgets.QVBoxLayout()
        self.login_input = QtWidgets.QLineEdit()
        self.login_input.setPlaceholderText("Логин")
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        login_button = QtWidgets.QPushButton()
        login_button.setText("Зарегистрироваться")
        login_button.clicked.connect(lambda checked: self.registration())
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def registration(self):
        login = self.login_input.text()
        password = self.password_input.text()

        print(login, password)

        if len(login) == 0:
            message = QMessageBox()
            message.critical(self, "Ошибка!", "Поле логина не может быть пустым!",
                             QMessageBox.StandardButton.Ok)
            return
        if len(password) == 0:
            message = QMessageBox()
            message.critical(self, "Ошибка!", "Поле пароля не может быть пустым!",
                             QMessageBox.StandardButton.Ok)
            return

        sqlite = sqlite3.connect('identifier.sqlite')
        cursor = sqlite.cursor()

        query = "INSERT INTO accounts(login, password, balance) VALUES (\'{0}\', {1}, {2});".format(login, password, 0)
        cursor.execute(query)
        sqlite.commit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HorseRace()
    window.show()
    sys.exit(app.exec())

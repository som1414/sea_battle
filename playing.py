from random import randint, choice
from time import sleep


class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "Вы пытаетесь выстрелить за доску!"


class BoardUsedException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эту клетку"


class BoardWrongShipException(BoardException):
    pass


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Dot({self.x}, {self.y})"


class Ship:
    def __init__(self, bow, l, o):
        self.bow = bow
        self.l = l
        self.o = o
        self.lives = l

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.l):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.o == 0:
                cur_x += i

            elif self.o == 1:
                cur_y += i

            ship_dots.append(Dot(cur_x, cur_y))

        return ship_dots

    def shooten(self, shot):
        return shot in self.dots


class Board:
    def __init__(self, hid=False, size=6):
        self.size = size
        self.hid = hid

        self.count = 0
        self.hit = False

        self.field = [["O"] * self.size for _ in range(self.size)]

        self.busy = []
        self.ships = []

        self.dots = [Dot(c, r) for r in range(self.size) for c in range(self.size)]

    @property
    def list_board(self):
        res = ""
        if self.size == 10:
            res += f"\033[33m{'     1   2   3   4   5   6   7   8   9  10  ;'}\033[0m"
        else:
            res += f'\033[33m{"    1   2   3   4   5   6  ;"}\033[0m'
        for i, row in enumerate(self.field):
            if self.size == 10:
                if i + 1 == 10:
                    res += f"\033[33m{i + 1}\033[0m" + " | " + " | ".join(row) + " |;"
                res += f"\033[33m {i + 1}\033[0m" + " | " + " | ".join(row) + " |;"
            else:
                res += f"\033[33m{i + 1}\033[0m" + " | " + " | ".join(row) + " |;"

        if self.hid:
            res = res.replace("■", f'\033[0m{"O"}')
        return res.split(';')

    def out(self, d):
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def contour(self, ship, verb=False):
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for d in ship.dots:
            for dx, dy in near:
                cur = Dot(d.x + dx, d.y + dy)
                if not (self.out(cur)) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = f'\033[31m{"."}\033[0m'
                    self.busy.append(cur)

    def add_ship(self, ship):
        for d in ship.dots:
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()
        for d in ship.dots:
            self.field[d.x][d.y] = f'\033[32m{"■"}\033[0m'
            self.busy.append(d)

        self.ships.append(ship)
        self.contour(ship)

    def shot_exception(self, d):
        if self.out(d):
            raise BoardOutException()

        if d in self.busy:
            raise BoardUsedException()
        return self.shot(d)

    def shot(self, d):

        self.busy.append(d)

        for ship in self.ships:
            if d in ship.dots:
                ship.lives -= 1
                self.field[d.x][d.y] = f'\033[31m{"X"}\033[0m'
                if ship.lives == 0:
                    self.count += 1
                    self.contour(ship, verb=True)
                    self.hit = False
                    print("Корабль уничтожен!")
                    return False
                else:
                    print("Корабль ранен!")
                    self.hit = True
                    return True

        self.field[d.x][d.y] = f'\033[31m{"."}\033[0m'
        print("Мимо!")
        return False

    def begin(self):
        self.busy = []

    @property
    def debacle(self):
        return self.count == len(self.ships)


class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy

    def ask(self):
        raise NotImplementedError()

    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot_exception(target)
                return repeat
            except BoardException as e:
                print(e)


class AI(Player):
    def __init__(self, board, enemy, hit=False):
        Player.__init__(self, board, enemy)
        self.hit = hit

    def ask(self):
        if self.hit:
            d = self.ask_injury()
        else:
            d = self.ask_back()
        sleep(10)
        print(f"Ход компьютера: {d.x + 1} {d.y + 1}")
        return d

    def ask_injury(self, dt=1):
        n = 1
        last = self.enemy.busy[-dt]
        for i in self.enemy.busy[-dt - 1:-5 - dt:-1]:
            if self.enemy.field[i.x][i.y] == f'\033[31m{"X"}\033[0m' and (
                    (i.y == last.y and abs(i.x - last.x <= 2)) or (i.x == last.x and abs(i.y - last.y <= 2))):
                n = self.enemy.busy[::-1].index(i) + 1
        first = self.enemy.busy[-dt]
        second = self.enemy.busy[-n]
        if n != 1:
            if second.x == first.x:
                d = choice([x for x in
                            [Dot(first.x, first.y - 1), Dot(first.x, first.y + 1), Dot(second.x, second.y - 1),
                             Dot(second.x, second.y + 1)] if
                            x not in self.enemy.busy and not self.enemy.out(x)])
            elif second.y == first.y:
                d = choice([x for x in
                            [Dot(first.x - 1, first.y), Dot(first.x + 1, first.y), Dot(second.x - 1, second.y),
                             Dot(second.x + 1, second.y)] if
                            x not in self.enemy.busy and not self.enemy.out(x)])
        else:
            d = choice([x for x in [Dot(first.x, first.y - 1), Dot(first.x, first.y + 1), Dot(first.x - 1, first.y),
                                    Dot(first.x + 1, first.y)] if x not in self.enemy.busy and not self.enemy.out(x)])
        return d

    def ask_back(self):
        if self.enemy.hit:
            n = 0
            for i in self.enemy.busy[::-1]:
                if self.enemy.field[i.x][i.y] == f'\033[31m{"X"}\033[0m':
                    n += 1
                    break
                n += 1
            d = self.ask_injury(n)
        else:
            d = choice([x for x in self.enemy.dots if x not in self.enemy.busy])
        return d

    def move(self):
        target = self.ask()
        repeat = self.enemy.shot(target)
        return repeat


class User(Player):
    def ask(self):
        while True:
            cords = input("Ваш ход: ").split()
            if len(cords) != 2:
                print(" Введите 2 координаты! ")
                continue

            x, y = cords

            if not (x.isdigit()) or not (y.isdigit()):
                print(" Введите числа! ")
                continue

            x, y = int(x), int(y)

            return Dot(x - 1, y - 1)


class Game:
    def __init__(self, size=6):
        self.size = size
        if self.size == 10:
            self.lens = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        else:
            self.lens = [3, 2, 2, 1, 1, 1, 1]
        pl = self.random_board()
        co = self.random_board()
        co.hid = True
        self.ai = AI(co, pl)
        self.us = User(pl, co)

    def try_board(self):
        board = Board(size=self.size)
        attempts = 0
        for l in self.lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), l, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    def random_board(self):
        board = None
        while board is None:
            board = self.try_board()
        return board

    def print_boards(self):
        if self.size == 10:
            print("-" * 95)
            print(" Доска пользователя:", "Доска компьютера:", sep=' ' * 30)
            [print(s) for s in
             [self.us.board.list_board[i] + '     ' + self.ai.board.list_board[i] for i in range(self.size + 1)]]
        else:
            print("-" * 60)
            print("Доска пользователя:", "Доска компьютера:", sep=' ' * 13)
            [print(s) for s in
             [self.us.board.list_board[i] + '     ' + self.ai.board.list_board[i] for i in range(self.size + 1)]]

    def loop(self):
        num = 0
        while True:
            self.print_boards()
            if num % 2 == 0:
                print("Ходит пользователь!")
                repeat = self.us.move()
            else:
                print("Ходит компьютер!")
                repeat = self.ai.move()
            if repeat:
                num -= 1
                self.ai.hit = True
            else:
                self.ai.hit = False

            if self.ai.board.debacle:
                self.print_boards()
                print("-" * 20)
                print("Пользователь выиграл!")
                break

            if self.us.board.debacle:
                self.print_boards()
                print("-" * 20)
                print("Компьютер выиграл!")
                break
            num += 1


flag = True
while flag:
    def start():
        print("-------------------")
        print("  Приветсвуем вас  ")
        print("      в игре       ")
        print("    морской бой    ")
        print("------------------------------------------")
        g = Game(int(input('Введите размер игрового моря - 6 или 10: ')))
        print("------------------------------------------")
        print(" формат ввода: x y ")
        print(" x - номер строки  ")
        print(" y - номер столбца ")

        g.loop()


    start()

    if input('Сыграете еще раз? д = да, н = нет\n') != 'д':
        flag = False
        break

import tkinter as tk
import os

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 10 # Kecepatan bola
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='white', outline='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 120 # Diperlebar agar lebih nyaman memantulkan bola
        self.height = 12
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#f1c40f', outline='#f39c12')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    # Skor dan warna bata: 1=Merah, 2=Biru, 3=Ungu/Keras
    COLORS = {1: '#e74c3c', 2: '#3498db', 3: '#8e44ad'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        self.points = hits * 10  # Poin berdasarkan ketebalan bata
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.high_score = self.load_high_score() # Load highest score
        self.level = 1
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#1a2634', # Warna background gelap (Dark Navy)
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width/2, 350)
        self.items[self.paddle.item] = self.paddle
        self.hud = None
        
        # Deteksi pergerakan tombol agar sangat smooth
        self.pressed_keys = {'Left': False, 'Right': False}
        self.canvas.focus_set()
        
        self.canvas.bind('<KeyPress-Left>', lambda _: self.pressed_keys.update({'Left': True}))
        self.canvas.bind('<KeyRelease-Left>', lambda _: self.pressed_keys.update({'Left': False}))
        self.canvas.bind('<KeyPress-Right>', lambda _: self.pressed_keys.update({'Right': True}))
        self.canvas.bind('<KeyRelease-Right>', lambda _: self.pressed_keys.update({'Right': False}))

        self.setup_level()
        self.setup_game()

    # --- SISTEM HIGHEST SCORE (MENYIMPAN KE FILE) ---
    def load_high_score(self):
        if os.path.exists("highscore.txt"):
            with open("highscore.txt", "r") as f:
                try:
                    return int(f.read())
                except:
                    return 0
        return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))
    # ------------------------------------------------

    def generate_bricks(self):
        self.canvas.delete('brick')
        items_to_remove = [k for k, v in self.items.items() if isinstance(v, Brick)]
        for k in items_to_remove:
            del self.items[k]

        # DATABASE POLA BENTUK BLOK (0=Kosong, 1=Merah, 2=Biru, 3=Ungu)
        patterns = [
            # LEVEL 1: Papan Catur (Checkerboard)
            [
                [1, 2, 1, 2, 1, 2, 1],
                [2, 1, 2, 1, 2, 1, 2],
                [1, 2, 1, 2, 1, 2, 1]
            ],
            # LEVEL 2: Pola Monster (Space Invader)
            [
                [0, 1, 0, 0, 0, 1, 0],
                [0, 0, 1, 0, 1, 0, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [1, 1, 0, 1, 0, 1, 1],
                [1, 1, 1, 1, 1, 1, 1],
                [1, 0, 1, 0, 1, 0, 1]
            ],
            # LEVEL 3: Pola Segitiga (Pyramid)
            [
                [0, 0, 0, 3, 0, 0, 0],
                [0, 0, 2, 2, 2, 0, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [1, 1, 1, 1, 1, 1, 1]
            ],
            # LEVEL 4: Pola Hati (Heart)
            [
                [0, 2, 2, 0, 2, 2, 0],
                [2, 1, 1, 2, 1, 1, 2],
                [2, 1, 3, 1, 3, 1, 2],
                [0, 2, 1, 3, 1, 2, 0],
                [0, 0, 2, 1, 2, 0, 0],
                [0, 0, 0, 2, 0, 0, 0]
            ]
        ]

        # Menentukan pola berdasarkan level (akan berulang jika level > 4)
        current_pattern = patterns[(self.level - 1) % len(patterns)]
        
        start_x = 75
        start_y = 50
        for r_idx, row in enumerate(current_pattern):
            for c_idx, val in enumerate(row):
                if val > 0:
                    # Jarak antar blok = 76px (horizontal), 22px (vertikal)
                    self.add_brick(start_x + (c_idx * 76), start_y + (r_idx * 22), val)

    def setup_level(self):
        self.generate_bricks()

    def setup_game(self):
        self.add_ball()
        self.update_hud()
        self.text = self.draw_text(self.width/2, 200, 'Press Space to Start', '30', 'white')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 330)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40', color='white'):
        font = ('Helvetica', size, 'bold')
        return self.canvas.create_text(x, y, text=text, font=font, fill=color)

    def update_hud(self):
        # Update teks di layar termasuk Highest Score
        text = f'❤ Lives: {self.lives}    🏆 Score: {self.score}    🥇 High Score: {self.high_score}    ⭐ Level: {self.level}'
        if self.hud is None:
            self.hud = self.draw_text(self.width/2, 15, text, '12', '#00ffcc')
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        # KECEPATAN PADDLE DITINGKATKAN MENJADI 20 (Sangat responsif)
        paddle_speed = 20
        if self.pressed_keys['Left']:
            self.paddle.move(-paddle_speed)
        if self.pressed_keys['Right']:
            self.paddle.move(paddle_speed)

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))

        if num_bricks == 0: 
            # LANJUT KE LEVEL BERIKUTNYA
            self.ball.speed = None
            self.level += 1
            self.save_high_score() # Save score tiap kali menang level
            self.draw_text(self.width/2, 200, f'Level {self.level} Unlocked!', '35', '#2ecc71')
            self.after(2000, self.setup_level)
            self.after(2000, self.setup_game)
        
        elif self.ball.get_position()[3] >= self.height: 
            # MATI / BOLA JATUH
            self.ball.speed = None
            self.lives -= 1
            self.update_hud()
            
            if self.lives < 0:
                # GAME OVER
                self.save_high_score() # Save skor terakhir
                self.draw_text(self.width/2, 180, 'GAME OVER', '40', '#e74c3c')
                self.draw_text(self.width/2, 230, f'Your Score: {self.score}', '20', 'white')
                self.draw_text(self.width/2, 260, f'Highest Score: {self.high_score}', '20', '#f1c40f')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(40, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

        for obj in objects:
            if isinstance(obj, Brick):
                self.score += 10 # Poin standar per benturan
                self.update_hud()
                if obj.hits == 0:
                    self.score += obj.points # Poin bonus saat blok pecah
                    self.update_hud()
                    
                    # Update high score secara real-time jika terlampaui
                    if self.score > self.high_score:
                        self.high_score = self.score 
                        self.update_hud()

                    del self.items[obj.item]


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Pro Breakout - Definitive Edition')
    root.resizable(False, False)
    game = Game(root)
    game.mainloop()
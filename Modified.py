import tkinter as tk
import os
import random

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


class PowerUp(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 8
        self.speed = 5
        # Kapsul power-up berwarna biru neon
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='#00f0ff', outline='', tags='powerup')
        super(PowerUp, self).__init__(canvas, item)

    def update(self):
        self.move(0, self.speed)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.base_radius = 10
        self.radius = self.base_radius
        self.direction = [1, -1]
        self.speed = 10
        self.damage = 1
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='#eceff4', outline='', tags='ball')
        super(Ball, self).__init__(canvas, item)

    def make_super(self):
        """Memperbesar bola dan menaikkan damage menjadi 2"""
        self.damage = 2
        self.radius = 16
        coords = self.get_position()
        center_x = (coords[0] + coords[2]) / 2
        center_y = (coords[1] + coords[3]) / 2
        self.canvas.coords(self.item, 
                           center_x-self.radius, center_y-self.radius, 
                           center_x+self.radius, center_y+self.radius)
        self.canvas.itemconfig(self.item, fill='#ff4a4a') # Merah menyala

    def reset_super(self):
        """Mengembalikan bola ke ukuran dan damage normal"""
        self.damage = 1
        self.radius = self.base_radius
        coords = self.get_position()
        center_x = (coords[0] + coords[2]) / 2
        center_y = (coords[1] + coords[3]) / 2
        self.canvas.coords(self.item, 
                           center_x-self.radius, center_y-self.radius, 
                           center_x+self.radius, center_y+self.radius)
        self.canvas.itemconfig(self.item, fill='#eceff4')

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
            if isinstance(game_object, PowerUp):
                return # Jangan mantul kalau nabrak powerup
            
            b_coords = game_object.get_position()
            if x > b_coords[2]:
                self.direction[0] = 1
            elif x < b_coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 140 # Papan lebih panjang karena layar melebar
        self.height = 12
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#88c0d0', outline='', tags='paddle')
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
    # Tema Minimalis Pastel: 1=Hijau Mint, 2=Kuning Pasir, 3=Merah Coral
    COLORS = {1: '#a3be8c', 2: '#ebcb8b', 3: '#bf616a'}

    def __init__(self, canvas, x, y, hits):
        self.width = 80 # Sedikit diperlebar
        self.height = 25
        self.hits = hits
        self.points = hits * 10
        color = Brick.COLORS.get(hits, '#ffffff')
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, outline='', tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self, damage):
        self.hits -= damage
        if self.hits <= 0:
            self.delete()
            return True # Tanda bata hancur
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS.get(self.hits, '#ffffff'))
            return False


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.high_score = self.load_high_score()
        self.level = 1
        
        # Jendela dibuat lebih lebar dan luas
        self.width = 900
        self.height = 600
        
        # Tema Minimalis (Background gelap yang elegan)
        self.canvas = tk.Canvas(self, bg='#1e1e2e', width=self.width, height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.powerups = [] # Menyimpan item jatuhan
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width/2, 540)
        self.items[self.paddle.item] = self.paddle
        self.hud = None
        
        self.pressed_keys = {'Left': False, 'Right': False}
        self.canvas.focus_set()
        
        self.canvas.bind('<KeyPress-Left>', lambda _: self.pressed_keys.update({'Left': True}))
        self.canvas.bind('<KeyRelease-Left>', lambda _: self.pressed_keys.update({'Left': False}))
        self.canvas.bind('<KeyPress-Right>', lambda _: self.pressed_keys.update({'Right': True}))
        self.canvas.bind('<KeyRelease-Right>', lambda _: self.pressed_keys.update({'Right': False}))

        self.setup_level()
        self.setup_game()

    def load_high_score(self):
        if os.path.exists("highscore.txt"):
            with open("highscore.txt", "r") as f:
                try:
                    return int(f.read())
                except:
                    pass
        return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open("highscore.txt", "w") as f:
                f.write(str(self.high_score))

    def trigger_shake(self, count=4):
        """Efek getaran layar yang dinamis dan memuaskan"""
        if count > 0:
            dx = random.choice([-5, -3, 3, 5])
            dy = random.choice([-5, -3, 3, 5])
            self.canvas.move('all', dx, dy)
            self.after(20, lambda: self.canvas.move('all', -dx, -dy))
            self.after(40, lambda: self.trigger_shake(count-1))

    def generate_bricks(self):
        self.canvas.delete('brick')
        self.canvas.delete('powerup')
        self.powerups.clear()
        
        items_to_remove = [k for k, v in self.items.items() if isinstance(v, Brick)]
        for k in items_to_remove:
            del self.items[k]

        patterns = [
            [
                [1, 2, 1, 2, 1, 2, 1, 2, 1],
                [2, 1, 2, 1, 2, 1, 2, 1, 2],
                [1, 2, 1, 2, 1, 2, 1, 2, 1]
            ],
            [
                [0, 1, 0, 0, 0, 1, 0],
                [0, 0, 1, 0, 1, 0, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [1, 1, 0, 1, 0, 1, 1],
                [1, 1, 1, 1, 1, 1, 1],
                [1, 0, 1, 0, 1, 0, 1]
            ],
            [
                [0, 0, 0, 0, 3, 0, 0, 0, 0],
                [0, 0, 0, 2, 2, 2, 0, 0, 0],
                [0, 0, 1, 1, 1, 1, 1, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 0],
                [1, 1, 1, 1, 1, 1, 1, 1, 1]
            ],
            [
                [0, 2, 2, 0, 2, 2, 0],
                [2, 1, 1, 2, 1, 1, 2],
                [2, 1, 3, 1, 3, 1, 2],
                [0, 2, 1, 3, 1, 2, 0],
                [0, 0, 2, 1, 2, 0, 0],
                [0, 0, 0, 2, 0, 0, 0]
            ]
        ]

        current_pattern = patterns[(self.level - 1) % len(patterns)]
        
        # Menghitung posisi agar tata letak otomatis ke tengah layar
        brick_w, brick_h = 82, 27
        row_width = len(current_pattern[0]) * brick_w
        start_x = (self.width - row_width) / 2 + (brick_w / 2)
        start_y = 70

        for r_idx, row in enumerate(current_pattern):
            for c_idx, val in enumerate(row):
                if val > 0:
                    self.add_brick(start_x + (c_idx * brick_w), start_y + (r_idx * brick_h), val)

    def setup_level(self):
        self.generate_bricks()

    def setup_game(self):
        self.add_ball()
        self.update_hud()
        if hasattr(self, 'text'):
            self.canvas.delete(self.text)
        self.text = self.draw_text(self.width/2, 300, 'Press Space to Start', '30', '#cdd6f4')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 520)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40', color='white'):
        font = ('Segoe UI', size, 'bold')
        return self.canvas.create_text(x, y, text=text, font=font, fill=color)

    def update_hud(self):
        text = f'❤ Lives: {self.lives}       🏆 Score: {self.score}       🥇 High Score: {self.high_score}       ⭐ Level: {self.level}'
        if self.hud is None:
            self.hud = self.draw_text(self.width/2, 25, text, '14', '#cdd6f4')
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        # Gerakan super responsif untuk ruangan yang luas
        paddle_speed = 22
        if self.pressed_keys['Left']:
            self.paddle.move(-paddle_speed)
        if self.pressed_keys['Right']:
            self.paddle.move(paddle_speed)

        # Proses pergerakan item Power-Up
        for pu in self.powerups[:]:
            pu.update()
            p_coords = pu.get_position()
            pad_coords = self.paddle.get_position()
            
            # Jika keluar batas bawah
            if p_coords[3] >= self.height:
                pu.delete()
                self.powerups.remove(pu)
            # Jika mengenai papan paddle
            elif (pad_coords[0] < p_coords[2] and pad_coords[2] > p_coords[0] and
                  pad_coords[1] < p_coords[3] and pad_coords[3] > p_coords[1]):
                self.ball.make_super() # Aktifkan efek super ball
                pu.delete()
                self.powerups.remove(pu)

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))

        if num_bricks == 0: 
            self.ball.speed = None
            self.ball.reset_super()
            self.level += 1
            self.save_high_score() 
            
            if hasattr(self, 'text'):
                self.canvas.delete(self.text)
            self.text = self.draw_text(self.width/2, 300, f'Level {self.level} Unlocked!', '35', '#a3be8c')
            
            self.after(2000, self.setup_level)
            self.after(2000, self.setup_game)
        
        elif self.ball.get_position()[3] >= self.height: 
            self.ball.speed = None
            self.ball.reset_super()
            self.lives -= 1
            self.update_hud()
            
            if self.lives < 0:
                self.save_high_score()
                if hasattr(self, 'text'):
                    self.canvas.delete(self.text)
                    
                self.draw_text(self.width/2, 260, 'GAME OVER', '50', '#bf616a')
                self.draw_text(self.width/2, 330, f'Your Score: {self.score}', '25', '#cdd6f4')
                self.draw_text(self.width/2, 370, f'Highest Score: {self.high_score}', '20', '#ebcb8b')
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
                # FIX: Ambil posisi bata SEBELUM bata dipukul/dihapus
                b_coords = obj.get_position() 
                
                is_destroyed = obj.hit(self.ball.damage)
                self.score += (10 * self.ball.damage)
                
                if is_destroyed:
                    self.trigger_shake()
                    self.score += obj.points 
                    
                    # 15% Peluang menjatuhkan Power-Up Biru
                    if random.random() < 0.15: 
                        # Gunakan b_coords yang sudah disimpan sebelumnya
                        px = (b_coords[0] + b_coords[2]) / 2
                        py = (b_coords[1] + b_coords[3]) / 2
                        new_powerup = PowerUp(self.canvas, px, py)
                        self.powerups.append(new_powerup)
                        
                    del self.items[obj.item]
                    
                if self.score > self.high_score:
                    self.high_score = self.score
                self.update_hud()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Pro Breakout - Minimalist Edition')
    root.resizable(False, False)
    game = Game(root)
    game.mainloop()
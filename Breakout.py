import sys
import random
import math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, 
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem)
from PyQt6.QtGui import QBrush, QPainter, QFont, QColor, QRadialGradient, QLinearGradient
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPen

# Paddle Class
class Paddle(QGraphicsRectItem):
    def __init__(self, scene_width, scene_height):
        super().__init__(0, 0, 100, 15)
        self.normal_width = 100
        self.setBrush(QBrush(QColor(70, 130, 180)))
        self.setPos(scene_width / 2 - 50, scene_height - 40)
        self.scene_width = scene_width
        self.scene_height = scene_height
        self.speed = 10
        self.sticky = False
        self.power_timer = QTimer()
        self.power_timer.timeout.connect(self.reset_power)
        self.power_timer.setSingleShot(True)

    def move_left(self):
        self.setX(max(0, self.x() - self.speed))

    def move_right(self):
        self.setX(min(self.scene_width - self.rect().width(), self.x() + self.speed))

    def expand(self):
        self.power_timer.stop()
        old_width = self.rect().width()
        new_width = self.normal_width * 1.5
        self.setRect(0, 0, new_width, self.rect().height())
        self.setX(self.x() - (new_width - old_width) / 2)
        self.power_timer.start(10000)

    def shrink(self):
        self.power_timer.stop()
        new_width = self.normal_width * 0.75
        current_center = self.x() + self.rect().width() / 2
        self.setRect(0, 0, new_width, self.rect().height())
        self.setX(current_center - new_width / 2)
        self.power_timer.start(8000)

    def make_sticky(self):
        self.power_timer.stop()
        self.sticky = True
        self.setBrush(QBrush(QColor(50, 205, 50)))
        self.power_timer.start(15000)

    def reset_power(self):
        current_center = self.x() + self.rect().width() / 2
        self.setRect(0, 0, self.normal_width, self.rect().height())
        self.setX(current_center - self.normal_width / 2)
        self.sticky = False
        self.setBrush(QBrush(QColor(70, 130, 180)))


# Ball Class
class Ball(QGraphicsEllipseItem):
    def __init__(self, scene_width, scene_height, game):
        super().__init__(0, 0, 15, 15)
        gradient = QRadialGradient(7, 7, 7, 3, 3)
        gradient.setColorAt(0, QColor(255, 255, 255))
        gradient.setColorAt(0.7, QColor(220, 20, 60))
        gradient.setColorAt(1, QColor(139, 0, 0))
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(Qt.GlobalColor.transparent))
        self.setPos(scene_width / 2, scene_height / 2)
        self.vx = random.choice([-4, 4])
        self.vy = -4
        self.scene_width = scene_width
        self.scene_height = scene_height
        self.in_play = True
        self.game = game
        self.trail_points = []
        self.trail_timer = 0

    def move(self):
        if not self.in_play:
            return

        self.setPos(self.x() + self.vx, self.y() + self.vy)

        # Wall collisions
        if self.x() <= 0 or self.x() + self.rect().width() >= self.scene_width:
            self.vx *= -1
        if self.y() <= 0:
            self.vy *= -1

        # Fell out
        if self.y() > self.scene_height:
            self.in_play = False
            self.game.ball_lost()

        # Trail
        self.trail_timer += 1
        if self.trail_timer >= 3:
            self.trail_points.append((self.x() + 7.5, self.y() + 7.5))
            self.trail_timer = 0
            if len(self.trail_points) > 8:
                self.trail_points.pop(0)

    def reset(self):
        self.setPos(self.scene_width / 2, self.scene_height / 2)
        self.vx = random.choice([-4, 4])
        self.vy = -4
        self.in_play = True
        self.trail_points = []

    def draw_trail(self, painter):
        if len(self.trail_points) < 2:
            return
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(len(self.trail_points) - 1):
            alpha = int(i / len(self.trail_points) * 255)
            size = 5 + i * 0.5
            gradient = QRadialGradient(self.trail_points[i][0], self.trail_points[i][1], size)
            gradient.setColorAt(0, QColor(255, 100, 100, alpha))
            gradient.setColorAt(1, QColor(255, 0, 0, 0))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(QPointF(self.trail_points[i][0], self.trail_points[i][1]), size, size)


# Brick Class
class Brick(QGraphicsRectItem):
    def __init__(self, x, y, width, height, type="normal", health=1, game=None):
        super().__init__(0, 0, width, height)
        self.type = type
        self.health = health
        self.max_health = health
        self.game = game
        self.setPos(x, y)
        self.update_color()
        self.setPen(QPen(Qt.PenStyle.NoPen))

    def update_color(self):
        if self.type == "normal":
            colors = [QColor(220, 20, 60), QColor(255, 140, 0), QColor(255, 215, 0),
                    QColor(50, 205, 50), QColor(65, 105, 225)]
            color_idx = min(self.max_health - self.health, len(colors) - 1)
            self.setBrush(QBrush(colors[color_idx]))
        elif self.type == "strong":
            self.setBrush(QBrush(QColor(70, 130, 180)))
        elif self.type == "explosive":
            self.setBrush(QBrush(QColor(178, 34, 34)))
        elif self.type == "powerup":
            gradient = QLinearGradient(0, 0, self.rect().width(), 0)
            gradient.setColorAt(0, QColor(255, 105, 180))
            gradient.setColorAt(0.5, QColor(255, 215, 0))
            gradient.setColorAt(1, QColor(255, 105, 180))
            self.setBrush(QBrush(gradient))

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            if self.type == "explosive":
                self.game.explode_brick(self)
            elif self.type == "powerup":
                self.game.spawn_powerup(self.x() + self.rect().width()/2, self.y() + self.rect().height()/2)
            return True
        else:
            self.update_color()
            return False


# PowerUp Class
class PowerUp(QGraphicsEllipseItem):
    def __init__(self, x, y, type, game):
        super().__init__(0, 0, 20, 20)
        self.type = type
        self.game = game
        self.setPos(x, y)
        self.vy = 2
        self.setPen(Qt.PenStyle.NoPen)
        colors = {"expand": QColor(65, 105, 225), "shrink": QColor(255, 99, 71),
                "multiball": QColor(255, 215, 0), "extra_life": QColor(50, 205, 50),
                "sticky": QColor(138, 43, 226)}
        self.setBrush(QBrush(colors.get(type, QColor(255, 255, 255))))

    def move(self):
        self.setPos(self.x(), self.y() + self.vy)
        if self.y() > self.game.scene_height:
            self.game.scene().removeItem(self)
            return True
        return False


# Particle Class
class Particle(QGraphicsEllipseItem):
    def __init__(self, x, y, color):
        super().__init__(0, 0, 4, 4)
        self.setPos(x, y)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.lifetime = 30
        self.setBrush(QBrush(color))
        self.setPen(Qt.PenStyle.NoPen)

    def update(self):
        self.setPos(self.x() + self.vx, self.y() + self.vy)
        self.lifetime -= 1
        self.setOpacity(max(0, self.lifetime / 30.0))
        return self.lifetime > 0


# GameView Class
class GameView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFixedSize(800, 600)
        self.setSceneRect(0, 0, 800, 600)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Game state
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.paused = False
        self.scene_width = 800
        self.scene_height = 600

        # Game objects
        self.paddle = Paddle(self.scene_width, self.scene_height)
        self.scene().addItem(self.paddle)
        self.balls = []
        self.bricks = []
        self.powerups = []
        self.particles = []

        # Load levels
        self.levels = self.load_levels()
        self.create_bricks()
        
        # Add initial ball after bricks are created
        initial_ball = Ball(self.scene_width, self.scene_height, self)
        self.scene().addItem(initial_ball)
        self.balls.append(initial_ball)

        # UI
        self.setup_ui()

        # Game loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(16)
        
        self.setFocus()

    # === Level and Brick Creation ===
    def load_levels(self):
        return [
            {
                "layout": [
                    "1111111111",
                    "1222222221",
                    "1233333321",
                    "1234444321",
                    "1234543210"
                ],
                "mapping": {
                    "1": {"type": "normal", "health": 1},
                    "2": {"type": "normal", "health": 2},
                    "3": {"type": "normal", "health": 3},
                    "4": {"type": "strong", "health": 2},
                    "5": {"type": "explosive", "health": 1}
                }
            }
        ]

    def create_bricks(self):
        if self.level > len(self.levels):
            return
            
        mapping = self.levels[self.level-1]["mapping"]
        brick_width = 70
        brick_height = 20
        layout = self.levels[self.level-1]["layout"]
        
        rows = len(layout)
        cols = max(len(row) for row in layout)

        for row_idx, row_data in enumerate(layout):
            for col_idx, brick_type in enumerate(row_data):
                if brick_type != "0" and brick_type in mapping:
                    brick_info = mapping[brick_type]
                    brick = Brick(
                        10 + col_idx * (brick_width + 5),
                        30 + row_idx * (brick_height + 5),
                        brick_width,
                        brick_height,
                        brick_info["type"],
                        brick_info["health"],
                        self
                    )
                    self.scene().addItem(brick)
                    self.bricks.append(brick)

        # Random power-up bricks
        for _ in range(3):
            row = random.randint(0, rows-1)
            col = random.randint(0, cols-1)
            if row < len(layout) and col < len(layout[row]) and layout[row][col] != "0":
                brick = Brick(10 + col * (brick_width + 5),
                              30 + row * (brick_height + 5),
                              brick_width, brick_height,
                              "powerup", 1, self)
                self.scene().addItem(brick)
                self.bricks.append(brick)

    # === UI Setup ===
    def setup_ui(self):
        self.score_text = QGraphicsTextItem(f"Score: {self.score}")
        self.score_text.setDefaultTextColor(Qt.GlobalColor.white)
        self.score_text.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.score_text.setPos(10, 10)
        self.scene().addItem(self.score_text)

        self.lives_text = QGraphicsTextItem(f"Lives: {self.lives}")
        self.lives_text.setDefaultTextColor(Qt.GlobalColor.white)
        self.lives_text.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.lives_text.setPos(700, 10)
        self.scene().addItem(self.lives_text)

        self.level_text = QGraphicsTextItem(f"Level: {self.level}")
        self.level_text.setDefaultTextColor(Qt.GlobalColor.white)
        self.level_text.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.level_text.setPos(350, 10)
        self.scene().addItem(self.level_text)

        self.game_over_text = QGraphicsTextItem("GAME OVER\nPress R to restart")
        self.game_over_text.setDefaultTextColor(Qt.GlobalColor.red)
        self.game_over_text.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.game_over_text.setPos(250, 250)
        self.game_over_text.setVisible(False)
        self.scene().addItem(self.game_over_text)

        self.pause_text = QGraphicsTextItem("PAUSED\nPress P to continue")
        self.pause_text.setDefaultTextColor(Qt.GlobalColor.yellow)
        self.pause_text.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.pause_text.setPos(280, 250)
        self.pause_text.setVisible(False)
        self.scene().addItem(self.pause_text)

    # === Game Loop ===
    def game_loop(self):
        try:
            if self.paused or self.game_over:
                return

            # Move balls
            for ball in self.balls[:]:
                try:
                    ball.move()
                except Exception as e:
                    print(f"Ball move error: {e}")
                    try:
                        self.scene().removeItem(ball)
                        self.balls.remove(ball)
                    except:
                        pass

            # Move power-ups
            for powerup in self.powerups[:]:
                try:
                    if powerup.move():
                        self.powerups.remove(powerup)
                except Exception as e:
                    print(f"Powerup move error: {e}")
                    try:
                        self.scene().removeItem(powerup)
                        self.powerups.remove(powerup)
                    except:
                        pass

            # Update particles
            for particle in self.particles[:]:
                try:
                    if not particle.update():
                        self.scene().removeItem(particle)
                        self.particles.remove(particle)
                except Exception as e:
                    print(f"Particle update error: {e}")
                    try:
                        self.scene().removeItem(particle)
                        self.particles.remove(particle)
                    except:
                        pass

            # Powerup collisions with paddle (using manual collision detection)
            for powerup in self.powerups[:]:
                try:
                    powerup_rect = powerup.sceneBoundingRect()
                    paddle_rect = self.paddle.sceneBoundingRect()
                    
                    if powerup_rect.intersects(paddle_rect):
                        self.apply_powerup(powerup.type)
                        self.scene().removeItem(powerup)
                        self.powerups.remove(powerup)
                except Exception as e:
                    print(f"Powerup collision error: {e}")
                    try:
                        self.scene().removeItem(powerup)
                        self.powerups.remove(powerup)
                    except:
                        pass

            # Ball collisions
            for ball in self.balls[:]:
                # Paddle collision
                try:
                    ball_rect = ball.sceneBoundingRect()
                    paddle_rect = self.paddle.sceneBoundingRect()
                    
                    if ball_rect.intersects(paddle_rect):
                        paddle_center = self.paddle.x() + self.paddle.rect().width()/2
                        ball_center = ball.x() + ball.rect().width()/2
                        offset = (ball_center - paddle_center)/(self.paddle.rect().width()/2)
                        ball.vx = offset * 5
                        ball.vy = -abs(ball.vy)
                        if self.paddle.sticky:
                            ball.in_play = False
                            ball.setPos(ball.x(), self.paddle.y() - ball.rect().height())
                except Exception as e:
                    print(f"Paddle collision error: {e}")

                # Brick collisions
                for brick in self.bricks[:]:
                    try:
                        ball_rect = ball.sceneBoundingRect()
                        brick_rect = brick.sceneBoundingRect()
                        
                        if ball_rect.intersects(brick_rect):
                            # Simple collision response
                            ball.vy *= -1
                            
                            if brick.hit():
                                self.scene().removeItem(brick)
                                self.bricks.remove(brick)
                                self.score += 10 * brick.max_health
                                self.score_text.setPlainText(f"Score: {self.score}")
                                self.create_particles(brick.x() + brick.rect().width()/2,
                                                      brick.y() + brick.rect().height()/2,
                                                      brick.brush().color())
                            
                            if len(self.bricks) == 0:
                                self.next_level()
                            break
                    except Exception as e:
                        print(f"Brick collision error: {e}")
                        try:
                            self.scene().removeItem(brick)
                            self.bricks.remove(brick)
                        except:
                            pass

            # Remove lost balls
            for ball in self.balls[:]:
                if not ball.in_play and ball.y() > self.scene_height:
                    try:
                        self.scene().removeItem(ball)
                        self.balls.remove(ball)
                    except:
                        pass
                    
            if len(self.balls) == 0:
                self.ball_lost()

        except Exception as e:
            print(f"Game loop critical error: {e}")
            import traceback
            traceback.print_exc()

    # === Game Logic Methods ===
    def ball_lost(self):
        self.lives -= 1
        self.lives_text.setPlainText(f"Lives: {self.lives}")
        if self.lives <= 0:
            self.end_game()
        else:
            new_ball = Ball(self.scene_width, self.scene_height, self)
            self.scene().addItem(new_ball)
            self.balls.append(new_ball)

    def end_game(self):
        self.game_over = True
        self.game_over_text.setVisible(True)

    def next_level(self):
        self.level += 1
        if self.level > len(self.levels):
            self.win_game()
            return
            
        self.level_text.setPlainText(f"Level: {self.level}")
        
        # Clear existing bricks
        for brick in self.bricks[:]:
            self.scene().removeItem(brick)
            self.bricks.remove(brick)
            
        # Create new bricks for the next level
        self.create_bricks()
        
        # Reset paddle position
        self.paddle.reset_power()
        self.paddle.setPos(self.scene_width/2 - self.paddle.rect().width()/2,
                           self.scene_height - 40)

    def win_game(self):
        self.game_over = True
        self.game_over_text.setPlainText("YOU WIN!\nPress R to play again")
        self.game_over_text.setVisible(True)

    def reset_game(self):
        # Clear all game objects
        for brick in self.bricks[:]:
            self.scene().removeItem(brick)
            self.bricks.remove(brick)
            
        for ball in self.balls[:]:
            self.scene().removeItem(ball)
            self.balls.remove(ball)
            
        for powerup in self.powerups[:]:
            self.scene().removeItem(powerup)
            self.powerups.remove(powerup)
            
        for particle in self.particles[:]:
            self.scene().removeItem(particle)
            self.particles.remove(particle)

        # Reset game state
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.score_text.setPlainText(f"Score: {self.score}")
        self.lives_text.setPlainText(f"Lives: {self.lives}")
        self.level_text.setPlainText(f"Level: {self.level}")
        self.game_over_text.setVisible(False)

        # Reset paddle and create new ball
        self.paddle.reset_power()
        self.paddle.setPos(self.scene_width/2 - self.paddle.rect().width()/2,
                           self.scene_height - 40)
                           
        new_ball = Ball(self.scene_width, self.scene_height, self)
        self.scene().addItem(new_ball)
        self.balls.append(new_ball)
        
        # Create bricks for the first level
        self.create_bricks()

    def explode_brick(self, brick):
        self.create_particles(brick.x() + brick.rect().width()/2,
                              brick.y() + brick.rect().height()/2,
                              QColor(255, 165, 0), 30)
        
        # Remove nearby bricks (explosion effect)
        for other_brick in self.bricks[:]:
            if other_brick is not brick:
                dx = (other_brick.x() + other_brick.rect().width()/2) - (brick.x() + brick.rect().width()/2)
                dy = (other_brick.y() + other_brick.rect().height()/2) - (brick.y() + brick.rect().height()/2)
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 100:  # Explosion radius
                    self.scene().removeItem(other_brick)
                    self.bricks.remove(other_brick)
                    self.score += 10 * other_brick.max_health
                    self.score_text.setPlainText(f"Score: {self.score}")

    def spawn_powerup(self, x, y):
        powerup_types = ["expand", "shrink", "multiball", "extra_life", "sticky"]
        powerup_type = random.choice(powerup_types)
        powerup = PowerUp(x - 10, y - 10, powerup_type, self)
        self.scene().addItem(powerup)
        self.powerups.append(powerup)

    def apply_powerup(self, type):
        if type == "expand":
            self.paddle.expand()
        elif type == "shrink":
            self.paddle.shrink()
        elif type == "multiball":
            for _ in range(2):
                new_ball = Ball(self.scene_width, self.scene_height, self)
                new_ball.setPos(self.paddle.x() + self.paddle.rect().width()/2,
                                self.paddle.y() - new_ball.rect().height())
                new_ball.vx = random.choice([-4, -3, 3, 4])
                new_ball.vy = -4
                self.scene().addItem(new_ball)
                self.balls.append(new_ball)
        elif type == "extra_life":
            self.lives += 1
            self.lives_text.setPlainText(f"Lives: {self.lives}")
        elif type == "sticky":
            self.paddle.make_sticky()

    # === Particles and Sound ===
    def create_particles(self, x, y, color, count=15):
        for _ in range(count):
            particle = Particle(x, y, color)
            self.scene().addItem(particle)
            self.particles.append(particle)

    def play_sound(self, sound_type):
        pass  # Placeholder

    # === Drawing ===
    def drawBackground(self, painter, rect):
        gradient = QLinearGradient(0, 0, 0, self.scene_height)
        gradient.setColorAt(0, QColor(25, 25, 50))
        gradient.setColorAt(1, QColor(10, 10, 30))
        painter.fillRect(rect, gradient)
        
        # Draw ball trails
        for ball in self.balls:
            ball.draw_trail(painter)

    # === Input Handling ===
    def keyPressEvent(self, event):
        if self.game_over and event.key() == Qt.Key.Key_R:
            self.reset_game()
            return
            
        if event.key() == Qt.Key.Key_P:
            self.paused = not self.paused
            self.pause_text.setVisible(self.paused)
            return
            
        if event.key() == Qt.Key.Key_Left:
            self.paddle.move_left()
        elif event.key() == Qt.Key.Key_Right:
            self.paddle.move_right()
        elif event.key() == Qt.Key.Key_Space:
            for ball in self.balls:
                if not ball.in_play:
                    ball.in_play = True
                    ball.vy = -4


# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Breakout - PyQt6")
        self.setFixedSize(800, 600)
        
        # Create scene first
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        
        # Then create view with the scene
        self.view = GameView(self.scene, self)
        self.setCentralWidget(self.view)


# Run Game
def main():
    app = QApplication(sys.argv)
    
    try:
        win = MainWindow()
        win.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

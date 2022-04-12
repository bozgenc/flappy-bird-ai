# import packages to build the game
from __future__ import print_function
import pygame
import neat
import time
import os
import random

pygame.font.init()
pygame.init()
pygame.display.set_caption("Flappy Bird AI")

GEN = 0
ALIVE = 25

WIN_WIDTH = 500
WIN_HEIGHT = 800
SCREEN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

STAT_FONT = pygame.font.SysFont("comicsans", 30)
END_FONT = pygame.font.SysFont("comicsans", 70)

# görseller yüklenip, render edilmeye hazır hale getirilir
pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird" + str(x) + ".png"))) for x in
               range(1, 4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")).convert_alpha())


class Bird:
    IMGS = bird_images
    MAX_ROTATION = 25  # kuş zıplayınca ne kadar rotate olacak
    ROT_VEL = 20  # rotate hızı
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x  # kuşun başlangıç x koordinatı
        self.y = y  # kuşun başlangıç y koordinatı
        self.tilt = 0  # tilt açısı
        self.tick_count = 0  #
        self.vel = 0  # hız
        self.height = self.y
        self.img_count = 0  # anlık olarak hangi bird image render ediliyor
        self.img = self.IMGS[0] # image arrayinden uygun olan kuş görselini alıyoruz

    def jump(self):
        self.vel = -10.5  # zıplarken velocitynin negatif olması gerekli çünkü ekranın sol üst köşesi (0,0) noktası
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1  # her kare 1 geçişinde artırıyoruz

        # düşerken
        displacement = self.vel * (self.tick_count) + 0.5 * (3) * (self.tick_count) ** 2  # yer değiştirme miktarı

        # hız çok artarsa bi noktada yer değiştirme miktarını sabitliyoruz aksi takdirde animasyon açısından tuhaf görünüyor
        if displacement >= 16:
            displacement = 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 160  # borular arasındaki mesafe
    VEL = 8    # boruların hareket hızı

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)  # üst boru
        self.PIPE_BOTTOM = pipe_img  # alt boru

        self.passed = False # boru geçildi mi
        self.set_height()

    def set_height(self): # boruya random bir yükseklik veriyoruz (50, 450 piksel arası)
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):  # kuşun yere ya da boruya çarptığını anlamak için lazım
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        return False


class Base: # oyundaki zemin için class
    VEL = 8
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self): # zemini hareket ettiriyoruz
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen, alive):
    win.blit(bg_img, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()


def main(genomes, config):
    global GEN
    GEN += 1
    alive = 25
    nets = []  # genome ile associate edilen neural network
    ge = []  # genome
    birds = []  # networku kullanarak ilerleyen bird

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config) # konfigürasyon dosyamız ile sinir ağını besliyoruz
        nets.append(net)
        birds.append(Bird(230,250))
        g.fitness = 0 # başlangıçta fitness skorları 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        pipe_ind  = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width(): # ilk pipe geçildiyse ikinci pipe'a bak
                pipe_ind = 1

        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1 # bird hareket ettikçe devam etmesi için fitness skorunu artırıyoruz, bu kadar az olmasının sebebi saniyede 30 kere çalışıyor (30 fps) yani saniye başına fitness skoru 1 artar

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom))) # bird ile en yakın pipe 'ın y koordinatlarını karşılaştırıyoruz
                                                                                                                            # sonuca göre aktivasyon fonksiyonu çalışıyor
            if output[0] > 0.5: # tan(h) 0.5 den büyükse kuş zıplıyor
                bird.jump()
        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird): # genomlardan biri boruya çarparsa, fitness scorundan bir azalıyor, böylece  # hata yapan bird favor olmamış oluyor
                    ge[x].fitness -= -1  # kuş çarparsa genomun fitness skorunu düşürüyoruz ki neural network sonraki jenerasyon için daha iyi genomlar seçsin
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)
                    alive -= 1

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe: # bird pipe'ı geçiyorsa fitness skorunu artırıyoruz
            score += 1
            for g in ge:
                g.fitness += 5  # boruyu geçen genomun fitness skoru 5 artıyor
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds): # bird yere çakılırsa çıkarıyoruz
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0 :
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN, alive)



def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path) # config dosyasını içeri aldık

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)

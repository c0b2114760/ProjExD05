import math
import random
import sys
import time
from typing import Any

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ

global kokaton_hp
global boss_hp

def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate

def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0)
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル 
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"
        self.hyper_life = -1

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def change_state(self, state: str, hyper_life: int):

        """
        こうかとんに敵機、爆弾、ボスが当たったときのstateを変更する
        引数１ state:キャラクターの状態("normal" or "hyper")
        引数２ hyper_life:効果時間
        """
        self.state = state
        self.hyper_life = hyper_life


    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """

        if key_lst[pg.K_LSHIFT]:  # 左のShiftを押すと
            self.speed = 20  # 高速化する
            
        else:
            self.speed = 10
        #print(self.speed)

        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
                
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
        if self.hyper_life < 0:
            self.change_state("normal", -1)
        screen.blit(self.image, self.rect)
    
    def get_direction(self) -> tuple[int, int]:
        return self.dire


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, rad = 0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        # print(f"rad = {rad}")
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/beam.png"), angle + rad, 2.0)
        self.vx = math.cos(math.radians(angle + rad))
        self.vy = -math.sin(math.radians(angle + rad))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width*self.vx
        self.speed = 10


    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex04/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"EX05/fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        # self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        # self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル
        self.vx = random.randint(5,10)
        self.vy = random.randint(5,10)
        self.speed = 1

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

    
class Boss(pg.sprite.Sprite):
    """
    ボスに関するクラス
    """

    #boss_img = pg.transform.rotozoom(pg.image.load("ex05/fig/alien3.png"), 0, 3.0)
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("ex05/fig/alien3.png"), 0, 3.0)
        self.rect = self.image.get_rect()
        self.vy = +1
        self.vx = +1
        self.rect.center = random.randint(0, WIDTH - self.rect.x * 2), random.randint(0, HEIGHT - self.rect.y * 2)
        self.interval = random.randint(500, 1000)  # 爆弾投下インターバル

    def update(self):
        self.rect.centerx += self.vy
        self.rect.centery += self.vx
        self.speed = 6



class NeoBeam(pg.sprite.Sprite):
    def __init__(self, bird: Bird, num: int):   # NeoBeamクラスのイニシャライザの引数を，こうかとんbirdとビーム数numとする
        super().__init__()
        self.num = num
        self.bird = bird

    def gen_beams(self):
        """
        NeoBeamクラスのgen_beamsメソッドで，
        ‐50°～+51°の角度の範囲で指定ビーム数の分だけBeamオブジェクトを生成し，
        リストにappendする → リストを返す
        """
        start_angle = -50
        end_angle = 51
        
        range_size = end_angle - start_angle
        angle_interval = range_size / (self.num-1)

        angles = [start_angle + i * angle_interval for i in range(self.num)]

        #print(angles)

        neo_beams = [Beam(self.bird,rad=angles[i]) for i in range(self.num)]
        return neo_beams

class Flame(pg.sprite.Sprite):
    """
    ボスが放つ攻撃に関するクラス
    """
    def __init__(self, s_boss: "Boss", bird: Bird):
        super().__init__()
        self.image = pg.transform.rotozoom((pg.image.load("ex05/fig/flame.png")), 0, 0.1)
        self.rect = self.image.get_rect()
        # flameを放つbossから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(s_boss.rect, bird.rect)  
        self.rect.centerx = s_boss.rect.centerx
        self.rect.centery = s_boss.rect.centery+s_boss.rect.height/2
        self.speed = 5

    def update(self):
        """
        攻撃を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

        
        

def main():
    pg.display.set_caption("生き残れ！こうかとん！")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    
    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    boss = pg.sprite.Group()
    flame = pg.sprite.Group()
    
    

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            #print(event.type == pg.KEYDOWN, event.key == pg.K_SPACE, key_lst[pg.K_LSHIFT])
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE and key_lst[pg.K_LSHIFT] :
                    # print("f_key ON")
                """
                発動条件が満たされたら，NeoBeamクラスのイニシャライザにこうかとんと
                ビーム数を渡し，戻り値のリストをBeamグループに追加する
                """
                n_beams = NeoBeam(bird,5)
                beam_lst = n_beams.gen_beams()
                #print("a")
                #print(f"list in {beam_lst}")
                for i in beam_lst:
                    beams.add(i)
                
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))

        screen.blit(bg_img, [0, 0])
        
        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        # for bomb in pg.sprite.spritecollide(bird, bombs, True):
        #     if (bird.num > 1) and (bird.state == "normal") :
        #         exps.add(Explosion(bomb, 50))  # 爆発エフェクト
        #         bird.num -= 1
        #         bird.change_state("hyper", 100)
        #     elif bird.state == "hyper":
        #         bomb.kill()
                
        #     else:
        #         bird.change_img(8, screen) # こうかとん悲しみエフェクト
        #         pg.display.update()
        #         time.sleep(2)
        #         return
            
        if (tmr % 300) == 0:
            boss.add(Boss())

        for s_boss in boss:
            if (tmr%50) == 0:
                flame.add(Flame(s_boss, bird))
            
        
        if pg.sprite.spritecollide(bird, boss, True):
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            # pg.display.update()
            # time.sleep(2)
            #return
        
        if pg.sprite.groupcollide(boss, beams, True, True):
            
            exps.add(Explosion(s_boss, 100))
            bird.change_img(6, screen) # こうかとん喜びエフェクト
            # pg.display.update()
            # time.sleep(2)
            #return
        
        if pg.sprite.spritecollide(bird, flame, True):
            bird.change_img(6, screen) # こうかとん喜びエフェクト
            pg.display.update()
            time.sleep(2)
            return
        for s_flame in pg.sprite.groupcollide(flame, beams, True, True).keys():
            exps.add(Explosion(s_flame, 50))

    
        
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        boss.update()
        boss.draw(screen)
        flame.update()
        flame.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)
            
if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()



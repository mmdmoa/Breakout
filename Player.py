import pygame as pg
from pygame.locals import *
from pygame.math import Vector2 as Pos
from pygame.rect import Rect
from pygame.color import Color
from typing import Optional
from pygame.surface import Surface

from Window import Window
from EventHolder import EventHolder
from Assets import Assets
from Colors import Colors

import random as r
from Map import Map
from CommonResources import CommonResources

now = lambda: pg.time.get_ticks() / 1000

class Player :
    """
        Upgradeable abilities:
            paddle size,
            paddle speed,

    """

    def __init__( self, rect: Rect, color: Color) :

        self.events = CommonResources.event_holder
        self.colors = CommonResources.colors
        self.assets = CommonResources.assets
        self.window = CommonResources.window

        self.edge = 0

        self.init_rect = rect

        self.pos = Pos(rect.x, rect.y)
        self.size = Pos(rect.width, rect.height)

        self.color = color

        self.hype_armed = False
        self.gun_timer = -100
        self.shoot_timer = 0
        self.hype_gun_duration = 3
        self.gun_duration = 10
        self.gun_shoot_interval = 0.75
        self.hype_gun_shoot_interval = 0.1
        self.bullets = []
        self.bullet_size = Pos(3,10)
        self.bullet_speed = 0.2
        self.bullets_color = Colors.BLACK

        self.size_list  = []
        self.speed_list = []


        min_size = self.size.x * 0.1
        self.size_wing = 6
        self.size_index = 0
        self.min_size_index = -self.size_wing
        self.max_size_index = self.size_wing

        size_step = abs(self.size.x-min_size) / abs(self.min_size_index)


        for i in range(self.min_size_index,self.max_size_index+1):
            mult = i
            if i > 0:
                mult = (i * 2) ** 1.5

            new_size = self.size.x + (size_step * mult)
            self.size_list.append(new_size)


        self.size_index += abs(self.min_size_index)
        self.max_size_index += abs(self.min_size_index)
        self.min_size_index += abs(self.min_size_index)

        min_speed = self.size.y * 0.1

        self.speed_index = 0
        self.speed_wing = 6
        self.min_speed_index = -self.speed_wing
        self.max_speed_index = self.speed_wing

        speed_step = abs(self.size.y - min_speed) / abs(self.min_speed_index)

        for i in range(self.min_speed_index, self.max_speed_index+ 1) :
            new_speed = self.size.y + (speed_step * i)
            self.speed_list.append(new_speed)

        self.speed_list = self.speed_list[::-1]


        self.speed_index += abs(self.min_speed_index)
        self.max_speed_index += abs(self.min_speed_index)
        self.min_speed_index += abs(self.min_speed_index)



    def reset( self ):
        rect = self.init_rect
        self.gun_timer = -100
        self.bullets.clear()
        self.pos = Pos(rect.x, rect.y)
        self.size = Pos(rect.width, rect.height)
        self.size_index = self.size_wing
        self.speed_index = self.speed_wing

    @property
    def map_( self ) -> Map:
        return CommonResources.map_

    @property
    def border_color( self ):
        return self.color.lerp(Colors.BLACK,0.5)

    @property
    def rect( self ) :
        return Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)


    @property
    def speed( self ) :
        return (self.window.size.y * 0.07 - self.rect.height) * 0.1

    @property
    def speed_change_speed( self ):
        return self.rect.height * 0.1

    @property
    def size_change_speed( self ) :
        return self.rect.width * 0.1

    def move( self, hkeys ) :
        right = K_RIGHT in hkeys or K_d in hkeys
        left = K_LEFT in hkeys or K_a in hkeys
        if right and left : right = left = False

        if right :
            self.pos.x += self.speed
        if left :
            self.pos.x -= self.speed

        stick = not self.window.rect.contains(self.rect)

        if stick :
            if right :
                self.pos.x = self.window.size.x - self.rect.width
            if left :
                self.pos.x = 0


    def respeed( self ):
        center = self.rect.center
        self.size.y = self.speed_list[self.speed_index]
        rect = self.rect
        rect.center = center
        self.pos.x, self.pos.y = rect.x, rect.y


    def speed_up( self ):
        if self.speed_index == self.max_speed_index :
            return
        self.speed_index += 1

        self.respeed()


    def speed_down( self ):
        if self.speed_index == self.min_speed_index :
            return
        self.speed_index -= 1

        self.respeed()

    def resize( self ):
        center = self.rect.center
        self.size.x = self.size_list[self.size_index]
        rect = self.rect
        rect.center = center
        self.pos.x, self.pos.y = rect.x, rect.y

        fix = not self.window.rect.contains(self.rect)

        right = self.rect.center[0] >= self.window.size.x / 2

        if fix:
            if right:
                self.pos.x = self.window.size.x - self.size.x
            else:
                self.pos.x = 0


    def grow( self ) :
        if self.size_index == self.max_size_index:
            return
        self.size_index += 1

        self.resize()

    def shrink( self ) :
        if self.size_index == self.min_size_index:
            return
        self.size_index -= 1

        self.resize()

    def arm_up( self ):
        self.gun_timer = now()
        self.shoot_timer = self.gun_timer

    def hype_arm_up( self ):
        self.hype_armed = True
        self.arm_up()

    def shoot( self ):
        bullet_1 = Rect(self.pos.x,self.pos.y,self.bullet_size.x,self.bullet_size.y)
        bullet_2 = Rect(self.pos.x+self.size.x,self.pos.y
                            ,self.bullet_size.x,self.bullet_size.y)

        bullet_2.x -= bullet_2.w

        color = lambda: self.bullets_color
        if self.hype_armed:
            color = lambda: Colors.random_color()

        self.bullets.extend([(bullet_1,color()),(bullet_2,color())])

    def bullets_march( self ):
        for bullet,color in self.bullets:
            bullet.y -= bullet.h * self.bullet_speed

    def check_bullet_collisions( self ):


        breaker = False
        for brick in self.map_.bricks:
            brick_rect = brick.rect

            for bullet,c in zip(self.bullets,range(len(self.bullets))):
                bullet_rect = bullet[0]

                if brick_rect.colliderect(bullet_rect):
                    self.bullets.pop(c)
                    brick.health -= 1
                    breaker = True
                    break

            if breaker: break


    @property
    def is_armed( self ):
        duration = self.gun_duration
        if self.hype_armed:
            duration = self.hype_gun_duration

        return now() <= self.gun_timer + duration

    def check_events( self ) :
        hkeys = self.events.held_keys

        pkeys = self.events.pressed_keys



        if self.is_armed:

            gun_shoot_interval = self.gun_shoot_interval
            if self.hype_armed:
                gun_shoot_interval = self.hype_gun_shoot_interval

            if now() >= self.shoot_timer + gun_shoot_interval:
                self.shoot_timer = now()
                self.shoot()
        else:
            if self.hype_armed:
                self.hype_armed = False


        self.bullets_march()
        self.check_bullet_collisions()

        if self.events.is_dev:

            if K_v in pkeys:
                self.hype_arm_up()
            if K_f in pkeys:
                self.arm_up()
            if K_UP in pkeys :
                self.grow()
            if K_DOWN in pkeys :
                self.shrink()
            if K_w in pkeys:
                self.speed_up()
            if K_s in pkeys:
                self.speed_down()


        self.move(hkeys)


    def render( self, surface: Surface ) :
        for bullet,color in self.bullets:
            pg.draw.rect(surface,color,bullet)

        edge = self.edge
        if self.size.y < 10:
            edge = 0

        pg.draw.rect(surface, self.color, self.rect,border_radius=edge)
        pg.draw.rect(surface, self.border_color, self.rect,width=3,border_radius=edge)

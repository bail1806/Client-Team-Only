'''
Created on Nov 28, 2013

@author: Sean
'''

import os
import sys
import math
import pygame
import environments
import buttons
import rpyc

pygame.init()


def main(client, setupinfo=None):
    screensize = (1024, 720)
    screen = pygame.display.set_mode(screensize)
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(0)
    animate = True
    running = True

    background, background_rect = load_image("stars.jpg")
    screen.blit(background, background_rect)
    mouse_ptr = MouseCursor("pointer2.png")
    mouse_sel = MouseCursor("selected2.png")
    mouse = pygame.sprite.RenderUpdates((mouse_ptr))
    mouse.draw(screen)
    pygame.display.flip()
    #===========================================================================
    # Object Initialization:
    #===========================================================================
    star_system = System(screen, background, animate)
    characterresponse = client.root.get_state(object_id=0, object_type="Character")
    print characterresponse
    for character in characterresponse["response"]["Character"]:
        star_system.addunit(character)
    
    selected_unit = None

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if not mouse_ptr.down:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if selected_unit:
                        hover_unit = left_mouse_select_check(mouse_sel, star_system)
                        if hover_unit != selected_unit:
                            selected_unit.add_unit(hover_unit)
                            star_system.unit_list.remove(hover_unit)
                    print "SPACE BAR"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_ptr.pressed = mouse_sel.pressed = True
                        mouse_ptr.released = mouse_sel.released = False
                        selected_unit = left_mouse_select_check(mouse_ptr, star_system)
                        # while the mouse button is down, change its cursor
                        mouse.remove(mouse_ptr)
                        mouse.add(mouse_sel)
                    elif event.button == 3:
                        key_mod = pygame.key.get_mods()
                        if key_mod == 4097 or key_mod == 1:
                            hover_unit = star_system.unit_list.get_sprites_at(mouse_ptr.pos)
                            print "STACK REMOVING FROM", hover_unit
                            if hover_unit:
                                sprite = hover_unit[0].remove_unit()
                                if sprite:
                                    #splitresponse = client.root.split_stack(hover_unit[0].stack_id, sprite.id)
                                    #if splitresponse["Success"]:
                                    #   sprite.set_stack_id(splitresponse["response"]["stack id"])
                                    star_system.unit_list.add(sprite)
                                    #else:
                                    #   hover_unit[0].add_unit(sprite)
                            print "SHIFT RIGHT CLICK"
                        else:
                            hover_unit = star_system.unit_list.get_sprites_at(mouse_ptr.pos)
                            if hover_unit:
                                hover_unit[0].cycle_unit()
                            print "RIGHT CLICK"

            if event.type == pygame.MOUSEBUTTONUP:
                mouse_ptr.released = mouse_sel.released = True
                selected_unit = left_mouse_unselect_check(mouse, selected_unit, star_system)
                # while the mouse button is up, change its cursor
                mouse.remove(mouse_sel)
                mouse.add(mouse_ptr)

        screen.blit(background, background_rect)
        star_system.update()
        if selected_unit:
            selected_unit.update(True)
        mouse.update()
        star_system.draw()
        mouse.draw(screen)
        pygame.display.flip()


def left_mouse_select_check(mouse, star_system):
    for unit in star_system.unit_list:
        if unit.rect.collidepoint(mouse.pos) and unit.visible == 1:
            star_system.unit_list.move_to_front(unit)
            return unit
    for planet in star_system.planet_list:
        if planet.rect.collidepoint(mouse.pos):
            star_system.planets_move(planet)
            return None


def left_mouse_unselect_check(mouse, selected_unit, star_system):
    if selected_unit:
        for planet in star_system.planet_list:
            if planet.collide_rect.colliderect(selected_unit.rect):
                #moveresponse = client.root.move(stack_id=selected_unit.stack_id, location_id=(star_system.id * 10 + planet.id) * 10)
                selected_unit.loc_id = (star_system.id * 10 + planet.id) * 10 #=moveresponse["response"]["location"]
                return None
            for environ in planet.environment.environ_list:
                for point in environ.collision_points:
                    if selected_unit.rect.colliderect(pygame.Rect((point), (10, 10))):
                        #moveresponse = client.root.move(stack_id=selected_unit.stack_id, location_id=(star_system.id * 10 + planet.id) * 10 + environ.id)
                        selected_unit.loc_id = (star_system.id * 10 + planet.id) * 10 + environ.id #=moveresponse["response"]["location"]
                        return None
    '''    for unit in star_system.unit_list:
            if unit is not selected_unit:
                if unit.rect.colliderect(selected_unit.rect):
                    mergeresponse = client.root.merge_stack(unit.stack_id, selected_unit.stack_id)
                    if mergeresponse["Success"]:
                        unit.add_unit(selected_unit)
                        star_system.unit_list.remove(selected_unit)
    '''

class System():
    def __init__(self, screen, background, animate=None):
        self.screen = screen
        self.background = background
        self.id = 1
        self.animate = animate
        self.move_dir = None
        #=======================================================================
        # Planet Population
        #=======================================================================
        purple = Planet(self, 1, "purple", "left", "purple_planet.png")
        earth = Planet(self, 2, "earth", "center", "earth_planet.png")
        blue = Planet(self, 3, "blue", "right", "blue_planet.png")
        self.planet_list = pygame.sprite.LayeredUpdates((purple, earth, blue))
        #=======================================================================
        # Unit Population
        #=======================================================================
        cis = Unit("cis", 110, 5466, 9, "rebel_cis.jpg")
        megathron = Unit("megathron", 123, 5467, 9, "rebel_megathron.jpg")
        vagabond = Unit("vagabond", 123, 5468, 9, "imperial_vagabond.jpg")
        viper = Unit("viper", 130, 5469, 9, "imperial_viper.jpg")
        self.unit_list = pygame.sprite.LayeredDirty((cis, megathron, vagabond, viper))

    def addunit (self, unitdict):
        newunit = Unit(unitdict["name"], 110, unitdict["id"], unitdict["stack_id"], unitdict["img"])
        for unit in self.unit_list:
            if newunit.stack_id == unit.stack_id:
                unit.add_unit(newunit)
                break
            else:
                self.unit_list.add(newunit)
        
    def update(self):
        for planet in self.planet_list:
            planet.update()
            planet.environment.update()
        self._update_unit_location()
        for unit in self.unit_list:
            unit.update()

    def draw(self):
        self.planet_list.draw(self.screen)
        for planet in self.planet_list:
            if planet.orient is "center":
                planet.environment.draw(self.screen)
                break
        self.unit_list.draw(self.screen)

    def planets_move(self, planet):
        self.move_dir = None
        # Move planets to the right
        if planet.orient is "left":
            self.move_dir = "right"
            self.planet_list.move_to_front(planet)
            for planet in self.planet_list:
                planet.update(self.move_dir, self.animate)
        # Move planets to the left
        elif planet.orient is "right":
            self.move_dir = "left"
            self.planet_list.move_to_front(planet)
            for planet in self.planet_list:
                planet.update(self.move_dir, self.animate)
        if self.move_dir and self.animate:
            self._planets_animate()

    def _planets_animate(self):
        # These need to be set in the singleton screen class
        cur_frame = 0    # <--
        frames = 64      # <--

        if self.move_dir is "right":
            while cur_frame < frames:
                for planet in self.planet_list:
                    if planet.prev_orient is "left":
                        planet.rect.move_ip(8, 0)
                    elif planet.prev_orient is "center":
                        planet.rect.move_ip(8, 0)
                    elif planet.prev_orient is "right":
                        planet.rect.move_ip(-16, 0)
                self.screen.blit(self.background, (0, 0))
                self.planet_list.draw(self.screen)
                pygame.display.flip()
                cur_frame += 1
        elif self.move_dir is "left":
            while cur_frame < frames:
                for planet in self.planet_list:
                    if planet.prev_orient is "left":
                        planet.rect.move_ip(16, 0)
                    elif planet.prev_orient is "center":
                        planet.rect.move_ip(-8, 0)
                    elif planet.prev_orient is "right":
                        planet.rect.move_ip(-8, 0)
                self.screen.blit(self.background, (0, 0))
                self.planet_list.draw(self.screen)
                pygame.display.flip()
                cur_frame += 1
        self.update()

    def _update_unit_location(self):
        for unit in self.unit_list:
            loc_id = unit.loc_id
            unit.visible = 1
            while loc_id:
                digits = int(math.log10(loc_id)) + 1
                if digits >= 3:
                    environ_id = loc_id % 10
                elif digits >= 2:
                    planet_id = loc_id % 10
                elif digits >= 1:
                    self.system_id = loc_id % 10
                loc_id /= 10
            for planet in self.planet_list:
                if planet.id == planet_id:
                    if environ_id == 0:
                        unit.pos = None
                        unit.loc = planet.collide_rect
                    else:
                        if planet.orient is "center":
                            for point in planet.environment.environ_list[environ_id - 1].collision_points:
                                if unit.rect.colliderect(pygame.Rect((point), (2, 2))):
                                    unit.pos = point
                                    unit.loc = None
                                    unit.update()
                                    break
                                else:
                                    if len(self.unit_list.get_sprites_at(point)) == 0:
                                        unit.pos = point
                                        unit.loc = None
                                        unit.update()
                                        break
                        else:
                            unit.visible = 0
                            break


class Planet(pygame.sprite.Sprite):
    def __init__(self, parent_system, planet_id, planet_name, planet_orientation, image):
        self.parent = parent_system
        self.id = planet_id
        self.name = planet_name
        self.orient = planet_orientation
        self.prev_orient = None
        if self.orient is "left":
            self.pos = self.parent.screen.get_rect().midleft
        elif self.orient is "center":
            self.pos = self.parent.screen.get_rect().center
        elif self.orient is "right":
            self.pos = self.parent.screen.get_rect().midright
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(image, -1)
        self.collide_rect = self.rect.inflate(-50, -50)
        #=======================================================================
        # Environment Population
        #=======================================================================
        self.environment = environments.EnvironBox(self, self.rect)
        self.environment.addEnviron(1, 'W', 2, "Humans", "Animals", 'C')
        self.environment.addEnviron(2, 'U', 1, "Bricktons", "Animals", 'C')
        self.environment.addEnviron(3, 'F', 3, "Corruptons", "Animals", 'A')

    def update(self, move_dir=None, animate=None):
        self.prev_orient = self.orient
        if move_dir is "right":
            if self.orient is "left":
                self.pos = self.parent.screen.get_rect().center
                self.orient = "center"
            elif self.orient is "center":
                self.pos = self.parent.screen.get_rect().midright
                self.orient = "right"
            elif self.orient is "right":
                self.pos = self.parent.screen.get_rect().midleft
                self.orient = "left"
            if not animate:
                self.rect.center = self.pos
                self.collide_rect.center = self.pos
        elif move_dir is "left":
            if self.orient is "left":
                self.pos = self.parent.screen.get_rect().midright
                self.orient = "right"
            elif self.orient is "center":
                self.pos = self.parent.screen.get_rect().midleft
                self.orient = "left"
            elif self.orient is "right":
                self.pos = self.parent.screen.get_rect().center
                self.orient = "center"
            if not animate:
                self.rect.center = self.pos
                self.collide_rect.center = self.pos
        else:
            self.rect.center = self.pos
            self.collide_rect.center = self.pos

class Unit(pygame.sprite.DirtySprite):
    def __init__(self, unit_name, unit_location_id, unit_id, stack_id, image):
        self.name = unit_name
        self.id = unit_id
        self.stack_id = stack_id
        self.loc_id = unit_location_id
        self.pos = None
        self.loc = None
        pygame.sprite.DirtySprite.__init__(self)
        self.image, self.rect = load_image(image)
        self.prev_image = self.image
        self.dirty = 2
        self.stack_list = list()
        self.stack_list.append(self)

    def set_stack_id (self, new_stack_id):
        for unit in self.stack_list:
            unit.stack_id = new_stack_id
    
    def cycle_unit(self):
        if len(self.stack_list) > 1:
            sprite = self.stack_list.pop()
            self.stack_list.insert(0, sprite)
            if sprite == self:
                self.image = self.prev_image
            else:
                self.image = sprite.image

    def add_unit(self, sprite):
        #sprite.visible = 0
        #sprite.loc_id = self.loc_id
        #sprite.pos = self.pos
        #sprite.loc = self.loc
        sprite.set_stack_id(self.stack_id)
        self.stack_list.extend(sprite.stack_list)
        sprite.stack_list = list()
        for sprite in self.stack_list:
            sprite.image = sprite.prev_image

    def remove_unit(self):
        if len(self.stack_list) > 1:
            sprite = self.stack_list.pop()
            if sprite == self:
                self.stack_list.insert(0, self)
                sprite = self.stack_list.pop()
            if len(self.stack_list) == 1:
                self.image = self.prev_image
            sprite.visible = 1
            sprite.loc_id = self.loc_id
            sprite.pos = self.pos
            sprite.loc = self.loc
            sprite.stack_list.append(sprite)
            return sprite
        else:
            return None

    def update(self, selected=None, animate=None):
        if selected:
            self.pos = pygame.mouse.get_pos()
            self.rect.center = self.pos
        else:
            try:
                if self.loc:
                    self.rect.clamp_ip(self.loc)
                else:
                    self.rect.center = self.pos
            except:
                print "ERROR:", self.name, "is drifting"
                return


class MouseCursor(pygame.sprite.Sprite):
    def __init__(self, name):
        self.screen = pygame.display.get_surface()
        self.pos = self.screen.get_rect().center
        self.pressed = False
        self.down = False
        self.released = False
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(name, -1)
        self.rect.center = self.pos

    def update(self):
        self.pos = pygame.mouse.get_pos()
        self.rect.midtop = self.pos
        if self.pressed:
            self.down = True
            self.rect.move_ip(-10, -10)
        if self.released:
            self.down = False
            self.pressed = False


def load_image(image, colorkey=None):
    path = os.path.join('Data', image)
    print path
    try:
        image = pygame.image.load(path)
    except pygame.error, message:
        print 'Can not load image:', image
        raise SystemExit, message
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)  # pygame.RLEACCEL can improve performance
    else:
        image = image.convert_alpha()
    return image, image.get_rect()

if __name__ == '__main__':
    main()

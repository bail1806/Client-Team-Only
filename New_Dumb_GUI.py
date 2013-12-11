'''
Created on Nov 28, 2013

@author: Sean
'''

import pygame
import buttons
import rpyc
from system import System
from loadimage import load_image



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




if __name__ == '__main__':
    main()

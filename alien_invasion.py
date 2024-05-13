import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    '''Overall class to manage game assets and behavior'''

    def __init__(self):
        '''Initialize the game, create game resources'''
        pygame.init()
        self.settings = Settings()
        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("AL13N 1NV3S10N")

        self.stats = GameStats(self)
        self.sb =Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        #Make the play button
        self.play_button= Button(self, "PLAY THE GAME")
        
        
    def run_game(self):
        '''Start the main loop for the game'''    
        while True:
            self._check_events()
            
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()
            
            
    def _check_events(self):
        ''' Responds to key and mouse events'''
        for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    self._check_play_button(mouse_pos)
                elif event.type == pygame.KEYDOWN:
                    self._check_keydown_events(event)
                elif event.type == pygame.KEYUP:
                    self._check_keyup_events(event)
    

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks play"""
        button_clicked =self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            #Reset the game settings
            self.settings.initialize_dynamic_settings()

            #Reset game stats
            self.stats.reset_stats()
            self.stats.game_active = True  
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            #discard remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            #Create new alien fleet and center ship
            self._create_fleet()
            self.ship.center_ship()

            #Hide the mouse cursor
            pygame.mouse.set_visible(False)              
    

    def _check_keydown_events(self, event):
        """responds to pressing of keys"""
        #Move the ship to the right
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        #Move the ship to the left
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        #Move the ship up
        elif event.key == pygame.K_UP:
            self.ship.moving_up = True
        #Move the ship down
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = True
        #Press q to quit
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """Responds to key releases"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_UP:
            self.ship.moving_up = False
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = False
    

    def _create_fleet(self):
        """Create a fleet of aliens"""
        #Spacing between aliens is one alien width, height

        #Make an alien
        alien = Alien(self)
        self.aliens.add(alien)
        alien_width, alien_height = alien.rect.size

        available_space_x = self.settings.screen_width - (2*alien_width)
        number_aliens_x = available_space_x // (2*alien_width)

        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - 3*alien_height - ship_height)
        number_rows = available_space_y // (2*alien_height)

        #Create the full fleet of aliens
        for row_num in range(number_rows):
            for alien_num in range(number_aliens_x):
                self._create_alien(alien_num, row_num)


    def _create_alien(self, alien_number, row_number):
        """Create an alien and place it in a row"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width +2*alien_width*alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2*alien.rect.height*row_number
        self.aliens.add(alien)

    
    def _check_fleet_edges(self):
        """Respond appropriately if any aliens hit the edges"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break
    

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet direction"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1


    def _fire_bullet(self):
        """Create a new bullet and adds it to the bullet group"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
    

    def _update_bullets(self):
        """Update bullet position and discard old ones"""
        #Update bullet position
        self.bullets.update()

        #Get rid of old bullets
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        #print(len(self.bullets))

        self._check_bullet_alien_collisions()
    

    def _check_bullet_alien_collisions(self):
        """respond to bullet-alien collisions"""
        #Remove any aliens and bullet that collided
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points*len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            #Discard all existing bullets and spawn new fleet
            self.bullets.empty()
            self._create_fleet()
            self.ship.center_ship()
            self.settings.increase_speed()  

            #increase level
            self.stats.level += 1
            self.sb.prep_level()
    

    def _check_aliens_bottom(self):
        """Check if any aliens havce reached the bottom of screen"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                #Treat this as if the ship is hit
                self._ship_hit()
                break
    

    def _ship_hit(self):
        """Responds to ship being hit by alien"""
        if self.stats.ships_left > 0:
            #Decrement ships_left
            self.stats.ships_left -=1
            self.sb.prep_ships()

            #Discard remaining aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

            #Create new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()

            #Pause
            sleep(0.5)
        else:
            self.ship.center_ship()
            self.stats.game_active = False
            pygame.mouse.set_visible(True)
    

    def _update_aliens(self):
        """Update the positions of all aliens in the fleet"""
        self._check_fleet_edges()
        self.aliens.update()

        #Look for alien-ship collisions
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            #print('Ship hit!')
            self._ship_hit()
        
        self._check_aliens_bottom()


    def _update_screen(self):
        #update screen background
        self.screen.fill(self.settings.bg_color)

        #set ship on the screen
        self.ship.blitme()

        #sets bullet on the screen
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        #Draw the score info
        self.sb.show_score()

        #dRAW THE PLAY BUTTON IF THE GAME IS INACTIVE.
        if not self.stats.game_active:
            self.play_button.draw_button()
            
        # Update the screen
        pygame.display.flip()


if __name__ == '__main__':
    # Make a game instance and run the game
    ai = AlienInvasion()
    ai.run_game()

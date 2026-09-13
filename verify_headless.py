"""Headless verify: run real main(), screenshot at frame 60, auto-QUIT."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import pygame
import office_monitor as om

orig_flip = pygame.display.flip
count = [0]

def flip():
    count[0] += 1
    orig_flip()
    if count[0] == 60:
        scr = pygame.display.get_surface()
        os.makedirs('screenshots', exist_ok=True)
        pygame.image.save(scr, 'screenshots/headless_verify.png')
        pygame.event.post(pygame.event.Event(pygame.QUIT))

pygame.display.flip = flip
om.main()
print('VERIFY_OK screenshot saved at frame', count[0])
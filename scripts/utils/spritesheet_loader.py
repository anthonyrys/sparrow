import pygame

SPRITESHEET_STOP_COLOR = (255, 0, 0, 255)

def load_spritesheet(pngpath, frames=None, colorkey=(0, 0, 0), scale=1.0):
    images = []
    sheet = pygame.image.load(pngpath).convert_alpha()

    width = sheet.get_width()
    height = sheet.get_height()

    image_count = 0
    start, stop = 0, 0
    i = 0

    for i in range(width):
        if sheet.get_at((i, 0)) != SPRITESHEET_STOP_COLOR:
            continue
    
        stop = i
        image = pygame.Surface((stop - start, height)).convert_alpha()
        image.set_colorkey(colorkey)
        image.blit(sheet, (0, 0), (start, 0, stop - start, height))

        if scale != 1.0:
            image = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale)).convert_alpha()

        if frames:
            for _ in range(frames[image_count]):
                images.append(image)

        else:
            images.append(image)

        image_count += 1
        start = stop + 1

    return images

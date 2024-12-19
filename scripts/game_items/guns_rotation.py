import pygame


def get_rotated_parameters(image, pos, origin_pos, angle):
    """
    Calculates the position of an image rotated around a given point.

    Parameters:
    - image: the image surface to be rotated
    - pos: the final position on the screen
    - origin_pos: the pivot point for rotation relative to the top-left corner of the image
    - angle: the rotation angle in degrees (counterclockwise)

    Returns:
    - rotated_image: the rotated image surface
    - rotated_image_rect: the bounding rect of the rotated image
    """
    origin_pos = (image.get_width() // 2, image.get_height() // 2)
    adjusted_topleft = (pos[0] - origin_pos[0], pos[1] - origin_pos[1])
    image_rect = image.get_rect(topleft=adjusted_topleft)
    original_center = image_rect.center
    pivot_offset = pygame.math.Vector2(pos) - pygame.math.Vector2(original_center)
    rotated_offset = pivot_offset.rotate(-angle)
    rotated_image_center = (original_center[0] + rotated_offset.x, original_center[1] + rotated_offset.y)
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)

    return rotated_image, rotated_image_rect
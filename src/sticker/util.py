from PIL import Image
import numpy as np

def is_image_suitable_for_achievement(image: Image.Image) -> bool:
    image_array = np.array(image)

    if image_array.shape[2] == 4:
        alpha_channel = image_array[:, :, 3]
    else:
        return False

    mask = alpha_channel > 0

    def dfs(x, y):
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cy < 0 or cx >= mask.shape[0] or cy >= mask.shape[1] or not mask[cx, cy]:
                continue
            mask[cx, cy] = 0
            stack.extend([(cx + dx, cy + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]])

    num_clusters = 0
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            if mask[i, j]:
                num_clusters += 1
                dfs(i, j)

    return num_clusters == 1

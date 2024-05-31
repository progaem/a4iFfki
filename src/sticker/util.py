from PIL import Image
import numpy as np

from PIL import Image
import numpy as np
from typing import Tuple, List

def is_image_suitable_for_achievement(image: Image.Image) -> bool:
    image_array: np.ndarray = np.array(image)

    if image_array.shape[2] == 4:
        alpha_channel: np.ndarray = image_array[:, :, 3]
    else:
        False

    mask: np.ndarray = alpha_channel > 0

    def dfs(x: int, y: int) -> int:
        stack: List[Tuple[int, int]] = [(x, y)]
        cluster_size: int = 0
        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cy < 0 or cx >= mask.shape[0] or cy >= mask.shape[1] or not mask[cx, cy]:
                continue
            mask[cx, cy] = 0
            cluster_size += 1
            stack.extend([(cx + dx, cy + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]])
        return cluster_size

    cluster_sizes: List[int] = []
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            if mask[i, j]:
                cluster_size = dfs(i, j)
                cluster_sizes.append(cluster_size)

    if len(cluster_sizes) == 0:
        return False
    if len(cluster_sizes) == 1:
        return True
    
    cluster_sizes.sort(reverse=True)

    if cluster_sizes[1] * 100 / cluster_sizes[0] > 5:
        return False
    
    return True

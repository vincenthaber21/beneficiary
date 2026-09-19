from collections import Counter, deque
from io import BytesIO

from PIL import Image


def _color_distance(c1, c2):
    return max(abs(c1[0] - c2[0]), abs(c1[1] - c2[1]), abs(c1[2] - c2[2]))


def _detect_background_color(pixels, width, height):
    samples = []
    for x in range(width):
        samples.append(pixels[x, 0][:3])
        samples.append(pixels[x, height - 1][:3])
    for y in range(height):
        samples.append(pixels[0, y][:3])
        samples.append(pixels[width - 1, y][:3])

    buckets = [((r // 8) * 8, (g // 8) * 8, (b // 8) * 8) for r, g, b in samples]
    return Counter(buckets).most_common(1)[0][0]


def remove_solid_background(image_file, tolerance=40):
    """Remove a solid RGB background connected to the image edges."""
    img = Image.open(image_file).convert("RGBA")
    width, height = img.size
    pixels = img.load()
    bg_color = _detect_background_color(pixels, width, height)

    def matches_background(x, y):
        r, g, b, a = pixels[x, y]
        if a == 0:
            return True
        return _color_distance((r, g, b), bg_color) <= tolerance

    to_remove = set()
    queue = deque()

    for x in range(width):
        for y in (0, height - 1):
            if matches_background(x, y):
                to_remove.add((x, y))
                queue.append((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if matches_background(x, y) and (x, y) not in to_remove:
                to_remove.add((x, y))
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in to_remove:
                if matches_background(nx, ny):
                    to_remove.add((nx, ny))
                    queue.append((nx, ny))

    for x, y in to_remove:
        r, g, b, _ = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)

    output = BytesIO()
    img.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output

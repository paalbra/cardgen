import argparse
import fractions
import logging
import os.path
import random
import sys

from PIL import (
    Image,
    ImageColor,
    ImageDraw,
    ImageFilter,
    ImageFont,
)

# A card is about 2.5 x 3.5 inches, or 63.5 x 88.9 mm.
# 750 x 1050 px will give the image 300 dpi.

COLORS = {
    "white": {
        "background": "#000",
        "main": "#dfd3ab",
        "second": "#fffef5",
        "card": "#fff",
    },
    "blue": {
        "background": "#000",
        "main": "#0073b2",
        "second": "#83cef1",
        "card": "#eef",
    },
    "black": {
        "background": "#000",
        "main": "#3a3833",
        "second": "#525347",
        "card": "#ddd",
    },
    "red": {
        "background": "#000",
        "main": "#d94029",
        "second": "#e5a38d",
        "card": "#fee",
    },
    "green": {
        "background": "#000",
        "main": "#226248",
        "second": "#bcd0c7",
        "card": "#dde6e9",
    },
}

FONTS = [
    "/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoMono-Regular.ttf",
]


class Card():

    def __init__(self, colors, font_path, size=(750, 1050)):
        self.colors = colors
        self.font_path = font_path
        self.size = size

        self.im = Image.new("RGB", self.size, self.colors["background"])
        self.grid_size = 30  # 30 results in a grid 25 x 35 when the card is 750 x 1050.
        self.grid = (size[0] // self.grid_size, size[1] // self.grid_size)
        self.draw = ImageDraw.Draw(self.im)

        self.big_font = ImageFont.truetype(self.font_path, int(self.grid_size))
        self.medium_font = ImageFont.truetype(self.font_path, int(self.grid_size / 1.2))
        self.small_font = ImageFont.truetype(self.font_path, int(self.grid_size / 1.8))

    def coordinates2xy(self, coordinates, x_grow=0, y_grow=0):
        xy = [coordinates[0] * self.grid_size,
              coordinates[1] * self.grid_size,
              coordinates[2] * self.grid_size,
              coordinates[3] * self.grid_size]

        xy[0] = xy[0] if xy[0] >= 0 else self.im.size[0] + xy[0]
        xy[1] = xy[1] if xy[1] >= 0 else self.im.size[1] + xy[1]
        xy[2] = xy[2] if xy[2] >= 0 else self.im.size[0] + xy[2]
        xy[3] = xy[3] if xy[3] >= 0 else self.im.size[1] + xy[3]

        if x_grow:
            xy[0] = xy[0] - (x_grow * self.grid_size)
            xy[2] = xy[2] + (x_grow * self.grid_size)
        if y_grow:
            xy[1] = xy[1] - (y_grow * self.grid_size)
            xy[3] = xy[3] + (y_grow * self.grid_size)

        return xy

    def save(self, file_path):
        logging.info("Saving card to: %s", os.path.abspath(file_path))
        self.im.save(file_path)

    def draw_frame(self):
        coordinates = [1, 1, -1, -3]
        paste_noisy_rectangle(self.im, self.coordinates2xy(coordinates), self.colors["second"], self.colors["main"], pixel_size=6, blur_radius=2)

    def draw_content(self, image_path=None, head1=None, head2=None, text=None, stats=None):

        large_image = not text

        # Image
        if large_image:
            coordinates = [2, 4, -2, -6]
        else:
            coordinates = [2, 4, -2, 23]
        if image_path:
            paste_image(self.im, self.coordinates2xy(coordinates), image_path)
        else:
            paste_noisy_rectangle(self.im, self.coordinates2xy(coordinates), self.colors["second"], self.colors["main"], pixel_size=30)
        draw_box(self.draw, self.coordinates2xy(coordinates), fill=None, outline=self.colors["main"], width=8)

        if not large_image:
            # Bottom box
            coordinates = [2, 25, -2, -2]
            draw_box(self.draw, self.coordinates2xy(coordinates), fill=self.colors["card"], outline=self.colors["main"], width=8)
            if text:
                xy = self.coordinates2xy(coordinates)
                write_text(self.draw, xy, text, self.medium_font)

        # Title bar
        coordinates = [2, 2, -2, 4]
        draw_box(self.draw, self.coordinates2xy(coordinates, x_grow=0.5), round=True, fill=self.colors["card"], outline=self.colors["main"], width=8)
        if head1:
            draw_center_text(self.draw, self.coordinates2xy(coordinates), head1, font=self.big_font)

        # Info bar
        if large_image:
            coordinates = [2, -6, -2, -4]
        else:
            coordinates = [2, 23, -2, 25]
        draw_box(self.draw, self.coordinates2xy(coordinates, x_grow=0.5), round=True, fill=self.colors["card"], outline=self.colors["main"], width=8)
        if head2:
            draw_center_text(self.draw, self.coordinates2xy(coordinates), head2, font=self.big_font)

        # Stats bar
        coordinates = [-6, -3, -2, -1]
        draw_box(self.draw, self.coordinates2xy(coordinates, x_grow=0.5), round=True, fill=self.colors["card"], outline=self.colors["main"], width=8)
        if stats:
            draw_center_text(self.draw, self.coordinates2xy(coordinates), stats, font=self.big_font, horizontal=True)

        # Bottom text
        coordinates = [1, -1.5, -6, -0.5]
        draw_center_text(self.draw, self.coordinates2xy(coordinates), "Might contain traces of cyber", font=self.small_font, fill="#ccc")


def draw_box(draw, xy, round=False, fill=None, outline=None, width=2):
    if outline:
        if width % 2 != 0:
            logging.warning("Box border width should preferably be divisibly by two to render properly: %d.", width)
        # Make sure the outline/border is drawn on the edge of the box, not inside.
        # This makes sure boxes next to each other don't get double borders.
        xy[0] = xy[0] - width / 2
        xy[1] = xy[1] - width / 2
        xy[2] = xy[2] + width / 2
        xy[3] = xy[3] + width / 2

    radius = 0 if not round else (xy[3] - xy[1]) / 2.3
    draw.rounded_rectangle(xy, radius, fill=fill, outline=outline, width=width)


def draw_center_text(draw, xy, text, font, fill="#000", horizontal=False):
    """Draws the given text in the center of a rectangle xy. Only vertical align unless horizontal."""

    m_width = draw.textlength("T", font=font)
    bounding_box = font.getbbox(text)
    x_grow = (xy[2] - xy[0] - (bounding_box[2] - bounding_box[0])) / 2 if horizontal else m_width
    y_grow = (xy[3] - xy[1] - (bounding_box[3] - bounding_box[1])) / 2
    y_grow = y_grow - (m_width / 5)  # It looks better if you move the text a bit up
    draw.text((xy[0] + x_grow, xy[1] + y_grow), text, font=font, fill=fill)


def get_color_gradient(c1, c2, count=100):
    """Returns a list of count colors between the two colors c1 and c2."""

    colors = []

    rgb1 = ImageColor.getrgb(c1)
    rgb2 = ImageColor.getrgb(c2)
    diff = (rgb2[0] - rgb1[0], rgb2[1] - rgb1[1], rgb2[2] - rgb1[2])
    step = (diff[0] / count, diff[1] / count, diff[2] / count)

    for i in range(count):
        color = tuple(abs(int(value)) for value in (rgb1[0] + step[0] * i, rgb1[1] + step[1] * i, rgb1[2] + step[2] * i))
        colors.append(color)

    return colors


def paste_image(image, xy, image_path):
    temp = Image.open(image_path)

    image_ratio = fractions.Fraction(temp.size[0], temp.size[1])
    box_ratio = fractions.Fraction(xy[2] - xy[0], xy[3] - xy[1])

    if image_ratio != box_ratio:
        logging.warning("The given image ratio (%d:%d) does not match the box ratio (%d:%d). Image will be scaled.", *image_ratio.as_integer_ratio(), *box_ratio.as_integer_ratio())
    if xy[2] - xy[0] > temp.size[0] or xy[3] - xy[1] > temp.size[1]:
        logging.warning("The given image (%s) is smaller than the box (%s). Image will be scaled.", f"{temp.size[0]} x {temp.size[1]}", f"{xy[2] - xy[0]} x {xy[3] - xy[1]}")

    temp = temp.resize((xy[2] - xy[0], xy[3] - xy[1]))
    image.paste(temp, (xy[0], xy[1]))


def paste_noisy_rectangle(image, xy, color1, color2, pixel_size=1, blur_radius=1):
    colors = get_color_gradient(color1, color2, 5)

    temp = Image.new("RGB", (xy[2] - xy[0], xy[3] - xy[1]))
    draw = ImageDraw.Draw(temp)

    # Draw pixel noise with the colors
    for x in range(0, temp.size[0], pixel_size):
        for y in range(0, temp.size[1], pixel_size):
            draw.rectangle((x, y, x + pixel_size, y + pixel_size), fill=random.choice(colors))

    # Draw some random circles
    min_radius = 50
    max_radius = 100
    for _ in range(temp.size[0] * temp.size[1] // 1000):
        x, y = random.randint(-min_radius // 2, temp.im.size[0] + min_radius // 2), random.randint(-min_radius // 2, temp.im.size[1] + min_radius // 2)
        size = random.randint(min_radius, max_radius)
        draw.ellipse((x, y, x + size, y + size), outline=random.choice(colors), width=pixel_size)

    temp = temp.filter(ImageFilter.BoxBlur(blur_radius))

    image.paste(temp, (xy[0], xy[1]))


def write_text(draw, xy, text, font, fill="#000"):
    """Try to write text within a bounding box xy. Words that match '\\n' will be replaced with newlines."""
    m_width = draw.textlength("T", font=font)
    xy = [xy[0] + m_width, xy[1] + m_width, xy[2] - m_width, xy[3] - m_width]

    words = text.strip().split(" ")

    new_text = ""
    line = ""
    width = 0
    for word in words:
        word_width = draw.textlength(word, font=font)

        if word_width > xy[2] - xy[0]:
            logging.warning("Word is to long to be printed properly: %s.", repr(word))

        if word == "\\n":
            new_text += f"{line}\n"
            line = ""
        elif width + word_width < xy[2] - xy[0]:
            line = f"{line} {word}" if line else word
            width = draw.textlength(line, font=font)
        else:
            new_text += f"{line}\n"
            line = word
            width = draw.textlength(line, font=font)

    new_text += line

    new_text_box = draw.multiline_textbbox((xy[0], xy[1]), new_text, font=font)
    new_text_height = new_text_box[3] - new_text_box[1]
    if new_text_height > xy[3] - xy[1]:
        logging.warning("Too much text to fit in bounding box: %s > %s.", f"{new_text_height}", f"{xy[3] - xy[1]}")

    draw.text((xy[0], xy[1]), new_text, font=font, fill="#000")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--color", required=True, choices=COLORS.keys(), help="Name of card color")
    parser.add_argument("-o", "--output", default="output.jpg", help="Path to output file.")
    parser.add_argument("-h1", "--head1", help="First text header on card")
    parser.add_argument("-h2", "--head2", help="Second text header on card")
    parser.add_argument("-t", "--text", help="Text in text box on card")
    parser.add_argument("-s", "--stats", help="Text in stats box")
    parser.add_argument("-i", "--image", help="Path to image")
    parser.add_argument("-f", "--font", help="Path to font")
    args = parser.parse_args()

    if not args.font:
        for font in FONTS:
            if os.path.exists(font):
                font_path = font
                break
        else:
            logging.error("Unable to find a font.")
            sys.exit(1)
    else:
        if not os.path.exists(args.font):
            logging.error("Unable to find font: %s.", args.font)
            sys.exit(1)
        font_path = args.font

    card = Card(COLORS[args.color], font_path=font_path)
    card.draw_frame()
    card.draw_content(image_path=args.image, head1=args.head1, head2=args.head2, text=args.text, stats=args.stats)
    card.save(args.output)

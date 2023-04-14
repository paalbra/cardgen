# About

Cardgen is a simple image generator that creates MTG (Magic The Gathering) like playing cards.

It takes both images and text as input.

It depends on [PIL/Pillow](https://pypi.org/project/Pillow/).

# Example

```
python cardgen.py -c "white" -h1 "Top text" -h2 "Middle text" -t "Main text of card. \\n \\n Newlines are possible if '\\n' is a word (spaces on both sides)." -s "5/7"
```

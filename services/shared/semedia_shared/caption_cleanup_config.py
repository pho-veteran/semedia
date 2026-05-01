"""Caption cleanup configuration constants."""

from __future__ import annotations

# Malformed tokens to strip from captions (e.g., "arafed pier" -> "pier")
MALFORMED_TOKENS = frozenset([
    "arafed",
    "araffe",
])

# Generic exact-match captions that provide no retrieval signal
GENERIC_EXACT = frozenset([
    "an image",
    "a picture",
    "a photo",
    "something",
    "unclear",
])

# Minimum word count for a caption to be considered useful
MIN_WORDS = 3

# Minimum character count for a caption to be considered useful
MIN_CHARS = 10

# Useful terms that indicate a caption has retrieval value
USEFUL_TERMS = frozenset([
    # Natural
    "lake", "moon", "water", "pier", "ocean", "beach", "sky",
    "tree", "trees", "forest", "mountain", "mountains", "sunset",
    "night", "river", "waves",
    # Human
    "person", "people", "man", "woman", "boy", "girl", "group",
    # Animal
    "dog", "cat", "horse", "bird",
    # Object
    "laptop", "phone", "table", "desk", "conference", "room",
    "surfboard", "airplane",
    # Action
    "sitting", "running", "walking",
])

# Prefix rewrites to clean up verbose model output
REWRITE_PREFIXES = (
    ("a close up of a ", ""),
    ("a close up of an ", ""),
    ("a close up of the ", ""),
    ("a close up of ", ""),
    ("close up of a ", ""),
    ("close up of an ", ""),
    ("close up of the ", ""),
    ("close up of ", ""),
    ("this is a black and white photo of an ", "black and white "),
    ("this is a black and white photo of a ", "black and white "),
    ("this is a black and white photo of ", "black and white "),
    ("this is a ", ""),
    ("this is an ", ""),
    ("this is the ", ""),
)

# Fragment rewrites to remove filler phrases
REWRITE_FRAGMENTS = (
    (" that is ", " "),
    (" who is ", " "),
    (" which is ", " "),
    (" there is a ", " "),
    (" there is an ", " "),
    (" there are ", " "),
)

# Suffix rewrites to remove boilerplate endings
REWRITE_SUFFIXES = (
    (" in the background", ""),
)

# Fallback caption when all else fails
FALLBACK_CAPTION = "Image content unclear."

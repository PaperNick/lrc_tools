import re

# LRC timestamp pattern: [mm:ss.xx] or [mm:ss.xxx]
RE_LRC_TIMESTAMP = re.compile(r"\[\d+:\d+(?:\.\d+)?\]")
# Metadata tag: [ti:Title], [ar:Artist], etc.
RE_LRC_METADATA = re.compile(r"\[[a-z]+:.+\]", re.IGNORECASE)

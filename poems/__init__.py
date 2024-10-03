from .context import Context # noqa
from .curator import Curator # noqa
from .poem import Poem # noqa
from .objects import Author, Time # noqa

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from .context import Context # noqa
from .curator import Curator # noqa
from .objects import Poem, Author, Time # noqa

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

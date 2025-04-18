# Set default logging handler to avoid "No handler found" warnings.
import logging
from logging import NullHandler

from .core import (FeedType, Note, NoteType, SearchNoteType, SearchSortType,
                   XhsClient)
from .exception import DataFetchError, ErrorEnum, IPBlockError, SignError

logging.getLogger(__name__).addHandler(NullHandler())

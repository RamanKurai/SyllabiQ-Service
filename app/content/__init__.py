"""Content routes package."""
from .courses import router as courses_router  # noqa: F401
from .subjects import router as subjects_router  # noqa: F401
from .syllabi import router as syllabi_router  # noqa: F401
from .topics import router as topics_router  # noqa: F401
from .contexts import router as contexts_router  # noqa: F401


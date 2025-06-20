from aiogram import Dispatcher

from .logging import LoggingMiddleware

def register_middlewares(dp: Dispatcher):
    """Register all dialogs."""
    dp.update.middleware(LoggingMiddleware())
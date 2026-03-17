import os
import threading

from django.apps import AppConfig


class RecognitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recognition'

    def ready(self) -> None:
        if os.environ.get("RUN_MAIN") != "true":
            return

        from recognition.utils import get_detector, get_embedder

        def warm_up():
            try:
                get_detector()
                get_embedder()
            except Exception:
                pass

        threading.Thread(target=warm_up, daemon=True).start()

from django.apps import AppConfig


class LibraryServicesConfig(AppConfig):
    name = 'library_services'

    def ready(self):
        # signals are imported, so that they are defined and can be used
        import library_services.signals

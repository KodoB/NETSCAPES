from PyQt6.QtWidgets import QWidget
from PyQt6.uic import loadUi


class PageController(QWidget):
    """
    Clase base para las PÁGINAS DE CONTENIDO que viven dentro del
    QStackedWidget de MainWindowController.

    IMPORTANTE: esta clase YA NO maneja navegación ni sidebar (eso ahora
    vive una sola vez en MainWindowController). Su única responsabilidad
    es cargar el .ui de contenido y guardar user_data.

    Nota: se mantiene el nombre "PageController" en vez de "BaseController"
    para dejar claro que representa una PÁGINA, no una ventana.
    Si prefieres conservar el nombre BaseController, puedes hacer:
        BaseController = PageController
    al final de este archivo para no romper imports existentes.
    """

    def __init__(self, user_data, ui_file):
        super().__init__()
        loadUi(ui_file, self)
        self.user_data = user_data


# Alias por compatibilidad, así no tienes que tocar los imports que ya
# tengas escritos como "from controladores.base_controller import BaseController"
BaseController = PageController

from domain import Moviment


class MovimentsSessio:
    """Moviments carregats a la sessió actual. És l'únic estat modificable de l'aplicació."""

    def __init__(self):
        self._moviments = []

    def actuals(self):
        return Moviment.clone_list(self._moviments)

    def substituir(self, moviments):
        self._moviments = Moviment.clone_list(moviments)

from objects.existence import Existence


class Wall(Existence):
    def __init__(self, position, gamestate):
        super().__init__(position, gamestate, icon='wall-vertical.png', symbol='%')

from gym_cooking.cooking_world.abstract_classes import *
from gym_cooking.cooking_world.constants import *
from typing import List


class Floor(StaticObject):

    def __init__(self, location):
        super().__init__(location, True)

    def accepts(self, dynamic_objects) -> bool:
        return False

    def file_name(self) -> str:
        return "floor"


class Counter(StaticObject):

    def __init__(self, location):
        super().__init__(location, False)

    def accepts(self, dynamic_objects) -> bool:
        return True

    def file_name(self) -> str:
        return "counter"


class DeliverSquare(StaticObject):

    def __init__(self, location):
        super().__init__(location, False)

    def accepts(self, dynamic_objects) -> bool:
        return True

    def file_name(self) -> str:
        return "delivery"


class CutBoard(StaticObject, ActionObject):

    def __init__(self, location):
        super().__init__(location, False)

    def action(self, dynamic_objects: List):
        if len(dynamic_objects) == 1:
            try:
                return dynamic_objects[0].chop()
            except AttributeError:
                return False
        return False

    def accepts(self, dynamic_objects) -> bool:
        return len(dynamic_objects) == 1 and isinstance(dynamic_objects[0], ChopFood)

    def file_name(self) -> str:
        return "cutboard"


class Blender(StaticObject, ProgressingObject):

    def __init__(self, location):
        super().__init__(location, False)
        self.content = None

    def progress(self, dynamic_objects):
        assert len(dynamic_objects) < 2, "Too many Dynamic Objects placed into the Blender"
        if not dynamic_objects:
            self.content = None
            return
        elif not self.content:
            self.content = dynamic_objects
        elif self.content:
            if self.content[0] == dynamic_objects[0]:
                self.content[0].blend()
            else:
                self.content = dynamic_objects

    def accepts(self, dynamic_objects) -> bool:
        return len(dynamic_objects) == 1 and isinstance(dynamic_objects[0], BlenderFood)

    def file_name(self) -> str:
        return "blender3"


class Plate(Container):

    def __init__(self, location):
        super().__init__(location)

    def add_content(self, content):
        if not isinstance(content, Food):
            raise TypeError(f"Only Food can be added to a plate! Tried to add {content.name()}")
        if not content.done():
            raise Exception(f"Can't add food in unprepared state.")
        self.content.append(content)

    def file_name(self) -> str:
        return "Plate"


class Onion(ChopFood):

    def __init__(self, location):
        super().__init__(location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

    def file_name(self) -> str:
        if self.done():
            return "ChoppedOnion"
        else:
            return "FreshOnion"
        

class Tomato(ChopFood):

    def __init__(self, location):
        super().__init__(location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

    def file_name(self) -> str:
        if self.done():
            return "ChoppedTomato"
        else:
            return "FreshTomato"


class Lettuce(ChopFood):

    def __init__(self, location):
        super().__init__(location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

    def file_name(self) -> str:
        if self.done():
            return "ChoppedLettuce"
        else:
            return "FreshLettuce"


class Carrot(BlenderFood, ChopFood):

    def __init__(self, location):
        super().__init__(location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED or self.blend_state == BlenderFoodStates.MASHED:
            return True
        else:
            return False

    def file_name(self) -> str:
        if self.done():
            return "ChoppedCarrot"
        else:
            return "FreshCarrot"


class Potato(ChopFood):

    def __init__(self, location):
        super().__init__(location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

    def file_name(self) -> str:
        if self.done():
            return "ChoppedPotato"
        else:
            return "FreshPotato"


class Broccoli(ChopFood):

    def __init__(self, location):
        super().__init__(location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

    def file_name(self) -> str:
        if self.done():
            return "ChoppedBroccoli"
        else:
            return "FreshBroccoli"


class Agent(Object):

    def __init__(self, location, color, name):
        super().__init__(location, False, False)
        self.holding = None
        self.color = color
        self.name = name
        self.orientation = 1

    def grab(self, obj: DynamicObject):
        self.holding = obj
        obj.move_to(self.location)

    def put_down(self, location):
        self.holding.move_to(location)
        self.holding = None

    def move_to(self, new_location):
        self.location = new_location
        if self.holding:
            self.holding.move_to(new_location)

    def change_orientation(self, new_orientation):
        assert 0 < new_orientation < 5
        self.orientation = new_orientation

    def file_name(self) -> str:
        pass


StringToClass = {
    "Floor": Floor,
    "Counter": Counter,
    "CutBoard": CutBoard,
    "DeliverSquare": DeliverSquare,
    "Tomato": Tomato,
    "Lettuce": Lettuce,
    "Onion": Onion,
    "Plate": Plate,
    "Agent": Agent,
    "Blender": Blender,
    "Carrot": Carrot,
    "Potato": Potato,
    "Broccoli": Broccoli
}

ClassToString = {
    Floor: "Floor",
    Counter: "Counter",
    CutBoard: "CutBoard",
    DeliverSquare: "DeliverSquare",
    Tomato: 'Tomato',
    Lettuce: "Lettuce",
    Onion: "Onion",
    Plate: "Plate",
    Agent: "Agent",
    Blender: "Blender",
    Carrot: "Carrot",
    Potato: "Potato",
    Broccoli: "Broccoli"
}

GAME_CLASSES = [Floor, Counter, CutBoard, DeliverSquare, Tomato, Lettuce, Onion, Plate, Agent, Blender, Carrot, Potato, Broccoli]
GAME_CLASSES_STATE_LENGTH = [(Floor, 1), (Counter, 1), (CutBoard, 1), (DeliverSquare, 1), (Tomato, 2),
                             (Lettuce, 2), (Onion, 2), (Plate, 1), (Agent, 5), (Blender, 1), (Carrot, 3), (Potato, 2), (Broccoli, 2)]
GAME_CLASSES_HOLDABLE_IDX = {cls:i for i, cls in enumerate(["Tomato", "Lettuce", "Onion", "Plate", "Carrot", "Potato", "Broccoli"])}
FOOD_CLASSES = ["Tomato", "Lettuce", "Onion", "Carrot", "Potato", "Broccoli"]
FOOD_CLASSES_IDX = {cls:i for i, cls in enumerate(FOOD_CLASSES)}
OBJ_IDX = {ClassToString[cls]:i for i, cls in enumerate(GAME_CLASSES[1:])}
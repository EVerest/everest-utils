from abc import ABC, abstractmethod
from typing import Dict


class EverestConfigAdjustmentVisitor(ABC):
    """ Visitor that manipulates a (parsed) EVerest config when called.

     Used to build up / adapt EVerest configurations for tests.
     """

    @abstractmethod
    def adjust_everest_configuration(self, config: Dict) -> Dict:
        """ Adjusts the provided configuration by making a (deep) copy and returning the adjusted configuration. """
        pass

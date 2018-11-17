import random
from hackathon.utils.utils import DataMessage

class Environment:
    def __init(self):
        self.state = None
        '''STATUS -- [load1_Status, load2_Status, load3_Status, solar_Status]'''
        self.status = [True, True, True, True]

    def update(self, DataMsg : DataMessage):
        self.state = DataMsg

    def getState(self):
        '''INPUT -- grid_Status, bess_SOC, solar_production'''
        return [self.state.grid_status,
                self.state.bessSOC,
                self.state.solar_production]

    def penal(self, action):
        '''action [load1_State, load2_State, load3_State, bess_PowerReference, solar_StateCoef]'''

        penal = 0

        i = 0
        if action[i] < 0.5 and self.status[i]:
            self.status[i] = False
            penal -= 20
        elif action[i] < 0.5 and not self.status[i]:
            penal -= 1
        elif action[i] >= 0.5:
            self.status[i] = True

        i = 1
        if action[i] < 0.5 and self.status[i]:
            self.status[i] = False
            penal -= 4
        elif action[i] < 0.5 and not self.status[i]:
            penal -= 0.4
        elif action[i] >= 0.5:
            self.status[i] = True

        i = 2
        if action[i] < 0.5 and self.status[i]:
            self.status[i] = False
        elif action[i] < 0.5 and not self.status[i]:
            penal -= 0.3
        elif action[i] >= 0.5:
            self.status[i] = True

        return penal

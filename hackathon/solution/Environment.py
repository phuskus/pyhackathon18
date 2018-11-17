import random
from hackathon2018.hackathon.utils.utils import DataMessage

class Environment:
    def __init__(self):
        self._state_count = 1
        self._state = None
        self.consumers = []
        self.status = [True, True, True, True]
        self.battery = 0

    def get_state(self):
        return self._state

    def setState(self, msg: DataMessage):
        self.state = msg
        self.consumers = [self.state.current_load * 0.2, self.state.current_load * 0.4, self.state.current_load * 0.4]
        self.battery = self.state.bessSOC * self.state.bessPower

    def next_state(self, action):
        if self.state.grid_status:
            "Ako je grid ukljucen imas posebnu politiku odlucivanja"

            "obracunaj koliko snage imas na raspolaganju"
            powerAtDisposal = sum([self.state.mainGridPower, self.state.solar_production, self.state.bessPower])

            "izracunaj koliko snage potrosaci zahtevaju"
            powerDemand = sum(self.consumers)
            penalty = [0,0,0,0,0]

            if powerDemand > 0:
                if action[0] * powerAtDisposal < self.consumers[0]:
                    if self.status[0]:
                        "Ako smatram da treba da iskljucim prvog potrosaca"
                        penalty[0] += 20
                        self.status[0] = False
                    else:
                        "Ako mi je prvi potrosac vec bio iskljucen i sada zelim da ga takvog ostavim"
                        penalty[0] += 1
                else:
                    "Ako ne smatram da treba da iskljucim prvog potrosaca"
                    if not self.status[0]:
                        "Ako je prvi potrosac bio iskljucen opet ga samo upalim"
                        self.status[0] = True
                    "ako sam ukljucio prvog potrosaca, smanjujem energiju na raspolaganju za druga dva potrosaca"
                    powerAtDisposal -= self.consumers[0]
                if action[1] * powerAtDisposal < self.consumers[1]:
                    if self.status[0]:
                        "Ako smatram da treba da iskljucim drugog potrosaca"
                        penalty[1] += 4
                        self.status[1] = False
                    else:
                        "Ako mi je drugi potrosac vec bio iskljucen i sada zelim da ga takvog ostavim"
                        penalty[1] += 0.4
                else:
                    "Ako ne smatram da treba da iskljucim drugog potrosaca"
                    if not self.status[1]:
                        "Ako je drugi potrosac bio iskljucen opet ga samo upalim"
                        self.status[1] = True
                    "ako sam ukljucio drugog potrosaca, smanjujem energiju na raspolaganju za treceg potrosaca"
                    powerAtDisposal -= self.consumers[1]

                if action[2] * powerAtDisposal < self.consumers[2]:
                    if self.status[2]:
                        "Ako smatram da treba da iskljucim treceg potrosaca"
                        self.status[2] = False
                    else:
                        "Ako mi je treci potrosac vec bio iskljucen i sada zelim da ga takvog ostavim"
                        penalty[2] += 0.3
                else:
                    "Ako ne smatram da treba da iskljucim treceg potrosaca"
                    if not self.status[2]:
                        "Ako je treci potrosac bio iskljucen opet ga samo upalim"
                        self.status[2] = True
                    "ako sam ukljucio treceg potrosaca, smanjujem energiju na raspolaganju"
                    powerAtDisposal -= self.consumers[1]

            #if powerAtDisposal > 0:







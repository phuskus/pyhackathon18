import torch.nn as nn
import torch.nn.functional as F

class Network(nn.Module):
    def __init__(self):
        super().__init__()
        '''INPUT -- grid_Status, bess_SOC, solar_production'''
        self.input = nn.Linear(5, 8)
        self.layer1 = nn.Linear(8, 8)
        self.layer2 = nn.Linear(8, 8)

        '''OUTPUT -- load1_StateCoef, load2_StateCoef, load3_StateCoef, bess_PowerReference, solar_StateCoef'''
        self.output = nn.Linear(8, 5)

    def forward(self, x):
        '''Forward propagation'''
        x = F.relu(self.input(x))
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        x = F.relu(self.output(x))

        return x

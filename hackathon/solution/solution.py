"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir

from hackathon.solution.Environment import Environment
from hackathon.solution.Network import Network
from hackathon.solution.ReplayMemory import ReplayMemory
import torch
env = Environment()
memory = ReplayMemory(10000)

device = torch.device("cpu")
agent = Network().to(device)

def worker(msg: DataMessage):

    #Primi stanje okruzenja
    env.update(msg)
    #Smisli odluku (neuronska mreza)
    action = agent(env.getState())
    #Odredi penal i zapamti
    penalty = env.penal(action)
    memory.push(env.getState(), action, penalty)


    #Odradi odluku
    load_one = env.status[0]
    load_two = env.status[1]
    load_three = env.status[2]
    power_reference = action[3]
    if env.status[3]:
        pv_mode = PVMode.ON
    else:
        pv_mode = PVMode.OFF

    return ResultsMessage(data_msg=msg,
                          load_one=load_one,
                          load_two=load_two,
                          load_three=load_three,
                          power_reference=power_reference,
                          pv_mode=pv_mode)



def run(args) -> None:
    prepare_dot_dir()
    config_outs(args, 'solution')
    cntrl = Control()

    for data in cntrl.get_data():
        cntrl.push_results(worker(data))

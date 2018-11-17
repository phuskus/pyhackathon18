"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir

from hackathon.solution.Environment import Environment
from hackathon.solution.Network import Network
from hackathon.solution.ReplayMemory import ReplayMemory, Transition
import torch.optim as optim
import torch
import torch.nn.functional as F


env = Environment()
memory = ReplayMemory(10000)

device = torch.device("cpu")
agent1 = Network().to(device)
agent2 = Network().to(device)

agent2.load_state_dict(agent1.state_dict())
agent2.eval()
optimizer = optim.RMSprop(agent1.parameters())


def optimize_model(batch_size=1000, gamma=0.9):
    if len(memory) < batch_size:
        return
    transitions = memory.sample(batch_size)
    batch = Transition(*zip(*transitions))
    state_batch = torch.cat(batch.state)
    next_states = torch.cat(batch.next_state)
    reward_batch = torch.cat(batch.reward)

    state_action_values = agent1(state_batch)
    #next_state_values = torch.zeros(batch_size, device=device)
    next_state_values = agent2(next_states)

    expected_state_action_values = (next_state_values * gamma) + reward_batch
    loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.detach())

    optimizer.zero_grad()
    loss.backward()
    for param in agent1.parameters():
        param.grad.data.clamp_(-1, 1)
    optimizer.step()

    return loss.item()


def worker(msg: DataMessage):

    #Primi stanje okruzenja
    env.update(msg)
    #Smisli odluku (neuronska mreza)
    action = agent1(env.getState())
    #Odredi penal i zapamti
    penalty = env.penal(action)
    memory.push(env.getState(), action, penalty)

    loss = optimize_model()

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

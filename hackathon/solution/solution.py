"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir

prev_buyingPrice = 0
failsafe_percentage = 0.3
high_priority_failsafe_percentage = 0.25
bessCap = 1200.0 # Expressed in kW * minutes
prev_load = []
prev_load[0] = [True, 0.2]
prev_load[1] = [True, 0.4]
prev_load[2] = [True, 0.4]
number_of_consumers = 3
lowest_activated_priority = 2

def clamp(val, minv, maxv):
    return max(min(val, maxv), minv)

def worker(msg: DataMessage) -> ResultsMessage:
    global prev_buyingPrice, failsafe_percentage, high_priority_failsafe_percentage, bessCap
    global load, lowest_activated_priority, prev_load, number_of_consumers

    #Init vars
    load = [True] * 3
    power_reference = 0.0
    pv_mode = PVMode.ON


    if msg.grid_status:
        #Grid is ONLINE

        # All consumers on
        # Solar panel on

        # DAY, EXPENSIVE BUYING PRICE - check if buyingPrice > prev_buyingPrice AND prev_buyingPrice <= sellingPrice
        if msg.buying_price > prev_buyingPrice and prev_buyingPrice <= msg.selling_price:
            #Reduce consumption by using previously bought power at a lower price, up until failsafe_percentage
            power_required = msg.current_load - msg.solar_production
            power_bess_can_supply = (clamp(power_required, -5.0, 5.0))
            newSOC = msg.bessSOC - power_bess_can_supply/bessCap

            if newSOC >= failsafe_percentage:
                power_reference = power_bess_can_supply
            else:
                power_reference = 0.0

        #NIGHT, CHEAP BUYING PRICE - check if buyingPrice < prev_buyingPrice
        elif msg.buying_price < prev_buyingPrice:
            #Charge bess to full with cheap, tasty nocturnal energy
            if msg.bessSOC < 1:
                power_reference = clamp(-((1 - msg.bessSOC) * bessCap), -5.0, 0.0)
    else:
        #GRID IS OFFLINE
        #print("BLACKOUT (msgid: " + str(msg.id) + ")")


        '''If power at disposal is not enough to satisfy power required, kill the lowest priority load, and check again'''
        kWminutes_left_in_bess = bessCap * msg.bessSOC
        max_draw = 5.0  # kW
        bess_power_at_disposal = clamp(kWminutes_left_in_bess, 0, 5)
        current_load = msg.current_load
        while True:
            solar_production = msg.solar_production
            if pv_mode == PVMode.OFF:
                solar_production = 0

            power_at_disposal = solar_production + bess_power_at_disposal
            power_required = current_load
            if power_at_disposal >= power_required:
                '''If solar power is enough to satisfy consumption, send excess to charge Bess'''
                if solar_production >= power_required:
                    power_reference = power_required - solar_production
                    if power_reference < -5:
                        '''Kill solar panel so as not to overcharge Bess'''
                        pv_mode = PVMode.OFF
                        continue
                    newSOC = msg.bessSOC + power_reference/bessCap
                    if newSOC > 1:
                        '''Kill solar panel so as not to overcharge Bess'''
                        pv_mode = PVMode.OFF
                        continue
                    break
                elif solar_production < power_required:
                    '''If solar is not enough, substitute power from Bess (if she be capable!)'''
                    power_reference = power_required - solar_production
                    if power_reference > 5:
                        '''Kill the lowest pri load'''
                        load[lowest_activated_priority] = False
                        if lowest_activated_priority == 2:
                            current_load = current_load * 0.6
                        if lowest_activated_priority == 1:
                            beginning_current_load = 10 / 6 * current_load
                            current_load = beginning_current_load - 2 * 0.4 * beginning_current_load
                        if lowest_activated_priority == 0:
                            current_load = 0

                        lowest_activated_priority -= 1
                        if lowest_activated_priority < 0:
                            break
                        continue
                    newSOC = msg.bessSOC - power_reference/bessCap

                    if newSOC < 0:
                        '''Kill the lowest pri load'''
                        load[lowest_activated_priority] = False
                        if lowest_activated_priority == 2:
                            current_load = current_load * 0.6
                        if lowest_activated_priority == 1:
                            beginning_current_load = 10/6 * current_load
                            current_load = beginning_current_load - 2 * 0.4 * beginning_current_load
                        if lowest_activated_priority == 0:
                            current_load = 0

                        lowest_activated_priority -= 1
                        if lowest_activated_priority < 0:
                            break
                        continue
                    break

            elif power_at_disposal < power_required:
                '''Kill the lowest priority load'''
                load[lowest_activated_priority] = False
                if lowest_activated_priority == 2:
                    current_load = current_load * 0.6
                if lowest_activated_priority == 1:
                    beginning_current_load = 10 / 6 * current_load
                    current_load = beginning_current_load - 2 * 0.4 * beginning_current_load
                if lowest_activated_priority == 0:
                    current_load = 0

                lowest_activated_priority -= 1
                if lowest_activated_priority < 0:
                    break

    prev_load[0] = load[0]
    prev_load[1] = load[1]
    prev_load[2] = load[2]
    return ResultsMessage(data_msg=msg,
                          load_one=load[0],
                          load_two=load[1],
                          load_three=load[2],
                          power_reference=power_reference,
                          pv_mode=pv_mode)


def run(args) -> None:
    prepare_dot_dir()
    config_outs(args, 'solution')

    cntrl = Control()

    for data in cntrl.get_data():
        cntrl.push_results(worker(data))

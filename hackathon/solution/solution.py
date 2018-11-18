"""This module is main module for contestant's solution."""

from hackathon.utils.control import Control
from hackathon.utils.utils import ResultsMessage, DataMessage, PVMode, \
    TYPHOON_DIR, config_outs
from hackathon.framework.http_server import prepare_dot_dir

prev_buyingPrice = 0
failsafe_percentage = 0.5
high_priority_failsafe_percentage = 0.25
bessCap = 1200.0 # Expressed in kW * minutes
prev_load_one = True
prev_load_two = True
prev_load_three = True
def clamp(val, minv, maxv):
    return max(min(val, maxv), minv)

def worker(msg: DataMessage) -> ResultsMessage:
    global prev_buyingPrice, failsafe_percentage, high_priority_failsafe_percentage, bessCap
    global prev_load_one, prev_load_two, prev_load_three

    #Init vars
    load_one = True
    load_two = True
    load_three = True
    power_reference = 0.0
    pv_mode = PVMode.ON


    if msg.grid_status:
        #Grid is ONLINE

        # All consumers on
        load_one = True
        load_two = True
        load_three = True

        # Solar panel on
        pv_mode = PVMode.ON

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
        print("BLACKOUT")
        # Consumer three off
        load_one = True
        load_two = True
        load_three = False

        coef = 1
        if prev_load_three:
            coef -= 0.4
        if prev_load_two:
            coef -= 0.4
        if prev_load_one:
            coef -= 0.2

        power_required = msg.current_load * coef - msg.solar_production

        # If solar is enough to satisfy consumption (negative power_required), excess power charges bess ---> Prevent overcharging bess
        # If solar is NOT enough to satisfy consumption (positive power required), help with bess
        if power_required > 5:
            # Kill load_two, leave load_one
            load_two = False
            power_reference = 5.0
        elif power_required > 0:
            newSOC = msg.bessSOC - power_required/bessCap
            if newSOC >= 0:
                power_reference = power_required
            else:
                load_two = False
                if prev_load_two:
                    power_required = msg.current_load * 0.12 - msg.solar_production
                    newSOC = msg.bessSOC - power_required / bessCap
                    if newSOC < 0:
                        load_one = False
                        power_reference = 0.0
                    else:
                        power_reference = power_required

    prev_load_one = load_one
    prev_load_two = load_two
    prev_load_three = load_three

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

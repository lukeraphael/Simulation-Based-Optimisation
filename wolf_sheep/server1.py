from requests_futures.sessions import FuturesSession
from wolf_sheep.model import WolfSheep
from wolf_sheep.agents import Sheep, Wolf
from flask import Flask, request, jsonify

import sys

app = Flask(__name__)


def run_simulation(wolves: int, regrowth: int):
    model = WolfSheep()
    model._seed = 1
    model.initial_wolves = wolves
    model.initial_sheep = 100
    model.grass_regrowth_time = regrowth
    model.run_model(step_count=70)

    # Store the results
    return model.schedule.get_breed_count(Wolf), model.schedule.get_breed_count(Sheep)


@app.route('/tests/endpoint', methods=['POST'])
def my_test_endpoint():
    input_json = request.get_json(force=True)
    wolves = input_json['wolves']
    regrowth = input_json['regrowth']
    # force=True, above, is necessary if another developer
    # forgot to set the MIME type to 'application/json'
    print('data from client:', input_json)
    _, sheep = run_simulation(wolves, regrowth)

    dictToReturn = {'answer': sheep}
    return jsonify(dictToReturn)


@app.route("/simulate")
def simulate():
    print('test')


# get the port as an argument (from argo / docker)
port = int(sys.argv[1])
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)

import argparse
import csv
import json
import random
import string

import dill
import numpy as np
import pandas as pd
from desdeo_problem.problem import _ScalarObjective
from desdeo_problem.problem import DiscreteDataProblem
from desdeo_problem.surrogatemodels.lipschitzian import LipschitzianRegressor
from desdeo_problem.problem import Variable

from app import db
from models.problem_models import Problem as ProblemModel
from models.user_models import UserModel

parser = argparse.ArgumentParser(
    description="Add N new user to the database with a pre-defined problem. and a given username prefix."
)
parser.add_argument("--N", type=int, help="The number of usernames to be added.", required=True)

dill.settings["recurse"] = True

db.drop_all()
db.create_all()

args = vars(parser.parse_args())


def main():
    letters = string.ascii_lowercase
    args = vars(parser.parse_args())
    methods = ["rpm", "nimbus", "enautilus"]
    usernames = [[f"{method}_{n}" for n in range(1, args["N"]+1)] for method in methods]
    usernames = sum(usernames, [])
    passwords = [("".join(random.choice(letters) for i in range(6))) for j in range(len(usernames))]

    try:
        for (username, password) in zip(usernames, passwords):
            add_user(username, password)
            add_sus_problem(username)
    except Exception as e:
        print("something went wrong...")
        print(e)
        exit()

    with open("users_and_pass.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        list(map(lambda x: writer.writerow(x), zip(usernames, passwords)))

    print(f"Added users {usernames} to the database succesfully.")


def add_user(username, password):
    db.session.add(UserModel(username=username, password=UserModel.generate_hash(password)))
    db.session.commit()


def add_sus_problem(username):
    user_query = UserModel.query.filter_by(username=username).first()
    if user_query is None:
        print(f"USername {username} not found")
        return
    else:
        id = user_query.id

    file_name = "./tests/data/sustainability_spanish.csv"

    data = pd.read_csv(file_name)
    # minus because all are to be maximized
    data[["social", "economic", "environmental"]] = -data[["social", "economic", "environmental"]]

    var_names = [f"x{i}" for i in range(1, 12)]

    ideal = data[["social", "economic", "environmental"]].min().values
    nadir = data[["social", "economic", "environmental"]].max().values

    # define the sus problem
    var_names = [f"x{i}" for i in range(1, 12)]
    obj_names = ["social", "economic", "environmental"]

    problem = DiscreteDataProblem(data, var_names, obj_names, ideal, nadir)

    db.session.add(
        ProblemModel(
            name="Spanish sustainability problem",
            problem_type="Discrete",
            problem_pickle=problem,
            user_id=id,
            minimize=json.dumps([-1, -1, -1]),
        )
    )
    db.session.commit()
    print(f"Sustainability problem added for user '{username}'")


if __name__ == "__main__":
    main()

from flask import Flask, jsonify, request
import json

operators = ["AND", "OR", "NAND", "NOT"]
app = Flask(__name__)


def gen_truthtable(n):
    if n < 1:
        return [[]]
    subtable = gen_truthtable(n - 1)
    return [row + [v] for row in subtable for v in [0, 1]]


def gate(input1, operator, input2=0):
    if operator == "NOT":
        return not input1
    elif operator == "AND":
        if not (input1 and input2):
            return False
    elif operator == "OR":
        if not (input1 or input2):
            return False
    elif operator == "NAND":
        if not (input1 and input2):
            return True
        else:
            return False

    return True


def calc_truth_value(row, expression):
    # expression = "A B and C or"
    stack = []
    index = 0
    for token in expression.split():
        token = token.upper()
        if token in operators:
            input1 = stack.pop()
            if token == "NOT":
                stack.append(gate(input1, token))
            else:
                input2 = stack.pop()
                stack.append(gate(input2, token, input1))
        else:
            stack.append(row[index])
            index = index + 1
    return stack


def calc_circuit_table(table, expression):
    result = []
    for row in table:
        result.append(calc_truth_value(row, expression))
    return result


def write_to_file(data):
    file = open("./db.json", "r")
    json_file = json.load(file)
    file.close()
    keys = list(json_file.keys())
    if keys == []:
        json_file["0"] = data
    else:
        json_file[str(int(max(keys)) + 1)] = data

    with open("./db.json", "w") as f:
        f.write(json.dumps(json_file))


@app.get("/test")
def home():
    print(request.get_json()["text"])
    return jsonify({"message": "Hello :)"})


@app.get("/calculate")
def calculate_truth_table():
    data = request.get_json()
    expression = data["expression"]
    number_of_inputs = data["inputs"]
    result = calc_circuit_table(gen_truthtable(int(number_of_inputs)), expression)
    return jsonify(
        {"truth_table": gen_truthtable(int(number_of_inputs)), "output": result}
    )


@app.post("/save")
def save():
    data = request.get_json()
    expression = data["expression"]
    number_of_inputs = data["inputs"]
    result = calc_circuit_table(gen_truthtable(int(number_of_inputs)), expression)
    data["result"] = result
    data["truth_table"] = gen_truthtable(int(number_of_inputs))
    write_to_file(data)
    return jsonify({"message": "Saved!"})


@app.get("/get")
def get():
    file = open("./db.json", "r")
    json_file = json.load(file)
    file.close()
    return jsonify(json_file)


@app.get("/get/<id>")
def get_by_id(id):
    file = open("./db.json", "r")
    json_file = json.load(file)
    file.close()
    return jsonify(json_file[id])


if __name__ == "__main__":
    app.run()

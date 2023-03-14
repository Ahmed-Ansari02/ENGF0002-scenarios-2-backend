from flask import Flask, jsonify, request
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate('serviceAccountKey.json')

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

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



@app.get("/calculate")
def calculate_truth_table():
    data = request.get_json()
    expression = data["expression"]
    number_of_inputs = data["inputs"]
    result = calc_circuit_table(gen_truthtable(int(number_of_inputs)), expression)
    return jsonify(
        {"truth_table": gen_truthtable(int(number_of_inputs)), "output": result}
    )

# post information about some new cirsuits. If the cirsuir is saved, return the id of the circuit
@app.post("/save")
def save():
    circuits = request.get_json()
    id_ignore = []
    for i in range(len(circuits)):
        if db.collection(u'preset_circuits').document(str(circuits[i]["id"])).get().exists:
            id_ignore.append(circuits[i]["id"])
            continue
        else:
            doc_ref = db.collection(u'preset_circuits').document(str(circuits[i]["id"]))
            doc_ref.set(circuits[i])
    if len(id_ignore) == 0:
        return {'success': "All circuits are saved!"}
    else:
        return {'success': "All circuits are saved!", 'ignore': id_ignore}

# update some circuits, if the circuit is not exist, return the id of the circuit
@app.put("/update")
def update():
    circuits = request.get_json()
    id_not_exist = []
    for i in range(len(circuits)):
        if not db.collection(u'preset_circuits').document(str(circuits[i]["id"])).get().exists:
            id_not_exist.append(circuits[i]["id"])
            continue
        else:
            doc_ref = db.collection(u'preset_circuits').document(str(circuits[i]["id"]))
            doc_ref.set(circuits[i])
    if len(id_not_exist) == 0:
        return {'success': "All circuits are saved!"}
    else:
        return {'success': "All circuits are saved!", 'not exist': id_not_exist}

# get all circuits
@app.get("/get")
def get():
    docs = db.collection(u'preset_circuits').stream()
    circuits = []
    for doc in docs:
        circuits.append(doc.to_dict())
    if len(circuits) == 0:
        return {'not exist': "No circuits!"}
    else:
        return jsonify(circuits)

# get a circuit by one id, if the circuit is not exist, return the id of the circuit
@app.get("/get/<id>")
def get_by_id(id):
    id_not_exist = None
    if not db.collection(u'preset_circuits').document(str(id)).get().exists:
        id_not_exist = id
    else:
        circuit = []
        circuit.append(doc = db.collection(u'preset_circuits').document(str(id)).get().to_dict())
    if id_not_exist is None:
        return jsonify(circuit)
    else:
        return {'not exist': id_not_exist}


if __name__ == "__main__":
    app.run()

# read from experiments/server_kubernetes_output.csv

file = open("../experiments/server_kubernetes_output.csv", "r")
lines = file.readlines()
groups = {}

def add_to_counter(key, runtime, counter):
    if key not in counter:
        counter[key] = [0, 0]

    counter[key][0] += 1
    counter[key][1] += runtime

for line in lines:
    line = line.split(",")
    print(line)
    if len(line) < 4:
        continue

    a, b, c, d = map(float, line)

    if (a, b, "vary pop") not in groups:
        groups[(a, b, "vary pop")] = {}
    if (a, c, "vary gen") not in groups:
        groups[(a, c, "vary gen")] = {}
    if (b, c, "vary workers") not in groups:
        groups[(b, c, "vary workers")] = {}

    add_to_counter((a, b, c), d, groups[(a, b, "vary pop")])
    add_to_counter((a, b, c), d, groups[(a, c, "vary gen")])
    add_to_counter((a, b, c), d, groups[(b, c, "vary workers")])

valid_groups = [[k, v] for k, v in groups.items() if len(v) > 3]
    

print("gen", "workers", "pop_size", "count", "avg_time")
for k, v in valid_groups:
    print(f"group: {k}")

    # create csv file
    with open(f"serverk8_{k}.csv", "w") as f:
        counter = v
        res = [[k, v[0], v[1]/v[0]] for k,v in counter.items()]
        res.sort()
        for row in res:
            print(*row)
            f.write(f"\n{row[0][0]},{row[0][1]},{row[0][2]},{row[-1]}")
experiment_workload = []
negative_workload = []
stress_workload = []

with open('workload.txt', 'r') as f:
    workload_pattern = f.read().split(' ')

    count = 0
    neg_count = 0
    stress_count = 0
    for item in workload_pattern:
        item = int(item)
        
        if item < 20:
            negative_workload.append(item)
            neg_count += item
        else:
            stress_workload.append(item)
            stress_count += item
        
        experiment_workload.append(item)
        count += item

print(len(experiment_workload), len(negative_workload), len(stress_workload))
print(list(map(lambda r: int(r / 2), experiment_workload)))
print("Experiment workload:{}, exp_count:{}".format(experiment_workload, count))         
print("Negative:{}, Neg_count:{}".format(negative_workload, neg_count))
print("Stress:{}, Stress_Count:{}".format(stress_workload, stress_count))
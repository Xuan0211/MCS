# 这是一个示例 Python 脚本。

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。
import math
import random
import matplotlib.pyplot as plt

WORKER_NUMBER = 4
TARGET_NUMBER = 10
MIDDLE = 100
BAD_CHANCE = 20
CRYPTOGRAPHIC_NUMBER = 2 ** 16
BAD_RANGE = 30
GOOD_RANGE = 15


def data_generation(workers_number, target_number, bad_chance, middle, bad_range, good_range):
    data_bank = []
    worker_state = []
    for worker in range(workers_number):
        worker_data_bank = []
        worker_bad_chance = random.randint(0, 100)
        for target in range(target_number):
            if worker_bad_chance < bad_chance:
                temp = random.randint(- bad_range, bad_range)
                if temp < 0:
                    temp = temp - 10
                else:
                    temp = temp + 10
                worker_data_bank.append(middle + temp)
            else:
                worker_data_bank.append(random.randint(middle - good_range, middle + good_range))
        data_bank.append(worker_data_bank)
        if worker_bad_chance < bad_chance:
            worker_state.append("bad")
        else:
            worker_state.append("good")
    return data_bank, worker_state


data, state = data_generation(WORKER_NUMBER, TARGET_NUMBER, BAD_CHANCE, MIDDLE, BAD_RANGE, GOOD_RANGE)

S1 = []
S2 = []
S3 = []


def divide_to_three(data, workers_number, target_number):
    r = []
    for target in range(target_number):
        r1 = random.random()
        r2 = random.uniform(0, r1)
        r3 = 1 - r1 - r2
        r.append([r1, r2, r3])

    for worker in range(workers_number):
        worker_temp_s1 = []
        worker_temp_s2 = []
        worker_temp_s3 = []

        for target in range(target_number):
            data_item = data[worker][target]
            worker_temp_s1.append(data_item * r[target][0])
            worker_temp_s2.append(data_item * r[target][1])
            worker_temp_s3.append(data_item * r[target][2])

        S1.append(worker_temp_s1)
        S2.append(worker_temp_s2)
        S3.append(worker_temp_s3)


divide_to_three(data, WORKER_NUMBER, TARGET_NUMBER)
S = S1, S2, S3


def main(iteration):
    def truth_discovery(databank, workers_number, target_number, iterations):
        truth_S1 = []
        truth_S2 = []
        truth_S3 = []
        truth = [truth_S1, truth_S2, truth_S3]
        w_S1 = []
        w_S2 = []
        w_S3 = []
        w = [w_S1, w_S2, w_S3]
        # 第一轮 随机生成真值
        for i in range(target_number):
            truth_S1.append(random.randint(0, CRYPTOGRAPHIC_NUMBER))
            truth_S2.append(random.randint(0, CRYPTOGRAPHIC_NUMBER))
            truth_S3.append(random.randint(0, CRYPTOGRAPHIC_NUMBER))

        for round in range(iterations):
            # 安全权重更新
            for k in range(3):
                numerator = 0
                for i in range(workers_number):
                    for j in range(target_number):
                        numerator += (S[k][i][j] - truth[k][j]) ** 2

                for i in range(workers_number):
                    denominator = 0
                    for j in range(target_number):
                        denominator += (S[k][i][j] - truth[k][j]) ** 2

                    w[k].append(math.log(numerator / denominator, 10))

            # 安全真值更新
            for k in range(3):
                for j in range(target_number):
                    numerator = 0
                    denominator = 0
                    for i in range(workers_number):
                        numerator += w[k][i] * S[k][i][j]
                        denominator += w[k][i]

                    truth[k][j] = numerator / denominator

        return truth, w

    truth, w = truth_discovery(data, WORKER_NUMBER, TARGET_NUMBER, iteration)

    w_worker = []
    truth_target = []
    for i in range(WORKER_NUMBER):
        w_sum = 0
        for k in range(3):
            w_sum += w[k][i]
        w_worker.append(w_sum)
    for j in range(TARGET_NUMBER):
        truth_sum = 0
        for k in range(3):
            truth_sum += truth[k][j] % CRYPTOGRAPHIC_NUMBER
        truth_sum %= CRYPTOGRAPHIC_NUMBER
        #truth_sum = int(truth_sum)
        truth_target.append(truth_sum)

    good_min = 10000
    good_max = 0
    bad_min = 10000
    bad_max = 0

    for i in range(WORKER_NUMBER):
        if state[i] == "good":
            if w_worker[i] > good_max:
                good_max = w_worker[i]
            if w_worker[i] < good_min:
                good_min = w_worker[i]
        else:
            if w_worker[i] > bad_max:
                bad_max = w_worker[i]
            if w_worker[i] < bad_min:
                bad_min = w_worker[i]

    def print_info():
        print("-" * 50)
        print("this is generated data")
        print(data)
        print(state)
        print("-" * 50)
        print("this is weight")
        print(w_worker)
        print("good_min: " + str(good_min))
        print("good_max: " + str(good_max))
        print("bad_min: " + str(bad_min))
        print("bad_max: " + str(bad_max))
        print("-" * 50)
        print("this is truth")
        print(truth)
        print(truth_target)

    print_info()

    RMSE = 0
    for truth in truth_target:
        RMSE += (truth - MIDDLE) ** 2
    RMSE = math.sqrt(RMSE / TARGET_NUMBER)
    return RMSE


RMSE = []


def test(iteration_range):
    for iteration in range(1, iteration_range):
        RMSE.append(main(iteration))


test(30)
plt.plot(RMSE)
plt.show()
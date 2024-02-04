import math
import random
import time
from tqdm import tqdm, trange

import matplotlib.pyplot as plt
import numpy as np
SEED = 1
random.seed(SEED)
np.random.seed(SEED)

WORKER_NUMBER = 30
TARGET_NUMBER = 10
MIDDLE = 100
BAD_CHANCE = 30
APPLY_CHANCE = 40
BAD_RANGE = 60
GOOD_RANGE = 5
MAX_TRUTH = 150

W_THRESHOLD = 0.025
TRUSTED_DOT_THRESHOLD = 0.8
UNTRUSTED_DOT_THRESHOLD = 0.2
TRUSTED_SU_SC = 3
UNKNOWN_SU_SC = 1
BASE_UNKNOWN_SU = 2
MIN_SC = 20

K = 15

UNKNOWN_SU = 0
UNTRUSTED_SU = 1
TRUSTED_SU = 2

worker_state = []

INIT_TIME = 0
SELECT_TIME = 1
DISCOVERY_TIME = 2
runtime_history = [[], [], []]

def su_generation(workers_number, bad_chance):
    worker_state = []
    worker_state.append("good")
    for worker in range(workers_number - 1):
        worker_bad_chance = random.randint(0, 100)
        if worker_bad_chance < bad_chance:
            worker_state.append("bad")
        else:
            worker_state.append("good")
    return worker_state

def data_generation(workers_number, target_number, middle, bad_range, good_range):
    data_bank = []
    for worker in range(workers_number):
        worker_data_bank = []
        for target in range(target_number):
            middle_new = np.round( middle * random.randint(95, 105) / 100 )
            if worker_state[worker] == "bad":
                temp = random.randint(- np.round(bad_range * random.random()), np.round(bad_range * random.random()))
                if temp < 0:
                    temp = temp - 10
                else:
                    temp = temp + 10
                worker_data_bank.append(middle_new + temp)
            else:
                worker_data_bank.append(random.randint(middle_new - np.round(good_range * random.random()),
                                                       middle_new + np.round(good_range * random.random())))
        data_bank.append(worker_data_bank)
    return data_bank


def truth_discovery(databank, workers_number, target_number, iterations):
    truth = []
    w = []
    # 第一轮 随机生成真值
    for i in range(target_number):
        truth.append(random.randint(0, MAX_TRUTH))

    for round in range(iterations):
        # 安全权重更新
        numerator = 0
        for i in range(workers_number):
            for j in range(target_number):
                numerator += (databank[i][j] - truth[j]) ** 2

        for i in range(workers_number):
            denominator = 0
            for j in range(target_number):
                denominator += (databank[i][j] - truth[j]) ** 2

            w.append(math.log(numerator / denominator, 10))

        # 安全真值更新
        for j in range(target_number):
            numerator = 0
            denominator = 0
            for i in range(workers_number):
                numerator += w[i] * databank[i][j]
                denominator += w[i]

            truth[j] = numerator / denominator

    return truth, w


def RMSE_cal(data):
    numerator = 0
    for i in range(TARGET_NUMBER):
        numerator += (data[i] - MIDDLE) ** 2
    return math.sqrt(numerator / TARGET_NUMBER)


def RC(request_number):
    init_start_time = time.clock()
    # system init
    SU_state = []
    DOT = []
    # 0 represent unknown SU, 1 represent untrusted SU, 2 represent trusted SU
    # add first trusted person
    SU_state.append(TRUSTED_SU)
    DOT.append(1)
    # on start init all SU as unknown
    for i in range(WORKER_NUMBER - 1):
        SU_state.append(UNKNOWN_SU)
    # on start init all DOT as 0.5
    for i in range(WORKER_NUMBER - 1):
        DOT.append(0.5)

    request_count = 0

    init_end_time = time.clock()
    init_time = init_end_time - init_start_time

    recruit_time_history = []
    truth_update_time_history = []

    # deal with request
    for i in range(request_number):
        request_count += 1
        if request_count % 10 == 0:
            print(f'{request_count}/{request_number}')
        # generate data (stimulate SU upload)
        data = data_generation(WORKER_NUMBER, TARGET_NUMBER, MIDDLE, BAD_RANGE, GOOD_RANGE)
        truth, w = truth_discovery(data, WORKER_NUMBER, TARGET_NUMBER, request_number)
        # apply for tasks
        su_apply_state = []
        su_apply_count = [0, 0, 0]
        for su in range(WORKER_NUMBER):
            if random.randint(0, 100) < APPLY_CHANCE:
                su_apply_state.append(True)
                su_apply_count[SU_state[su]] += 1
            else:
                su_apply_state.append(False)
        # upload DOT
        # calculate w mean in trusted su
        recruit_start_time = time.clock()
        # select SU
        su_selected_state = []
        su_selected_count = 0
        current_sc = 0
        sum_sc = su_apply_count[TRUSTED_SU] * TRUSTED_SU_SC + su_apply_count[UNKNOWN_SU] * UNKNOWN_SU_SC
        # init su_selected_state as false
        for su in range(WORKER_NUMBER):
            su_selected_state.append(False)
        su_selected_state[0] = True
        # select init SU
        # select trusted_su first
        # than select unknown su
        for su in range(WORKER_NUMBER):
            if su_selected_count >= min(BASE_UNKNOWN_SU, su_apply_count[UNKNOWN_SU]):
                break
            if SU_state[su] == UNKNOWN_SU:
                su_selected_state[su] = True
                su_selected_count += 1
                current_sc += UNKNOWN_SU_SC
        for su in range(WORKER_NUMBER):
            if current_sc >= min(sum_sc, MIN_SC):
                break
            if SU_state[su] == TRUSTED_SU:
                su_selected_state[su] = True
                su_selected_count += 1
                current_sc += TRUSTED_SU_SC
        for su in range(WORKER_NUMBER):
            if current_sc >= min(sum_sc, MIN_SC):
                break
            if SU_state[su] == UNKNOWN_SU:
                su_selected_state[su] = True
                su_selected_count += 1
                current_sc += UNKNOWN_SU_SC

        # calculate w mean variance in selected su
        # if variance is too large, then select more su
        while True:
            if current_sc >= min(sum_sc, MIN_SC):
                break
            else:
                for su_new in range(WORKER_NUMBER):
                    if su_selected_state[su_new] is False and SU_state[su_new] == TRUSTED_SU:
                        su_selected_state[su_new] = True
                        su_selected_count += 1
                        current_sc += TRUSTED_SU_SC
                        break
                if current_sc >= min(sum_sc, MIN_SC):
                    break
                else:
                    for su_new in range(WORKER_NUMBER):
                        if su_selected_state[su_new] is False and SU_state[su_new] == UNKNOWN_SU:
                            su_selected_state[su_new] = True
                            su_selected_count += 1
                            current_sc += UNKNOWN_SU_SC
                            break

        recruit_end_time = time.clock()
        recruit_time = recruit_end_time - recruit_start_time

        recruit_time_history.append(recruit_time)


        truth_update_start_time = time.clock()

        w_trusted_mean = 0
        trusted_number = 0
        for su in range(WORKER_NUMBER):
            if SU_state[su] == TRUSTED_SU and su_selected_state[su]:
                trusted_number += 1
                w_trusted_mean += w[su]

        w_trusted_mean = w_trusted_mean / trusted_number

        # upload each DOT and reclassify SU
        for su in range(WORKER_NUMBER):
            if su_selected_state[su] is False:
                continue
            if SU_state[su] == UNKNOWN_SU:
                if abs(w[su] - w_trusted_mean) < W_THRESHOLD * w_trusted_mean:
                    DOT[su] = DOT[su] + (1 - DOT[su]) / K
                else:
                    DOT[su] = DOT[su] - DOT[su] / K

                if DOT[su] > TRUSTED_DOT_THRESHOLD:
                    SU_state[su] = TRUSTED_SU
                    DOT[su] = 1
                if DOT[su] < UNTRUSTED_DOT_THRESHOLD:
                    SU_state[su] = UNTRUSTED_SU
                    DOT[su] = 0

        # update truth
        truth_new = []
        for target in range(TARGET_NUMBER):
            numerator = 0
            denominator = 0
            for su in range(WORKER_NUMBER):
                if su_selected_state is False:
                    continue
                numerator += DOT[su] * data[su][target]
                denominator += DOT[su]
            truth_new.append(numerator / denominator)

        truth_update_end_time = time.clock()
        truth_update_time = truth_update_end_time - truth_update_start_time

        truth_update_time_history.append(truth_update_time)

    return init_time, truth_update_time_history, recruit_time_history


for i in tqdm(range(5, 20),  desc="RC"):
    TARGET_NUMBER = i
    worker_state = su_generation(WORKER_NUMBER, BAD_CHANCE)
    init_time, select_time, discovery_time = RC(200)
    runtime_history[INIT_TIME].append(init_time)
    runtime_history[SELECT_TIME].append(np.array(select_time).sum())
    runtime_history[DISCOVERY_TIME].append(np.array(discovery_time).sum())

plt.figure(figsize=(10, 6))
# set x-axis from 5 to 20
plt.xticks(range(5, 21))
plt.plot(runtime_history[INIT_TIME], label="init_time")
plt.plot(runtime_history[SELECT_TIME], label="select_time")
plt.plot(runtime_history[DISCOVERY_TIME], label="discovery_time")
plt.legend()
plt.show()
# 实现Sharemind的基本功能
import requests
import json
import time
import os
import sys
import re
import random
import numpy as np
import pandas as pd


CRYPTOGRAPHIC_NUMBER = 2 ** 4


def generate_random():
    return random.randint(0, CRYPTOGRAPHIC_NUMBER)


class SharemindServer(object):
    """
    半可信服务器
    """

    def __init__(self, name):
        self.__databank = []
        self.__stack = {}
        self.__truth = []
        self.name = name

    def init_truth(self, target_number):
        for _ in range(target_number):
            self.__truth.append(generate_random())

    def get_truth(self):
        return self.__truth

    def get_into_stack(self, key, value):
        self.__stack[key] = value

    def get_frome_stack(self, key):
        return self.__stack[key]

    def get_data(self, data):
        """
        接受客户端传来的数据
        """
        self.__databank.append(data)
        print(f"{self.name} get data {data}")
        print(f"{self.name} truth {self.__databank}")

    def scale(self, c, i, j):
        """
        数乘
        """
        self.__databank[i][j] = self.__databank[i][j] * c

    def add(self, i_1, j_1, i_2, j_2):
        """
        数相加
        """
        return self.__databank[i_1][j_1] + self.__databank[i_2][j_2]

    def minus(self, i_1, j_1, i_2, j_2):
        """
        数相减
        """
        return self.__databank[i_1][j_1] - self.__databank[i_2][j_2]

    def minus_truth(self, i, j):
        """
        数相减
        """
        return self.__databank[i][j] - self.__truth[j]

    def share_multiply(self, i_1, j_1, i_2, j_2):
        """
        share multiply
        """
        return self.__databank[i_1][j_1] * self.__databank[i_2][j_2] % CRYPTOGRAPHIC_NUMBER

    def Du_Atallah_P1_stage1(self, r, i_1, j_1, i_2, j_2, P2):
        x1_plus_r1 = self.__databank[i_1][j_1] + r
        x1_plus_r1 = x1_plus_r1 % CRYPTOGRAPHIC_NUMBER
        self.get_into_stack("x1_plus_r1", x1_plus_r1)
        P2.get_into_stack("x1_plus_r1", x1_plus_r1)

    def Du_Atallah_P1_stage2(self, r, i_1, j_1, i_2, j_2, P2):
        x1_plus_r1 = self.get_frome_stack("x1_plus_r1")
        x2_plus_r2 = self.get_frome_stack("x2_plus_r2")
        w1 = - x1_plus_r1 * x2_plus_r2 + self.__databank[i_1][j_1] * x2_plus_r2
        w1 = w1 % CRYPTOGRAPHIC_NUMBER
        return w1

    def Du_Atallah_P2_stage1(self, r, i_1, j_1, i_2, j_2, P1):
        x2_plus_r2 = self.__databank[i_2][j_2] + r
        x2_plus_r2 = x2_plus_r2 % CRYPTOGRAPHIC_NUMBER
        P1.get_into_stack("x2_plus_r2", x2_plus_r2)
        self.get_into_stack("x2_plus_r2", x2_plus_r2)

    def Du_Atallah_P2_stage2(self, r, i_1, j_1, i_2, j_2, P1):
        x1_plus_r1 = self.get_frome_stack("x1_plus_r1")
        x2_plus_r2 = self.get_frome_stack("x2_plus_r2")
        w2 = x1_plus_r1 * self.__databank[i_2][j_2]
        w2 = w2 % CRYPTOGRAPHIC_NUMBER
        return w2

    def Du_Atallah(self, i_1, j_1, i_2, j_2, P1, P2):
        """
        Use Du_Atallah protocol to computing shares of u_i*v_j while i != j
        """
        r1 = generate_random()
        r2 = generate_random()
        # r1 = 1
        # r2 = 2
        P1.Du_Atallah_P1_stage1(r1, i_1, j_1, i_2, j_2, P2)
        P2.Du_Atallah_P2_stage1(r2, i_1, j_1, i_2, j_2, P1)
        w1 = P1.Du_Atallah_P1_stage2(r1, i_1, j_1, i_2, j_2, P2)
        w2 = P2.Du_Atallah_P2_stage2(r2, i_1, j_1, i_2, j_2, P1)
        w3 = r1 * r2
        w3 = w3 % CRYPTOGRAPHIC_NUMBER

        ans = (w1 + w2 + w3) % CRYPTOGRAPHIC_NUMBER
        # print(f"{self.name} w1 {w1}")
        # print(f"{self.name} w2 {w2}")
        # print(f"{self.name} w3 {w3}")
        # print(f"{self.name} Du_Atallah {ans}")
        return ans


class SharemindPlatform(SharemindServer):
    """
    核心平台
    """

    def get_weight(self):
        numerator = 0
        denominator = 0
        pass

    def multiply(self, i_1, j_1, i_2, j_2, P1, P2):
        """
        乘法
        """
        u1_times_v1 = P1.share_multiply(i_1, j_1, i_2, j_2)
        u2_times_v2 = P2.share_multiply(i_1, j_1, i_2, j_2)
        u3_times_v3 = self.share_multiply(i_1, j_1, i_2, j_2)

        u1_times_v2 = self.Du_Atallah(i_1, j_1, i_2, j_2, P1, P2)
        u1_times_v3 = P2.Du_Atallah(i_1, j_1, i_2, j_2, P1, self)
        u2_times_v1 = self.Du_Atallah(i_1, j_1, i_2, j_2, P2, P1)
        u2_times_v3 = P1.Du_Atallah(i_1, j_1, i_2, j_2, P2, self)
        u3_times_v1 = P2.Du_Atallah(i_1, j_1, i_2, j_2, self, P1)
        u3_times_v2 = P1.Du_Atallah(i_1, j_1, i_2, j_2, self, P2)

        # print(f"u1_times_v1:  {u1_times_v1}")
        # print(f"u2_times_v2:  {u2_times_v2}")
        # print(f"u3_times_v3:  {u3_times_v3}")
        #
        # print(f"u1_times_v2:  {u1_times_v2}")
        # print(f"u1_times_v3:  {u1_times_v3}")
        # print(f"u2_times_v3:  {u2_times_v3}")
        # print(f"u2_times_v1:  {u2_times_v1}")
        # print(f"u3_times_v1:  {u3_times_v1}")
        # print(f"u3_times_v2:  {u3_times_v2}")

        ans = u1_times_v1 + u2_times_v2 + u3_times_v3
        ans = ans + u1_times_v2 + u1_times_v3 + u2_times_v3 + u2_times_v1 + u3_times_v1 + u3_times_v2
        ans = ans % CRYPTOGRAPHIC_NUMBER
        return ans


class Sharemind(object):
    """
    运行在用户端的 Sharemind client
    """

    # 定义类属性记录单例对象引用
    instance = None

    def __new__(cls, *args, **kwargs):

        # 1. 判断类属性是否已经被赋值
        if cls.instance is None:
            cls.instance = super().__new__(cls)

        # 2. 返回类属性的单例引用
        return cls.instance

    def __init__(self):
        self.__S1 = SharemindServer("S1")
        self.__S2 = SharemindServer("S2")
        self.__Platform = SharemindPlatform("Platform")
        self.workers_number = 0
        self.target_number = 0
        print("Sharemind init")

    def data_upload(self, data):
        """
        上传数据
        """
        S1_data = []
        S2_data = []
        Platform_data = []

        for item in data:
            r1 = generate_random()
            r2 = generate_random()
            # r1 = 1
            # r2 = 0
            r3 = (item - r1 - r2) % CRYPTOGRAPHIC_NUMBER
            S1_data.append(r1)
            S2_data.append(r2)
            Platform_data.append(r3)

        self.__S1.get_data(S1_data)
        self.__S2.get_data(S2_data)
        self.__Platform.get_data(Platform_data)

        self.workers_number = len(data)
        self.target_number = data[0]

    def multiply(self, i_1, j_1, i_2, j_2):
        """
        乘法
        """
        return self.__Platform.multiply(i_1, j_1, i_2, j_2, self.__S1, self.__S2)

    def truth_discovery(self):
        truth = []
        self.__S1.init_truth(self.target_number)
        self.__S2.init_truth(self.target_number)
        self.__Platform.init_truth(self.target_number)

        truth.append(self.__S1.get_truth())
        truth.append(self.__S2.get_truth())
        truth.append(self.__Platform.get_truth())

        truth = np.array(truth)
        ans = np.sum(truth, axis=0)
        ans = ans % CRYPTOGRAPHIC_NUMBER

        print(ans)


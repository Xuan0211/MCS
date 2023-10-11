from sharemind import Sharemind
databank = [[1,2,3],[4,5,6],[7,8,9]]
sm = Sharemind()
for user_data in databank:
    sm.data_upload(user_data)

print(sm.multiply(1, 0, 1, 1))

sm.truth_discovery()
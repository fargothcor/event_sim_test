import simpy
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from config import *

# Массивы для хранения значений длины очередей 
DESK_QUEUE_STATES = []
SECURITY_QUEUE_STATES = []
TIME = []


# Класс среды, где описаны все процессы и пункты
class Desk:
    def __init__(self, env, N_tickets_desk, T_ticket, N_security, T_security, halls, T_room_entrance):
        self.env = env
        self.T_desk = T_ticket
        self.T_security = T_security
        self.desks = simpy.Resource(env, N_tickets_desk)
        self.posts = simpy.Resource(env, N_security)
        # Поскольку залы разные, то каждый из них представляет собой отдельный ресурс
        self.halls = [simpy.Resource(env, 1) for i in range(halls)] 
        self.T_room_entrance = T_room_entrance

    
    # Покупка билета в кассе
    def buy_ticket(self, visitor):

        yield self.env.timeout(self.T_desk)
        
        # print(f'ticket bought by visitor {visitor} at {self.env.now}')


    # Пункт досмотра
    def sec_check(self, visitor):
        yield self.env.timeout(self.T_security)
        # print(f'visitor {visitor} was checked at {self.env.now}')

    
    # Проход в зал
    def hall_check(self, visitor):
        yield self.env.timeout(self.T_room_entrance)



# Генератор, в котором описаны все действия посетителя
def visitor(env, name, desk, hall, begin_time):
    # Максимум берется для того, чтобы не получить отрицательное время ожидания
    arrive_time = max(1, int(np.random.normal(begin_time - T_before_start, 5*60)))
    yield env.timeout(arrive_time)
    # print(f'visitor {name} arrives to queue at {env.now} to movie {hall}')

    # Покупка билета на кассе
    with desk.desks.request() as request:
        yield request
        yield env.process(desk.buy_ticket(name))

    
    # Проход пункта досмотра
    with desk.posts.request() as request:
        # print(f'Security queue is: {len(desk.posts.queue)} at {env.now}')
        yield request
        # print(f'visitor {name} arrives to check post at {env.now}')
        yield env.process(desk.sec_check(name))
        # print(f'visitor {name} leaves check post at {env.now}')


    # Проход в зал
    with desk.halls[hall].request() as request:
        # print(f'Hall {hall} queue is: {len(desk.posts.queue)} at {env.now}')
        yield request
        # print(f'visitor {name} arrives to hall {hall} post at {env.now}')
        yield env.process(desk.hall_check(name))
        # print(f'visitor {name} leaves hall {hall} at {env.now}')
    

# Преобразования формата времени
def to_seconds(hh_mm):
    h = int(hh_mm[0:2]) * 3600
    m = int(hh_mm[3:5]) * 60
    return h + m


# Проверка длины очередей
def check_state(env, desk):
    while True:
        global DESK_QUEUE_STATES, TIME, SECURITY_QUEUE_STATES
        desk_max = 0
        sec_max = 0
        halls_max = [0 for _ in range(len(desk.halls))]
        # Вычисляем самую большую длину очереди за 15 минут 
        for minute in range(15):
            if len(desk.desks.queue) > desk_max:
                desk_max = len(desk.desks.queue)
            if len(desk.posts.queue) > sec_max:
                sec_max = len(desk.posts.queue)
            for i in range(len(desk.halls)):
                if len(desk.halls[i].queue) > halls_max[i]:
                    halls_max[i] = len(desk.halls[i].queue)
            yield env.timeout(60)
        DESK_QUEUE_STATES.append(desk_max)
        SECURITY_QUEUE_STATES.append(sec_max)
        for i in range(len(desk.halls)):
            HALLS_QUEUE_STATES[i].append(halls_max[i])
        TIME.append(env.now // (60*15))


# Создание объектов и добавление посетителей
def setup(env, N_tickets_desk, T_ticket, N_security, T_security, halls, T_room_entrance, df):
    desk = Desk(env, N_tickets_desk, T_ticket, N_security, T_security, halls, T_room_entrance)
    env.process(check_state(env, desk))
    i = 0
    yield env.timeout(1) # Без этого не работает
    for film in range(len(df.index)):
        num_of_visitors = df.iloc[film]["number_of_visitors"]
        hall = df.iloc[film]["hall_number"]
        begin_time = to_seconds(df.iloc[film]["begin_time"])
        for i in range(num_of_visitors):
            env.process(visitor(env, i, desk, hall, begin_time))


env = simpy.Environment()
df = pd.read_csv('./data.csv')
halls = len(df['hall_number'].unique())

HALLS_QUEUE_STATES = [ [] for i in range(halls)]

env.process(setup(env, N_tickets_desk, T_ticket,N_security, T_security, halls, T_room_entrance, df))

print('start sim')
env.run(until=12*3600)


# Построение графиков
plt.figure()
plt.subplot(211)
plt.bar(TIME, DESK_QUEUE_STATES)
plt.title('Очереди на кассах')
for i in range(len(df.index)):
    time = to_seconds(df.iloc[i]['begin_time']) // (60*15)
    plt.plot([time, time], [0, 40], c='r')

plt.subplot(212)
plt.bar(TIME, SECURITY_QUEUE_STATES)

for i in range(len(df.index)):
    time = to_seconds(df.iloc[i]['begin_time']) // (60*15)
    plt.plot([time, time], [0, 40], c='r')

plt.title('Очереди на пунктах досмотра')

plt.subplots_adjust(hspace=0.5)



plt.savefig(f'./Report/images/{PREFIX}_desk_and_sec.png')


fig, ax = plt.subplots(halls, 1)
for i in range(halls):
    ax[i].bar(TIME, HALLS_QUEUE_STATES[i])
    times = df[df['hall_number'] == i]['begin_time'].reset_index(drop=True)
    for j in range(len(times)):
        time = to_seconds(times[j]) // (60*15)
        ax[i].plot([time, time], [0, 40], c='r')
        ax[i].set_title(f'Зал номер {i}')
    fig.subplots_adjust(hspace=0.5)

plt.savefig(f'./Report/images/{PREFIX}_halls.png')
plt.show()

print('end sim')


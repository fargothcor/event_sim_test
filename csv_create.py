import pandas as pd

df = pd.DataFrame({
    'hall_number': [0, 1, 2, 1],
    'begin_time': ['00:45', '04:45', '11:30', '09:00'],
    'number_of_visitors': [43, 51, 27, 62]
})

df.to_csv('./data.csv')
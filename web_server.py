from flask import Flask, send_file
from flask import request
from matplotlib import pyplot as plt
import pandas as pd
import os
from matplotlib.dates import DateFormatter
import matplotlib as mpl
import numpy as np


def save_plot(dataset=-1, max_points=300, max_hours=12)->str:
    max_points=min(max_points, 2000)
    datasets = [f for f in os.listdir(
        'data/') if os.path.isfile(os.path.join('data', f))]

    datasets.sort()
    df = pd.read_csv(os.path.join('data', datasets[dataset]))

    df=df[df['timestamp'].max()-df['timestamp']<=max_hours*3600e9]
    if len(df) > max_points:
        rows_per_group = len(df) // max_points
        df['group'] = df.index // rows_per_group
        df = df.groupby('group').agg({
            'mean_amplitude': 'max',
            'timestamp': lambda x: x.iloc[np.argmax(df.loc[x.index, 'mean_amplitude'])]
        }).reset_index(drop=True)
        df.drop(columns='group', inplace=True, errors='ignore')
    df['datetime'] = pd.to_datetime(df['timestamp']+1*3600*1e9, unit='ns')

    fig, ax = plt.subplots()
    colourmap = mpl.colormaps['plasma']

    ax.plot(df['datetime'], df['mean_amplitude'], label='Noise', c='black')

    normalize = mpl.colors.Normalize(vmin=0, vmax=.8)
    for i in range(len(df) - 1):
        plt.fill_between([df['datetime'][i], df['datetime'][i+1]],
                        [df['mean_amplitude'][i], df['mean_amplitude'][i+1]],
                        color=colourmap(normalize(df['mean_amplitude'][i]))
                        ,alpha=1)

    plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M'))
    fig.set_size_inches(24, 8)
    plt.xlabel("Time (HH:MM)")
    plt.ylabel("Noise Amplitude")
    plt.xticks(rotation=45)
    plt.grid(True)
    fig.savefig('plots/plot.jpg', format='jpg', bbox_inches='tight', pad_inches=0 )
    return 'plots/plot.jpg'

app = Flask(__name__)

@app.route('/noise/plot')
def noise_plot():
    max_points = request.args.get('max_points', default = 300, type = int)
    max_hours = request.args.get('max_hours', default = 12, type = int)
    dataset=request.args.get('dataset',default=-1,type=int)
    file=save_plot(dataset=dataset,max_points=max_points,max_hours=max_hours)
    return send_file(file, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(
            debug=False,
            host='0.0.0.0',
            port=8080, 
            ssl_context=('secrets/cert.pem', 'secrets/key.pem')
        )

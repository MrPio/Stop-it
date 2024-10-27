import sounddevice as sd
import numpy as np
from pygame import mixer
import time
import os
import random
import pandas as pd
import datetime
from time import time_ns


SEND_ALERT=False
MIC_SENSITIVITY=25
VOLUME_NIGHT=50
VOLUME_DAY=120
THRESHOLD_NIGHT = .35
THRESHOLD_DAY = .5
CHECK_INTERVAL = 1.5
CHECK_DURATION = .25
WAIT_FOR_NEXT_ONE = 300
SAVE_EVERY=120
BUFFER_FILL=.35
BUFFER_DEFILL=.005
start = datetime.datetime.now().strftime('%Y %m %d - %H %M %S')
os.system(f'amixer set Capture {MIC_SENSITIVITY}%')

mixer.init()
alert_files = [os.path.join('alerts', f) for f in os.listdir(
    'alerts/') if os.path.isfile(os.path.join('alerts', f))]
beep_file='alerts/others/beep.wav'

def is_night():
    return time.localtime().tm_hour in range(1, 9)

def detect_noise():
    recording = sd.rec(int(CHECK_DURATION * 44100), samplerate=44100, channels=1)
    sd.wait()
    return np.mean(np.abs(recording))

def log(msg:str):
    print(f"({datetime.datetime.now().strftime('%Y/%m/%d - %H:%M:%S')}) - {msg}")
    
def play(clip:str, volume_scale:int=1):
    os.system(f"amixer set 'Master' {(VOLUME_NIGHT if is_night() else VOLUME_DAY)//(1/volume_scale)}%") 
    mixer.Sound(clip).play()

if __name__ == '__main__':
    last_alert=0
    buffer=0
    data = []
    iteration = 1
    log('Starting recording...')
    while True:
        mean_amplitude = detect_noise()
        data.append({
            'timestamp': time_ns(),
            'mean_amplitude': round(mean_amplitude, 3),
        })
        if (iteration % (SAVE_EVERY//(CHECK_DURATION+CHECK_INTERVAL)) == 0 and len(data) > 0):
            pd.DataFrame.from_records(data[1:]).to_csv(f'data/{start}')
            log(f'[Iteration {iteration}] saving...')
        if SEND_ALERT and (time_ns()-last_alert)>WAIT_FOR_NEXT_ONE*1e9:
            if mean_amplitude>(THRESHOLD_NIGHT if is_night() else THRESHOLD_DAY):
                buffer+=BUFFER_FILL
                if buffer>=1:
                    play(random.choice(alert_files))
                    buffer=0
                    last_alert=time_ns()
                    log(f"Noise detected! Now playing alert. Waiting {WAIT_FOR_NEXT_ONE}sec for the next one.")
                else:
                    play(beep_file,volume_scale=0.5)
                    log(f"Noise detected! Buffer={buffer}")
            else:
                buffer=max(0,buffer-BUFFER_DEFILL)
        iteration += 1
        time.sleep(CHECK_INTERVAL)

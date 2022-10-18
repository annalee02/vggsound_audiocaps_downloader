import sys
import time
import logging
import soundfile
import numpy
import os

def flac2wav(filename, dir_path):
    # Define flac audio filename and path
    flac_filename = 'flac/{}'.format(filename)
    flac_full_path = dir_path + flac_filename
    wav_dir_path = dir_path + 'wav'
    # Extract name without extension
    filename = os.path.splitext(filename)[0]
    wav_filename = '{}.wav'.format(filename)
    # Create wav audio files if it doesn't exist
    if wav_filename not in os.listdir(wav_dir_path):
        wav_full_path = wav_dir_path + '/' + wav_filename
        # Read and write a file
        audio, sr = soundfile.read(flac_full_path)
        soundfile.write(wav_full_path, audio, sr, 'PCM_16')
        print(wav_full_path)

if __name__ == "__main__":
    dir_path_list = ['/data/dlt/clap/raw_data/AUDIOCAPS/', '/data/dlt/clap/raw_data/VGGSound/']

    # list to store files
    res = []
    # Iterate directory
    for dir_path in dir_path_list:
        flac_dir_path = dir_path + 'flac'
        for filename in os.listdir(flac_dir_path):
            if os.path.isfile(os.path.join(flac_dir_path, filename)):
                res.append(filename)
                # Convert flac file to wav
                try:
                    flac2wav(filename, dir_path)
                except:
                    pass
        print(res[:10])
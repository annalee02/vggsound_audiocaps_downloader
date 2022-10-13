'''
Find mp4 and wav pairs and save as csv
'''
import sys
import time
import logging
import soundfile
import numpy
import os
import pandas as pd

df = pd.DataFrame(columns=['ytid', 'spoken_description'])

class AUDIOVIDEOPAIRS:
    def __init__(self):
        self.df = df
    
    def find_pairs(self, filename, dir_path):
        # Define mp4 audio filename and path
        mp4_filename = 'mp4/{}'.format(filename)
        mp4_full_path = dir_path + mp4_filename
        wav_dir_path = dir_path + 'wav'
        filename = os.path.splitext(filename)[0]
        wav_filename = '{}.wav'.format(filename)
        vggsound_meta = pd.read_csv('data/vggsound.csv', header=None)
        # Write in dataframe if a corresponding wav file exists
        if wav_filename in os.listdir(wav_dir_path):
            wav_full_path = wav_dir_path + '/' + wav_filename
            row_loc = vggsound_meta.loc[vggsound_meta.iloc[:,0] == wav_filename[:11]]
            #print(row_loc)
            sound_description = row_loc[2].values[0]
            # Append a row
            filename = filename + '.mp4'
            self.df = self.df.append([{'ytid': filename, 'spoken_description': sound_description}], ignore_index=True)
    
    def run(self, dir_path):
        # list to store files
        res = []
        # Iterate directory
        mp4_dir_path = dir_path + 'mp4'
        for filename in os.listdir(mp4_dir_path):
            if os.path.isfile(os.path.join(mp4_dir_path, filename)):
                res.append(filename)
                # Convert mp4 file to wav
                self.find_pairs(filename, dir_path)
        return self.df
        

if __name__ == "__main__":
    dir_path = '/data/dlt/clap/raw_data/VGGSound/'

    output_df = AUDIOVIDEOPAIRS().run(dir_path)
    print(output_df.head())
    # save to csv that will be used for model training
    output_df.to_csv('data/split/sample.csv', index=False, header=False)

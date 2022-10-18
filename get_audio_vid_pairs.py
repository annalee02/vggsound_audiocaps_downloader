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
# data_name = 'AUDIOCAPS'
data_name = 'VGGSound'

class AUDIOVIDEOPAIRS:
    def __init__(self):
        self.df = df
        self.cnt = 0
    
    def find_pairs(self, filename, dir_path):
        # Define mp4 audio filename and path
        mp4_filename = 'mp4/{}'.format(filename)
        mp4_full_path = dir_path + mp4_filename
        wav_dir_path = dir_path + 'wav'
        filename = os.path.splitext(filename)[0]
        wav_filename = '{}.wav'.format(filename)
        # Write in dataframe if a corresponding wav file exists
        if wav_filename in os.listdir(wav_dir_path):
            wav_full_path = wav_dir_path + '/' + wav_filename
            filename = filename + '.mp4'
            if data_name == 'VGGSound':
                meta_filename = 'vggsound'
                meta_path = 'data/{}/{}.csv'.format(data_name, meta_filename)
                youtube_meta = pd.read_csv(meta_path, header=None)
                row_loc = youtube_meta.loc[youtube_meta.iloc[:,0] == wav_filename[:11]] # 11 == ytid length
                sound_description = row_loc[2].values[0]
                train_test = row_loc[3].values[0]
                # Append a row
                self.df = self.df.append([{'ytid': filename, 'spoken_description': sound_description, 'split': train_test}], ignore_index=True)
                self.cnt += 1
            elif data_name == 'AUDIOCAPS':
                meta_filenames = ['train', 'val', 'test']
                for meta_filename in meta_filenames:
                    meta_path = 'data/{}/{}.csv'.format(data_name, meta_filename)
                    youtube_meta = pd.read_csv(meta_path, usecols=['youtube_id','start_time','caption'])
                    sound_description_df = youtube_meta.loc[youtube_meta['youtube_id'] == wav_filename[:11]]
                    sound_description = sound_description_df['caption'].tolist()
                    # Append a row
                    if len(sound_description) != 0:
                        self.df = self.df.append([{'ytid': filename, 'spoken_description': sound_description, 'split': meta_filename}], ignore_index=True)
                        self.cnt += 1
    
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
            if self.cnt % 100 == 0:
                print(self.cnt)
            break
        return self.df
        

if __name__ == "__main__":
    dir_path = '/data/dlt/clap/raw_data/{}/'.format(data_name)

    output_df = AUDIOVIDEOPAIRS().run(dir_path)
    print(output_df.head())
    # save to csv that will be used for model training
    output_df.to_csv('data/split/{}/sample.csv'.format(data_name), index=False, header=False)
    output_df.to_csv('/data/dlt/clap/raw_data/{}/split/sample.csv'.format(data_name), index=False, header=False)

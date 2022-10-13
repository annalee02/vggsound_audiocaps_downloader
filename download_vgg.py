# Path to ffmpeg
ffmpeg_path = './bin/ffmpeg-3.3.4-64bit-static/ffmpeg'
ffprobe_path = './bin/ffmpeg-3.3.4-64bit-static/ffprobe'

import sys
import os.path
# sys.path.append(os.path.dirname(ffmpeg_path))

import multiprocessing_logging
import pafy # pip install pafy, youtube-dl==2020.12.2
import subprocess as sp
from utils import run_command, is_url, get_filename, \
    get_subset_name, get_media_filename, HTTP_ERR_PATTERN

from download_audioset import ffmpeg
from validation import validate_audio, validate_video

import logging.handlers
LOGGER = logging.getLogger('audiosetdl')
LOGGER.setLevel(logging.DEBUG)

# Set output settings
audio_codec = 'flac'
audio_container = 'flac'
video_codec = 'h264'
video_container = 'mp4'

# Load the AudioSet training set
with open('./data/vggsound.csv') as f:
    lines = f.readlines()

dl_list = [line.strip().split(',')[:3] for line in lines[3:]]
num_dl_list = len(dl_list)

# Select a YouTube video from the training set
ytid, ts_start, label = dl_list[0]

# Test
# ytid = 'BzW-Wd4fBQ4'#'---1_cCGK4M'
# ts_start = 0

ts_end = int(ts_start) + 10
ts_start, ts_end = float(ts_start), float(ts_end)
duration = ts_end - ts_start

print("YouTube ID: " + ytid)
print("Trim Window: ({}, {})".format(ts_start, ts_end))


# Get the URL to the video page
video_page_url = 'https://www.youtube.com/watch?v={}'.format(ytid)
print('video_page_url: ', video_page_url)

# Test
# video_page_url = 'https://www.youtube.com/watch?v=---1_cCGK4M'
# video_page_url = 'https://www.youtube.com/watch?v=--5OkAjCI7g'

# Get the direct URLs to the videos with best audio and with best video (with audio)
video = pafy.new(video_page_url)

best_video = video.getbestvideo(preftype=video_container)
best_video_url = best_video.url
print("Video URL: " + best_video_url)

best_audio = video.getbestaudio()#preftype='m4a')
best_audio_url = best_audio.url
print("Audio URL: " + best_audio_url)

# Test download raw files
# best_video.download(filepath='./data')
# best_audio.download(filepath='./data')

# Get output video and audio filepaths
v_basename_fmt = 'data/VGGSound/{}/{}'.format(video_container, ytid)
a_basename_fmt = 'data/VGGSound/{}/{}'.format(audio_container, ytid)
video_filepath = os.path.join('.', v_basename_fmt + '.' + video_container)
audio_filepath = os.path.join('.', a_basename_fmt + '.' + audio_container)
print("video_filepath: ", video_filepath)
print("audio_filepath: ", audio_filepath)

def download_without_ffmpeg():
    # Download the video
    print("\n\n")
    video_dl_args = [ffmpeg_path, '-n',
        '-ss', str(ts_start),   # The beginning of the trim window
        '-i', best_video_url,   # Specify the input video URL
        '-t', str(duration),    # Specify the duration of the output
        '-f', video_container,  # Specify the format (container) of the video
        '-framerate', '30',     # Specify the framerate
        '-vcodec', 'h264',      # Specify the output encoding
        video_filepath]

    proc = sp.Popen(video_dl_args, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print(stderr)
    else:
        print("Downloaded video to " + video_filepath)

    # Download the audio
    print("\n\n")
    audio_dl_args = [ffmpeg_path, '-n',
        '-ss', str(ts_start),    # The beginning of the trim window
        '-i', best_audio_url,    # Specify the input video URL
        '-t', str(duration),     # Specify the duration of the output
        '-vn',                   # Suppress the video stream
        '-ac', '2',              # Set the number of channels
        '-sample_fmt', 's16',    # Specify the bit depth
        '-acodec', audio_codec,  # Specify the output encoding
        '-ar', '44100',          # Specify the audio sample rate
        audio_filepath]

    proc = sp.Popen(audio_dl_args, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        print(stderr)
    else:
        print("Downloaded audio to " + audio_filepath)

# for i in range(10):
#     download_without_ffmpeg()

def download_yt_video(ytid, ts_start, ts_end, output_dir, ffmpeg_path, ffprobe_path,
                      audio_codec='flac', audio_format='flac',
                      audio_sample_rate=48000, audio_bit_depth=16,
                      video_codec='h264', video_format='mp4',
                      video_mode='bestvideoaudio', video_frame_rate=30,
                      num_retries=1):
    """
    Download a Youtube video (with the audio and video separated).

    The audio will be saved in <output_dir>/audio and the video will be saved in
    <output_dir>/video.

    The output filename is of the format:
        <YouTube ID>_<start time in ms>_<end time in ms>.<extension>

    """
    print("start")
    # Compute some things from the segment boundaries
    duration = ts_end - ts_start

    # Make the output format and video URL
    # Output format is in the format:
    #   <YouTube ID>_<start time in ms>_<end time in ms>.<extension>
    media_filename = get_media_filename(ytid, ts_start, ts_end)
    video_filepath = os.path.join(output_dir, video_format, media_filename + '.' + video_format)
    audio_filepath = os.path.join(output_dir, audio_format, media_filename + '.' + audio_format)
    video_page_url = 'https://www.youtube.com/watch?v={}'.format(ytid)

    # Get the direct URLs to the videos with best audio and with best video (with audio)

    video = pafy.new(video_page_url)
    video_duration = video.length
    end_past_video_end = False
    if ts_end > video_duration:
        warn_msg = "End time for segment ({} - {}) of video {} extends past end of video (length {} sec)"
        LOGGER.warning(warn_msg.format(ts_start, ts_end, ytid, video_duration))
        duration = video_duration - ts_start
        ts_end = ts_start + duration
        end_past_video_end = True

    if video_mode in ('bestvideo', 'bestvideowithaudio'):
        best_video = video.getbestvideo()
        # If there isn't a video only option, go with best video with audio
        if best_video is None:
            best_video = video.getbest()
    elif video_mode in ('bestvideoaudio', 'bestvideoaudionoaudio'):
        best_video = video.getbest()
    else:
        raise ValueError('Invalid video mode: {}'.format(video_mode))
    best_audio = video.getbestaudio()
    best_video_url = best_video.url
    best_audio_url = best_audio.url

    audio_info = {
        'sample_rate': audio_sample_rate,
        'channels': 2,
        'bitrate': audio_bit_depth,
        'encoding': audio_codec.upper(),
        'duration': duration
    }
    video_info = {
        "r_frame_rate": "{}/1".format(video_frame_rate),
        "avg_frame_rate": "{}/1".format(video_frame_rate),
        'codec_name': video_codec.lower(),
        'duration': duration
    }
    # Download the audio
    audio_input_args = ['-n', '-ss', str(ts_start)]
    audio_output_args = ['-t', str(duration),
                         '-ar', str(audio_sample_rate),
                         '-vn',
                         '-ac', str(audio_info['channels']),
                         '-sample_fmt', 's{}'.format(audio_bit_depth),
                         '-f', audio_format,
                         '-acodec', audio_codec]
    ffmpeg(ffmpeg_path, best_audio_url, audio_filepath,
           input_args=audio_input_args, output_args=audio_output_args,
           num_retries=num_retries, validation_callback=validate_audio,
           validation_args={'audio_info': audio_info,
                            'end_past_video_end': end_past_video_end})

    if video_mode != 'bestvideowithaudio':
        # Download the video
        video_input_args = ['-n', '-ss', str(ts_start)]
        video_output_args = ['-t', str(duration),
                             '-f', video_format,
                             '-r', str(video_frame_rate),
                             '-vcodec', video_codec]
        # Suppress audio stream if we don't want to audio in the video
        if video_mode in ('bestvideo', 'bestvideoaudionoaudio'):
            video_output_args.append('-an')

        ffmpeg(ffmpeg_path, best_video_url, video_filepath,
               input_args=video_input_args, output_args=video_output_args,
               num_retries=num_retries, validation_callback=validate_video,
               validation_args={'ffprobe_path': ffprobe_path,
                                'video_info': video_info,
                                'end_past_video_end': end_past_video_end})
    else:
        # Download the best quality video, in lossless encoding
        if video_codec != 'h264':
            error_msg = 'Not currently supporting merging of best quality video with video for codec: {}'
            raise NotImplementedError(error_msg.format(video_codec))
        video_input_args = ['-n', '-ss', str(ts_start)]
        video_output_args = ['-t', str(duration),
                             '-f', video_format,
                             '-crf', '0',
                             '-preset', 'medium',
                             '-r', str(video_frame_rate),
                             '-an',
                             '-vcodec', video_codec]

        ffmpeg(ffmpeg_path, best_video_url, video_filepath,
               input_args=video_input_args, output_args=video_output_args,
               num_retries=num_retries)

        # Merge the best lossless video with the lossless audio, and compress
        merge_video_filepath = os.path.splitext(video_filepath)[0] \
                               + '_merge.' + video_format
        video_input_args = ['-n']
        video_output_args = ['-f', video_format,
                             '-r', str(video_frame_rate),
                             '-vcodec', video_codec,
                             '-acodec', 'aac',
                             '-ar', str(audio_sample_rate),
                             '-ac', str(audio_info['channels']),
                             '-strict', 'experimental']

        ffmpeg(ffmpeg_path, [video_filepath, audio_filepath], merge_video_filepath,
               input_args=video_input_args, output_args=video_output_args,
               num_retries=num_retries, validation_callback=validate_video,
               validation_args={'ffprobe_path': ffprobe_path,
                                'video_info': video_info,
                                'end_past_video_end': end_past_video_end})

        # Remove the original video file and replace with the merged version
        if os.path.exists(merge_video_filepath):
            os.remove(video_filepath)
            shutil.move(merge_video_filepath, video_filepath)
        else:
            error_msg = 'Cannot find merged video for {} ({} - {}) at {}'
            LOGGER.error(error_msg.format(ytid, ts_start, ts_end, merge_video_filepath))

    LOGGER.info('Downloaded video {} ({} - {})'.format(ytid, ts_start, ts_end))
    print("end")
    return video_filepath, audio_filepath

# Test
# download_yt_video(ytid, ts_start, ts_end, './data/', ffmpeg_path, ffprobe_path)

for i in range(0, num_dl_list):
    # Select a YouTube video from the training set
    print('{}/{}'.format(i, num_dl_list))
    ytid, ts_start, label = dl_list[i]
    ts_end = int(ts_start) + 10
    ts_start, ts_end = float(ts_start), float(ts_end)
    try:
        download_yt_video(ytid, ts_start, ts_end, '/data/dlt/clap/raw_data/VGGSound/', ffmpeg_path, ffprobe_path)
    except:
        pass
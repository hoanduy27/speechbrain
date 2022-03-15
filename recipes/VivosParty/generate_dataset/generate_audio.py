from pydub import AudioSegment
import os
import random

# class DataConfig:
#     SPEECH_PATH = '/home/duy/datasets/s3/downloads/vivos/test/waves'

def create_segment(audio, duration_s):
    audio_duration = len(audio)
    segment_duration = int(duration_s * 1000)
    if audio_duration <= segment_duration:
        loop_n = segment_duration // audio_duration
        remainer = segment_duration - loop_n * audio_duration
        segment = audio * loop_n + audio[0:remainer]

    else:
        start = random.randint(0, audio_duration - segment_duration - 1)
        segment = audio[start : start + segment_duration]
    return segment
    

def create_single_file_test(speaker_id, speaker_audios, background_audios, output_dir):
    """
    input:
    yêu cầu: trả về (1) một audio có nhiều segment, mỗi segment có thể là non-speech (music, noise); hoặc là speech của một người nói (2) file segments chứa mô tả  của audio đó
    ví dụ 
    segment_001  0.00  0.23 NON_SPEECH
    segment_002  0.23  5.58 SPEECH
    segment_003  5.58  10.90 NON_SPEECH
    segment_004  10.90  16.63 SPEECH
    segment_005  16.63  20.45 NON_SPEECH

    :param 1: speaker_id
    :param 2: speaker_audios: audios of this speaker

    :param 3: background_audios
    :param 4: output_dir - to save .wav and .segment file

    random number segments [50,70], duration [5s, 15s] 
    """
    MIN_N_SEGMENTS = 50
    MAX_N_SEGMENTS = 70
    MIN_DURATION_S = 5
    MAX_DURATION_S = 15

    # Segment config
    is_speech = True
    start = 0
    end = 0
    segment_infos = []

    # Generate segment
    new_audio = AudioSegment.empty()
    n_segments = random.randint(MIN_N_SEGMENTS, MAX_N_SEGMENTS)
    for i in range(n_segments):
        name = f'segment_{i}'
        # Randomly choose speech or background depend on 
        audio = random.choice(speaker_audios if is_speech else background_audios)
        duration_s = random.uniform(MIN_DURATION_S, MAX_DURATION_S)

        segment = create_segment(audio, duration_s)
        end = start + segment.duration_seconds
        label = 'SPEECH' if is_speech else 'NON_SPEECH'
        
        segment_infos.append('%s\t%.2f\t%.2f\t%s'%(name, start, end, label))
        new_audio += segment

        # Prepare for next loop
        is_speech = not is_speech
        start = end

    wave_dir = os.path.join(output_dir, 'waves')
    segment_dir = os.path.join(output_dir, 'segments')
    if not os.path.exists(wave_dir):
        os.makedirs(wave_dir)
    if not os.path.exists(segment_dir):
        os.makedirs(segment_dir)

    new_audio.export(
        os.path.join(wave_dir, f'{speaker_id}_gen.wav'), 
        format='wav'
    )

    with open(os.path.join(segment_dir, f'{speaker_id}_gen.segment'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(segment_infos))

    return segment_infos


def create_all_test(speech_dir, background_dir, output_dir):
    """
    :param 1: speech_dir: directory of speaker's audios
    :param 2: backgroud_dir

    :param 3: output_dir
    """
    background_audios = []
    for bgfile in os.listdir(background_dir):
        background_audios.append(AudioSegment.from_file(
            os.path.join(background_dir, bgfile)
        ))

    for speaker_id in os.listdir(speech_dir):
        speaker_audios = []
        for wavfile in os.listdir(os.path.join(speech_dir, speaker_id)):
            speaker_audios.append(AudioSegment.from_file(
                os.path.join(speech_dir, speaker_id, wavfile)
            ))

        create_single_file_test(speaker_id, speaker_audios, background_audios, output_dir)

if __name__ == '__main__':
    ROOT = '/home/duy/datasets/duy-vivos'
    create_all_test(
        speech_dir=os.path.join(ROOT, 's3/downloads/vivos/test/waves'),
        background_dir=os.path.join(ROOT, 'vivos-with-bg/background/youtube_converted_wavs'),
        output_dir=os.path.join(ROOT, 'vivos-with-bg/test_1')
    )
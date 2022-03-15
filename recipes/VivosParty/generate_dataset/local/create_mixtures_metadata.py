"""
This file contains functions to create json metadata used to create
mixtures which simulate a multi-party conversation in a noisy scenario.

Author
------
Samuele Cornell, 2020
"""


import numpy as np
from pathlib import Path
import json
import os
from tqdm import tqdm
import torchaudio


def _read_metadata(file_path, configs):
    meta = torchaudio.info(file_path)
    if meta.num_channels > 1:
        channel = np.random.randint(0, meta.num_channels - 1)
    else:
        channel = 0
    # print(file_path, meta.sample_rate)
    assert (
        
        meta.sample_rate == configs["samplerate"]

    ), "file samplerate is different from the one specified"

    return meta, channel

def draw(prob):
    return np.random.uniform() < prob

def create_metadata(
    output_filename,
    n_sessions,
    configs,
    utterances_dict,
    words_dict,
    rir_list,
    impulsive_noises_list=None,
    musics_list = None,
    background_noises_list=None,
):

    dataset_metadata = {}
    rir_prob = configs['rir_prob']
    background_prob = configs['background_prob']

    #Logic:
    # - If not background, must rir
    # - If background, rir can be add or not


    for n_sess in tqdm(range(n_sessions)):
        has_background = draw(background_prob)
        if has_background:
            session_rir_prob = rir_prob
        else:
            session_rir_prob = 1.0

        # we sample randomly n_speakers ids
        c_speakers = np.random.choice(
            list(utterances_dict.keys()), configs["n_speakers"], replace=False
        )
        # we select all utterances from selected speakers
        c_utts = [utterances_dict[spk_id] for spk_id in c_speakers]

        activity = {}
        for spk in c_speakers:
            activity[spk] = []

        tot_length = 0
        min_spk_lvl = np.inf
        for i in range(len(c_speakers)):
            c_spk = c_speakers[i]
            spk_utts = c_utts[i]
            np.random.shuffle(spk_utts)  # random shuffle
            # we use same technique as in EEND repo for intervals distribution
            intervals = np.random.exponential(
                configs["interval_factor_speech"], len(spk_utts)
            )
            cursor = 0
            for j, wait in enumerate(intervals):
                meta, channel = _read_metadata(spk_utts[j], configs)
                get_rir = draw(rir_prob)
                c_rir = np.random.choice(rir_list, 1)[0] if get_rir else None
                # check if the rir is monaural
                meta_rir, rir_channel = _read_metadata(c_rir, configs) if get_rir else (None, None)

                length = meta.num_frames / meta.sample_rate
                id_utt = Path(spk_utts[j]).stem
                cursor += wait
                if cursor + length > configs["max_length"]:
                    break

                lvl = np.clip(
                    np.random.normal(
                        configs["speech_lvl_mean"], configs["speech_lvl_var"]
                    ),
                    configs["speech_lvl_min"],
                    configs["speech_lvl_max"],
                )
                min_spk_lvl = min(lvl, min_spk_lvl)
                # we save to metadata only relative paths
                activity[c_spk].append(
                    {
                        "start": cursor,
                        "stop": cursor + length,
                        "words": words_dict[id_utt],
                        "rir": str(
                            Path(c_rir).relative_to(configs["rirs_noises_root"])
                        ) if c_rir is not None else None,
                        "utt_id": id_utt,
                        "file": str(
                            Path(spk_utts[j]).relative_to(
                                configs["vivos_root"]
                            )
                        ),
                        "lvl": lvl,
                        "channel": channel,
                        "rir_channel": rir_channel,
                    }
                )
                tot_length = max(cursor + length, tot_length)
                cursor = cursor + length

        # we add also impulsive noises as it were a speaker
        if impulsive_noises_list:
            activity["noises"] = []
            # sampling intervals for impulsive noises.
            intervals = np.random.exponential(
                configs["interval_factor_noises"], len(impulsive_noises_list)
            )
            cursor = 0
            for j, wait in enumerate(intervals):
                # we sample with replacement an impulsive noise.
                c_noise = np.random.choice(impulsive_noises_list, 1)[0]
                meta, channel = _read_metadata(c_noise, configs)
                c_rir = np.random.choice(rir_list, 1)[0]
                # we reverberate it.
                meta_rir, rir_channel = _read_metadata(c_rir, configs)
                length = meta.num_frames / meta.sample_rate
                cursor += wait
                if cursor + length > configs["max_length"]:
                    break
                lvl = np.clip(
                    np.random.normal(
                        configs["imp_lvl_mean"], configs["imp_lvl_var"]
                    ),
                    configs["imp_lvl_min"],
                    min(min_spk_lvl + configs["imp_lvl_rel_max"], 0),
                )

                activity["noises"].append(
                    {
                        "start": cursor,
                        "stop": cursor + length,
                        "rir": str(
                            Path(c_rir).relative_to(configs["rirs_noises_root"])
                        ),
                        "file": str(
                            Path(c_noise)
                            # .relative_to(configs["rirs_noises_root"])
                        ),
                        "lvl": lvl,
                        "channel": channel,
                        "rir_channel": rir_channel,
                    }
                )
                tot_length = max(tot_length, cursor + length)
                cursor += length

        if musics_list:
            np.random.shuffle(musics_list)
            activity["musics"] = []
            # sampling intervals for impulsive noises.
            intervals = np.random.exponential(
                configs["interval_factor_noises"], len(musics_list)
            )
            cursor = 0
            for j, wait in enumerate(intervals):
                # we sample with replacement an impulsive noise.
                c_musics = np.random.choice(musics_list, 1)[0]
                meta, channel = _read_metadata(c_noise, configs)
                c_rir = np.random.choice(rir_list, 1)[0]
                # we reverberate it.
                meta_rir, rir_channel = _read_metadata(c_rir, configs)
                # length = meta.num_frames / meta.sample_rate
                length = np.random.uniform(
                    configs["music_min_duration"],
                    configs["music_max_duration"],
                    1
                )[0]
                # print(length)
                cursor += wait
                if cursor + length > configs["max_length"]:
                    break
                lvl = np.clip(
                    np.random.normal(
                        configs["music_lvl_mean"], configs["music_lvl_var"]
                    ),
                    configs["music_lvl_min"],
                    min(min_spk_lvl + configs["music_lvl_rel_max"], 0),
                )

                activity["musics"].append(
                    {
                        "start": cursor,
                        "stop": cursor + length,
                        "rir": str(
                            Path(c_rir).relative_to(configs["rirs_noises_root"])
                        ),
                        "file": str(
                            Path(c_musics)
                            # .relative_to(configs["rirs_noises_root"])
                        ),
                        "lvl": lvl,
                        "channel": channel,
                        "rir_channel": rir_channel,
                    }
                )
                tot_length = max(tot_length, cursor + length)
                cursor += length
        if background_noises_list:
            # we add also background noise.
            lvl = np.random.randint(
                configs["background_lvl_min"],
                min(min_spk_lvl + configs["background_lvl_rel_max"], 0),
            )
            # we scale the level but do not reverberate.
            background = np.random.choice(background_noises_list, 1)[0]
            meta, channel = _read_metadata(background, configs)
            assert (
                meta.num_frames >= configs["max_length"] * configs["samplerate"]
            ), "background noise files should be >= max_length in duration"
            offset = 0
            if meta.num_frames > configs["max_length"] * configs["samplerate"]:
                offset = np.random.randint(
                    0,
                    meta.num_frames
                    - int(configs["max_length"] * configs["samplerate"]),
                )

            activity["background"] = {
                "start": 0,
                "stop": tot_length,
                "file": str(
                    Path(background).relative_to(configs["backgrounds_root"])
                ),
                "lvl": lvl,
                "orig_start": offset,
                "orig_stop": offset + int(tot_length * configs["samplerate"]),
                "channel": channel,
            }
        else:
            # we use as background gaussian noise
            lvl = np.random.randint(
                configs["background_lvl_min"],
                min(min_spk_lvl + configs["background_lvl_rel_max"], 0),
            )
            activity["background"] = {
                "start": 0,
                "stop": tot_length,
                "file": None,
                "lvl": lvl,
                "orig_start": None,
                "orig_stop": None,
                "channel": None,
            }

        dataset_metadata["session_{}".format(n_sess)] = activity

    with open(
        os.path.join(configs["out_folder"], output_filename + ".json"), "w"
    ) as f:
        json.dump(dataset_metadata, f, indent=4)

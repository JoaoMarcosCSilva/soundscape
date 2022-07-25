from functools import partial
import pandas as pd
import sys, os
from tqdm import tqdm
from glob import glob

import constants


def class_is_frog(species):
    return species in constants.FROG_CLASSES


def class_is_bird(species):
    return species in constants.BIRD_CLASSES


def process_txt_file(txts_path, wav_files, period, filename):
    """
    Takes a path to a .txt labels file and returns a pandas dataframe.
    """

    # Reads the .txt file
    df = pd.read_csv(os.path.join(txts_path, period, filename), sep="\t")

    # Drops the columns that are not needed
    df = df.drop(columns=["Selection", "View", "Channel"])

    df["file"] = filename.replace(".txt", ".wav")
    df["period"] = period

    # Creates series to indicate whether a species is part of the pre-selected 12 classes (6 birds, 6 frogs)
    isBird = df["species"].apply(class_is_bird)
    isFrog = df["species"].apply(class_is_frog)

    # Creates a column to indicate whether a species is part of the pre-selected classes
    df["selected"] = isBird | isFrog

    # Indicates whether a species is a bird or a frog
    df["group"] = pd.Series(dtype=str)
    df.loc[isBird, "group"] = "bird"
    df.loc[isFrog, "group"] = "frog"

    # Checks that the audio file exists
    df["exists"] = df["file"].apply(lambda x: x in wav_files)

    return df


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: python process_txts.py <txts-dir> <wavs-dir>")
        sys.exit(1)

    txts_path = sys.argv[1]
    wavs_path = sys.argv[2]

    # Creates a list of all the audio files
    wav_files = set(
        os.listdir(os.path.join(wavs_path, "supervised/day"))
        + os.listdir(os.path.join(wavs_path, "supervised/night"))
        + os.listdir(os.path.join(wavs_path, "unsupervised/day"))
        + os.listdir(os.path.join(wavs_path, "unsupervised/night"))
    )

    periods = os.listdir(txts_path)

    dfs = []

    for period in periods:
        txt_files = os.listdir(os.path.join(txts_path, period))
        dfs.extend(
            map(
                partial(process_txt_file, txts_path, wav_files, period), tqdm(txt_files)
            )
        )

    df = pd.concat(dfs)

    df.to_csv("labels.csv", index=False)

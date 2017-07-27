#!/usr/bin/env python
import os
import json
from abc import ABC, abstractmethod

import pandas as pd

from gulpio.utils import (get_single_video_path,
                          resize_images,
                          burst_video_into_frames,
                          clear_temp_dir,
                         )


class AbstractDatasetAdapter(ABC):
    """ Base class adapter for gulping (video) datasets.

    Inherit from this class and implement the `iter_data` method. This method
    should iterate over your entire dataset and for each element return a
    dictionary with the following fields:

        id     : a unique(?) ID for the element.
        frames : a list of frames (PIL images, numpy arrays..)
        meta   : a dictionary with arbitrary metadata (labels, start_time...)

    For examples, see the custom adapters below.

    """

    @abstractmethod
    def iter_data():
        return NotImplementedError

    def __getitem__(self, i):
        return NotImplementedError


class Custom20BNJsonAdapter(object):

    def __init__(self, json_file, folder,
                 frame_size=-1, shm_dir_path='/dev/shm'):
        self.json_file = json_file
        self.data = self.read_json(json_file)
        self.folder = folder
        self.frame_size = frame_size
        self.shm_dir_path = shm_dir_path

    def read_json(self, json_file):
        with open(json_file, 'r') as f:
            content = json.load(f)
        return content

    def get_meta(self):
        return [{'id': entry['id'], 'label': entry['template']}
                for entry in self.data]

    def iter_data(self):
        for meta in self.get_meta():
            video_folder = os.path.join(self.folder, str(meta['id']))
            video_path = get_single_video_path(video_folder)
            tmp_path, frame_paths = burst_video_into_frames(video_path,
                                                            self.shm_dir_path)
            frames = resize_images(frame_paths, self.frame_size)
            clear_temp_dir(tmp_path)
            result = {'meta': meta,
                      'frames': frames,
                      'id': meta['id']}
            yield result


class Input_from_csv(object):

    def __init__(self, csv_file, num_labels=None):
        self.num_labels = num_labels
        self.data = self.read_input_from_csv(csv_file)
        self.labels2idx = self.create_labels_dict()

    def read_input_from_csv(self, csv_file):
        print(" > Reading data list (csv)")
        return pd.read_csv(csv_file)

    def create_labels_dict(self):
        labels = sorted(pd.unique(self.data['label']))
        if self.num_labels:
            assert len(labels) == self.num_labels
        labels2idx = {}
        for i, label in enumerate(labels):
            labels2idx[label] = i
        return labels2idx

    def get_data(self):
        output = []
        for idx, row in self.data.iterrows():
            entry_dict = {}
            entry_dict['id'] = row.youtube_id
            entry_dict['label'] = row.label
            entry_dict['start_time'] = row.time_start
            entry_dict['end_time'] = row.time_end
            output.append(entry_dict)
        return output, self.labels2idx



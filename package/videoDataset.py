import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from itertools import cycle
from typing import List, Union, Tuple, Any
import cv2
from PIL import Image

import torch
import torchvision
from torchvision import transforms, io
from torchvision.transforms import functional as F

import random
np.random.seed(2022)
random.seed(2022)
torch.manual_seed(2022)



# Helper Functions
def readVideo(pth_video):
    videoCapture = cv2.VideoCapture(pth_video)

    fps = videoCapture.get(cv2.CAP_PROP_FPS)
    size = (int(videoCapture.get(cv2.CAP_PROP_FRAME_WIDTH)), 
            int(videoCapture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fNUMS = videoCapture.get(cv2.CAP_PROP_FRAME_COUNT)

    frames = list()
    while (videoCapture.isOpened()):
        ret, frame = videoCapture.read()

        if ret: frames.append( cv2.cvtColor(frame,cv2.COLOR_BGR2RGB) )
        else: break
    
    videoCapture.release()
    # print("video size:", size)

    return fps, size, fNUMS, frames



# Classes
class VideoDataset(torch.utils.data.Dataset):
    def __init__(self, file_list, transform):
        self.transform = transform
        with open(file_list, "rb") as f:
            self.file_list = pickle.load(f)
        

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, idx):
        pth_video = self.file_list.iloc[idx].file_pth
        label = self.file_list.iloc[idx].cls

        fps, size, fNUMS, frames = readVideo(pth_video)


        seed = np.random.randint(1e9)
        frames_tr = []
        for frame in frames:
            random.seed(seed)
            np.random.seed(seed)
            frame = self.transform(frame)
            frames_tr.append(frame)

        # print(fNUMS)
        if fNUMS > 80: del frames_tr[80:]
        elif fNUMS < 80: # repeat to length 80
            frames_tr = [next( cycle(frames_tr) )for i in range(80)]
        # print(len(frames_tr))
        # print("-"*8)

        if len(frames_tr) > 0: frames_tr = torch.stack(frames_tr)

        return frames_tr, label



# class FrameDataset(torch.utils.data.Dataset):
#     pass



# class VideoFrameDataset(torch.utils.data.Dataset):
#     r"""
#     A highly efficient and adaptable dataset class for videos.
#     Instead of loading every frame of a video,
#     loads x RGB frames of a video (sparse temporal sampling) and evenly
#     chooses those frames from start to end of the video, returning
#     a list of x PIL images or ``FRAMES x CHANNELS x HEIGHT x WIDTH``
#     tensors where FRAMES=x if the ``ImglistToTensor()``
#     transform is used.
#     More specifically, the frame range [START_FRAME, END_FRAME] is divided into NUM_SEGMENTS
#     segments and FRAMES_PER_SEGMENT consecutive frames are taken from each segment.
#     Note:
#         A demonstration of using this class can be seen
#         in ``demo.py``
#         https://github.com/RaivoKoot/Video-Dataset-Loading-Pytorch
#     Note:
#         This dataset broadly corresponds to the frame sampling technique
#         introduced in ``Temporal Segment Networks`` at ECCV2016
#         https://arxiv.org/abs/1608.00859.
#     Note:
#         This class relies on receiving video data in a structure where
#         inside a ``ROOT_DATA`` folder, each video lies in its own folder,
#         where each video folder contains the frames of the video as
#         individual files with a naming convention such as
#         img_001.jpg ... img_059.jpg.
#         For enumeration and annotations, this class expects to receive
#         the path to a .txt file where each video sample has a row with four
#         (or more in the case of multi-label, see README on Github)
#         space separated values:
#         ``VIDEO_FOLDER_PATH     START_FRAME      END_FRAME      LABEL_INDEX``.
#         ``VIDEO_FOLDER_PATH`` is expected to be the path of a video folder
#         excluding the ``ROOT_DATA`` prefix. For example, ``ROOT_DATA`` might
#         be ``home\data\datasetxyz\videos\``, inside of which a ``VIDEO_FOLDER_PATH``
#         might be ``jumping\0052\`` or ``sample1\`` or ``00053\``.
#     Args:
#         root_path: The root path in which video folders lie.
#                    this is ROOT_DATA from the description above.
#         annotationfile_path: The .txt annotation file containing
#                              one row per video sample as described above.
#         num_segments: The number of segments the video should
#                       be divided into to sample frames from.
#         frames_per_segment: The number of frames that should
#                             be loaded per segment. For each segment's
#                             frame-range, a random start index or the
#                             center is chosen, from which frames_per_segment
#                             consecutive frames are loaded.
#         imagefile_template: The image filename template that video frame files
#                             have inside of their video folders as described above.
#         transform: Transform pipeline that receives a list of PIL images/frames.
#         test_mode: If True, frames are taken from the center of each
#                    segment, instead of a random location in each segment.
#     """
#     def __init__(self,
#                  root_path: str,
#                  annotationfile_path: str,
#                  num_segments: int = 3,
#                  frames_per_segment: int = 1,
#                  imagefile_template: str='img_{:05d}.jpg',
#                  transform = None,
#                  test_mode: bool = False):
#         super(VideoFrameDataset, self).__init__()

#         self.root_path = root_path
#         self.annotationfile_path = annotationfile_path
#         self.num_segments = num_segments
#         self.frames_per_segment = frames_per_segment
#         self.imagefile_template = imagefile_template
#         self.transform = transform
#         self.test_mode = test_mode

#         self._parse_annotationfile()
#         self._sanity_check_samples()

#     def _load_image(self, directory: str, idx: int) -> Image.Image:
#         return Image.open(os.path.join(directory, self.imagefile_template.format(idx))).convert('RGB')

#     def _parse_annotationfile(self):
#         self.video_list = [VideoRecord(x.strip().split(), self.root_path) for x in open(self.annotationfile_path)]

#     def _sanity_check_samples(self):
#         for record in self.video_list:
#             if record.num_frames <= 0 or record.start_frame == record.end_frame:
#                 print(f"\nDataset Warning: video {record.path} seems to have zero RGB frames on disk!\n")

#             elif record.num_frames < (self.num_segments * self.frames_per_segment):
#                 print(f"\nDataset Warning: video {record.path} has {record.num_frames} frames "
#                       f"but the dataloader is set up to load "
#                       f"(num_segments={self.num_segments})*(frames_per_segment={self.frames_per_segment})"
#                       f"={self.num_segments * self.frames_per_segment} frames. Dataloader will throw an "
#                       f"error when trying to load this video.\n")

#     def _get_start_indices(self, record: VideoRecord) -> 'np.ndarray[int]':
#         """
#         For each segment, choose a start index from where frames
#         are to be loaded from.
#         Args:
#             record: VideoRecord denoting a video sample.
#         Returns:
#             List of indices of where the frames of each
#             segment are to be loaded from.
#         """
#         # choose start indices that are perfectly evenly spread across the video frames.
#         if self.test_mode:
#             distance_between_indices = (record.num_frames - self.frames_per_segment + 1) / float(self.num_segments)

#             start_indices = np.array([int(distance_between_indices / 2.0 + distance_between_indices * x)
#                                       for x in range(self.num_segments)])
#         # randomly sample start indices that are approximately evenly spread across the video frames.
#         else:
#             max_valid_start_index = (record.num_frames - self.frames_per_segment + 1) // self.num_segments

#             start_indices = np.multiply(list(range(self.num_segments)), max_valid_start_index) + \
#                       np.random.randint(max_valid_start_index, size=self.num_segments)

#         return start_indices

#     def __getitem__(self, idx: int) -> Union[
#         Tuple[List[Image.Image], Union[int, List[int]]],
#         Tuple['torch.Tensor[num_frames, channels, height, width]', Union[int, List[int]]],
#         Tuple[Any, Union[int, List[int]]],
#         ]:
#         """
#         For video with id idx, loads self.NUM_SEGMENTS * self.FRAMES_PER_SEGMENT
#         frames from evenly chosen locations across the video.
#         Args:
#             idx: Video sample index.
#         Returns:
#             A tuple of (video, label). Label is either a single
#             integer or a list of integers in the case of multiple labels.
#             Video is either 1) a list of PIL images if no transform is used
#             2) a batch of shape (NUM_IMAGES x CHANNELS x HEIGHT x WIDTH) in the range [0,1]
#             if the transform "ImglistToTensor" is used
#             3) or anything else if a custom transform is used.
#         """
#         record: VideoRecord = self.video_list[idx]

#         frame_start_indices: 'np.ndarray[int]' = self._get_start_indices(record)

#         return self._get(record, frame_start_indices)

#     def _get(self, record: VideoRecord, frame_start_indices: 'np.ndarray[int]') -> Union[
#         Tuple[List[Image.Image], Union[int, List[int]]],
#         Tuple['torch.Tensor[num_frames, channels, height, width]', Union[int, List[int]]],
#         Tuple[Any, Union[int, List[int]]],
#         ]:
#         """
#         Loads the frames of a video at the corresponding
#         indices.
#         Args:
#             record: VideoRecord denoting a video sample.
#             frame_start_indices: Indices from which to load consecutive frames from.
#         Returns:
#             A tuple of (video, label). Label is either a single
#             integer or a list of integers in the case of multiple labels.
#             Video is either 1) a list of PIL images if no transform is used
#             2) a batch of shape (NUM_IMAGES x CHANNELS x HEIGHT x WIDTH) in the range [0,1]
#             if the transform "ImglistToTensor" is used
#             3) or anything else if a custom transform is used.
#         """

#         frame_start_indices = frame_start_indices + record.start_frame
#         images = list()

#         # from each start_index, load self.frames_per_segment
#         # consecutive frames
#         for start_index in frame_start_indices:
#             frame_index = int(start_index)

#             # load self.frames_per_segment consecutive frames
#             for _ in range(self.frames_per_segment):
#                 image = self._load_image(record.path, frame_index)
#                 images.append(image)

#                 if frame_index < record.end_frame:
#                     frame_index += 1

#         if self.transform is not None:
#             images = self.transform(images)

#         return images, record.label

#     def __len__(self):
#         return len(self.video_list)



# class ImglistToTensor(torch.nn.Module):
#     """
#     Converts a list of PIL images in the range [0,255] to a torch.FloatTensor
#     of shape (NUM_IMAGES x CHANNELS x HEIGHT x WIDTH) in the range [0,1].
#     Can be used as first transform for ``VideoFrameDataset``.
#     """
#     @staticmethod
#     def forward(img_list: List[Image.Image]) -> 'torch.Tensor[NUM_IMAGES, CHANNELS, HEIGHT, WIDTH]':
#         """
#         Converts each PIL image in a list to
#         a torch Tensor and stacks them into
#         a single tensor.
#         Args:
#             img_list: list of PIL images.
#         Returns:
#             tensor of size ``NUM_IMAGES x CHANNELS x HEIGHT x WIDTH``
#         """
#         return torch.stack([transforms.functional.to_tensor(pic) for pic in img_list])
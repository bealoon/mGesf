import pickle
import time
import warnings
from collections import OrderedDict

import numpy as np
import os


def resolve_sample_feature(ls_dict, lb, f_dict, s_slice, sensor):
    for feature_name, f_array in f_dict.items():
        if feature_name not in ls_dict[lb][sensor].keys():
            ls_dict[lb][sensor][feature_name] = \
                np.expand_dims(f_array[s_slice], axis=0)  # expand dim: sample
        else:
            ls_dict[lb][sensor][feature_name] = \
                np.concatenate([ls_dict[lb][sensor][feature_name],
                                np.expand_dims(f_array[s_slice], axis=0)])


def resolve_points_per_sample(period, input_interval):
    return (1 / period) * input_interval * 1000


def idp_preprocess(path, input_interval, classes, num_repeat, period=33):
    """
    In this implementation, the tail of the data that does not make up an input_interval is automatically ignored.
    However, it is important to note that if the actual last sample does not expand a full input_interval, it also will
    be discarded. To make up for this, during data collection, always end recording with a brief PAUSE after the last
    gesture; at the same time, ensure the pause is not longer than an input_interval (this is not as hard as it sounds).
    :param path:
    :param input_interval:
    :param classes:
    :param num_repeat:
    :param period: frame period in milliseconds
    """
    mgesf_data_list = (pickle.load(open(os.path.join(path, p), 'rb')) for p in os.listdir(path))

    # self.buffer = {'mmw': {'timestamps': [], 'range_doppler': [], 'range_azi': [], 'detected_points': []}}

    labeled_sample_dict = OrderedDict([(label, {'mmw': {}}) for label in classes])
    sample_frame_durations = []

    sample_num_expected = len(classes) * num_repeat  # expected number of samples per data block
    points_per_sample = resolve_points_per_sample(period, input_interval)

    mmw_features = ['range_doppler', 'range_azi']

    for d, p in zip(mgesf_data_list, os.listdir(path)):
        sample_ts_list = []

        mmw_list = d['mmw']
        label_list = [[x for i in range(num_repeat)] for x in classes]
        label_list = [item for sublist in label_list for item in sublist]  # flattten

        ts_array = np.array(mmw_list['timestamps'])

        # checks data shapes
        # invalid_rdpl_list = [(i, a) for i, a in enumerate(mmw_list['range_doppler']) if a.shape != (8, 16)]
        # invalid_rzm_list = [(i, a) for i, a in enumerate(mmw_list['range_azi']) if a.shape != (8, 64)]

        mmwf_dict = dict([(f, np.array(mmw_list[f])) for f in mmw_features])

        # slice the ts list by the interval duration
        ts_array = ts_array - ts_array[0]  # ground by the first frame's timestamp
        ts_index_last = 0
        for sample_index in range(1, sample_num_expected + 1):
            for ts_index, ts in enumerate(ts_array):
                if ts - input_interval * sample_index >= 0.:  # end of a sample
                    if ts_index - ts_index_last != int(points_per_sample):
                        print('Too many samples: ' + str(ts_index - ts_index_last))
                        print('Using Slice: ' + str(
                            slice(ts_index_last, ts_index_last + int(points_per_sample))) + ' instead of ' + str(
                            slice(ts_index_last, ts_index)))
                    sample_slice = slice(ts_index_last, ts_index if ts_index - ts_index_last == int(
                        points_per_sample) else ts_index_last + int(points_per_sample))
                    sample_ts = ts_array[sample_slice]
                    lb = label_list[sample_index - 1]
                    # lb = classes[(sample_index - 1) % len(classes)]  # sample_index decrement for class index offset
                    sample_frame_durations.append(max(sample_ts) - min(sample_ts))
                    sample_ts_list.append(sample_ts)

                    # append the features and labels
                    resolve_sample_feature(labeled_sample_dict, lb, mmwf_dict, sample_slice, 'mmw')  # mmw features

                    label_list.append(lb)  # labels
                    ts_index_last = ts_index
                    break  # break to the next sample
        if len(sample_ts_list) != sample_num_expected:
            raise Exception(
                'Sample number mismatch, got ' + str(len(sample_ts_list)) + ', expected: ' + str(sample_num_expected) +
                '\n for ' + p)

    return labeled_sample_dict

    # retrieve the timestamp making sure the data is synced
    # print('Processing ' + str(i + 1) + ' of ' + str(len(radar_points)) + ', interval = ' + str(interval_index))

    #     if is_plot:
    #         figure_intervaled_path = os.path.join(figure_path, str(interval_index))
    #
    #         if not os.path.isdir(figure_intervaled_path):
    #             os.mkdir(figure_intervaled_path)
    #
    #         closest_video_timestamp = min(video_frame_timestamps,
    #                                       key=lambda x: abs(x - this_timestamp))
    #         closest_video_path = os.path.join(videoData_path, str(closest_video_timestamp) + '.jpg')
    #         closest_video_img = Image.open(closest_video_path)
    #
    #         # plot the radar scatter
    #         # ax1 = plt.subplot(2, 2, 1, projection='3d')
    #         # ax1.set_xlim((-0.3, 0.3))
    #         # ax1.set_ylim((-0.3, 0.3))
    #         # ax1.set_zlim((-0.3, 0.3))
    #         # ax1.set_xlabel('X', fontsize=10)
    #         # ax1.set_ylabel('Y', fontsize=10)
    #         # ax1.set_zlabel('Z', fontsize=10)
    #         # ax1.set_title('Detected Points', fontsize=10)
    #         # # plot the detected points
    #         # ax1.scatter(this_points[:, 0], this_points[:, 1], this_points[:, 2], c=this_points[:, 3], marker='o')
    #
    #     # assert np.all(produce_voxel(this_points) == this_voxel)
    #
    #     # apply augmentation to hand cluster #############################
    #     if len(this_points) > 0:
    #         if 'trans' in augmentation:
    #             for p in np.nditer(this_points[:, :3], op_flags=['readwrite']):
    #                 p[...] = p + random.choice(seeds)
    #         if 'rot' in augmentation:
    #             this_points[:, :3] = rotateX(this_points[:, :3], 720 * random.choice(seeds))
    #             this_points[:, :3] = rotateY(this_points[:, :3], 720 * random.choice(seeds))
    #             this_points[:, :3] = rotateZ(this_points[:, :3], 720 * random.choice(seeds))
    #         if 'scale' in augmentation:
    #             s = 1 + random.choice(seeds)
    #             this_points[:, :3] = scale(this_points[:, :3], x=s, y=s, z=s)
    #
    #     if is_plot:
    #         # ax3 = plt.subplot(2, 2, 3, projection='3d')
    #         ax3 = plt.subplot(111, projection='3d')
    #
    #         ax3.set_xlim((-0.3, 0.3))
    #         ax3.set_ylim((-0.3, 0.3))
    #         ax3.set_zlim((-0.3, 0.3))
    #         ax3.set_xlabel('X', fontsize=10)
    #         ax3.set_ylabel('Y', fontsize=10)
    #         ax3.set_zlabel('Z', fontsize=10)
    #         ax3.set_title('Detected Points', fontsize=20)
    #
    #         ax3.scatter(this_points[:, 0], this_points[:, 1], this_points[:, 2], ',', c=this_points[:, 3], s=28,
    #                     marker='o')
    #
    #     # create 3D feature space #############################
    #     produced_voxel = produce_voxel(this_points, isClipping='clp' in augmentation)
    #
    #     this_voxel_list.append(produced_voxel)
    #     # Plot the hand cluster #########################################
    #     # Combine the three images
    #     if is_plot:
    #         # plot the voxel
    #         # ax4 = plt.subplot(2, 2, 4, projection='3d')
    #         # ax4.set_aspect('equal')
    #         # ax4.set_xlabel('X', fontsize=10)
    #         # ax4.set_ylabel('Y', fontsize=10)
    #         # ax4.set_zlabel('Z', fontsize=10)
    #         # ax4.set_title('voxel', fontsize=10)
    #         # ax4.voxels(produced_voxel[0])
    #
    #         plt.savefig(os.path.join(util_path, str(this_timestamp) + '.jpg'))
    #         radar_3dscatter_img = Image.open(os.path.join(util_path, str(this_timestamp) + '.jpg'))
    #
    #         images = [closest_video_img, radar_3dscatter_img]  # add image here to arrange them horizontally
    #         widths, heights = zip(*(i.size for i in images))
    #         total_width = sum(widths)
    #         max_height = max(heights)
    #         new_im = Image.new('RGB', (total_width, max_height))
    #         x_offset = 0
    #         for im in images:
    #             new_im.paste(im, (x_offset, 0))
    #             x_offset += im.size[0]
    #
    #         if False:
    #             timestamp_difference = abs(float(this_timestamp) - float(closest_video_timestamp))
    #             draw = ImageDraw.Draw(new_im)
    #
    #             # draw the timestamp difference on the image
    #             (x, y) = (20, 10)
    #             message = "Timestamp Difference, abs(rt-vt): " + str(timestamp_difference)
    #             draw.text((x, y), message, fill=white_color, font=fnt)
    #             # draw the timestamp
    #             (x, y) = (20, 30)
    #             message = "Timestamp: " + str(this_timestamp)
    #             draw.text((x, y), message, fill=white_color, font=fnt)
    #
    #             # draw the number of points
    #             (x, y) = (20, 60)
    #             message = "Number of detected points: " + str(this_points.shape[0])
    #             draw.text((x, y), message, fill=white_color, font=fnt)
    #
    #         # save the combined image
    #         new_im.save(
    #             os.path.join(figure_intervaled_path,
    #                          str(this_timestamp) + '_' + str(this_timestamp.as_integer_ratio()[0]) +
    #                          '_' + str(this_timestamp.as_integer_ratio()[1]) + '_' + str(interval_index) + '.jpg'))
    #         plt.close('all')
    #
    #     # calculate the interval ############################
    #     if (this_timestamp - starting_timestamp) >= input_interval or i == len(radar_voxel) - 1:
    #         # increment the timestamp and interval index
    #         starting_timestamp = starting_timestamp + input_interval
    #         this_label = math.floor(interval_index / 2)
    #         interval_index = interval_index + 1
    #
    #         # decide the label
    #         # if interval_index % inter_arg == 1 or interval_index % inter_arg == 2:
    #         #     this_label = 0  # for label DEL
    #         # elif interval_index % inter_arg == 3 or interval_index % inter_arg == 4:
    #         #     this_label = 1  # for label D
    #         # elif interval_index % inter_arg == 5 or interval_index % inter_arg == 6:
    #         #     this_label = 2  # for label E
    #         # elif interval_index % inter_arg == 7 or interval_index % inter_arg == 8:
    #         #     this_label = 3  # for label H
    #         # elif interval_index % inter_arg == 9 or interval_index % inter_arg == 0:
    #         #     this_label = 4  # for label L
    #         # elif interval_index % inter_arg == 11 or interval_index % inter_arg == 12:
    #         #     this_label = 5  # for label O
    #         # elif interval_index % inter_arg == 13 or interval_index % inter_arg == 14:
    #         #     this_label = 6  # for label R
    #         # elif interval_index % inter_arg == 15 or interval_index % inter_arg == 16:
    #         #     this_label = 7  # for label W
    #         # elif interval_index % inter_arg == 17 or interval_index % inter_arg == 18:
    #         #     this_label = 8  # for label SPC
    #         # elif interval_index % inter_arg == 19 or interval_index % inter_arg == 0:
    #         #     this_label = 9  # for label EXC
    #         label_array.append(this_label)
    #
    #         print('Interval' + str(interval_index) + ': Label-' + str(this_label) + ' # of Samples- ' + str(
    #             len(this_voxel_list)))
    #         print('')
    #
    #         # add padding, pre-padded
    #         if len(this_voxel_list) < sample_per_interval:
    #             while len(this_voxel_list) < sample_per_interval:
    #                 this_voxel_list.insert(0, np.expand_dims(np.zeros(volume_shape), axis=0))
    #         elif len(this_voxel_list) > sample_per_interval:  # we take only the most recent timesteps
    #             this_voxel_list = this_voxel_list[-sample_per_interval:]
    #         this_voxel_list = np.asarray(this_voxel_list)
    #         interval_voxel_list.append(this_voxel_list)
    #         this_voxel_list = []
    #
    #     # end of end of interval processing
    #
    # # start of post processing ##########################################################################
    # sps = min(samples_per_session, key=lambda x: abs(x - len(label_array)))
    #
    # label_array = np.asarray(label_array)[:sps]
    # interval_volume_array = np.asarray(interval_voxel_list)[:sps]
    #
    # assert len(interval_volume_array) == len(label_array) and len(label_array) in samples_per_session
    #
    # interval_mean = np.mean(interval_volume_array)
    # print('Interval mean is ' + str(interval_mean))
    # assert interval_mean < 1.0
    #
    # # validate the output shapes
    #
    # dataset_path = 'F:/alldataset/idp_dataset'
    # label_dict_path = 'F:/alldataset/idp_label_dict.p'
    #
    # print('Saving chunks to ' + dataset_path + '...')
    #
    # # load label dict
    # if os.path.exists(label_dict_path):
    #     label_dict = pickle.load(open(label_dict_path, 'rb'))
    # else:  # create anew if does not exist
    #     label_dict = {}
    #
    # # put the label into the dict and save data
    # for i, l_and_d in enumerate(zip(label_array, interval_volume_array)):
    #     print('Saving chunk #' + str(i))
    #
    #     label_dict[identity_string + '_' + str(i) + aug_string] = l_and_d[0]
    #     np.save(os.path.join(dataset_path, identity_string + '_' + str(i) + aug_string), l_and_d[1])
    #
    # # save label dict to disk
    # pickle.dump(label_dict, open(label_dict_path, 'wb'))
    #
    # print('Current number of labels is ' + str(len(label_dict)))
    # print('Done saving to ' + dataset_path)

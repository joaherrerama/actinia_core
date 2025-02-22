# -*- coding: utf-8 -*-
#######
# actinia-core - an open source REST API for scalable, distributed, high
# performance processing of geographical data that uses GRASS GIS for
# computational tasks. For details, see https://actinia.mundialis.de/
#
# Copyright (c) 2021 mundialis GmbH & Co. KG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#######

"""
Interim Result class
"""

import os
import subprocess
import shutil
from .messages_logger import MessageLogger
from actinia_core.core.common.config import global_config, DEFAULT_CONFIG_PATH
from actinia_core.core.common.exceptions import RsyncError

__license__ = "GPLv3"
__author__ = "Anika Weinmann"
__copyright__ = "Copyright 2021, mundialis GmbH & Co. KG"
__email__ = "info@mundialis.de"


def get_directory_size(directory):
    """Returns the directory size in bytes.
    Args:
        directory (string): The path to a directory

    Returns:
        total: the size of the directory in bytes

    """
    total = 0
    try:
        for entry in os.scandir(directory):
            if entry.is_file():
                total += os.path.getsize(entry)
            elif entry.is_dir():
                total += get_directory_size(entry.path)
    except NotADirectoryError:
        return os.path.getsize(directory)
    except PermissionError:
        return 0
    return total


class InterimResult(object):
    """This class manages the interim results
    """

    def __init__(self, user_id, resource_id, iteration):
        """Init method for InterimResult class
        Args:
            user_id (str): The unique user name/id
            resource_id (str): The id of the resource
            old_pc_step (int): The number of the successfully finished steps of
                               the process chain in the previous iteration
        """
        global_config.read(DEFAULT_CONFIG_PATH)
        self.logger = MessageLogger()
        self.user_resource_interim_storage_path = os.path.join(
            global_config.GRASS_RESOURCE_DIR, user_id, "interim")
        self.saving_interim_results = global_config.SAVE_INTERIM_RESULTS
        self.resource_id = resource_id
        self.iteration = iteration if iteration is not None else 1
        self.old_pc_step = None

    def set_old_pc_step(self, old_pc_step):
        """Set method for the number of the successfully finished steps of
        the process chain in the previous iteration

        Args:
            old_pc_step (int): The number of the successfully finished steps of
                               the process chain in the previous iteration
        """
        self.old_pc_step = old_pc_step

    def _get_step_folder_name(self, pc_step):
        """Return the name of the interim folder for the process chain step
        Args:
            pc_step (int): The number of the step in the process chain where to
                           continue

        Returns:
            (str): The name of the interim folder for the process chain step

        """
        return f"step{pc_step}"

    def _get_step_tmpdir_name(self, pc_step):
        """Return the name of the interim folder for the process chain step
        Args:
            pc_step (int): The number of the step in the process chain where to
                           continue

        Returns:
            (str): The name of the interim folder for the process chain step

        """
        return f"tmpdir{pc_step}"

    def check_interim_result_mapset(self, pc_step, iteration):
        """Helper method to check if the interim result mapset is saved

        Args:
            pc_step (int): The number of the step in the process chain where to
                           continue

        Returns:
            interim_mapset (str): The path to the interim result mapset which
                                  has to be copied to the temporary mapsets
                                  (with _create_temporary_grass_environment)
            interim_file_path (str): The path to the interim result temporary
                                     file path which has to be copied to the
                                     temporary path
                                     (with _create_temporary_grass_environment)
        """
        iterim_error = False
        if self.saving_interim_results is False:
            iterim_error = True
            msg = "Saving iterim results is not configured"
        if os.path.isdir(os.path.join(
                self.user_resource_interim_storage_path, self.resource_id)):
            interim_folder = os.listdir(os.path.join(
                self.user_resource_interim_storage_path, self.resource_id))
        else:
            iterim_error = True
            msg = "No interim results saved in previous iteration"

        if (iterim_error is False
                and (self._get_step_folder_name(pc_step) not in interim_folder
                     or self._get_step_tmpdir_name(pc_step) not in interim_folder)):
            iterim_error = True
            msg = f"No interim results saved in previous iteration for step {pc_step}"
        if iterim_error is True:
            self.logger.error(msg)
            return None

        interim_mapset = os.path.join(
            self.user_resource_interim_storage_path, self.resource_id,
            self._get_step_folder_name(pc_step))
        interim_file_path = os.path.join(
            self.user_resource_interim_storage_path, self.resource_id,
            self._get_step_tmpdir_name(pc_step))

        return interim_mapset, interim_file_path

    def _compare_sha512sums_of_folders(self, folder1, folder2):
        """Compares the sha512sums of two folders.
        Args:
            folder1 (str): Path to one folder
            folder2 (str): Path to another folder

        Returns:
            (bool): A boolean "True" if the sha512sums of the folder are the same
                    otherwise "False" (also if one of the folder does not exist)
        """
        for folder in [folder1, folder2]:
            if not os.path.isdir(folder):
                self.logger.error(
                    f"<{folder}> is no folder")
                return False

        # get sha512sum of the folder
        cur_working_dir = os.getcwd()
        sha512sum_cmd = "find . -type f -exec sha512sum {} \; | " + \
                        "sort -k 2 | sha512sum"
        sha512sums = list()
        for folder in [folder1, folder2]:
            os.chdir(folder)
            p_sha512sum_prev = os.popen(sha512sum_cmd)
            sha512sums.append(p_sha512sum_prev.read().strip())
        os.chdir(cur_working_dir)
        del cur_working_dir

        # compare sha512sums
        if sha512sums[0] == sha512sums[1]:
            return True
        else:
            return False

    def rsync_mapsets(self, src, dest):
        """Using rsync to update the mapset folder.
        Args:
            src (str): Path of the source mapset
            dest (str): Path to destination mapset (where to rsync the src mapset)

        Returns:
            (str): "success" if the rsync has worked otherwise "error"
        """
        rsync_cmd = [
            "rsync",
            "--recursive",
            "--compress",
            "--partial",
            "--progress",
            "--times",
            "--exclude", ".gislock",
            "--delete",
            src + os.sep,
            dest]
        p_rsync = subprocess.Popen(
            rsync_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, rsync_err = p_rsync.communicate()

        if rsync_err.decode('utf-8') != '':
            return 'error'

        # remove .gislock
        gislock_file = os.path.join(dest, '.gislock')
        if os.path.isfile(gislock_file):
            os.remove(gislock_file)
        return 'success'

    def _saving_folder(self, src, dest, old_dest, progress_step):
        """Saves the src folder to the dest folder by copying the directory or
        rsyncing it
        """
        # check if directory has changed
        same_dir = self._compare_sha512sums_of_folders(
            old_dest, src)
        if same_dir is True:
            self.logger.info(
                "Sha512sums of maspsets are equal; renaming interim result")
            os.rename(old_dest, dest)
            return

        # get folder sizes in bytes
        size_prev_step = get_directory_size(old_dest)
        size_curr_step = get_directory_size(src)

        # rsync or copy folder
        if size_curr_step > size_prev_step * 0.9:
            self.logger.info("Copy old interim result")
            shutil.copytree(old_dest, dest)
        self.logger.info(
            "Rsync mapset %s to interim result" % src)
        rsync_status = self.rsync_mapsets(src, dest)
        if rsync_status == 'success':
            shutil.rmtree(old_dest)
        else:
            raise RsyncError(
                "Error while rsyncing of step %d" % progress_step)

    def save_interim_results(self, progress_step, temp_mapset_path, temp_file_path):
        """Saves the temporary mapset to the
        `user_resource_interim_storage_path` by copying the directory or
        rsyncing it
        """

        if self.old_pc_step is not None:
            progress_step += self.old_pc_step
        self.logger.info(
            "Saving interim results of step %d" % progress_step)
        dest_base_path = self.user_resource_interim_storage_path
        dest_mapset = os.path.join(
            dest_base_path, self.resource_id,
            self._get_step_folder_name(progress_step))
        dest_tmpdir = os.path.join(
            dest_base_path, self.resource_id,
            self._get_step_tmpdir_name(progress_step))

        if progress_step == 1:
            # copy temp mapset for first step
            shutil.copytree(temp_mapset_path, dest_mapset)
            shutil.copytree(temp_file_path, dest_tmpdir)
            self.logger.info(
                "Maspset %s and temp_file_path %s are copied"
                % (temp_mapset_path, temp_file_path))
        else:
            old_dest_mapset = os.path.join(
                dest_base_path, self.resource_id,
                self._get_step_folder_name(progress_step - 1))
            old_dest_tmpdir = os.path.join(
                dest_base_path, self.resource_id,
                self._get_step_tmpdir_name(progress_step - 1))

            # saving mapset
            self._saving_folder(
                temp_mapset_path, dest_mapset, old_dest_mapset, progress_step)
            # saving temporary file path
            self._saving_folder(
                temp_file_path, dest_tmpdir, old_dest_tmpdir, progress_step)

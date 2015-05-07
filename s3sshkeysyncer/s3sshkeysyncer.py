# -*- coding: utf-8 -*-

"""
This module does all the 'heavy lifting' to keep local system
users in sync with an s3 bucket with public ssh keys
"""

import subprocess
import pwd
import glob
import shutil
import tempfile


class UserSyncer(object):
    """ Self-contained class that does everything """

    def __init__(self, s3_path, ignored_users, logger):
        """ set configuration """
        self._s3_path = s3_path
        self._ignored_users = ignored_users
        self._local_path = tempfile.mkdtemp()
        self._logger = logger

    def create_user(self, username, ssh_key_contents):
        """ create a local user """
        self._logger.warn("Creating user: " +
            username + " with key: '" +
            ssh_key_contents + "'"
        )

    def disable_user(self, username):
        """ disable a local user """
        self._logger.warn("Deleting user: " + username)

    def download_keys(self, s3_path, local_path):
        """ download public keys from s3 to a tmp directory """
        self._logger.debug("syncing to: " + local_path)
        sync_exit_code = subprocess.call(
            [
                "aws",
                "--region",
                "ap-southeast-2",
                "s3",
                "sync",
                s3_path,
                local_path
            ]
        )

        if sync_exit_code != 0:
            self._logger.warn("s3 sync returned non-zero")
            return False
        else:
            return True

    # pylint: disable=R0201
    def list_remote_users(self, local_path):
        """ list the users downloaded from s3 """
        key_files = glob.glob(local_path + "/*.pub")
        users = []
        for key in key_files:
            ssh_key = key.replace(local_path + "/", "")
            split = ssh_key.split(".")
            split.pop()
            users.append(".".join(split))

        return users


    # pylint: disable=R0201
    def list_local_users(self, ignored_users):
        """ list and filter local users """
        currently_active_users = []
        for user in pwd.getpwall():
            if user.pw_uid >= 1000 and user.pw_name not in ignored_users:
                currently_active_users.append(user.pw_name)

        return currently_active_users

    # pylint: disable=R0201
    def get_users_to_be_created(self, existing_users, from_s3):
        """ get a diff between existing and should_exist """
        return list(
                set(from_s3) - set(existing_users)
        )

    def get_users_to_be_deleted(self, existing_users, from_s3):
        """ get a diff between should_exist and existing """
        return list(
            set(existing_users) - set(from_s3)
        )

    def get_ssh_pubkey_contents(self, username):
        """ get the ssh public key contents from the temp path """
        open(self._local_path + "/" + username + ".pub", "r").read().strip()

    def run(self):
        """ actually run the thing """
        self.download_keys(self._s3_path, self._local_path)

        currently_active_users = self.list_local_users(self._ignored_users)
        should_be_active_users = self.list_remote_users(self._local_path)

        create_user_list = self.get_users_to_be_created(
            currently_active_users, should_be_active_users
        )

        delete_user_list = self.get_users_to_be_deleted(
            currently_active_users, should_be_active_users
        )

        self._logger.info("currently active: " + str(currently_active_users))
        self._logger.info("should be active: " + str(should_be_active_users))
        self._logger.info("should be created: " + str(create_user_list))
        self._logger.info("should be deleted: " + str(delete_user_list))

        for username in create_user_list:
            ssh_key_contents = self.get_ssh_pubkey_contents(username)
            if not self.create_user(username, ssh_key_contents):
                self._logger.warn("failed to create user '" + username + "'")

        for username in delete_user_list:
            if not self.disable_user(username):
                self._logger.warn("failed to create user '" + username + "'")

        shutil.rmtree(self._local_path)

        return True

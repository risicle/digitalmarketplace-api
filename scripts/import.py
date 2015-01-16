#!/usr/bin/env python
import sys
import os
import requests


def list_files(directory):
    for root, subdirs, files in os.walk(directory):
        print("ROOT: {}".format(root))
        for file in files:
            yield os.path.abspath(os.path.join(root, file))

        for subdir in subdirs:
            for subfile in list_files(subdir):
                yield subfile


if __name__ == "__main__":
    _, base_url, access_token, listing_dir = sys.argv

    endpoint = "{}/services".format(base_url)
    print("Base URL: {}".format(base_url))
    print("Access token: {}".format(access_token))
    print("Listing dir: {}".format(listing_dir))

    for file_path in list_files(listing_dir):
        with open(file_path) as f:
            response = requests.post(
                endpoint,
                data='{"services":%s}' % f.read(),
                headers={
                    "content-type": "application/json",
                    "authorization": "Bearer {}".format(access_token),
                })
            print(response)

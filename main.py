import argparse
import os
import subprocess
import sys
from termcolor import colored
import requests
import shutil

RECONSTRUCTED_GIT = "reconstructed_git"

GIT_COMMAND_TO_USE = 'git log'

GIT_DIR = ".git"

GIT_OBJECTS_DIR = "/objects/"

hashes = []
failed_files = []
url = "http://localhost:8000"


def initialize_local_repo():
    print_header("Initializing new local git repo")
    process = subprocess.run("git init", capture_output=True, shell=True)
    errors = process.stderr.decode("utf-8")

    if errors:
        print_error("initializing local git repository failed")
        print_git_error(errors)

    print_success("New git repo initialized at: ", RECONSTRUCTED_GIT)


def print_header(text, args=''):
    count = len(text)
    line = count * 2 * "_"
    print("\n"+line)
    print('\t' + text, args)
    print(line)


def print_info(text, args=''):
    print(colored("\tINFO: " + text + args, 'blue'))


def print_success(text, args=''):
    print(colored("\tSUCCESS: " + text + args, 'green'))


def print_error(text, args=''):
    print(colored("\tERROR: " + text + args, 'red'))


def print_git_error(text, args=''):
    print(colored("\tGIT ERROR: " + text + args, 'magenta'))


def create_dir():
    print_header("Creating new empty directory for reconstructed git repo")
    dirname = RECONSTRUCTED_GIT
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    os.mkdir("%s" % dirname)
    os.chdir(dirname)
    print_success("New directory created at: ", RECONSTRUCTED_GIT)


def set_git_head():
    global url
    print_header("Reconstructing the the HEAD reference")
    print_info("Checking if URL contains a %s directory" % GIT_DIR)
    # Check if URL has .git directory
    if not url.endswith("/"):
        url = url + "/"
    if url.find("%s" % GIT_DIR) < 0:
        url = url + GIT_DIR + "/"
    head_response = requests.get(url + "HEAD")
    if head_response.ok:
        print_success("Remote %s directory found and readable" % GIT_DIR)
        head = head_response.text
        head_ref = head.split(" ")[1]
        head_ref = head_ref.strip()
        print_info("Head at: ", head_ref)
        try:
            if os.path.exists("%s/HEAD" % GIT_DIR):
                os.remove("%s/HEAD" % GIT_DIR)
            head_file = open("%s/HEAD" % GIT_DIR, "x+")
            head_file.write(head)
            print_success("Wrote head ref path to %s/HEAD" % GIT_DIR)

        except Exception as e:
            print_error("failed to write %s/HEAD" % GIT_DIR)
            print(e)
            exit(1)
        print_info("Downloading main current hash reference")
        head_object_response = requests.get(url + head_ref)
        if head_object_response.ok:
            head_object_hash = head_object_response.text.strip()
            print_info("Head object hash: ", head_object_hash)

            try:
                if os.path.exists(GIT_DIR + "/" + head_ref):
                    os.remove(GIT_DIR + "/" + head_ref)
                head_file = open(GIT_DIR + "/" + head_ref, "x+")
                head_file.write(head_object_hash)
                print_success("Wrote head object hash to " + GIT_DIR + "/" + head_ref)
                print_info("Retrieving actual head object")
                retrieve_object(head_object_hash)

            except Exception as e:
                print_error("failed to write %s/HEAD" % GIT_DIR)
                print(e)
                exit(1)

        else:
            print_error("Failed to retrieve head object hash ", head_object_response.status_code)
    else:
        print_error("No %s directory found" % GIT_DIR, head_response.status_code)


def retrieve_objects():
    print_info("Using errors from '" + GIT_COMMAND_TO_USE + "' to know which objects are missing")
    proc = subprocess.run(GIT_COMMAND_TO_USE, capture_output=True, shell=True)
    if proc.stderr:
        print_info("Git contains errors. Checking if errors contain object hashes")
        errors = proc.stderr.decode("utf-8")
        print_git_error(errors)
        error_lines = errors.split("\n")
        for line in error_lines:
            if line.find("error: Could not read") == 0:
                error_words = error_lines[0].split(" ")
                next_hash = error_words[4]
                hashes.append(next_hash)
                print_info("Collected hash: " + next_hash)

        if len(hashes) > 0:
            print_info("Retrieving objects next")
            for objectHash in hashes:
                print_info("Trying to retrieve object ", objectHash)
                retrieve_object(objectHash)

        return True
    else:
        return False


def retrieve_object(object_hash):
    global failedFiles
    object_dir = object_hash[:2]
    object_file_name = object_hash[2:]
    print_info(
        "Downloading object from: " + url + "objects/" + object_dir + "/" + object_file_name)
    if not os.path.exists(GIT_DIR + GIT_OBJECTS_DIR + object_dir):
        os.mkdir(GIT_DIR + GIT_OBJECTS_DIR + object_dir)
    object_file_response = requests.get(url + GIT_OBJECTS_DIR + object_dir + "/" + object_file_name)
    if object_file_response.ok:
        object_file = bytearray(object_file_response.content)
        try:
            object_file_handle = open(GIT_DIR + GIT_OBJECTS_DIR + object_dir + "/" + object_file_name, "xb")
            object_file_handle.write(object_file)
            print_success(
                "Wrote object " + object_hash + " to " + GIT_DIR + GIT_OBJECTS_DIR + object_dir + "/" + object_file_name)
        except IOError as e:
            print_error("Failed to write object to git objects: ", e)
            failedFiles.append(object_hash)
    else:
        print_error("Could not download object: ", object_file_response.text)


def main(argv):
    global url

    print('\n'
          ' _____ _ _    ______                         _                   _   \n'
          '|  __ (_) |   | ___ \                       | |                 | |  \n'
          '| |  \/_| |_  | |_/ /___  ___ ___  _ __  ___| |_ _ __ _   _  ___| |_ \n'
          '| | __| | __| |    // _ \/ __/ _ \| \'_ \/ __| __| \'__| | | |/ __| __|\n'
          '| |_\ \ | |_  | |\ \  __/ (_| (_) | | | \__ \ |_| |  | |_| | (__| |_ \n'
          ' \____/_|\__| \_| \_\___|\___\___/|_| |_|___/\__|_|   \__,_|\___|\__|\n'
          ' @blaudoom                                                                \n'
          ' ')

    print_info("Working with the directory:\n\t"+os.path.abspath(os.curdir))

    try:
        parser = argparse.ArgumentParser(
            prog='python3 main.py ',
            description='Reconstructs git repo from remote .git directory HEAD',
            epilog='Examples:$ python3 main.py -u http://example.com '
                   '$python3 main.py --url http://example.com:8080'
                   '$python3 main.py -u http://example.com/.git/')

        parser.add_argument('-u', metavar='--url', type=str, dest=url, required=True,
                            help='Remote url for git repo')
        args = parser.parse_args()
        print_info("Using url: ", url)

    except Exception as e:
        parser.print_help()
        print(e)
        sys.exit(1)

    create_dir()

    initialize_local_repo()

    set_git_head()

    print_header("Reconstructing rest of the objects")
    while retrieve_objects():
        print_info("Checking git output for missing objects")

    print_success("!!!No more missing objects, repository is most likely completely rebuilt. "
                  "All possible branches and re-bases "
                  "are not necessarily included", 'green')


if __name__ == '__main__':
    main(sys.argv[1:])

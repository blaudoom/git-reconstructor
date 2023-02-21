# git_reconstructor

Tool to reconstruct current HEAD of a remote git repository with the .git directory exposed.

Useful in CTFs mostly.

- Tested on :
  - `git version 2.37.1 (Apple Git-137.1)`

## Git .git directory structure
- .git
  - HEAD
  - config
  - description
  - hooks
  - index
  - info
  - objects
  - refs
  

- The ones we are interested in are HEAD, refs and objects
  - HEAD tells us which branch we are on. f.e. '/refs/heads/main', which is also an actual file
  - refs/head/main tells us the hash-name of the git object which is the position of the current working tree.
  f.e `3cfa5a09551d82eada38415307da569e980a64a0to`
  - These object files can be found in the objects directory under a directory named after the first two characters
  or first byte of their name. f.e. Object `3cfa5a09551d82eada38415307da569e980a64a0` is located in 
`.git/objects/3c/fa5a09551d82eada38415307da569e980a64a0`
  - These objects contain blobs of data which also contain references to other blobs previously created in the tree's history.
  - Trying to use a git repository without proper references to all the blobs will result in an error, which tells you which blobs are missing.
- The script works by :
  - initializing an empty git repository
  - retrieving the HEAD first
  - then the object referenced by the file stated in HEAD
  - Saving these files in their proper location in the .git directory
  - Then executing a git command like `git log` which most likely results in errors
  - If these errors are of the format `error: Could not read 3cfa5a09551d82eada38415307da569e980a64a0`
    - The hashes are parsed from the errors
  - These hashes are used to download new objects from the remote .git directory 
  - When the files are downloaded, the script executes the command again and parses new errors until there are none.

## Example run

```
% python3 main.py -u http://localhost:8000

 _____ _ _    ______                         _                   _   
|  __ (_) |   | ___ \                       | |                 | |  
| |  \/_| |_  | |_/ /___  ___ ___  _ __  ___| |_ _ __ _   _  ___| |_ 
| | __| | __| |    // _ \/ __/ _ \| '_ \/ __| __| '__| | | |/ __| __|
| |_\ \ | |_  | |\ \  __/ (_| (_) | | | \__ \ |_| |  | |_| | (__| |_ 
 \____/_|\__| \_| \_\___|\___\___/|_| |_|___/\__|_|   \__,_|\___|\__|
 @blaudoom                                                                
 
        INFO: Working with the directory:
        /Users/blaudoom/reconstructor
        INFO: Using url: http://localhost:8000

______________________________________________________________________________________________________________
        Creating new empty directory for reconstructed git repo 
______________________________________________________________________________________________________________
        SUCCESS: New directory created at: reconstructed_git

______________________________________________________________
        Initializing new local git repo 
______________________________________________________________
        SUCCESS: New git repo initialized at: reconstructed_git

__________________________________________________________________________
        Reconstructing the the HEAD reference 
__________________________________________________________________________
        INFO: Checking if URL contains a .git directory
        SUCCESS: Remote .git directory found and readable
        INFO: Head at: refs/heads/main
        SUCCESS: Wrote head ref path to .git/HEAD
        INFO: Downloading main current hash reference
        INFO: Head object hash: 3721c9549f8933a3da73dc60b68275cd1c94c305
        SUCCESS: Wrote head object hash to .git/refs/heads/main
        INFO: Retrieving actual head object
        INFO: Downloading object from: http://localhost:8000/.git/objects/37/21c9549f8933a3da73dc60b68275cd1c94c305
        SUCCESS: Wrote object 3721c9549f8933a3da73dc60b68275cd1c94c305to .git/objects/37/21c9549f8933a3da73dc60b68275cd1c94c305

____________________________________________________________________
        Reconstructing rest of the objects 
____________________________________________________________________
        INFO: Using errors from 'git log' to know which objects are missing
        INFO: Git contains errors. Checking if errors contain object hashes
        GIT ERROR: error: Could not read 3cfa5a09551d82eada38415307da569e980a64a0
fatal: Failed to traverse parents of commit 3721c9549f8933a3da73dc60b68275cd1c94c305

        INFO: Collected hash: 3cfa5a09551d82eada38415307da569e980a64a0
        INFO: Retrieving objects next
        INFO: Trying to retrieve object 3cfa5a09551d82eada38415307da569e980a64a0
        INFO: Downloading object from: http://localhost:8000/.git/objects/3c/fa5a09551d82eada38415307da569e980a64a0

```
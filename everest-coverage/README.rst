======================
EVerest code coverage
======================

This python project currently consists of the following packages

- `everest-coverage`: EVerest module auto generation

Install
-------
To install `everest-coverage`:

    python3 -m pip install .

everest-coverage-remove-unnecessary-files
-----------------------------------------

Script to be able to remove unnecessary files that are used for coverage information.

| When compiling the C++ code, for each class a `.o` object file is created.
| When compiling with coverage flags, the compiler also creates `.gcno` files.
| When running the executable, it will write the coverage information to `.gcda` files.
| `.gcov` files are created when the gcovr is running. This will read the `.gcda` files combined with the `.gcno` files
  and creates the `.gcov` files and depending on the options also xml and html files containing readable coverage
  information.

This script is doing two things:
- It removes all gcda files.
- It searches for dangling / orphaned object files and removes them. It will also remove the dangling `.gcno` files.

Dangling / orphaned object files can exist when switching branches and in the old branch was a file that does not exist
in the new branch. When running gcovr in the new branch, it will fail with a file not found error. After running this
script and re-running the unit tests and gcovr, this should not occur anymore.


Usage:

    everest-coverage-remove-unnecessary-files --source-dirs <source dirs> --build-dir <build-dir>

Required options:
- --source-dirs
  Enter one or more source directories to search for the dangling cpp files. Can be space separated or --source-dirs
  can be added multiple times
- --build-dir
  Build directory. In some subdirectory of this build dir, the object, gcno and gcda files are present.


Example usage:

For only removing the files from libocpp built from the everest repo:
`everest-coverage-remove-unnecessary-files --source-dirs /data/work/pionix/workspace/libocpp --build-dir=/data/work/pionix/workspace/everest-core/build/_deps/libocpp-build`
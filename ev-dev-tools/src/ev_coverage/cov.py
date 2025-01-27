#!/bin/python3

"""
With this script, orphaned object (.o) and gcovr (gcno) files can be removed. This is especially necessary when branches
are switched and there is an orphaned object / gcno file. gcovr will then give an error. When gcno and object files
of the orphaned class are removed, gcovr will run fine.
This script will also remove all gcda files from the given build directory.
"""

import os
import glob
import pathlib
import argparse
from ev_coverage import __version__


def remove_all_gcda_files(build_dir: str):
    print("Removing all gcda files from build directory")

    dir = pathlib.Path(build_dir)
    [os.remove(f) for f in dir.rglob("*.gcda")]


def remove_orphaned_object_files(build_dir: str, source_dirs: list[str]):
    print("Removing orphaned object files and gcno files from build directory")
    # Find all object files (*.o) in the build directory
    object_files = glob.glob(f"{build_dir}/**/*.o", recursive=True)

    for obj_file in object_files:
        # 1. Remove everything in the path until "*.dir/"
        strip_substr = ".dir" + os.sep
        split_len = obj_file.find(strip_substr) + len(strip_substr)
        relative_path_obj = obj_file[split_len:]

        # 2. Remove the source directory part from the path
        for src_dir in source_dirs:
            if relative_path_obj.startswith(src_dir[1:]):
                # Remove the source directory part
                relative_path_obj = relative_path_obj[len(src_dir):].lstrip(os.sep)
                break

        # Get the base name of the object file (remove the path)
        obj_basename = os.path.basename(obj_file)

        # Convert the object file base name to the corresponding cpp file name
        cpp_basename = obj_basename[:-2] if obj_basename.endswith("cpp.o") else obj_basename.replace(".o", ".cpp")

        relative_dir = os.path.split(relative_path_obj)
        relative_path_cpp = relative_dir[0] + os.sep + cpp_basename

        cpp_file_exists = False

        # Loop through each source directory to check for the existence of the corresponding .cpp file
        for src_dir in source_dirs:
            for p in pathlib.Path(src_dir).rglob(relative_path_cpp):
                if os.path.isfile(p):
                    cpp_file_exists = True
                    break

        # If no corresponding .cpp file was found, remove the orphaned .o file
        if not cpp_file_exists:
            print(f"Removing orphaned object file: {obj_file}")
            for p in pathlib.Path(build_dir).rglob(relative_path_cpp + "*"):
                if os.path.isfile(p):
                    print(f"Removing other orphaned file: {p}")
                    os.remove(p)
            # If obj file is not removed in the previous loop, remove it now
            if os.path.isfile(obj_file):
                print(f"Removing object file: {p}")
                os.remove(obj_file)


def remove_unnecessary_files(args):
    remove_all_gcda_files(build_dir=args.build_dir)
    remove_orphaned_object_files(build_dir=args.build_dir, source_dirs=args.source_dirs)


def main():
    parser = argparse.ArgumentParser('Everest coverage command line tools')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    subparsers = parser.add_subparsers(metavar='<command>', help='available commands', required=True)
    parser_file_remover = subparsers.add_parser('remove_files', aliases=['rm'], help='Remove orphaned / unnecessary files')


    parser_file_remover.add_argument('--source-dirs', nargs='+', type=str, action='extend', required=True,
                        help="Source files directories to search in for cpp files. Can be multiple, "
                             "separated by a space.")
    parser_file_remover.add_argument('--build-dir', type=str, required=True, help="Build directory")
    parser_file_remover.set_defaults(action_handler=remove_unnecessary_files)
    args = parser.parse_args()

    args.action_handler(args)


if __name__ == '__main__':
    main()



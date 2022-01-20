#!/usr/bin/env -S python3 -tt
# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: Apache-2.0
# Copyright 2020 - 2021 Pionix GmbH and Contributors to EVerest
#
"""
author: aw@pionix.de
FIXME (aw): Module documentation.
"""

from . import helpers

from datetime import datetime
from pathlib import Path
import jinja2 as j2
import argparse


# Global variables
everest_dir = None

# jinja template environment and global variable
env = j2.Environment(loader=j2.FileSystemLoader(Path(__file__).parent / 'templates'),
                     lstrip_blocks=True, trim_blocks=True, undefined=j2.StrictUndefined,
                     keep_trailing_newline=True)

templates = {
    'interface_base': env.get_template('interface-Base.hpp.j2'),
    'interface_exports': env.get_template('interface-Exports.hpp.j2'),
    'interface_impl.hpp': env.get_template('interface-Impl.hpp.j2'),
    'interface_impl.cpp': env.get_template('interface-Impl.cpp.j2'),
    'module.hpp': env.get_template('module.hpp.j2'),
    'module.cpp': env.get_template('module.cpp.j2'),
    'ld-ev.hpp': env.get_template('ld-ev.hpp.j2'),
    'ld-ev.cpp': env.get_template('ld-ev.cpp.j2'),
    'cmakelists': env.get_template('CMakeLists.txt.j2')
}

validators = {}

# Function declarations


def setup_jinja_env():
    env.globals['timestamp'] = datetime.utcnow()
    # FIXME (aw): which repo to use? everest or everest-framework?
    env.globals['git'] = helpers.gather_git_info(everest_dir)
    env.filters['snake_case'] = helpers.snake_case
    env.filters['create_dummy_result'] = helpers.create_dummy_result


def generate_tmpl_data_for_if(interface, if_def):

    vars = []
    for var, var_info in if_def.get('vars', {}).items():
        type_info = helpers.build_type_info(var, var_info['type'])

        vars.append(type_info)

    cmds = []
    for cmd, cmd_info in if_def.get('cmds', {}).items():
        args = []
        for arg, arg_info in cmd_info.get('arguments', {}).items():
            type_info = helpers.build_type_info(arg, arg_info['type'])

            args.append(type_info)

        result_type_info = None
        if 'result' in cmd_info:
            result_info = cmd_info['result']

            result_type_info = helpers.build_type_info(None, result_info['type'])

        cmds.append({'name': cmd, 'args': args, 'result': result_type_info})

    tmpl_data = {
        'info': {
            'base_class_header': f'generated/{interface}/Implementation.hpp',
            'interface': interface,
            'desc': if_def['description'],
        },
        'vars': vars,
        'cmds': cmds
    }

    return tmpl_data


def generate_tmpl_data_for_module(module, module_def):

    provides = []
    for impl, impl_info in module_def.get('provides', {}).items():
        config = []
        for conf_id, conf_info in impl_info.get('config', {}).items():
            type_info = helpers.build_type_info(conf_id, conf_info['type'])
            config.append(type_info)

        provides.append({
            'id': impl,
            'type': impl_info['interface'],
            'desc': impl_info['description'],
            'config': config,
            'class_name': f'{impl_info["interface"]}Impl',
            'base_class': f'{impl_info["interface"]}ImplBase',
            'base_class_header': f'generated/{impl_info["interface"]}/Implementation.hpp'
        })

    requires = []
    for impl, impl_info in module_def.get('requires', {}).items():
        is_optional = impl.startswith('optional:')
        if is_optional:
            impl = impl[9:]
        requires.append({
            'id': impl,
            'optional': is_optional,
            'type': impl_info['interface'],
            'class_name': f'{impl_info["interface"]}Intf',
            'exports_header': f'generated/{impl_info["interface"]}/Interface.hpp'
        })

    module_config = []
    for conf_id, conf_info in module_def.get('config', {}).items():
        type_info = helpers.build_type_info(conf_id, conf_info['type'])
        module_config.append(type_info)

    tmpl_data = {
        'info': {
            'name': module,
            'class_name': module,  # FIXME (aw): enforce capital case?
            'desc': module_def['description'],
            'module_header': f'{module}.hpp',
            'module_config': module_config,
            'enable_external_mqtt': module_def.get('enable_external_mqtt', False)
        },
        'provides': provides,
        'requires': requires,
    }

    return tmpl_data


def generate_module_files(mod, update_flag):
    mod_files = {'core': [], 'interfaces': []}
    mod_path = everest_dir / f'modules/{mod}/manifest.json'
    mod_def = helpers.load_validated_module_def(mod_path, validators['module'])

    tmpl_data = generate_tmpl_data_for_module(mod, mod_def)

    output_path = mod_path.parent

    cmakelists_blocks = {
        'version': 'v1',
        'format_str': '# ev@{uuid}:{version}',
        'regex_str': '^(?P<indent>\s*)# ev@(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}):(?P<version>.*)$',
        'definitions': {
            'add_general': {
                'id': 'bcc62523-e22b-41d7-ba2f-825b493a3c97',
                'content': '# insert your custom targets and additional config variables here'
            },
            'add_other': {
                'id': 'c55432ab-152c-45a9-9d2e-7281d50c69c3',
                'content': '# insert other things like install cmds etc here'
            }
        }
    }

    if_impl_hpp_blocks = {
        'version': 'v1',
        'format_str': '// ev@{uuid}:{version}',
        'regex_str': '^(?P<indent>\s*)// ev@(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}):(?P<version>.*)$',
        'definitions': {
            'add_headers': {
                'id': '75ac1216-19eb-4182-a85c-820f1fc2c091',
                'content': '// insert your custom include headers here'
            },
            'public_defs': {
                'id': '8ea32d28-373f-4c90-ae5e-b4fcc74e2a61',
                'content': '// insert your public definitions here'
            },
            'protected_defs': {
                'id': 'd2d1847a-7b88-41dd-ad07-92785f06f5c4',
                'content': '// insert your protected definitions here'
            },
            'private_defs': {
                'id': '3370e4dd-95f4-47a9-aaec-ea76f34a66c9',
                'content': '// insert your private definitions here'
            },
            'after_class': {
                'id': '3d7da0ad-02c2-493d-9920-0bbbd56b9876',
                'content': '// insert other definitions here'
            }
        }
    }

    mod_hpp_blocks = {
        'version': 'v1',
        'format_str': '// ev@{uuid}:{version}',
        'regex_str': '^(?P<indent>\s*)// ev@(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}):(?P<version>.*)$',
        'definitions': {
            'add_headers': {
                'id': '4bf81b14-a215-475c-a1d3-0a484ae48918',
                'content': '// insert your custom include headers here'
            },
            'public_defs': {
                'id': '1fce4c5e-0ab8-41bb-90f7-14277703d2ac',
                'content': '// insert your public definitions here'
            },
            'protected_defs': {
                'id': '4714b2ab-a24f-4b95-ab81-36439e1478de',
                'content': '// insert your protected definitions here'
            },
            'private_defs': {
                'id': '211cfdbe-f69a-4cd6-a4ec-f8aaa3d1b6c8',
                'content': '// insert your private definitions here'
            },
            'after_class': {
                'id': '087e516b-124c-48df-94fb-109508c7cda9',
                'content': '// insert other definitions here'
            }
        }
    }

    # provided interface implementations (impl cpp & hpp)
    for impl in tmpl_data['provides']:
        interface = impl['type']
        impl_output_path = output_path / f'{impl["id"]}'
        if_impl_hpp_file = impl_output_path / f'{interface}Impl.hpp'
        if_impl_cpp_file = impl_output_path / f'{interface}Impl.cpp'

        # add module related info to interface implementation
        impl['cpp_file_rel_path'] = str(if_impl_cpp_file.relative_to(output_path))
        impl['class_header'] = str(if_impl_hpp_file.relative_to(output_path))

        # load template data for interface
        if_def, last_mtime = load_interface_defintion(interface)

        if_tmpl_data = generate_tmpl_data_for_if(interface, if_def)

        if_tmpl_data['info'].update({
            'hpp_guard': helpers.snake_case(f'{impl["id"]}_{interface}').upper() + '_IMPL_HPP',
            'config': impl['config'],
            'class_name': interface + 'Impl',
            'class_parent': interface + 'ImplBase',
            'module_header': f'../{mod}.hpp',
            'module_class': mod,
            'interface_implementation_id': impl['id']
        })

        if_tmpl_data['info']['blocks'] = helpers.load_tmpl_blocks(if_impl_hpp_blocks, if_impl_hpp_file, update_flag)

        # FIXME (aw): time stamp should include parent interfaces modification dates
        mod_files['interfaces'].append({
            'abbr': f'{impl["id"]}.hpp',
            'path': if_impl_hpp_file,
            'printable_name': if_impl_hpp_file.relative_to(output_path),
            'content': templates['interface_impl.hpp'].render(if_tmpl_data),
            'last_mtime': last_mtime
        })

        mod_files['interfaces'].append({
            'abbr': f'{impl["id"]}.cpp',
            'path': if_impl_cpp_file,
            'printable_name': if_impl_cpp_file.relative_to(output_path),
            'content': templates['interface_impl.cpp'].render(if_tmpl_data),
            'last_mtime': last_mtime
        })

    cmakelists_file = output_path / 'CMakeLists.txt'
    tmpl_data['info']['blocks'] = helpers.load_tmpl_blocks(cmakelists_blocks, cmakelists_file, update_flag)
    mod_files['core'].append({
        'abbr': 'cmakelists',
        'path': cmakelists_file,
        'content': templates['cmakelists'].render(tmpl_data),
        'last_mtime': mod_path.stat().st_mtime
    })

    # ld-ev.hpp
    ld_ev_hpp_file = output_path / 'ld-ev.hpp'
    tmpl_data['info']['hpp_guard'] = 'LD_EV_HPP'
    tmpl_data['info']['ld_ev_header'] = 'ld-ev.hpp'

    mod_files['core'].append({
        'abbr': 'ld-ev.hpp',
        'path': ld_ev_hpp_file,
        'content': templates['ld-ev.hpp'].render(tmpl_data),
        'last_mtime': mod_path.stat().st_mtime
    })

    # ld-ev.cpp
    tmpl_data['info']['module_header'] = f'{mod}.hpp'
    ld_ev_cpp_file = output_path / 'ld-ev.cpp'
    mod_files['core'].append({
        'abbr': 'ld-ev.cpp',
        'path': ld_ev_cpp_file,
        'content': templates['ld-ev.cpp'].render(tmpl_data),
        'last_mtime': mod_path.stat().st_mtime
    })

    # module.hpp
    tmpl_data['info']['hpp_guard'] = helpers.snake_case(mod).upper() + '_HPP'
    mod_hpp_file = output_path / f'{mod}.hpp'
    tmpl_data['info']['blocks'] = helpers.load_tmpl_blocks(mod_hpp_blocks, mod_hpp_file, update_flag)
    mod_files['core'].append({
        'abbr': 'module.hpp',
        'path': mod_hpp_file,
        'content': templates['module.hpp'].render(tmpl_data),
        'last_mtime': mod_path.stat().st_mtime
    })

    # module.cpp
    mod_cpp_file = output_path / f'{mod}.cpp'
    mod_files['core'].append({
        'abbr': 'module.cpp',
        'path': mod_cpp_file,
        'content': templates['module.cpp'].render(tmpl_data),
        'last_mtime': mod_path.stat().st_mtime
    })

    for file_info in [*mod_files['core'], *mod_files['interfaces']]:
        file_info['printable_name'] = file_info['path'].relative_to(output_path)

    return mod_files


def load_interface_defintion(interface):
    if_path = everest_dir / f'interfaces/{interface}.json'

    if_def = helpers.load_validated_interface_def(if_path, validators['interface'])

    if 'vars' not in if_def:
        if_def['vars'] = {}
    if 'cmds' not in if_def:
        if_def['cmds'] = {}

    last_mtime = if_path.stat().st_mtime

    # load parents
    if_parent = if_def.get('parent', None)
    while (if_parent):
        if_parent_path = everest_dir / f'interfaces/{if_parent}.json'
        try:
            if_parent_def = helpers.load_validated_interface_def(if_parent_path, validators['interface'])
        except Exception as e:
            raise Exception(
                f'Failed to load parent interface definition file {if_parent_path} for interface {interface}') from e

        last_mtime = max(last_mtime, if_parent_path.stat().st_mtime)
        if_def['vars'].update(if_parent_def.get('vars', {}))
        if_def['cmds'].update(if_parent_def.get('cmds', {}))
        if_parent = if_parent_def.get('parent', None)

    return if_def, last_mtime


def generate_interface_headers(interface, all_interfaces_flag):
    if_parts = {'base': None, 'exports': None}

    try:
        if_def, last_mtime = load_interface_defintion(interface)
    except Exception as e:
        if not all_interfaces_flag:
            raise
        else:
            print(f'Ignoring interface {interface} with reason: {e}')
            return

    tmpl_data = generate_tmpl_data_for_if(interface, if_def)

    output_path = everest_dir / f'generated/include/generated/{interface}'
    output_path.mkdir(parents=True, exist_ok=True)

    # generate Base file (providers view)
    tmpl_data['info']['hpp_guard'] = helpers.snake_case(interface).upper() + '_IMPLEMENTATION_HPP'
    tmpl_data['info']['class_name'] = f'{interface}ImplBase'

    base_file = output_path / 'Implementation.hpp'

    if_parts['base'] = {
        'path': base_file,
        'content': templates['interface_base'].render(tmpl_data),
        'last_mtime': last_mtime,
        'printable_name': base_file.relative_to(output_path.parent)
    }

    # generate Exports file (users view)
    tmpl_data['info']['hpp_guard'] = helpers.snake_case(interface).upper() + '_INTERFACE_HPP'
    tmpl_data['info']['class_name'] = f'{interface}Intf'

    exports_file = output_path / 'Interface.hpp'

    if_parts['exports'] = {
        'path': exports_file,
        'content': templates['interface_exports'].render(tmpl_data),
        'last_mtime': last_mtime,
        'printable_name': exports_file.relative_to(output_path.parent)
    }

    return if_parts


def module_create(args):
    create_strategy = 'force-create' if args.force else 'create'

    mod_files = generate_module_files(args.module, False)

    if args.only == 'which':
        helpers.print_available_mod_files(mod_files)
        return
    else:
        try:
            helpers.filter_mod_files(args.only, mod_files)
        except Exception as err:
            print(err)
            return

    for file_info in mod_files['core'] + mod_files['interfaces']:
        if not args.disable_clang_format:
            helpers.clang_format(args.clang_format_file, file_info)

        helpers.write_content_to_file(file_info, create_strategy, args.diff)


def module_update(args):
    primary_update_strategy = 'force-update' if args.force else 'update'
    update_strategy = {'module.cpp': 'update-if-non-existent'}
    for file_name in ['ld-ev.hpp', 'ld-ev.cpp', 'cmakelists', 'module.hpp']:
        update_strategy[file_name] = primary_update_strategy

    # FIXME (aw): refactor out this only handling and rename it properly

    mod_files = generate_module_files(args.module, True)

    if args.only == 'which':
        helpers.print_available_mod_files(mod_files)
        return
    else:
        try:
            helpers.filter_mod_files(args.only, mod_files)
        except Exception as err:
            print(err)
            return

    if not args.disable_clang_format:
        for file_info in mod_files['core'] + mod_files['interfaces']:
            helpers.clang_format(args.clang_format_file, file_info)

    for file_info in mod_files['core']:
        helpers.write_content_to_file(file_info, update_strategy[file_info['abbr']], args.diff)

    for file_info in mod_files['interfaces']:
        if file_info['abbr'].endswith('.hpp'):
            helpers.write_content_to_file(file_info, primary_update_strategy, args.diff)
        else:
            helpers.write_content_to_file(file_info, 'update-if-non-existent', args.diff)


def interface_genhdr(args):
    primary_update_strategy = 'force-update' if args.force else 'update'

    interfaces = args.interfaces
    all_interfaces = False
    if not interfaces:
        interfaces = []
        all_interfaces = True
        if_dir = everest_dir / 'interfaces'
        for if_path in if_dir.iterdir():
            interfaces.append(if_path.stem)

    for interface in interfaces:
        if_parts = generate_interface_headers(interface, all_interfaces)

        if not args.disable_clang_format:
            helpers.clang_format(args.clang_format_file, if_parts['base'])
            helpers.clang_format(args.clang_format_file, if_parts['exports'])

        helpers.write_content_to_file(if_parts['base'], primary_update_strategy, args.diff)
        helpers.write_content_to_file(if_parts['exports'], primary_update_strategy, args.diff)


def helpers_genuuids(args):
    if (args.count <= 0):
        raise Exception(f'Invalid number ("{args.count}") of uuids to generate')
    helpers.generate_some_uuids(args.count)


def main():
    global validators, everest_dir

    parser = argparse.ArgumentParser(description='Everest command line tool')

    common_parser = argparse.ArgumentParser(add_help=False)
    # parser.add_argument("--framework-dir", "-fd", help='directory of everest framework')
    common_parser.add_argument("--everest-dir", "-ed", type=str,
                               help='everest directory containing the interface definitions (default: .)', default=str(Path.cwd()))
    common_parser.add_argument("--framework-dir", "-fd", type=str,
                               help='everest framework directory containing the schema definitions (default: ../everest-framework)', default=str(Path.cwd() / '../everest-framework'))
    common_parser.add_argument("--clang-format-file", type=str, default=str(Path.cwd()),
                               help='Path to the directory, containing the .clang-format file (default: .)')
    common_parser.add_argument("--disable-clang-format", action='store_true', default=False,
                               help="Set this flag to disable clang-format")

    subparsers = parser.add_subparsers(metavar='<command>', help='available commands', required=True)
    parser_mod = subparsers.add_parser('module', aliases=['mod'], help='module related actions')
    parser_if = subparsers.add_parser('interface', aliases=['if'], help='interface related actions')
    parser_hlp = subparsers.add_parser('helpers', aliases=['hlp'], help='helper actions')

    mod_actions = parser_mod.add_subparsers(metavar='<action>', help='available actions', required=True)
    mod_create_parser = mod_actions.add_parser('create', aliases=['c'], parents=[
                                               common_parser], help='create module(s)')
    mod_create_parser.add_argument('module', type=str, help='name of the module, that should be created')
    mod_create_parser.add_argument('-f', '--force', action='store_true', help='force overwriting - use with care!')
    mod_create_parser.add_argument('-d', '--diff', '--dry-run', action='store_true',
                                   help='show resulting diff on create or overwrite')
    mod_create_parser.add_argument('--only', type=str,
                                   help='Comma separated filter list of module files, that should be created.  '
                                   'For a list of available files use "--only which".')
    mod_create_parser.set_defaults(action_handler=module_create)

    mod_update_parser = mod_actions.add_parser('update', aliases=['u'], parents=[
                                               common_parser], help='update module(s)')
    mod_update_parser.add_argument('module', type=str, help='name of the module, that should be updated')
    mod_update_parser.add_argument('-f', '--force', action='store_true', help='force overwriting')
    mod_update_parser.add_argument('-d', '--diff', '--dry-run', action='store_true', help='show resulting diff')
    mod_update_parser.add_argument('--only', type=str,
                                   help='Comma separated filter list of module files, that should be updated.  '
                                   'For a list of available files use "--only which".')
    mod_update_parser.set_defaults(action_handler=module_update)

    if_actions = parser_if.add_subparsers(metavar='<action>', help='available actions', required=True)
    if_genhdr_parser = if_actions.add_parser(
        'generate-headers', aliases=['gh'], parents=[common_parser], help='generate headers')
    if_genhdr_parser.add_argument('-f', '--force', action='store_true', help='force overwriting')
    if_genhdr_parser.add_argument('-d', '--diff', '--dry-run', action='store_true', help='show resulting diff')
    if_genhdr_parser.add_argument('interfaces', nargs='*', help='a list of interfaces, for which header files should '
                                  'be generated - if no interface is given, all will be processed and non-processable '
                                  'will be skipped')
    if_genhdr_parser.set_defaults(action_handler=interface_genhdr)

    hlp_actions = parser_hlp.add_subparsers(metavar='<action>', help='available actions', required=True)
    hlp_genuuid_parser = hlp_actions.add_parser('generate-uuids', help='generete uuids')
    hlp_genuuid_parser.add_argument('count', type=int, default=3)
    hlp_genuuid_parser.set_defaults(action_handler=helpers_genuuids)

    args = parser.parse_args()

    if 'everest_dir' in args:
        everest_dir = Path(args.everest_dir).resolve()
        if not (everest_dir / 'interfaces').exists():
            print('The default (".") xor supplied (via --everest-dir) everest directory\n'
                  'doesn\'t contain an "interface" directory and therefore does not seem to be valid.\n'
                  f'dir: {everest_dir}')
            exit(1)

        setup_jinja_env()

    if 'framework_dir' in args:
        framework_dir = Path(args.framework_dir).resolve()
        if not (framework_dir / 'schemas').exists():
            print('The default ("../everest-framework") xor supplied (via --framework-dir) everest framework directory\n'
                  'doesn\'t contain an "schemas" directory and therefore does not seem to be valid.\n'
                  f'dir: {framework_dir}')
            exit(1)

        validators = helpers.load_validators(framework_dir / 'schemas')

    args.action_handler(args)


if __name__ == '__main__':
    main()

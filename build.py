from argparse import ArgumentParser
import os
import sys
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
from rigproc import __version__ as version


# RIGPROC & RIGCAM


RIGPROC_PATH= os.path.join('src', 'rigproc', 'central', '__main__.py')
RIGPROC_NAME= f'rigproc_{version}'

RIGCAM_PATH= os.path.join('src', 'rigcam', 'main.py')
RIGCAM_NAME= f'rigcam_{version}'

ZIP_NAME= f'rig_{version}.zip'

BUILD_CMD= 'pyinstaller {} -n {} --specpath build --distpath {} --onefile'
PERM_CMD= 'chmod +x {}'


def build_rigproc(dist_path='dist'):
	print('Building rigproc...')

	FBUILD_CMD = BUILD_CMD.format(RIGPROC_PATH, RIGPROC_NAME, dist_path)
	print('Executing: ' + FBUILD_CMD)
	os.system(FBUILD_CMD)

	def dist(file_name):
		return os.path.join(dist_path, file_name)

	print('Updating permissions...')
	os.system(PERM_CMD.format(dist(RIGPROC_NAME)))

	print('Done')


def build_rigcam(dist_path='dist'):
	print('Building rigcam...')

	FBUILD_CMD = BUILD_CMD.format(RIGCAM_PATH, RIGCAM_NAME, dist_path)
	print('Executing: ' + FBUILD_CMD)
	os.system(FBUILD_CMD)

	def dist(file_name):
		return os.path.join(dist_path, file_name)

	print('Updating permissions...')
	os.system(PERM_CMD.format(dist(RIGCAM_NAME)))

	print('Done')


def create_zip(dist_path='dist'):
	print('Creating zip...')

	def dist(file_name):
		return os.path.join(dist_path, file_name)
	
	print('Creating zip...')
	zip_file= ZipFile(dist(ZIP_NAME), 'w')
	zip_file.write(dist(RIGPROC_NAME), RIGPROC_NAME, compress_type=ZIP_DEFLATED)
	zip_file.write(dist(RIGCAM_NAME), RIGCAM_NAME, compress_type=ZIP_DEFLATED)
	zip_file.close()

	print('Done')


# RIGBOOT


def build_rigboot(dist_path='dist'):
	print('Building rigboot...')
	BUILD_CMD= 'pyinstaller {} -n {} --specpath build --distpath {} --onefile'

	RIGBOOT_PATH= os.path.join('src', 'rigboot', 'rigboot.py')
	RIGBOOT_NAME= f'rigboot_{version}'

	FBUILD_CMD = BUILD_CMD.format(RIGBOOT_PATH, RIGBOOT_NAME, dist_path)
	print('Executing: ' + FBUILD_CMD)
	os.system(FBUILD_CMD)

	def dist(file_name):
		return os.path.join(dist_path, file_name)

	print('Updating permissions...')
	PERM_CMD= 'chmod +x {}'
	os.system(PERM_CMD.format(dist(RIGBOOT_NAME)))

	print('Done')


# RIGMAN


def build_rigman(dist_path='dist'):
	print('Building rigman...')
	BUILD_CMD= 'pyinstaller {} -n {} --specpath build --distpath {} --onefile'

	print(f'Current platform: {sys.platform}')

	PATCH_APPLIED= False
	backup_file= None 	# .../__init__.py.bak
	patch_file= None	# .../__init__.py

	"""
	In Windows systems, there is a bug using Pyinstaller (4.2) and confluent-kafka (1.7.0).
	When initialized, confluent-kafka searches for libraries in a path relative to the package location.
	Pyinstaller set the variable "__file__", used by confluent-kafka to obtain the package location, to a temp file.
	Confluent-kafka is therefore not able to find its libraries when running in an executable file.
	To fix this bug, this script injects the library files in the Pyinstaller executable file.
	Then, it substitutes the confleunt-kafka's "__init__.py" file with a patched one, that uses the injected libraries.
	The patch is reverted when all the operations ended.
	"""
	if sys.platform == 'win32':
		print('Adding kafka libraries to build command...')
		import confluent_kafka
		libs_dir = os.path.abspath(os.path.join(os.path.dirname(confluent_kafka.__file__), os.pardir, 'confluent_kafka.libs'))
		for file_name in os.listdir(libs_dir):
			print('    ' + file_name)
		BUILD_CMD += f' --add-data {libs_dir};confluent_kafka.libs'

		print('Applying patch to confluent_kafka')
		pkg_init_file= confluent_kafka.__file__
		pkg_dir= os.path.abspath(str(Path(pkg_init_file).parent))
		backup_file= os.path.join(pkg_dir, '__init__.py.bak')

		print(f'Renaming {pkg_init_file} to {backup_file}')
		os.rename(pkg_init_file, backup_file)
		local_patch= os.path.abspath(str(Path(__file__).parent / 'patch' / 'confluent_kafka' / '__init__.py'))
		patch_file= pkg_init_file

		print(f'Copying {local_patch} to {patch_file}')
		shutil.copyfile(local_patch, patch_file)
		
		PATCH_APPLIED= True

	RIGMAN_PATH= os.path.join('src', 'rigman', 'main.py')
	RIGMAN_NAME= f'rigman_{version}'

	FBUILD_CMD= BUILD_CMD.format(RIGMAN_PATH, RIGMAN_NAME, dist_path)
	print(f'Executing: {FBUILD_CMD}')
	os.system(FBUILD_CMD)

	if sys.platform == 'linux':
		def dist(file_name):
			return os.path.join(dist_path, file_name)

		print('Granting execution permission to dist file...')
		PERM_CMD= 'chmod +x {}'
		os.system(PERM_CMD.format(dist(RIGMAN_NAME)))

	if PATCH_APPLIED:
		print('Reverting patch...')
		print(f'Removing {patch_file}')
		os.remove(patch_file)

		print(f'Renaming {backup_file} to {patch_file}')
		os.rename(backup_file, patch_file)

	print('Done')


# CONSOLE


def build_console(dist_path='dist'):
	print('Building console...')
	BUILD_CMD= 'pyinstaller {} -n {} --specpath build --distpath {} --onefile'

	CONSOLE_PATH= os.path.join('src', 'rigproc', 'console', 'client.py')
	CONSOLE_NAME= f'console_{version}'

	FBUILD_CMD = BUILD_CMD.format(CONSOLE_PATH, CONSOLE_NAME, dist_path)
	print('Executing: ' + FBUILD_CMD)
	os.system(FBUILD_CMD)

	def dist(file_name):
		return os.path.join(dist_path, file_name)

	print('Updating permissions...')
	PERM_CMD= 'chmod +x {}'
	os.system(PERM_CMD.format(dist(CONSOLE_NAME)))

	print('Done')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--dist', help='Specify dist folder (default = ./dist)', type=str, default='dist')
    parser.add_argument('--rigproc', help='Build rigproc (if none is specified, all modules are built)', action='store_true')
    parser.add_argument('--rigcam', help='Build rigcam (if none is specified, all modules are built)', action='store_true')
    parser.add_argument('--rigboot', help='Build rigboot (if none is specified, all modules are built)', action='store_true')
    parser.add_argument('--rigman', help='Build rigman (if none is specified, all modules are built)', action='store_true')
    parser.add_argument('--console', help='Build console (if none is specified, all modules are built)', action='store_true')
    parser.add_argument('--nozip', help='Do not create zip file (only if both rigproc and rigboot are selected)', action='store_true')
    args = parser.parse_args()

    dist_path = args.dist

    # Build all modules if no module is specified
    build_all = not any([args.rigproc, args.rigcam, args.rigboot, args.rigman, args.console])

    if build_all or args.rigproc:
        build_rigproc(dist_path)
    if build_all or args.rigcam:
        build_rigcam(dist_path)
    if build_all or args.rigboot:
        build_rigboot(dist_path)
    if build_all or args.rigman:
        build_rigman(dist_path)
    if build_all or args.console:
        build_console(dist_path)

    if not args.nozip:
        if build_all or (args.rigproc and args.rigcam):
            create_zip(dist_path)
        else:
            print('Skipping zip file creations since both rigproc and rigcam must be built')

    print('All done.')
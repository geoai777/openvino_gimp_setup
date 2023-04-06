import subprocess
import inspect
import logging
import os
import requests
import pathlib
import distutils

def sanity_check(variable, variable_type: str) -> None:
    """
    Check strict typing, just in case
    :param variable:
    :param variable_type:
    :return:
    """
    if variable_type == 'list':
        compliance = True if isinstance(variable, list) else False
    elif variable_type == 'tuple':
        compliance = True if isinstance(variable, tuple) else False
    elif variable_type == 'str':
        compliance = True if isinstance(variable, str) else False
    elif variable_type == 'int':
        compliance = True if isinstance(variable, int) else False
    else:
        compliance = False

    if not compliance:
        # Not done via logging due to use of SystemExit.
        raise SystemExit(f'[{inspect.stack()[1].function}] variable {variable} is {type(variable)}, '
                         f'but should be of {variable_type} type.')


def download_url(url: str, directory: str):
    for v in [url, directory]:
        sanity_check(v, 'str')

    filename = url.split('/')[-1]
    filepath = os.path.join(directory, filename)

    request = requests.get(url, stream=True)
    if request.ok:
        logging.debug(f'Saving {filename} to {directory}')
        with open(filepath, 'wb') as f:
            for chunk in request.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:
        print(f' [error] Download of {url} failed!')



def load_runner(run_commands: list, encoding: str = 'utf-8') -> str:
    """
    This will run OS commands
    :return:
    """
    sanity_check(run_commands, 'list')

    process = subprocess.Popen(
        run_commands,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    ret = process.communicate()
    outs, errs = ret[0].strip().decode(encoding), ret[1].strip().decode(encoding)
    if errs:
        return errs

    return outs


def init_dir(directory_path: str) -> None:
    sanity_check(directory_path, 'str')

    if not os.path.isdir(directory_path):
        logging.debug(f'Directory {directory_path} not found. Creating...')
        os.mkdir(directory_path)


def check_success(message: str, success: tuple = ('Successfully', 'already satisfied')) -> bool:
    """
    Check message for success text
    :param message:
    :param success:
    :return:
    """
    sanity_check(message, 'str')
    sanity_check(success, 'tuple')

    ret = False
    for s in success:
        if s in message:
            ret = True
    return ret


def stop():
    raise SystemExit('Stop, stop, stop!')


class PipCommand:
    """
    Generates commands for pip. Just for convenience
    """
    def __init__(self):
        self.python = 'python'
        self.pip = [self.python, '-m', 'pip']
        self.version = [*self.pip, '--version']

    def show(self, package: str) -> list:
        sanity_check(package, 'str')

        return [*self.pip, 'show', package]

    def install(self, package: str) -> list:
        sanity_check(package, 'str')

        return [*self.pip, 'install', package]

    def remove(self, package: str) -> list:
        sanity_check(package, 'str')

        return [*self.pip, 'uninstall', '-y', package]


class PipOperation:
    def __init__(self):
        self.pip = PipCommand()
        self.version()

    def check_exists(self, package: str) -> bool:
        """
        Checks if pip package is installed
        :param package:
        :return:
        """
        sanity_check(package, 'str')

        if '==' in package:
            package = package.split('==')[0]

        return False if 'not found' in load_runner(self.pip.show(package)) else True

    def check_install(self, package: str) -> bool:
        """
        Installs specified package is does not exist
        :param package:
        :return:
        """
        sanity_check(package, 'str')

        if self.check_exists(package):
            logging.debug(f'Package {package} already exists, skipping...')
            return True
        else:
            logging.debug(f'Installing {package}...')
            ret = load_runner(self.pip.install(package))
            if not check_success(ret):
                print(ret)
            return check_success(ret)

    def remove(self, package: str) -> bool:
        """
        Removes pip package if present
        :param package:
        :return:
        """
        sanity_check(package, 'str')

        if self.check_exists(package):
            ret = load_runner(self.pip.remove(package))
            return check_success(ret)

    def version(self) -> None:
        """
        Checks if pip installed on a system
        :return:
        """
        if not load_runner(self.pip.version):
            raise SystemExit('python pip package manager does not exist, please install')


class GitCommand:
    def __init__(self):
        self.git = 'git'
        self.version = [*self.git, '--version']

    def clone(self, url: str, destination: str = '') -> list:
        """
        Generate command to clone url, possible clone to specific location
        :param url:
        :param destination:
        :return:
        """
        sanity_check(url, 'str')

        ret = [self.git, 'clone', url]
        if destination:
            sanity_check(destination, 'str')
            ret.append(destination)

        return ret


class GitOperation:
    def __init__(self):
        self.git = GitCommand()
        self.version()

    def clone(self, url: str, destination: str = '') -> bool:
        sanity_check(url, 'str')
        if destination:
            sanity_check(destination, 'str')

        print(f'Cloning {url} to {destination}')
        ret = load_runner(self.git.clone(url, destination))
        if check_success(ret, tuple('done')):
            return True

        raise SystemExit('Something went wrong.')

    def version(self) -> None:
        """
        Checks if git installed on a system
        :return:
        """
        if not load_runner(self.git.version):
            raise SystemExit('python pip package manager does not exist, please install')


class Directories:
    def __init__(self):
        workdir = os.getcwd()
        user_home_directory = pathlib.Path.home()
        self.tmp = os.path.join(workdir, 'tmp')
        self.virtualenv = 'gimpenv3'
        self.openvino_ai_plugin = os.path.join(workdir, 'openvino-ai')
        self.user_openvino_ai_plugin = os.path.join(user_home_directory, 'openvino-ai-plugins-gimp')
        self.user_weights = os.path.join(self.user_openvino_ai_plugin, 'weights')
        self.user_weights_stable_diffusion = os.path.join(self.user_weights, 'stable-diffusion-ov')


# --- [ MAIN ] -----------------------------------------------------------
def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
    )
    # [ variables ]
                                                                    # Set reinstall to True to recreate venv with --clear flag
    reinstall = False

    d = Directories()
    stable_diffusion_models_dir = os.path.join(d.tmp, 'sd_models')
    openvino_ai_plugin_url = 'https://github.com/intel/openvino-ai-plugins-gimp.git'
    stable_diffusion_models_url = 'https://huggingface.co/bes-dev/stable-diffusion-v1-4-openvino'
    patch_file_urls = [
        'https://huggingface.co/openai/clip-vit-large-patch14/raw/main/merges.txt',
        'https://huggingface.co/openai/clip-vit-large-patch14/raw/main/special_tokens_map.json',
        'https://huggingface.co/openai/clip-vit-large-patch14/raw/main/tokenizer_config.json',
        'https://huggingface.co/openai/clip-vit-large-patch14/raw/main/vocab.json'
    ]

    venv_path = os.path.join(d.openvino_ai_plugin, d.virtualenv)

    # --[ SYS ]-- init all dir structure -------------------------------------
    for this_d in [d.openvino_ai_plugin, d.tmp, d.user_openvino_ai_plugin, d.user_weights]:
        init_dir(this_d)

    logging.debug(' --[ Program started ]----- ')
    logging.debug(' --[ Installing requirements ]----- ')
    po = PipOperation()
    go = GitOperation()

    logging.debug(f'Running python {load_runner([po.pip.python, "--version"])} at {po.pip.python}')

    logging.debug(f'Git the road, Jack')
    go.clone(openvino_ai_plugin_url, d.openvino_ai_plugin)

    po.check_install('virtualenv')

    python_venv = ['python', '-m', 'virtualenv', venv_path]
    if reinstall:
        python_venv.insert(3, '--clear')

    if not os.path.isdir(venv_path) or reinstall:
        if not check_success(load_runner(python_venv), tuple('created virtual')):
            raise SystemExit('Could not install virtual environment')

    # Diving into virtual environment
    po.pip.python = os.path.join(d.virtualenv, 'Scripts', 'python')
    logging.debug(f'Virtualenv python {load_runner([po.pip.python, "--version"])} at {po.pip.python}')

    package_list = [
        'openvino==2022.3.0',
        'transformers==4.23.0',
        'diffusers==0.2.4',
        'tqdm==4.64.0',
        'huggingface_hub',
        'streamlit==1.12.0',
        'watchdog==2.1.9',
        'ftfy==6.1.1',
        d.openvino_ai_plugin
    ]

    for p in package_list:
        if not po.check_install(p):
            raise SystemExit(f'Could not install {p} package')

    logging.debug('Importing gimpopenvino weights')
    print(load_runner([po.pip.python, '-c', '"import gimpopenvino; gimpopenvino.setup_python_weights()"']))

    logging.debug(' --[ Populating user plugin directory with weights ]--')
    distutils.dir_util.copy_tree(os.path.join(d.openvino_ai_plugin, 'weights'), d.user_weights)

    logging.debug(' --[ Get Git going ]----- ')
    go.clone(stable_diffusion_models_url, d.user_weights_stable_diffusion)
    for u in patch_file_urls:
        if not os.path.isfile(os.path.join(d.user_weights_stable_diffusion, u.split('/')[-1])):
            download_url(u, d.user_weights_stable_diffusion)

    logging.debug(' --[ User related stuff ]--')


if __name__ == '__main__':
    main()

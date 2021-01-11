from sys import platform


def platform_subprocess_args():
    args = {}
    if platform == 'win32':
        args['shell'] = True

    return args

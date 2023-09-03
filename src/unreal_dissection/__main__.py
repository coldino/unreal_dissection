import sys
from logging import INFO, basicConfig, getLogger

basicConfig(level=INFO)
log = getLogger('unreal_dissection')


if __name__ == '__main__':
    from unreal_dissection import Image, fully_discover

    # Simply grab filename from commandline
    filename = sys.argv[1] if len(sys.argv) > 1 else 'Purlovia.exe'
    log.info('Beginning extraction of %s', filename)

    log.info('Loading exe...')
    image = Image(filename)

    discovery = fully_discover(image)

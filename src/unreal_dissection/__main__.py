import os
from logging import basicConfig

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
basicConfig(level=LOGLEVEL)


if __name__ == '__main__':
    # It is important that the log configuration above is completed
    # before we import anything else.

    from .cli import main

    main()

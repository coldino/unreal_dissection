from logging import INFO, basicConfig

basicConfig(level=INFO)


if __name__ == '__main__':
    # It is important that the log configuration above is completed
    # before we import anything else.

    from .cli import main

    main()

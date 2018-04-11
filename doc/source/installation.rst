Installing aMAP
===============

To install aMAP:
    #. Download or clone this repository
    #. If you downloaded the repository, extract the archive.
    #. Execute the installation script:
        .. code-block:: bash

            cd amap_python  # assuming this is where it is installed (change the path otherwise)
            pip3 install setuptools --user  # or remove --user and start with sudo to install system-wide
            # assuming you want to install the atlas use:
            python3 setup.py install --install-atlas --user

    #. If required download the test data

..    #. Download the `NiftyReg binaries <http://www.gatsby.ucl.ac.uk/%7Etest/aMAP-0.0.1.tar.gz>`__
..    #. Place these binaries inside the amap_python folder under amap_python;niftyReg;bin;
..        (the semi-colon represents the file separator on your operating system)
..    #. Download the atlas and place it under amap_python;data;atlas;

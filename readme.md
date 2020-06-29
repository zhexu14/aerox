# Overview

# Dependencies
- [gmsh](https://gmsh.info/)
- [SU2](https://su2code.github.io/)
- [naca456](http://www.pdas.com/naca456download.html)

# Setup dependencies

- Set up *naca456*. The source for this application is provided in this repository.
```bash
mkdir bin
sudo apt-get install gfortran
( cd drivers/naca456 ; gfortran naca456.f90 -o ../../bin/naca456 )
```

# Installation
```bash
sudo pip install -r python/requirements.txt
( cd python ; sudo python setup.py install )
```

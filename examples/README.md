## plugnpy examples

### Running the examples on python3

#### Create a virtual environment
To run the examples, first create a virtual env.

```sh
make clean venv3
```

This will create a virtual environment and install all the required libraries.

#### Activate the virtual environment

```sh
source venv3/bin/activate
```
#### Make the example executable

```sh
chmod +x examples/check_cpu.py
```

#### Run the example

```sh
./examples/check_cpu.py
```


### Running the examples on python2

#### Create a virtual environment
To run the examples, first create a virtual env.

```sh
make clean venv
```

This will create a virtual environment and install all the required libraries.

#### Activate the virtual environment

```sh
source venv/bin/activate
```

#### Run the example

```sh
venv/bin/python examples/check_cpu.py
```

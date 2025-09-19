To setup the repo, you need to create a virtual environment and install the required packages. Here are the steps:
```shell
pip3 install virtualenv
python3 -m venv venv
source venv/bin/activate
```

Once activated, install pip-tools:
```shell
pip3 install pip-tools
```

Then, install the required packages:
```shell
pip-sync
```

Now you can run the project:
```shell
python3 src/main.py
```

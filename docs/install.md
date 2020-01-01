## Installation  
### Raspberry Pi  
1. Install Dependencies  
    1. Raspbian

    ```
    sudo su -
    apt-get update
    apt-get install python3-matplotlib python3-scipy python3-pandas python3-serial
    pip3 install --upgrade pip
    reboot
    sudo pip3 install jupyter
    sudo ipython3 kernelspec install-self
    ```
    1. Test Install
    ```
    jupyter notebook
    ```
1. Clone Repo
```
$ git clone
```
1. Install local develop copy
```
 $ sudo python -m pip install -e [path_to_source]
```
1. Test install  
```
$ python3
>>> import meerkat
>>>
```    

### MicroPython  
Manually copy

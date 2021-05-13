# Virtual test bench

## Requirements:
* Virtualbox (https://www.virtualbox.org)
* Vagrant (https://www.vagrantup.com)
* An ssh client

## Instructions
1. Install virtualbox and vagrant.
2. Copy the configuration files to an empty folder. If you want, you can use git.
3. Open a terminal window in this new folder.
4. Instantiate and start the machine with `vagrant up`
5. To connect to the virtual machine `vagrant ssh`
6. The host machine disk is mounted in the `/vagrant` directory
7. To shut down the machine, exit the machine (`exit`) and stop it (`vagrant halt`)

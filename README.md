# NavSense-Computer-Vision-for-the-Visually-Impaired
The visually impaired rely heavily on hearing and touching (with their cane) to navigate through life. 
These senses cannot make up for the loss of vision when identifying objects in the user's path. 
In this paper, we propose NavSense, an assistive device that supplements existing technology to improve navigation and peace of mind in day to day life. 
NavSense relies on range detection, computer vision, and hardware acceleration mechanisms to provide real-time object identification and context to the user through auditory feedback. 
In particular, we use four hardware platforms -- Raspberry Pi 3 B+, Coral Accelerator, Coral Development Board, and Intel Neural Computer Stick -- to compare the efficiency of object detection in terms of time and energy during setup and inference phases.
Based on these results, it is possible to tailor the design for specific energy-accuracy requirements.
Also, we have implemented and used NavSense in real-world scenarios to show its effectiveness.

Installation Guide
==================

This guide covers how to install our software and replicate NavSense
given that you have the necessary hardware: a Raspberry Pi 3B+, the
Google Coral Accelerator, the Raspberry Pi Camera, TFMini Micro LiDAR
Module, a Micro SD card, push buttons, a switch, a battery pack, and a
set of headphones. The first section will focus on connecting all of the
hardware, and which GPIO pins need to be connected to which hardware
components. The second section discusses how to install our software,
and what dependencies need to be installed.

Installing Hardware
-------------------

Of the eight hardware components that need to be connected to the
Raspberry Pi, only three of them are interfaced via the GPIO pins. The
other five are easy to connect, and can probably be done so without
following these instructions. The Google Coral Accelerator is connected
through USB, the battery is connected to the micro USB port that is
usually used for power supply on the Raspberry Pi, the SD card is put
into the SD card slot, and the headphones are connected through the
audio jack. Finally, the Raspberry Pi Camera is connected via a ribbon
cable to the Raspberry Pi Camera port on the Raspberry Pi.

For the rest of this section, we need to be careful that the GPIO pins
are connected the the exact pins discussed here, otherwise NavSense will
not function correctly. The TFMini distance sensor is interfaced using a
serial connection. It uses a total of four wires: 5 volt, ground,
transmit (tx), and receive (rx). Clearly, we need to connect the 5v and
ground pins of the distance sensor to the 5v and ground pins of the
Raspberry Pi. The tx pin of the sensor is connected to the rx pin (pin
10) of the Raspberry Pi. Similarly, the rx pin of the sensor is
connected to the tx pin (pin 8) of the Raspberry Pi. NavSense also
utilizes three different buttons: one for forcing inference, and two for
changing volume/speaking speed.

The four buttons are all connected very similarly. On of the pins on
every button is connected to ground, and the other is connected to a
GPIO pin. NavSense also uses a switch to determine the output mode of
two of the buttons. The top pin of the swithc is connected to 3.3V, the
middle to a GPIO pin, and the third to ground. The GPIO pin numbers and
their functions are listed below:

| GPIO Pin Number | Type   | Function                           |
|-----------------|--------|------------------------------------|
| 3               | Button | Forces image capture and inference |
| 11              | Button | <mode> UP                          |
| 29              | Button | <mode> DOWN                        |
| 32              | Button | Power Off                          |
| 35              | Switch | <mode> Volume/Speaking Speed       |

Installing Software
-------------------

This section is a little bit more complicated than the Hardware section.
To begin with, download the Raspian Stretch operating system on a
personal computer. There are plenty of online resources explaining how
to download and install this OS on a Raspberry Pi. Finish the
installation on the Raspberry Pi before continuing with the following
steps (including the restart). Follow these steps in a
terminal window to complete the installation of software for NavSense:

``` {.bash language="bash" caption="Getting Started with NavSense Installation"}
cd ~
git clone https://github.com/dtokazaki/NavSense
cd NavSense/InstallScripts/
bash ./Install.sh
```

The install script does the following: updates the
Raspberry Pi, enables UART (necessary for the TFMini), installs the
Google Edge TPU API, edits a config file so NavSense runs on bootup, and
finally installs the text-to-speech library (pyttsx). At one point, the
installation for the Google Coral Edge TPU API will ask if the user
want's the Accelerator to operate at maximimum operating frequency.
Maximum operating frequency is not necessary, so enter 'n' and then
press enter. For all other inquiries, respond with yes (y). The script
will also reboot the Raspberry Pi once it finishes.

After the script has run, one file must be edited in order for the
TFMini to function correctly. Follow these instructions:\

The user will also need to enable serial for communication for the
TFMini. To do so, follow these commands on a terminal:\

With all of this finished, the NavSense program should start on reboot.
As long as all hardware components are connected in the right places,
NavSense should be fully functional. Below is the full bash script that
can also be found in the NavSense git repository. To run
the program manually (as opposed to only on reboot)

``` {.bash language="bash" caption="Installation Script for NavSense"}
#!/bin/bash

# General
sudo apt-get update -y
sudo apt-get upgrade -y
sudo rpi-update -y
sudo apt-get install vim -y

# TFMini
sudo mv /boot/config.txt temp.txt
cat temp.txt config_edits.txt > config.txt
sudo mv config.txt /boot/config.txt
rm temp.txt

# Google Coral Accelerator
cd ~/
wget https://dl.google.com/coral/edgetpu_api/edgetpu_api_latest.tar.gz -O edgetpu_api.tar.gz --trust-server-names
mv edgetpu_api* edgetpu_api.tar.gz
tar xzf edgetpu_api.tar.gz
rm edgetpu_api.tar.gz
cd edgetpu_api
bash ./install.sh

# Start program on reboot
cd ~/NavSense/InstallScripts/
sudo mv /etc/rc.local temp.txt
cat temp.txt startup.txt > rc.local
sudo mv rc.local /etc/rc.local
rm temp.txt

# pyttsx
sudo apt-get install espeak -y
pip3 install pyttsx3 


sudo reboot
```

``` {.bash language="bash" caption="How to Run NavSense Manually"}
cd ~/NavSense
python obj_detection.py
```


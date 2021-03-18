pw_eyesight_controller
By: Christopher Hyzer

Originally written: 03/2017
File updated: 03/2021

-------------
 DESCRIPTION
-------------

This code drove my Subaru EyeSight for Children project (https://youtu.be/0TgcKNAPId4).  Blog post here: https://www.bentperception.com/blog/?p=158 

There is no detailed build documentation for the hardware side of this project or a how-to on the code; basic requirements are outlined below.  It provides a very crude collision-avoidance mechanism for children's battery-powered cars (often referred to as PowerWheels, even if the vehicle is not made by Fisher-Price).  In addition, it drives Generation 6 (2015-2019) Subaru Legacy combination meter displays via the CAN bus to provide feedback to the driver.

Subaru, EyeSight, Fisher-Price, and PowerWheels are trademarks owned by their respective companies.  They're used here for comparison and reference purposes only.

------------
 COMPONENTS
------------

To build this project, you'll need basic circuit design and build skills and the following:

* A child's ride-on car.  12V cars are preferred, as are those with high and low speeds.
* A Raspberry Pi 2 or higher.  This acts as the brain of the project.  The Pi must be running Linux
* A LIDAR-Lite v3 (https://www.sparkfun.com/products/14032)
* A GlobalSat USB GPS receiver (used to drive the speedometer)
* A Pi-CAN 2 CAN bus hat for your Pi to interface with the Subaru Combination Meter.
* A combination meter assembly (with EyeSight displays) from an EyeSight-enabled 2015-2019 Subaru Legacy
* The wiring harness for the combination meter (a 5th Generation 2010-2014 harness will work)
* Pinout information for the combination meter (can be found on Subaru's technical documentation site for a fee)
* A protoboard or other platform onto which you can build your interface circuits between the Pi and vehicle (be careful, most cars run on 12V, so you'll need to create voltage diving circuitry to avoid blowing up the other components).
* Relays to cut off the high-speed and low speed stages of the vehicle's drive system as-triggered by the script.
* Time, wire, components for your interface circuitry, solder, a soldering iron, patience, and more time.
* Children to allow you to test your creation.

The code outlines how inputs are taken from GPIO pins, and for my implementation, which pins are associated with a particular function.

---------
 SUPPORT
---------

As-noted, this code is unsupported in every sense of the word.  I'm unable to provide specific support to getting it to run and build a working vehicle.

This is a very crude implementation of a collision avoidance system that uses a Subaru combination meter's EyeSight displays to provide feedback.  I wrote this code in 2017 and haven't touched it since; many details of this project are lost to time.  Therefore, any questions you may ask will likely go unanswered.

-------------
 LIMITATIONS
-------------

LIDAR is a direct line-of-sight tool and is easily confused by surfaces that are not completely solid.  In addition, reflective surfaces can trip it up.  Therefore, object detection is very crude.  

Please note that different generations of Subaru vehicles use different schemes for addressing messages on the CAN bus; therefore a newer or older generation combination meter will most assuredly not work with this application without significant time spent determining what your particular combination meter expects.  A feed from a working vehicle is needed at a minimum to be able to how to manipulate any other cluster/combination meter.

---------
 LICENSE
---------
    See LICENSE.TXT for details about the license for this software.

    pw_eyesight_controller - A collision avoidance system for children's ride-on toys using Subaru EyeSight displays.
    Copyright (C) 2017 Christopher Hyzer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

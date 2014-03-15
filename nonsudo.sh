#!/bin/bash
gpio-admin export 4
gpio-admin export 14
gpio-admin export 15

sudo python  backpack.py

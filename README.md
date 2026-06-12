# Python script that automatically decrypts ps3 isos using ps3dec


Get decryption keys here https://ps3.aldostools.org/dkey.html

I made a eboot.bin decryption script as well since most of my ISOs didn't work on RPCS3.

Install ps3dec-git from AUR or https://github.com/al3xtjames/PS3Dec

The new fork made with Rust uses different syntax and isn't supported.

AUR version puts the binary to /usr/bin and the script expects that PS3Dec (notice capitalization) is located there.

PS3dec.exe is included in the repo since it hasn't been updated in 7 years.

PS3De github https://github.com/al3xtjames/PS3Dec

PS3Dec binary https://www.romhacking.net/utilities/1456/

Made with AI for my personal use but wanted to put it public

This repo contains following 3rd party binaries:
PS3sce https://github.com/BitEdits/ps3sce

There's likely some stuff that hasn't been configured universally and you need to edit the script.

# Windows setup

Install pipx https://pipx.pypa.io/latest/installation/ (if you get warnings follow the installation steps)

Install tqdm using pipx

pipx install tqdm

# Usage

## Linux
```bash
python3 ps3dec-linux.py --help
```

## Windows
```bash
python ps3dec-windows.py --help
```

# Planned features
Splitting isos for FAT32 HDDs ✅ (use `--split` / `-s` flag)

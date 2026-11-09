#!/usr/bin/env python3
"""Install a guarded image pipeline into the disposable source checkout only."""
from pathlib import Path
import shutil
import sys

root, guard = map(Path, sys.argv[1:])
image_dir = root / 'target/linux/qualcommbe/image'
makefile = image_dir / 'Makefile'
device_file = image_dir / 'ipq95xx.mk'
make_text = makefile.read_text()
device_text = device_file.read_text()
include = 'include $(SUBTARGET).mk\n'
block_start = 'define Device/askey_sbe1v1k\n'
block_end = '\nendef'
if make_text.count(include) != 1 or device_text.count(block_start) != 1:
    raise SystemExit('Upstream image layout changed; cannot safely install SBE1V1K rootfs guard')
start = device_text.index(block_start)
end = device_text.find(block_end, start)
if end < 0:
    raise SystemExit('SBE1V1K device definition is incomplete')
block = device_text[start:end]
hook = '\t$(call Device/EmmcImage)\n'
if block.count(hook) != 1:
    raise SystemExit('SBE1V1K eMMC image recipe changed; cannot safely install guard')
# Preserve the current eMMC recipes, inserting the check after padding and before packaging.
old_factory = '\tIMAGE/factory.bin := append-rootfs | pad-rootfs | pad-to 64k\n'
old_upgrade = '\tIMAGE/sysupgrade.bin/squashfs := append-rootfs | pad-to 64k | sysupgrade-tar rootfs=$$$$@ | append-metadata\n'
if make_text.count(old_factory) != 1 or make_text.count(old_upgrade) != 1:
    raise SystemExit('Upstream eMMC image recipes changed; cannot safely install guard')
new_hook = hook + old_factory.replace(' | pad-to 64k', ' | pad-to 64k | sbe-rootfs-guard') + old_upgrade.replace(' | sysupgrade-tar', ' | sbe-rootfs-guard | sysupgrade-tar')
block = block.replace(hook, new_hook)
new_device_text = device_text[:start] + block + device_text[end:]
new_make_text = make_text.replace(include, 'define Build/sbe-rootfs-guard\n\tsh $(TOPDIR)/scripts/sbe-rootfs-guard.sh $@\nendef\n\n' + include)
script_dest = root / 'scripts/sbe-rootfs-guard.sh'
shutil.copyfile(guard, script_dest)
makefile.write_text(new_make_text)
device_file.write_text(new_device_text)
print('Installed 122 MiB padded rootfs guard for SBE1V1K in temporary source tree')

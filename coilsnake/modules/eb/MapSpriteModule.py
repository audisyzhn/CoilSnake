import yaml

from coilsnake.modules.eb.EbTablesModule import EbTable
from coilsnake.modules.eb.EbDataBlocks import DataBlock
from coilsnake.Progress import updateProgress
from coilsnake.modules.eb import EbModule


class SpritePlacement:
    def __init__(self, npcID, x, y):
        self.npcID = npcID
        self.x = x
        self.y = y


class MapSpriteModule(EbModule.EbModule):
    NAME = "Map Sprites"
    _PTR_LOC = 0x2261

    def __init__(self):
        EbModule.EbModule.__init__(self)
        self._ptrTbl = EbTable(0xCF61E7)
        self._entries = []

    def read_from_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        ptr = EbModule.toRegAddr(rom.read_multi(self._PTR_LOC, 3))
        updateProgress(5)
        self._ptrTbl.readFromRom(rom, ptr)
        pct = 45.0 / (40 * 32)
        for i in range(self._ptrTbl.height()):
            loc = self._ptrTbl[i, 0].val()
            # Format: AA AA [BB BB YY XX]
            # AA = # of entries. BB = TPT. YY = y pos. XX = x pos.
            if loc != 0:
                loc |= 0x0F0000
                entry = []
                size = rom.read_multi(loc, 2)
                loc += 2
                for j in range(size):
                    entry.append(SpritePlacement(
                        rom.read_multi(loc, 2),
                        rom[loc + 3], rom[loc + 2]))
                    loc += 4
                self._entries.append(entry)
            else:
                self._entries.append(None)
            updateProgress(pct)

    def write_to_project(self, resourceOpener):
        out = dict()
        x = y = 0
        rowOut = dict()
        pct = 45.0 / (40 * 32)
        for entry in self._entries:
            if entry is not None:
                rowOut[x % 32] = map(
                    lambda sp: {
                        "NPC ID": sp.npcID,
                        "X": sp.x,
                        "Y": sp.y},
                    entry)
            else:
                rowOut[x % 32] = None
            if (x % 32) == 31:
                # Start next row
                out[y] = rowOut
                x = 0
                y += 1
                rowOut = dict()
            else:
                x += 1
            updateProgress(pct)
        with resourceOpener("map_sprites", "yml") as f:
            yaml.dump(out, f, Dumper=yaml.CSafeDumper)
        updateProgress(5)

    def read_from_project(self, resourceOpener):
        self._entries = []
        pct = 45.0 / (40 * 32)
        with resourceOpener("map_sprites", "yml") as f:
            input = yaml.load(f, Loader=yaml.CSafeLoader)
            updateProgress(5)
            for y in input:
                row = input[y]
                for x in row:
                    if row[x] is None:
                        self._entries.append(None)
                    else:
                        self._entries.append(map(lambda x: SpritePlacement(
                            x["NPC ID"], x["X"], x["Y"]),
                                                 row[x]))
                    updateProgress(pct)

    def write_to_rom(self, rom):
        """
        @type rom: coilsnake.data_blocks.Rom
        """
        self._ptrTbl.clear(32 * 40)
        writeLoc = 0xf61e7
        writeRangeEnd = 0xf8984
        i = 0
        pct = 45.0 / (40 * 32)
        for entry in self._entries:
            if (entry is None) or (not entry):
                self._ptrTbl[i, 0].setVal(0)
            else:
                entryLen = len(entry)
                with DataBlock(2 + entryLen * 4) as block:
                    block[0] = entryLen & 0xff
                    block[1] = entryLen >> 8
                    j = 2
                    for sprite in entry:
                        block[j] = sprite.npcID & 0xff
                        block[j + 1] = sprite.npcID >> 8
                        block[j + 2] = sprite.y
                        block[j + 3] = sprite.x
                        j += 4
                    if writeLoc + len(block) > writeRangeEnd:
                        # TODO Error, not enough space
                        raise RuntimeError("Not enough map sprite space")
                    else:
                        block.writeToRom(rom, writeLoc)
                        self._ptrTbl[i, 0].setVal(writeLoc & 0xffff)
                        writeLoc += len(block)
            updateProgress(pct)
            i += 1
        loc = self._ptrTbl.writeToFree(rom)
        rom.write_multi(self._PTR_LOC, EbModule.toSnesAddr(loc), 3)
        # Mark any remaining space as free
        if writeLoc < writeRangeEnd:
            rom.deallocate((writeLoc, writeRangeEnd))
        updateProgress(5)

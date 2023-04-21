from io import BufferedIOBase
from typing import Union, Tuple


class WaveFile:
    def __init__(self, f: BufferedIOBase) -> None:
        assert f.readable(), "file must be readable"
        assert f.seekable(), "file must be seekable"
        assert f.writable(), "file must be writable"

        f.seek(0)
        riffKeyword = f.read(4)
        assert riffKeyword == b"RIFF", "must be a RIFF"

        riffLength = f.read(4)
        riffType = f.read(4)
        assert riffType == b"WAVE", "must be a wave file"
        
        fmtSubchunkType = f.read(4)
        assert fmtSubchunkType == b"fmt ", "missing fmt chunk"
        
        fmtChunkLength = f.read(4)
        
        audioFormat = int.from_bytes(f.read(2), "little")
        assert audioFormat == 1, "cannot handle non-PCM type file"
        
        numChannels = int.from_bytes(f.read(2), "little")
        assert numChannels in (1, 2), f"bad channel number: {numChannels}"
        self.numChannels = numChannels

        self.sampleRate = int.from_bytes(f.read(4), "little")
        byteRate = f.read(4)
        self.blockAlign = int.from_bytes(f.read(2), "little")
        self.bitsPerSample = int.from_bytes(f.read(2), "little")
        assert self.bitsPerSample in (8, 16), "bit depth must be 8 or 16"

        dataChunkType = f.read(4)
        assert dataChunkType == b"data", "missing data chunk"
        
        dataChunkLength = int.from_bytes(f.read(4), "little")
        assert dataChunkLength % self.blockAlign == 0, "invalid ending boundary"
        self.numSamples = dataChunkLength // self.blockAlign

        self.dataStart = f.tell()


    def __getitem__(self, i: int) -> Union[int, Tuple[int, int]]:
        assert type(i) == int, f"cannot index file with {type(i)}"
        if i < 0 or i >= self.numSamples:
            raise IndexError(f"index {i} is out of range")
        
        f.seek(self.dataStart + self.blockAlign * i)
        sample = f.read(self.blockAlign)
        if self.bitsPerSample == 8:
            signed = False
        elif self.bitsPerSample == 16:
            signed = True
        if self.numChannels == 1:
            return int.from_bytes(sample, "little", signed=signed)
        elif self.numChannels == 2:
            return int.from_bytes(sample[:self.blockAlign//2], "little", signed=signed), int.from_bytes(sample[self.blockAlign//2:], "little", signed=signed)
        
    
    def __setitem__(self, i: int, val: int) -> None:
        assert type(i) == int, f"cannot index file with {type(i)}"
        if i < 0 or i >= self.numSamples:
            raise IndexError(f"index {i} is out of range")
        
        f.seek(self.dataStart + self.blockAlign * i)
        if self.bitsPerSample == 8:
            signed = False
        elif self.bitsPerSample == 16:
            signed = True
        if self.numChannels == 1:
            f.write(val.to_bytes(self.blockAlign, "little", signed=signed))
        elif self.numChannels == 2:
            for sample in val:
                f.write(sample.to_bytes(self.blockAlign//2, "little", signed=signed))

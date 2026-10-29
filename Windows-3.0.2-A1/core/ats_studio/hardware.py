"""Offline physical-core/RAM worker defaults, with conservative fallbacks."""
import ctypes, os
from functools import lru_cache

@lru_cache(maxsize=1)
def machine_resources():
    cores=max(1,(os.cpu_count() or 2)//2);available=2*1024**3
    if os.name=='nt':
        size=ctypes.c_ulong(0)
        ctypes.windll.kernel32.GetLogicalProcessorInformationEx(0,None,ctypes.byref(size))
        buffer=ctypes.create_string_buffer(size.value)
        if ctypes.windll.kernel32.GetLogicalProcessorInformationEx(0,buffer,ctypes.byref(size)):
            pos=0;found=0
            while pos+8<=size.value:
                relationship=ctypes.c_ulong.from_buffer(buffer,pos).value
                length=ctypes.c_ulong.from_buffer(buffer,pos+4).value
                if length<8:break
                found+=relationship==0;pos+=length
            if found:cores=found
        class Memory(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(name,ctypes.c_ulonglong) for name in ['total','available','page_total','page_available','virtual_total','virtual_available','extended']]
        memory=Memory();memory.length=ctypes.sizeof(memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):available=memory.available
    return {'physical_cores':cores,'available_ram_bytes':available}

def default_workers():
    info=machine_resources()
    return max(1,min(8,info['physical_cores']-1,max(1,(info['available_ram_bytes']-512*1024**2)//(512*1024**2))))

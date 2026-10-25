"""Owned server process Job, extracted from the existing validated launcher helper."""
import ctypes,os
from ctypes import wintypes

class OwnedWindowsJob:
    def __init__(self, process):
        if os.name != 'nt':
            raise RuntimeError('Owned stdio reader is currently validated on Windows only')
        class Basic(ctypes.Structure):
            _fields_=[('processTime',ctypes.c_longlong),('jobTime',ctypes.c_longlong),('flags',wintypes.DWORD),
                      ('minimumWorkingSet',ctypes.c_size_t),('maximumWorkingSet',ctypes.c_size_t),
                      ('activeProcesses',wintypes.DWORD),('affinity',ctypes.c_size_t),
                      ('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_=[(key,ctypes.c_ulonglong) for key in ('readOps','writeOps','otherOps','readBytes','writeBytes','otherBytes')]
        class Extended(ctypes.Structure):
            _fields_=[('basic',Basic),('io',IO),('processMemory',ctypes.c_size_t),('jobMemory',ctypes.c_size_t),
                      ('peakProcessMemory',ctypes.c_size_t),('peakJobMemory',ctypes.c_size_t)]
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];self.api.CreateJobObjectW.restype=wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD];self.api.SetInformationJobObject.restype=wintypes.BOOL
        self.api.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p];self.api.QueryInformationJobObject.restype=wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];self.api.AssignProcessToJobObject.restype=wintypes.BOOL
        self.api.CloseHandle.argtypes=[wintypes.HANDLE];self.api.CloseHandle.restype=wintypes.BOOL
        self.handle=self.api.CreateJobObjectW(None,None)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        limits=Extended();limits.basic.flags=0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)) or not self.api.AssignProcessToJobObject(self.handle,wintypes.HANDLE(int(process._handle))):
            error=ctypes.WinError(ctypes.get_last_error());self.close();raise error
        actual=Extended()
        if not self.api.QueryInformationJobObject(self.handle,9,ctypes.byref(actual),ctypes.sizeof(actual),None) or not actual.basic.flags&0x2000:
            self.close();raise RuntimeError("Owned job kill-on-close policy was not applied")
        self.limit_flags=actual.basic.flags
    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None


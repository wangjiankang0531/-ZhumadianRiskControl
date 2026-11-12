"""Own a Windows process tree without an implicit terminate-on-close policy.

The caller must request normal component shutdown and retain this job until its
actual active-process count is zero. Creation failure never kills the child.
"""
import ctypes, os
from ctypes import wintypes


class OwnedWindowsJob:
    def __init__(self, process):
        if os.name != 'nt':
            raise RuntimeError('WINDOWS_OWNED_JOB_REQUIRED')
        class Basic(ctypes.Structure):
            _fields_=[('processTime',ctypes.c_longlong),('jobTime',ctypes.c_longlong),('flags',wintypes.DWORD),
                      ('minimumWorkingSet',ctypes.c_size_t),('maximumWorkingSet',ctypes.c_size_t),
                      ('activeProcesses',wintypes.DWORD),('affinity',ctypes.c_size_t),
                      ('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_=[(key,ctypes.c_ulonglong)for key in ('readOps','writeOps','otherOps','readBytes','writeBytes','otherBytes')]
        class Extended(ctypes.Structure):
            _fields_=[('basic',Basic),('io',IO),('processMemory',ctypes.c_size_t),('jobMemory',ctypes.c_size_t),
                      ('peakProcessMemory',ctypes.c_size_t),('peakJobMemory',ctypes.c_size_t)]
        class Accounting(ctypes.Structure):
            _fields_=[('totalUserTime',ctypes.c_longlong),('totalKernelTime',ctypes.c_longlong),
                      ('periodUserTime',ctypes.c_longlong),('periodKernelTime',ctypes.c_longlong),
                      ('pageFaults',wintypes.DWORD),('totalProcesses',wintypes.DWORD),
                      ('activeProcesses',wintypes.DWORD),('terminatedProcesses',wintypes.DWORD)]
        self.Accounting=Accounting
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];self.api.CreateJobObjectW.restype=wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD];self.api.SetInformationJobObject.restype=wintypes.BOOL
        self.api.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p];self.api.QueryInformationJobObject.restype=wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];self.api.AssignProcessToJobObject.restype=wintypes.BOOL
        self.api.CloseHandle.argtypes=[wintypes.HANDLE];self.api.CloseHandle.restype=wintypes.BOOL
        self.handle=self.api.CreateJobObjectW(None,None)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        self.limit_flags=0
        try:
            limits=Extended();limits.basic.flags=0
            if not self.api.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            actual=Extended()
            if not self.api.QueryInformationJobObject(self.handle,9,ctypes.byref(actual),ctypes.sizeof(actual),None):
                raise ctypes.WinError(ctypes.get_last_error())
            if actual.basic.flags!=0:raise RuntimeError('EXACT_NON_TERMINATING_JOB_POLICY_REQUIRED')
            if not self.api.AssignProcessToJobObject(self.handle,wintypes.HANDLE(int(process._handle))):
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            # This job never received a terminate-on-close flag, including before assignment.
            self.api.CloseHandle(self.handle);self.handle=None
            raise

    def active_processes(self):
        if self.handle is None:return 0
        value=self.Accounting()
        if not self.api.QueryInformationJobObject(self.handle,1,ctypes.byref(value),ctypes.sizeof(value),None):
            raise ctypes.WinError(ctypes.get_last_error())
        return value.activeProcesses

    def close(self):
        if self.handle is None:return
        if self.active_processes()!=0:raise RuntimeError('LIVE_OWNED_JOB_MUST_BE_RETAINED')
        if not self.api.CloseHandle(self.handle):raise ctypes.WinError(ctypes.get_last_error())
        self.handle=None

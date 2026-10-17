// Shared OS locks protect marker-to-decode handoff and all derived file reads.
#ifdef _WIN32
class ZhumadianCacheReadLock {
public:
  explicit ZhumadianCacheReadLock(const fs::path& path) {
    fs::create_directories(path.parent_path());
    file_ = CreateFileW(path.c_str(),
                        GENERIC_READ | GENERIC_WRITE,
                        FILE_SHARE_READ | FILE_SHARE_WRITE,
                        nullptr,
                        OPEN_ALWAYS,
                        FILE_ATTRIBUTE_NORMAL,
                        nullptr);
    if (file_ == INVALID_HANDLE_VALUE)
      throw std::runtime_error("Cannot open derived cache reader lock");
    const ULONGLONG deadline = GetTickCount64() + 100000;
    while (!LockFileEx(file_, LOCKFILE_FAIL_IMMEDIATELY, 0, 1, 0, &overlap_)) {
      const DWORD error = GetLastError();
      if ((error != ERROR_LOCK_VIOLATION && error != ERROR_SHARING_VIOLATION) || GetTickCount64() >= deadline) {
        CloseHandle(file_);
        file_ = INVALID_HANDLE_VALUE;
        throw std::runtime_error("Derived cache reader lock unavailable");
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(25));
    }
  }
  ~ZhumadianCacheReadLock() {
    if (file_ != INVALID_HANDLE_VALUE) {
      UnlockFileEx(file_, 0, 1, 0, &overlap_);
      CloseHandle(file_);
    }
  }
  ZhumadianCacheReadLock(const ZhumadianCacheReadLock&) = delete;
  ZhumadianCacheReadLock& operator=(const ZhumadianCacheReadLock&) = delete;

private:
  HANDLE file_ = INVALID_HANDLE_VALUE;
  OVERLAPPED overlap_{};
};
#endif

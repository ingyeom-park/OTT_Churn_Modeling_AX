# Gemini CLI 자격증명에서 API 키를 읽어서 streamlit 실행
$key = python -c "
import ctypes, ctypes.wintypes
class CREDENTIAL(ctypes.Structure):
    _fields_ = [('Flags',ctypes.wintypes.DWORD),('Type',ctypes.wintypes.DWORD),('TargetName',ctypes.c_wchar_p),('Comment',ctypes.c_wchar_p),('LastWritten',ctypes.wintypes.FILETIME),('CredentialBlobSize',ctypes.wintypes.DWORD),('CredentialBlob',ctypes.c_char_p),('Persist',ctypes.wintypes.DWORD),('AttributeCount',ctypes.wintypes.DWORD),('Attributes',ctypes.c_void_p),('TargetAlias',ctypes.c_wchar_p),('UserName',ctypes.c_wchar_p)]
cred_ptr = ctypes.pointer(CREDENTIAL())
ctypes.windll.advapi32.CredReadW('gemini-cli-api-key/default-api-key', 1, 0, ctypes.byref(cred_ptr))
b = cred_ptr.contents.CredentialBlob
print(b[:cred_ptr.contents.CredentialBlobSize].decode('utf-16-le'))
"
$env:GEMINI_API_KEY = $key
streamlit run app.py

Set objShell = CreateObject("WScript.Shell")
' Dapatkan path folder saat ini
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Ubah direktori kerja ke folder backend
objShell.CurrentDirectory = strPath & "\node\backend"

' Jalankan file run.bat secara tersembunyi (0) tanpa menahan script (False)
objShell.Run "cmd.exe /c run.bat", 0, False

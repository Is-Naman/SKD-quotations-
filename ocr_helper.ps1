[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null

$runtimeAssembly = [System.IO.Path]::Combine([System.Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory(), "System.Runtime.WindowsRuntime.dll")
[System.Reflection.Assembly]::LoadFile($runtimeAssembly) | Out-Null

function Invoke-WinRtAsync($asyncOp, $typeInput) {
    $resultType = $typeInput
    if ($typeInput -is [string]) {
        $typeName = $typeInput.Trim("[]")
        $resultType = "$typeName, Windows.Foundation, ContentType=WindowsRuntime" -as [Type]
        if ($null -eq $resultType) {
            $resultType = $typeName -as [Type]
        }
    }
    
    $asTaskMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
        $_.Name -eq 'AsTask' -and 
        $_.IsGenericMethod -and 
        $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name.StartsWith("IAsyncOperation")
    } | Select-Object -First 1
    
    $closedMethod = $asTaskMethod.MakeGenericMethod($resultType)
    $task = $closedMethod.Invoke($null, @($asyncOp))
    return $task.GetAwaiter().GetResult()
}

$file = $args[0]
if ($null -eq $file -or -not (Test-Path $file)) {
    Write-Error "Invalid file path."
    exit 1
}

$imageBytes = [System.IO.File]::ReadAllBytes($file)
$stream = [Windows.Storage.Streams.InMemoryRandomAccessStream]::new()
$writer = [Windows.Storage.Streams.DataWriter]::new($stream.GetOutputStreamAt(0))
$writer.WriteBytes($imageBytes)

$asyncStore = $writer.StoreAsync()
while ($asyncStore.Status -eq 'Started') { Start-Sleep -Milliseconds 10 }
$asyncStore.GetResults() | Out-Null
$writer.DetachStream() | Out-Null

$stream.Seek(0)
$asyncDecoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
$decoder = Invoke-WinRtAsync $asyncDecoder ([Windows.Graphics.Imaging.BitmapDecoder])

$asyncSoftwareBitmap = $decoder.GetSoftwareBitmapAsync()
$bitmap = Invoke-WinRtAsync $asyncSoftwareBitmap ([Windows.Graphics.Imaging.SoftwareBitmap])

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
    Write-Error "Failed to create OCR engine."
    exit 1
}

$asyncOcr = $engine.RecognizeAsync($bitmap)
$result = Invoke-WinRtAsync $asyncOcr ([Windows.Media.Ocr.OcrResult])
Write-Output $result.Text

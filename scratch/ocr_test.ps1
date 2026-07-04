[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null

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
$writer.DetachStream() | Out-Null

$stream.Seek(0)
$asyncDecoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
while ($asyncDecoder.Status -eq 'Started') { Start-Sleep -Milliseconds 10 }
$decoder = $asyncDecoder.GetResults()

$asyncSoftwareBitmap = $decoder.GetSoftwareBitmapAsync()
while ($asyncSoftwareBitmap.Status -eq 'Started') { Start-Sleep -Milliseconds 10 }
$bitmap = $asyncSoftwareBitmap.GetResults()

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) {
    Write-Error "Failed to create OCR engine."
    exit 1
}

$asyncOcr = $engine.RecognizeAsync($bitmap)
while ($asyncOcr.Status -eq 'Started') { Start-Sleep -Milliseconds 10 }
$result = $asyncOcr.GetResults()
Write-Output $result.Text

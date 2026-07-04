$source = @"
using System;
using System.IO;
using System.Threading.Tasks;

public class WinOcr {
    public static string Recognize(string file) {
        return RecognizeAsync(file).GetAwaiter().GetResult();
    }
    private static async Task<string> RecognizeAsync(string file) {
        var bytes = File.ReadAllBytes(file);
        using (var stream = new Windows.Storage.Streams.InMemoryRandomAccessStream()) {
            using (var writer = new Windows.Storage.Streams.DataWriter(stream.GetOutputStreamAt(0))) {
                writer.WriteBytes(bytes);
                await writer.StoreAsync();
            }
            stream.Seek(0);
            var decoder = await Windows.Graphics.Imaging.BitmapDecoder.CreateAsync(stream);
            var bitmap = await decoder.GetSoftwareBitmapAsync();
            var engine = Windows.Media.Ocr.OcrEngine.TryCreateFromUserProfileLanguages();
            if (engine == null) return "Error: Failed to create OCR engine";
            var result = await engine.RecognizeAsync(bitmap);
            return result.Text;
        }
    }
}
"@

# Load the WinRT runtime reference Assemblies
$windowsWinmd = "$env:windir\System32\WinMetadata\Windows.Media.winmd"
$runtimeAssembly = [System.IO.Path]::Combine([System.Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory(), "System.Runtime.WindowsRuntime.dll")

Add-Type -TypeDefinition $source -ReferencedAssemblies $windowsWinmd, $runtimeAssembly -ErrorAction Stop

$file = $args[0]
if ($null -eq $file -or -not (Test-Path $file)) {
    Write-Error "Invalid file path."
    exit 1
}

$text = [WinOcr]::Recognize((Get-Item $file).FullName)
Write-Output $text

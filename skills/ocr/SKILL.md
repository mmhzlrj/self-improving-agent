---
name: ocr
description: 使用 macOS Vision 框架本地识别图片文字（隐私安全）
---

# OCR Skill

当用户要求识别图片中的文字时使用。

## 使用方式

调用 exec 执行 Swift 本地 OCR：

```bash
swift << 'EOF'
import Foundation
import Vision
import AppKit

let imagePath = "图片实际路径"

guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("Cannot load image")
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = true

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])

do {
    try handler.perform([request])
    guard let observations = request.results else { exit(0) }
    for observation in observations {
        if let topCandidate = observation.topCandidates(1).first {
            print(topCandidate.string)
        }
    }
} catch {
    print("OCR Error: \(error)")
    exit(1)
}
EOF
```

## 依赖

- macOS 内置的 Swift
- Vision 框架（系统自带）
- **无需网络连接**
- **无需外部 API**，隐私安全

## 注意

- 第一次运行会编译标准库（约1分钟），之后会很快
- 识别效果取决于图片质量和文字清晰度

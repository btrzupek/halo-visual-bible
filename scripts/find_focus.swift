// Points of interest for the /read Ken Burns frames, using macOS Vision (no installs).
// swift scripts/find_focus.swift img1.webp img2.webp ... > focus.json
// Per image: faces (largest first) and attention-saliency boxes, all as [x, y, w, h] fractions,
// origin top-left.
import Foundation
import Vision
import ImageIO

func boxes(_ rects: [CGRect]) -> [[Double]] {
    rects.map { r in [Double(r.minX), Double(1 - r.maxY), Double(r.width), Double(r.height)].map { ($0 * 1000).rounded() / 1000 } }
}
var out: [String: Any] = [:]
for path in CommandLine.arguments.dropFirst() {
    guard let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let img = CGImageSourceCreateImageAtIndex(src, 0, nil) else { continue }
    let faces = VNDetectFaceRectanglesRequest()
    let sal = VNGenerateAttentionBasedSaliencyImageRequest()
    try? VNImageRequestHandler(cgImage: img, options: [:]).perform([faces, sal])
    let f = (faces.results ?? []).map { $0.boundingBox }.sorted { $0.width * $0.height > $1.width * $1.height }
    let s = (sal.results?.first?.salientObjects ?? []).sorted { $0.confidence > $1.confidence }.map { $0.boundingBox }
    out[(path as NSString).lastPathComponent] = ["faces": boxes(f), "salient": boxes(s)]
}
let data = try! JSONSerialization.data(withJSONObject: out, options: [.sortedKeys])
FileHandle.standardOutput.write(data)

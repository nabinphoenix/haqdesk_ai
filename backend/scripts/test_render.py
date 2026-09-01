import fitz

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" viewBox="0 0 400 200">
  <rect width="400" height="200" fill="#ffffff"/>
  <rect x="20" y="20" width="360" height="160" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
  <text x="200" y="105" font-family="Arial" font-size="16" fill="#0f172a" text-anchor="middle" font-weight="bold">HaqDesk AI Architecture Test</text>
</svg>"""

with open("test_arch.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

doc = fitz.open("test_arch.svg")
pix = doc[0].get_pixmap(dpi=300)
pix.save("test_arch.png")
print(f"Rendered successfully: {pix.width}x{pix.height}")
